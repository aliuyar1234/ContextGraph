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
    <section>
      <h1 className="headline">Admin Console</h1>
      <div className="grid">
        <article className="card">
          <h3>Connector Health</h3>
          {connectors.length === 0 ? <p>No connectors configured yet.</p> : null}
          {connectors.map((row) => (
            <p key={row.tool}>
              <strong>{row.tool}</strong> : {row.enabled ? "enabled" : "disabled"}{" "}
              <button onClick={() => toggle(row.tool, !row.enabled)}>
                {row.enabled ? "disable" : "enable"}
              </button>
            </p>
          ))}
        </article>
        <article className="card">
          <h3>Retention</h3>
          <p>Publishing stops automatically if retention is disabled.</p>
          <label>
            <input
              type="checkbox"
              checked={retentionEnabled}
              onChange={(e) => setRetentionEnabled(e.currentTarget.checked)}
            />{" "}
            Retention enabled
          </label>
          <p>
            Raw days{" "}
            <input value={rawDays} type="number" min={1} onChange={(e) => setRawDays(Number(e.currentTarget.value))} />
          </p>
          <p>
            Trace days{" "}
            <input
              value={traceDays}
              type="number"
              min={1}
              onChange={(e) => setTraceDays(Number(e.currentTarget.value))}
            />
          </p>
          <p>
            Context days{" "}
            <input
              value={contextDays}
              type="number"
              min={1}
              onChange={(e) => setContextDays(Number(e.currentTarget.value))}
            />
          </p>
          <button onClick={saveRetention}>Save retention</button>
        </article>
      </div>
    </section>
  );
}
