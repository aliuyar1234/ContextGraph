"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8080";
const HEADERS = { "X-Dev-User": "demo-user", "X-Dev-Role": "admin", "Content-Type": "application/json" };

type ConnectorRow = { tool: string; enabled: boolean; updated_at: string };

export default function AdminPage() {
  const [connectors, setConnectors] = useState<ConnectorRow[]>([]);
  const [retentionEnabled, setRetentionEnabled] = useState(true);
  const [rawDays, setRawDays] = useState(30);
  const [traceDays, setTraceDays] = useState(180);
  const [contextDays, setContextDays] = useState(365);

  async function refresh() {
    const [res, retentionRes] = await Promise.all([
      fetch(`${API_BASE}/api/v1/admin/connectors`, { headers: HEADERS }),
      fetch(`${API_BASE}/api/v1/admin/connectors/retention`, { headers: HEADERS })
    ]);
    if (res.ok) {
      const data = (await res.json()) as { connectors: ConnectorRow[] };
      setConnectors(data.connectors);
    }
    if (retentionRes.ok) {
      const data = (await retentionRes.json()) as {
        retention: { retention_enabled: boolean; raw_days: number; trace_days: number; context_days: number };
      };
      setRetentionEnabled(data.retention.retention_enabled);
      setRawDays(data.retention.raw_days);
      setTraceDays(data.retention.trace_days);
      setContextDays(data.retention.context_days);
    }
  }

  async function toggle(tool: string, enabled: boolean) {
    const path = enabled ? "enable" : "disable";
    await fetch(`${API_BASE}/api/v1/admin/connectors/${tool}/${path}`, {
      method: "POST",
      headers: HEADERS,
      body: enabled
        ? JSON.stringify({
            auth: { token_ref: `env:${tool.toUpperCase()}_TOKEN` },
            scopes: ["read:default"]
          })
        : "{}"
    });
    await refresh();
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function saveRetention() {
    await fetch(`${API_BASE}/api/v1/admin/connectors/retention`, {
      method: "POST",
      headers: HEADERS,
      body: JSON.stringify({
        retention_enabled: retentionEnabled,
        raw_days: rawDays,
        trace_days: traceDays,
        context_days: contextDays
      })
    });
    await refresh();
  }

  return (
    <section className="stack">
      <header className="section-intro reveal">
        <p className="eyebrow">Operations</p>
        <h1 className="headline">Admin Console</h1>
        <p className="subtitle">Connector status and retention controls for privacy-safe publishing.</p>
      </header>
      <div className="panel-grid two">
        <article className="panel reveal">
          <div className="panel-head">
            <h2 className="panel-title">Connector Health</h2>
            <span className="badge">{connectors.length} configured</span>
          </div>
          <div className="list">
            {connectors.length === 0 ? <p className="muted">No connectors configured yet.</p> : null}
            {connectors.map((row) => (
              <div className="row-line" key={row.tool}>
                <div>
                  <p className="row-title">{row.tool}</p>
                  <p className="metric">Updated {new Date(row.updated_at).toLocaleString()}</p>
                </div>
                <div className="row-actions">
                  <span className={`badge ${row.enabled ? "ok" : "off"}`}>
                    {row.enabled ? "enabled" : "disabled"}
                  </span>
                  <button className="button ghost" onClick={() => toggle(row.tool, !row.enabled)}>
                    {row.enabled ? "Disable" : "Enable"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </article>
        <article className="panel reveal">
          <h2 className="panel-title">Retention</h2>
          <p className="kicker">Publishing stops automatically if retention is disabled.</p>
          <div className="form-card">
            <label className="form-row inline">
              <input
                type="checkbox"
                checked={retentionEnabled}
                onChange={(e) => setRetentionEnabled(e.currentTarget.checked)}
              />
              <span>Retention enabled</span>
            </label>
            <label className="form-row">
              <span>Raw days</span>
              <input value={rawDays} type="number" min={1} onChange={(e) => setRawDays(Number(e.currentTarget.value))} />
            </label>
            <label className="form-row">
              <span>Trace days</span>
              <input
                value={traceDays}
                type="number"
                min={1}
                onChange={(e) => setTraceDays(Number(e.currentTarget.value))}
              />
            </label>
            <label className="form-row">
              <span>Context days</span>
              <input
                value={contextDays}
                type="number"
                min={1}
                onChange={(e) => setContextDays(Number(e.currentTarget.value))}
              />
            </label>
            <div className="form-actions">
              <button className="button accent" onClick={saveRetention}>
                Save retention
              </button>
            </div>
          </div>
        </article>
      </div>
    </section>
  );
}
