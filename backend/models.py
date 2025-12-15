from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Sequence


@dataclass
class Signal:
    title: str
    source: str
    published_at: date
    summary: str
    url: str | None = None
    tags: List[str] = field(default_factory=list)


@dataclass
class TopicMomentum:
    name: str
    weight: float
    signals: List[Signal]


@dataclass
class NicheCard:
    niche: str
    why_now: str
    audience: str
    venues: List[str]
    competition_keywords: List[str]
    differentiation: str
    commissioning_angle: str
    risks: str
    mitigation: str


@dataclass
class ProjectIdea:
    scale: str
    title: str
    hook: str
    medium_format: str
    duration_footprint: str
    why_now: str
    production_needs: str
    target_venues: List[str]
    promo_angle: str
    score: int
    score_rationale: Sequence[str]
