from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime
from importlib import util
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
import json

from .models import NicheCard, ProjectIdea, Signal, TopicMomentum

STOPWORDS = {
    "the",
    "a",
    "of",
    "and",
    "to",
    "in",
    "for",
    "with",
    "on",
    "at",
    "by",
    "from",
    "about",
    "into",
    "through",
    "over",
    "after",
    "is",
    "are",
    "an",
    "new",
    "art",
    "arts",
}


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    text = path.read_text()

    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore

            return yaml.safe_load(text) or {}
        except ModuleNotFoundError:
            # Fall back to JSON so the tool still works without PyYAML, but explain the issue.
            try:
                return json.loads(text)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "Install PyYAML or provide config as JSON; could not parse YAML file."
                ) from exc

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON config at {path}") from exc


def parse_date(value: str) -> date:
    try:
        return datetime.fromisoformat(value).date()
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date for signal: {value}") from exc


def load_signals(path: Path) -> List[Signal]:
    raw_items = json.loads(path.read_text())
    if not isinstance(raw_items, list):
        raise ValueError("Signals file must contain a JSON array of signal objects")

    signals: List[Signal] = []
    required_fields = {"title", "source", "published_at", "summary"}
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            raise ValueError(f"Signal at index {index} is not an object")

        missing = required_fields - item.keys()
        if missing:
            raise ValueError(f"Signal at index {index} missing required fields: {', '.join(sorted(missing))}")

        signals.append(
            Signal(
                title=str(item["title"]).strip(),
                source=str(item["source"]).strip(),
                published_at=parse_date(str(item["published_at"])),
                summary=str(item["summary"]).strip(),
                url=item.get("url"),
                tags=[str(tag).lower().strip() for tag in item.get("tags", []) if str(tag).strip()],
            )
        )

    return signals


def days_ago(published_at: date, today: date) -> int:
    return (today - published_at).days


def tokenize(text: str) -> List[str]:
    tokens: List[str] = []
    for raw in text.replace("/", " ").replace("-", " ").split():
        token = "".join(ch for ch in raw.lower() if ch.isalpha())
        if len(token) < 3 or token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def topic_weights(signals: Iterable[Signal], today: date) -> Dict[str, float]:
    weights: Dict[str, float] = defaultdict(float)
    for signal in signals:
        recency = days_ago(signal.published_at, today)
        recency_factor = 1 / (1 + recency / 30)
        topics = signal.tags or tokenize(signal.title + " " + signal.summary)
        for topic in topics:
            weights[topic] += recency_factor
    return weights


def select_top_topics(signals: List[Signal], today: date, limit: int) -> List[TopicMomentum]:
    weights = topic_weights(signals, today)
    counter = Counter(weights)
    top_topics: List[TopicMomentum] = []
    for name, weight in counter.most_common(limit):
        related = [s for s in signals if name in s.tags or name in tokenize(s.title + " " + s.summary)]
        top_topics.append(TopicMomentum(name=name, weight=round(weight, 2), signals=related))
    return top_topics


def horizon_split(signals: List[Signal], today: date) -> Tuple[List[Signal], List[Signal], List[Signal]]:
    horizon_90d: List[Signal] = []
    horizon_1y: List[Signal] = []
    horizon_3y: List[Signal] = []
    for signal in signals:
        age = days_ago(signal.published_at, today)
        if age <= 90:
            horizon_90d.append(signal)
        if age <= 365:
            horizon_1y.append(signal)
        if age <= 365 * 3:
            horizon_3y.append(signal)
    return horizon_90d, horizon_1y, horizon_3y


def build_niche_cards(signals: List[Signal], today: date, limit: int = 5) -> List[NicheCard]:
    weights = topic_weights(signals, today)
    niche_candidates = {
        topic: weight
        for topic, weight in weights.items()
        if weight < 3 and weight > 0.6
    }
    ranked = sorted(niche_candidates.items(), key=lambda item: item[1], reverse=True)
    cards: List[NicheCard] = []
    for topic, weight in ranked[:limit]:
        recent_signals = [s for s in signals if topic in s.tags or topic in tokenize(s.title + " " + s.summary)]
        sample = recent_signals[0] if recent_signals else None
        why_now = (
            f"Signals show fast uptick over the last quarter (weight {weight:.2f}); low competition keywords." if sample else ""
        )
        audience = "Curious publics + curators tracking AI/culture intersections"
        venues = [
            sample.source if sample else "Specialized biennales",
            "digital arts labs",
            "research-led residencies",
        ]
        cards.append(
            NicheCard(
                niche=topic,
                why_now=why_now,
                audience=audience,
                venues=venues,
                competition_keywords=[topic, "emerging format"],
                differentiation="Hybrid research-performance with transparency on process",
                commissioning_angle="Links to policy/ethics and community co-creation",
                risks="Signal volatility; shallow evidence",
                mitigation="Prototype quickly; validate with two venue partners",
            )
        )
    while len(cards) < limit:
        cards.append(
            NicheCard(
                niche=f"open-niche-{len(cards)+1}",
                why_now="Fill with curator observations",
                audience="TBD",
                venues=["open call platforms"],
                competition_keywords=["experimental"],
                differentiation="Sharper framing vs typical lab residencies",
                commissioning_angle="Pairs with civic tech / cultural policy",
                risks="Need stronger evidence",
                mitigation="Collect 2–3 more signals",
            )
        )
    return cards[:limit]


def project_title(topic: TopicMomentum, scale: str) -> str:
    verb = "Tracing" if scale == "Micro" else "Amplifying" if scale == "Mid" else "Reframing"
    return f"{verb} {topic.name.title()}"


def score_project(scale: str, topic_weight: float) -> int:
    appetite = min(25, 10 + int(topic_weight * 3))
    feasibility = 18 if scale == "Micro" else 20 if scale == "Mid" else 16
    distinctiveness = 20
    funding_fit = 14
    risk_penalty = 5 if scale == "Large" else 3
    score = appetite + feasibility + distinctiveness + funding_fit - risk_penalty
    return max(0, min(100, score))


def _preferred_mediums(preferences: Dict[str, Any]) -> str:
    mediums = preferences.get("medium_focus", [])
    if not mediums:
        return "performance + audiovisual + archive sampling"
    return " / ".join(str(medium).lower() for medium in mediums)


def _preferred_geography(preferences: Dict[str, Any]) -> str:
    geography = preferences.get("geography")
    return str(geography) if geography else "global"


def recommend_projects(topics: List[TopicMomentum], preferences: Dict[str, Any] | None = None) -> List[ProjectIdea]:
    preferences = preferences or {}
    scales = ["Micro", "Mid", "Large"]
    selected_topics = topics[:3] if len(topics) >= 3 else topics + topics[: 3 - len(topics)]
    projects: List[ProjectIdea] = []
    medium_focus = _preferred_mediums(preferences)
    geography = _preferred_geography(preferences)
    for scale, topic in zip(scales, selected_topics):
        score = score_project(scale, topic.weight)
        rationale = [
            f"Recent momentum score {topic.weight}",
            f"Aligns with {medium_focus} focus",
            f"Playable across {geography} venues",
            "Differentiated by transparent process + community proof"
        ]
        projects.append(
            ProjectIdea(
                scale=scale,
                title=project_title(topic, scale),
                hook=f"{scale} concept that spotlights {topic.name} through live research-performance.",
                medium_format=medium_focus,
                duration_footprint="Micro: pop-up / Mid: touring set / Large: multi-site installation",
                why_now=f"{topic.name.title()} rising in programming over last year; funders seeking credible, transparent AI/arts work.",
                production_needs="Creative technologist, dramaturg, rights-cleared datasets, disclosure plan",
                target_venues=["digital art festivals", "media labs", "museum project spaces", "policy-forward biennales"],
                promo_angle="Positioned as a living lab where audiences test narratives alongside artists; strong documentation for partners.",
                score=score,
                score_rationale=rationale,
            )
        )
    return projects


def summarize_signals(signals: List[Signal]) -> List[str]:
    return [f"- {signal.title} ({signal.source}, {signal.published_at.isoformat()})" for signal in signals]


def memo_sections(
    signals: List[Signal],
    today: date,
    config: Dict,
) -> Dict[str, object]:
    horizon_90d, horizon_1y, horizon_3y = horizon_split(signals, today)
    top_90d = select_top_topics(horizon_90d, today, limit=10)
    top_1y = select_top_topics(horizon_1y, today, limit=8)
    top_3y = select_top_topics(horizon_3y, today, limit=6)
    niches = build_niche_cards(horizon_1y, today)
    preferences = config.get("preferences", {})
    projects = recommend_projects(top_1y or top_3y or top_90d, preferences=preferences)
    return {
        "hot_signals": horizon_90d,
        "themes": top_1y,
        "macro_shifts": top_3y,
        "niche_cards": niches,
        "projects": projects,
    }


def render_topic_block(header: str, topics: List[TopicMomentum]) -> str:
    lines = [header]
    for topic in topics:
        lines.append(f"- **{topic.name}** (momentum {topic.weight}): " + ", ".join(s.title for s in topic.signals[:3]))
    return "\n".join(lines)


def render_niche_card(card: NicheCard) -> str:
    return "\n".join(
        [
            f"**Niche:** {card.niche}",
            f"**Why now:** {card.why_now}",
            f"**Audience:** {card.audience}",
            f"**Where it lives (venues/calls):** {', '.join(card.venues)}",
            f"**Competition keywords:** {', '.join(card.competition_keywords)}",
            f"**Differentiation / edge:** {card.differentiation}",
            f"**Commissioning angle:** {card.commissioning_angle}",
            f"**Risks:** {card.risks}",
            f"**Mitigation:** {card.mitigation}",
            "",
        ]
    )


def render_project(project: ProjectIdea) -> str:
    rationale_lines = "\n".join(f"- {item}" for item in project.score_rationale)
    return "\n".join(
        [
            f"## Project {project.scale}: {project.title}",
            f"**Hook (1 sentence):** {project.hook}",
            f"**Medium / format:** {project.medium_format}",
            f"**Duration / footprint:** {project.duration_footprint}",
            f"**Why now (trend links):** {project.why_now}",
            f"**Production needs:** {project.production_needs}",
            f"**Target venues / calls (3–7):** {', '.join(project.target_venues)}",
            f"**Promo angle (1 paragraph):** {project.promo_angle}",
            f"**Score (0–100):** {project.score}",
            "**Score rationale (bullets):**",
            rationale_lines,
            "",
        ]
    )


def render_pitch(project: ProjectIdea) -> str:
    lines = [
        f"{project.title} invites audiences into a transparent lab exploring {project.hook}.",
        f"It blends {project.medium_format}, giving visitors a participatory, research-driven experience.",
        project.why_now,
        "We have a nimble team, rights-cleared materials, and modular staging to keep production feasible.",
        "Looking for partners to commission/host a debut, with co-branded documentation for their audiences.",
    ]
    return " ".join(lines)


def render_actions() -> str:
    steps = [
        "Map next 20 open calls that mention AI/archives/performance",
        "Email top 5 venues asking for programming priorities",
        "Draft 2-page concept note per project scale",
        "Mock up production budget bands (micro/mid/large)",
        "Secure rights review for any datasets to be used",
        "Line up 3 potential collaborators (technologist, dramaturg, archivist)",
        "Collect 5 more signals per emerging niche",
        "Schedule pitch calls with two biennale curators",
        "Storyboard promo photography and teaser video",
        "Define consent + disclosure language for audiences",
    ]
    return "\n".join(f"- {step}" for step in steps)


def build_memo(sections: Dict[str, object]) -> str:
    hot_signals: List[Signal] = sections["hot_signals"]
    themes: List[TopicMomentum] = sections["themes"]
    macro_shifts: List[TopicMomentum] = sections["macro_shifts"]
    niche_cards: List[NicheCard] = sections["niche_cards"]
    projects: List[ProjectIdea] = sections["projects"]

    memo_parts = ["# Curatorial Opportunity Memo"]
    memo_parts.append("\n## Hot Signals (90D)")
    for signal in hot_signals[:10]:
        memo_parts.append(
            f"- {signal.title} ({signal.source}, {signal.published_at.isoformat()}): {signal.summary}"
        )

    memo_parts.append("\n## Themes (1Y)")
    memo_parts.append(render_topic_block("", themes))

    memo_parts.append("\n## Macro Shifts (3Y)")
    memo_parts.append(render_topic_block("", macro_shifts))

    memo_parts.append("\n## Niche Cards (Top 5)")
    memo_parts.append("\n".join(render_niche_card(card) for card in niche_cards))

    memo_parts.append("\n## Project Recommendations (Micro/Mid/Large)")
    for project in projects:
        memo_parts.append(render_project(project))

    selected_project = projects[0] if projects else None
    if selected_project:
        memo_parts.append("\n## Pitch (150 words)")
        memo_parts.append(render_pitch(selected_project))

    memo_parts.append("\n## Next Actions (7 days)")
    memo_parts.append(render_actions())

    return "\n".join(memo_parts)


def save_memo(memo: str, output_path: Path) -> None:
    sanitized = memo.rstrip() + "\n"
    output_path.write_text(sanitized)


def run(signals_path: Path, output_path: Path, today: date | None = None) -> Dict[str, object]:
    config = load_config(Path("config.yaml"))
    today = today or date.today()
    signals = load_signals(signals_path)
    sections = memo_sections(signals, today, config)
    memo = build_memo(sections)
    save_memo(memo, output_path)
    return {"sections": sections, "memo": memo, "config": config}


__all__ = [
    "run",
    "load_signals",
    "memo_sections",
    "build_memo",
    "save_memo",
]
