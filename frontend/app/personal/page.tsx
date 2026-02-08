"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8080";
const HEADERS = { "X-Dev-User": "demo-user", "X-Dev-Role": "user", "Content-Type": "application/json" };

type TimelineItem = { trace_event_id: string; sequence_rank: number; action_type: string; event_time: string };
type Task = { personal_task_id: string; label: string; confidence: number };

export default function PersonalPage() {
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [optIn, setOptIn] = useState(false);

  async function refresh() {
    const [timelineRes, tasksRes] = await Promise.all([
      fetch(`${API_BASE}/api/v1/personal/timeline`, { headers: HEADERS }),
      fetch(`${API_BASE}/api/v1/personal/tasks`, { headers: HEADERS })
    ]);
    if (timelineRes.ok) {
      const body = (await timelineRes.json()) as { items: TimelineItem[] };
      setTimeline(body.items);
    }
    if (tasksRes.ok) {
      const body = (await tasksRes.json()) as { tasks: Task[] };
      setTasks(body.tasks);
    }
  }

  async function toggleOptIn(value: boolean) {
    setOptIn(value);
    await fetch(`${API_BASE}/api/v1/personal/opt_in_aggregation`, {
      method: "POST",
      headers: HEADERS,
      body: JSON.stringify({ enabled: value })
    });
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <section className="stack">
      <header className="section-intro reveal">
        <p className="eyebrow">Personal View</p>
        <h1 className="headline">Personal Timeline</h1>
        <p className="subtitle">Private by default. Explicit opt-in is required before aggregation.</p>
      </header>
      <article className="panel reveal">
        <label className="form-row inline">
          <input type="checkbox" checked={optIn} onChange={(e) => toggleOptIn(e.currentTarget.checked)} />
          <span>Opt in to aggregation</span>
        </label>
      </article>
      <div className="panel-grid two">
        <article className="panel reveal">
          <h2 className="panel-title">Timeline</h2>
          <div className="list">
            {timeline.length === 0 ? <p className="muted">No events captured for this user yet.</p> : null}
            {timeline.map((item) => (
              <div className="row-line" key={item.trace_event_id}>
                <div>
                  <p className="row-title">
                    #{item.sequence_rank} {item.action_type}
                  </p>
                  <p className="metric">{new Date(item.event_time).toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        </article>
        <article className="panel reveal">
          <h2 className="panel-title">Tasks</h2>
          <div className="list">
            {tasks.length === 0 ? <p className="muted">No clustered tasks yet.</p> : null}
            {tasks.map((task) => (
              <div className="row-line" key={task.personal_task_id}>
                <p className="row-title">{task.label}</p>
                <span className="badge">{Math.round(task.confidence * 100)}%</span>
              </div>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}
