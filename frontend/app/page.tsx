"use client";

import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MemoResponse = {
  memo?: string;
  stdout?: string;
  error?: string;
  stderr?: string;
};

const sampleSignals = [
  {
    title: "UNESCO updates AI ethics guidance for cultural institutions",
    source: "UNESCO",
    published_at: "2024-05-20",
    summary:
      "Revised framework asks museums and festivals to disclose AI provenance and licensing, emphasizing community consent.",
    url: "https://unesco.org/ai-ethics",
    tags: ["ai-copyright", "provenance-transparency"],
  },
  {
    title: "Venice Biennale side program spotlights climate urgency in coastal cities",
    source: "Venice Biennale",
    published_at: "2024-04-18",
    summary:
      "New commissions pair sound walks with environmental data to reveal rising sea impacts on neighborhoods.",
    url: "https://example.com/venice-climate",
    tags: ["climate-urgency", "listening-spatial"],
  },
  {
    title: "Open call: diaspora archives for performance artists",
    source: "Performance Space New York",
    published_at: "2024-06-04",
    summary:
      "Residency invites artists to work with diaspora family archives, offering dramaturgy support and public showings.",
    tags: ["diaspora", "archive-practice"],
  },
  {
    title: "Research lab maps missing images in public datasets",
    source: "Digital Public Library",
    published_at: "2024-03-12",
    summary:
      "Fellowship cohort documents gaps in visual records across regions and proposes community-led digitization.",
    tags: ["missing-images", "archive-practice"],
  },
  {
    title: "Policy brief: European funding shifts toward provenance transparency",
    source: "Creative Europe",
    published_at: "2023-12-01",
    summary: "New funding lines prioritize traceable AI systems and open cultural data infrastructure.",
    tags: ["provenance-transparency", "policy"],
  },
  {
    title: "XR festival tests participatory public-space performances",
    source: "Sónar",
    published_at: "2024-01-20",
    summary:
      "Festival pilots multi-city AR interventions with citizen co-design sessions, focused on accessibility.",
    tags: ["participatory", "public-space", "accessibility"],
  },
  {
    title: "Art-tech lab explores decolonial methods for AI training",
    source: "Serpentine",
    published_at: "2023-10-15",
    summary:
      "Workshops critique dataset extraction and propose artist-led annotation circles using consent protocols.",
    tags: ["decolonial-method", "ai-copyright"],
  },
  {
    title: "Open data commons releases spatial audio field kit",
    source: "Open Data Commons",
    published_at: "2024-02-05",
    summary:
      "Toolkit standardizes community capture of spatial audio for public art and archives.",
    tags: ["listening-spatial", "public-space"],
  },
  {
    title: "University study links accessibility gaps in immersive arts",
    source: "MIT",
    published_at: "2024-05-01",
    summary:
      "Survey of 30 XR exhibitions finds low adoption of multi-sensory access plans and calls for new standards.",
    tags: ["accessibility", "public-space"],
  },
  {
    title: "Museum pilots provenance-first AI label on digital collections",
    source: "Tate",
    published_at: "2024-04-02",
    summary:
      "Labels show training data lineage and licenses, helping audiences understand AI-assisted restorations.",
    tags: ["provenance-transparency", "archive-practice"],
  },
  {
    title: "Biennale program explores participatory listening stations",
    source: "Sydney Biennale",
    published_at: "2024-01-28",
    summary: "Community groups co-create spatial audio maps of neighborhood care infrastructures.",
    tags: ["participatory", "listening-spatial"],
  },
  {
    title: "City arts fund backs public-space performances on climate resilience",
    source: "NYC Cultural Affairs",
    published_at: "2024-06-10",
    summary:
      "Grants support artists staging street performances with local climate researchers and youth groups.",
    tags: ["public-space", "climate-urgency"],
  },
];

const sampleText = JSON.stringify(sampleSignals, null, 2);

export default function HomePage() {
  const [signalsInput, setSignalsInput] = useState(sampleText);
  const [today, setToday] = useState<string>(new Date().toISOString().slice(0, 10));
  const [memo, setMemo] = useState<string>("");
  const [logs, setLogs] = useState<string>("");
  const [status, setStatus] = useState<"idle" | "running" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);

  const parsedSignals = useMemo(() => {
    try {
      return JSON.parse(signalsInput);
    } catch (err) {
      return null;
    }
  }, [signalsInput]);

  const signalsMeta = useMemo(() => {
    if (!Array.isArray(parsedSignals)) return null;
    const tags = new Set<string>();
    parsedSignals.forEach((item) => {
      if (item?.tags && Array.isArray(item.tags)) {
        item.tags.forEach((tag: string) => tags.add(tag));
      }
    });
    return { count: parsedSignals.length, tags: Array.from(tags).sort() };
  }, [parsedSignals]);

  const handleGenerate = async () => {
    if (!parsedSignals) {
      setError("Signals JSON is invalid. Please fix the syntax.");
      setStatus("error");
      return;
    }

    setStatus("running");
    setError(null);
    setMemo("");
    setLogs("");

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ signals: parsedSignals, today }),
      });

      const data: MemoResponse = await res.json();
      if (!res.ok || data.error) {
        setError(data.error || "Memo generation failed.");
        setLogs(data.stderr || data.stdout || "");
        setStatus("error");
        return;
      }

      setMemo(data.memo || "");
      setLogs(data.stdout || "");
      setStatus("done");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setStatus("error");
    }
  };

  const loadSample = () => {
    setSignalsInput(sampleText);
    setMemo("");
    setLogs("");
    setStatus("idle");
    setError(null);
  };

  return (
    <main>
      <div className="container">
        <div className="header">
          <div>
            <h1>Global Curator Scout</h1>
            <p style={{ color: "var(--text-muted)", margin: 0 }}>
              Run the memo generator from your browser. Paste signals, pick a date, and ship a Markdown memo.
            </p>
          </div>
          <div className="badge">
            <span>Next.js UI</span>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--accent-strong)" }} />
          </div>
        </div>

        <div className="grid">
          <div className="panel">
            <div className="label-row">
              <label htmlFor="signals">Signals JSON</label>
              {signalsMeta ? (
                <span className="tag">{signalsMeta.count} signals · {signalsMeta.tags.length} tags</span>
              ) : (
                <span className="tag" style={{ color: "var(--danger)", borderColor: "rgba(248, 113, 113, 0.4)" }}>
                  Invalid JSON
                </span>
              )}
            </div>
            <textarea
              id="signals"
              value={signalsInput}
              onChange={(e) => setSignalsInput(e.target.value)}
              spellCheck={false}
            />
            <div className="button-row" style={{ marginTop: "0.75rem" }}>
              <button className="button-secondary" type="button" onClick={loadSample}>
                Use sample signals
              </button>
              <button
                className="button-primary"
                type="button"
                onClick={handleGenerate}
                disabled={status === "running" || !parsedSignals}
              >
                {status === "running" ? "Generating..." : "Generate memo"}
              </button>
            </div>
          </div>

          <div className="panel">
            <div className="label-row">
              <label htmlFor="today">Run date</label>
              <span style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                Controls the 90d / 1y / 3y horizon split.
              </span>
            </div>
            <input id="today" type="date" value={today} onChange={(e) => setToday(e.target.value)} />

            <div style={{ marginTop: "1.1rem" }} className="status-row">
              <span>Status:</span>
              {status === "idle" && <span>Waiting to start</span>}
              {status === "running" && <span>Running Python memo generator...</span>}
              {status === "done" && <span style={{ color: "var(--success)" }}>Done — preview below</span>}
              {status === "error" && <span style={{ color: "var(--danger)" }}>Error</span>}
            </div>

            {error && (
              <div style={{ marginTop: "0.75rem", color: "var(--danger)" }}>
                <div className="card-title">Error</div>
                <div>{error}</div>
              </div>
            )}

            {logs && (
              <div style={{ marginTop: "0.75rem" }}>
                <div className="card-title">Logs</div>
                <div className="log">{logs}</div>
              </div>
            )}
          </div>
        </div>

        <div style={{ marginTop: "1rem" }} className="panel">
          <div className="label-row">
            <h2 style={{ margin: 0 }}>Memo preview</h2>
            <span style={{ color: "var(--text-muted)" }}>
              Uses the same Python pipeline as the CLI. Download or copy the Markdown after generation.
            </span>
          </div>

          {memo ? (
            <article className="memo-preview">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{memo}</ReactMarkdown>
            </article>
          ) : (
            <div style={{ color: "var(--text-muted)" }}>
              No memo yet. Paste signals and click “Generate memo” to run the backend pipeline.
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
