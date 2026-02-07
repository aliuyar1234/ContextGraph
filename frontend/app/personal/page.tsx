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
    <section>
      <h1 className="headline">Personal Timeline</h1>
      <article className="card">
        <label>
          <input type="checkbox" checked={optIn} onChange={(e) => toggleOptIn(e.currentTarget.checked)} /> Opt in to
          aggregation
        </label>
      </article>
      <div className="grid">
        <article className="card">
          <h3>Timeline</h3>
          {timeline.map((item) => (
            <p key={item.trace_event_id}>
              #{item.sequence_rank} {item.action_type} at {new Date(item.event_time).toLocaleString()}
            </p>
          ))}
        </article>
        <article className="card">
          <h3>Tasks</h3>
          {tasks.map((task) => (
            <p key={task.personal_task_id}>
              {task.label} ({Math.round(task.confidence * 100)}%)
            </p>
          ))}
        </article>
      </div>
    </section>
  );
}

