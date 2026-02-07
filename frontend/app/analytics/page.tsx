"use client";

import { FormEvent, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8080";
const HEADERS = { "X-Dev-User": "demo-user", "X-Dev-Role": "analyst", "Content-Type": "application/json" };

type Pattern = { pattern_id: string; process_key: string; distinct_user_count: number };
type Variant = { rank: number; frequency: number; steps: Array<{ hash: string }> };

export default function AnalyticsPage() {
  const [processKey, setProcessKey] = useState("chat:action=message");
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [bottlenecks, setBottlenecks] = useState<Array<{ from_step_hash: string; p95_ms: number }>>([]);

  async function loadPatterns(event: FormEvent) {
    event.preventDefault();
    const res = await fetch(`${API_BASE}/api/v1/analytics/processes/${encodeURIComponent(processKey)}/patterns`, {
      headers: HEADERS
    });
    if (!res.ok) {
      setPatterns([]);
      setVariants([]);
      return;
    }
    const data = (await res.json()) as { patterns: Pattern[] };
    setPatterns(data.patterns);
    if (data.patterns[0]) {
      await loadPattern(data.patterns[0].pattern_id);
    }
  }

  async function loadPattern(patternId: string) {
    const [v, b] = await Promise.all([
      fetch(`${API_BASE}/api/v1/analytics/patterns/${patternId}/variants`, { headers: HEADERS }),
      fetch(`${API_BASE}/api/v1/analytics/patterns/${patternId}/bottlenecks`, { headers: HEADERS })
    ]);
    if (v.ok) {
      const body = (await v.json()) as { variants: Variant[] };
      setVariants(body.variants);
    }
    if (b.ok) {
      const body = (await b.json()) as { bottlenecks: Array<{ from_step_hash: string; p95_ms: number }> };
      setBottlenecks(body.bottlenecks);
    }
  }

  return (
    <section>
      <h1 className="headline">Process Explorer</h1>
      <form className="card" onSubmit={loadPatterns}>
        <label>
          Process key{" "}
          <input value={processKey} onChange={(e) => setProcessKey(e.currentTarget.value)} />
        </label>{" "}
        <button type="submit">Load</button>
      </form>
      <div className="grid">
        <article className="card">
          <h3>Published Patterns</h3>
          {patterns.map((pattern) => (
            <p key={pattern.pattern_id}>
              <button onClick={() => loadPattern(pattern.pattern_id)}>{pattern.pattern_id}</button> users=
              {pattern.distinct_user_count}
            </p>
          ))}
        </article>
        <article className="card">
          <h3>Top Variants</h3>
          {variants.map((variant) => (
            <p key={variant.rank}>
              rank {variant.rank} freq {(variant.frequency * 100).toFixed(1)}% steps {variant.steps.length}
            </p>
          ))}
        </article>
        <article className="card">
          <h3>Bottlenecks</h3>
          {bottlenecks.map((b) => (
            <p key={`${b.from_step_hash}-${b.p95_ms}`}>
              {b.from_step_hash} : p95 {Math.round(b.p95_ms / 1000)}s
            </p>
          ))}
        </article>
      </div>
    </section>
  );
}

