"use client";

import { FormEvent, PointerEvent, WheelEvent, useEffect, useMemo, useRef, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8080";
const HEADERS = { "X-Dev-User": "demo-user", "X-Dev-Role": "analyst", "Content-Type": "application/json" };
const GRAPH_WIDTH = 1024;
const GRAPH_HEIGHT = 620;

type Pattern = {
  pattern_id: string;
  process_key: string;
  distinct_user_count: number;
  distinct_trace_count: number;
  title?: string;
};
type Variant = { rank: number; frequency: number; steps: Array<{ hash: string }> };
type Edge = { from_step_hash: string; to_step_hash: string; count: number; probability: number; timing: { p95_ms?: number } };

type GraphNode = { id: string; label: string; x: number; y: number; activity: number; radius: number };
type GraphEdge = {
  id: string;
  from: GraphNode;
  to: GraphNode;
  probability: number;
  weight: number;
  delayMs: number;
  isCritical: boolean;
};
type GraphModel = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  labels: Record<string, string>;
  strongestPath: string[];
  avgProbability: number;
  maxDelayMs: number;
};

type DemoStory = {
  process_key: string;
  title: string;
  description?: string;
  company_size?: number;
  team_count?: number;
  monthly_traces?: number;
  labels: Record<string, string>;
  patterns: Pattern[];
  variants: Variant[];
  edges: Edge[];
  bottlenecks: Array<{ from_step_hash: string; p95_ms: number }>;
};

const DEMO_STORIES: DemoStory[] = [
  {
    process_key: "chat:action=message",
    title: "Incident Swarm",
    labels: {
      __START__: "Start",
      alert_seen: "Alert Seen",
      triage: "Triage",
      owner_assigned: "Owner Assigned",
      scope_checked: "Scope Checked",
      workaround: "Workaround Shared",
      fix_pr: "Fix PR Opened",
      review: "Review Complete",
      deploy: "Patch Deployed",
      verify: "Recovery Verified"
    },
    patterns: [{ pattern_id: "demo-incident-01", process_key: "chat:action=message", distinct_user_count: 18, distinct_trace_count: 94, title: "Incident Swarm" }],
    variants: [{ rank: 1, frequency: 0.49, steps: [{ hash: "alert_seen" }, { hash: "triage" }, { hash: "owner_assigned" }, { hash: "fix_pr" }, { hash: "review" }, { hash: "deploy" }, { hash: "verify" }] }],
    edges: [
      { from_step_hash: "__START__", to_step_hash: "alert_seen", count: 94, probability: 1, timing: { p95_ms: 1000 } },
      { from_step_hash: "alert_seen", to_step_hash: "triage", count: 90, probability: 0.95, timing: { p95_ms: 18000 } },
      { from_step_hash: "triage", to_step_hash: "owner_assigned", count: 61, probability: 0.67, timing: { p95_ms: 66000 } },
      { from_step_hash: "triage", to_step_hash: "scope_checked", count: 25, probability: 0.28, timing: { p95_ms: 94000 } },
      { from_step_hash: "scope_checked", to_step_hash: "workaround", count: 18, probability: 0.72, timing: { p95_ms: 230000 } },
      { from_step_hash: "owner_assigned", to_step_hash: "fix_pr", count: 54, probability: 0.88, timing: { p95_ms: 260000 } },
      { from_step_hash: "workaround", to_step_hash: "fix_pr", count: 14, probability: 0.78, timing: { p95_ms: 350000 } },
      { from_step_hash: "fix_pr", to_step_hash: "review", count: 46, probability: 0.66, timing: { p95_ms: 510000 } },
      { from_step_hash: "review", to_step_hash: "deploy", count: 42, probability: 0.92, timing: { p95_ms: 160000 } },
      { from_step_hash: "deploy", to_step_hash: "verify", count: 58, probability: 0.93, timing: { p95_ms: 105000 } }
    ],
    bottlenecks: [{ from_step_hash: "fix_pr", p95_ms: 510000 }, { from_step_hash: "workaround", p95_ms: 350000 }, { from_step_hash: "owner_assigned", p95_ms: 260000 }]
  },
  {
    process_key: "code:action=merge",
    title: "Release Train",
    labels: {
      __START__: "Start",
      branch: "Branch Created",
      commit: "Commit Pushed",
      ci: "CI Started",
      qa: "QA Checks",
      approval: "Approval Granted",
      merge: "Merge Main",
      stage: "Deploy Staging",
      prod: "Deploy Production"
    },
    patterns: [{ pattern_id: "demo-release-01", process_key: "code:action=merge", distinct_user_count: 23, distinct_trace_count: 121, title: "Release Train" }],
    variants: [{ rank: 1, frequency: 0.56, steps: [{ hash: "branch" }, { hash: "commit" }, { hash: "ci" }, { hash: "approval" }, { hash: "merge" }, { hash: "stage" }, { hash: "prod" }] }],
    edges: [
      { from_step_hash: "__START__", to_step_hash: "branch", count: 121, probability: 1, timing: { p95_ms: 1000 } },
      { from_step_hash: "branch", to_step_hash: "commit", count: 118, probability: 0.97, timing: { p95_ms: 14000 } },
      { from_step_hash: "commit", to_step_hash: "ci", count: 112, probability: 0.95, timing: { p95_ms: 28000 } },
      { from_step_hash: "ci", to_step_hash: "qa", count: 41, probability: 0.37, timing: { p95_ms: 560000 } },
      { from_step_hash: "ci", to_step_hash: "approval", count: 63, probability: 0.57, timing: { p95_ms: 420000 } },
      { from_step_hash: "qa", to_step_hash: "approval", count: 33, probability: 0.8, timing: { p95_ms: 610000 } },
      { from_step_hash: "approval", to_step_hash: "merge", count: 89, probability: 0.94, timing: { p95_ms: 96000 } },
      { from_step_hash: "merge", to_step_hash: "stage", count: 75, probability: 0.84, timing: { p95_ms: 195000 } },
      { from_step_hash: "stage", to_step_hash: "prod", count: 67, probability: 0.89, timing: { p95_ms: 250000 } }
    ],
    bottlenecks: [{ from_step_hash: "qa", p95_ms: 610000 }, { from_step_hash: "ci", p95_ms: 560000 }, { from_step_hash: "stage", p95_ms: 250000 }]
  },
  {
    process_key: "tickets:action=status_change",
    title: "Escalation Loop",
    labels: {
      __START__: "Start",
      ticket: "Ticket Opened",
      severity: "Severity Set",
      callback: "Customer Callback",
      handoff: "Engineering Handoff",
      validation: "Fix Validated",
      resolved: "Resolved"
    },
    patterns: [{ pattern_id: "demo-support-01", process_key: "tickets:action=status_change", distinct_user_count: 16, distinct_trace_count: 88, title: "Escalation Loop" }],
    variants: [{ rank: 1, frequency: 0.44, steps: [{ hash: "ticket" }, { hash: "severity" }, { hash: "handoff" }, { hash: "validation" }, { hash: "resolved" }] }],
    edges: [
      { from_step_hash: "__START__", to_step_hash: "ticket", count: 88, probability: 1, timing: { p95_ms: 1000 } },
      { from_step_hash: "ticket", to_step_hash: "severity", count: 82, probability: 0.93, timing: { p95_ms: 36000 } },
      { from_step_hash: "severity", to_step_hash: "callback", count: 24, probability: 0.29, timing: { p95_ms: 320000 } },
      { from_step_hash: "severity", to_step_hash: "handoff", count: 52, probability: 0.64, timing: { p95_ms: 190000 } },
      { from_step_hash: "callback", to_step_hash: "handoff", count: 18, probability: 0.74, timing: { p95_ms: 430000 } },
      { from_step_hash: "handoff", to_step_hash: "validation", count: 58, probability: 0.83, timing: { p95_ms: 520000 } },
      { from_step_hash: "validation", to_step_hash: "resolved", count: 55, probability: 0.95, timing: { p95_ms: 140000 } }
    ],
    bottlenecks: [{ from_step_hash: "handoff", p95_ms: 520000 }, { from_step_hash: "callback", p95_ms: 430000 }, { from_step_hash: "severity", p95_ms: 320000 }]
  },
  {
    process_key: "org50:action=handoff",
    title: "50-Person Delivery Org",
    description: "Cross-team incident and release flow for a simulated 50-person software company.",
    company_size: 50,
    team_count: 4,
    monthly_traces: 684,
    labels: {
      __START__: "Signal Detected",
      support_triage: "Support Triage",
      severity_tagged: "Severity Tagged",
      owner_looped_in: "Product Owner Loop-In",
      workaround_shared: "Workaround Shared",
      eng_lead_assigned: "Eng Lead Assigned",
      squad_sync: "Squad Sync",
      scope_defined: "Fix Scope Defined",
      implementation_started: "Implementation Started",
      pr_opened: "PR Opened",
      review_round_1: "Review Round 1",
      qa_regression: "QA Regression",
      staging_rollout: "Staging Rollout",
      canary_monitor: "Canary Monitor",
      production_rollout: "Production Rollout",
      customer_confirmed: "Customer Confirmed",
      postmortem_queued: "Postmortem Queued"
    },
    patterns: [{ pattern_id: "demo-org50-01", process_key: "org50:action=handoff", distinct_user_count: 41, distinct_trace_count: 684, title: "50-Person Delivery Org" }],
    variants: [
      { rank: 1, frequency: 0.42, steps: [{ hash: "support_triage" }, { hash: "severity_tagged" }, { hash: "owner_looped_in" }, { hash: "eng_lead_assigned" }, { hash: "squad_sync" }, { hash: "scope_defined" }, { hash: "implementation_started" }, { hash: "pr_opened" }, { hash: "review_round_1" }, { hash: "qa_regression" }, { hash: "staging_rollout" }, { hash: "canary_monitor" }, { hash: "production_rollout" }, { hash: "customer_confirmed" }] },
      { rank: 2, frequency: 0.27, steps: [{ hash: "support_triage" }, { hash: "severity_tagged" }, { hash: "workaround_shared" }, { hash: "customer_confirmed" }, { hash: "postmortem_queued" }] },
      { rank: 3, frequency: 0.19, steps: [{ hash: "support_triage" }, { hash: "severity_tagged" }, { hash: "owner_looped_in" }, { hash: "eng_lead_assigned" }, { hash: "implementation_started" }, { hash: "pr_opened" }, { hash: "qa_regression" }, { hash: "implementation_started" }, { hash: "pr_opened" }, { hash: "review_round_1" }, { hash: "staging_rollout" }, { hash: "production_rollout" }, { hash: "customer_confirmed" }] }
    ],
    edges: [
      { from_step_hash: "__START__", to_step_hash: "support_triage", count: 684, probability: 1, timing: { p95_ms: 1200 } },
      { from_step_hash: "support_triage", to_step_hash: "severity_tagged", count: 652, probability: 0.95, timing: { p95_ms: 26000 } },
      { from_step_hash: "severity_tagged", to_step_hash: "owner_looped_in", count: 412, probability: 0.63, timing: { p95_ms: 180000 } },
      { from_step_hash: "severity_tagged", to_step_hash: "workaround_shared", count: 196, probability: 0.3, timing: { p95_ms: 220000 } },
      { from_step_hash: "owner_looped_in", to_step_hash: "eng_lead_assigned", count: 391, probability: 0.95, timing: { p95_ms: 210000 } },
      { from_step_hash: "eng_lead_assigned", to_step_hash: "squad_sync", count: 355, probability: 0.91, timing: { p95_ms: 340000 } },
      { from_step_hash: "squad_sync", to_step_hash: "scope_defined", count: 332, probability: 0.94, timing: { p95_ms: 390000 } },
      { from_step_hash: "scope_defined", to_step_hash: "implementation_started", count: 321, probability: 0.96, timing: { p95_ms: 460000 } },
      { from_step_hash: "implementation_started", to_step_hash: "pr_opened", count: 304, probability: 0.94, timing: { p95_ms: 560000 } },
      { from_step_hash: "pr_opened", to_step_hash: "review_round_1", count: 284, probability: 0.93, timing: { p95_ms: 710000 } },
      { from_step_hash: "review_round_1", to_step_hash: "qa_regression", count: 249, probability: 0.88, timing: { p95_ms: 910000 } },
      { from_step_hash: "qa_regression", to_step_hash: "staging_rollout", count: 224, probability: 0.87, timing: { p95_ms: 760000 } },
      { from_step_hash: "qa_regression", to_step_hash: "implementation_started", count: 34, probability: 0.13, timing: { p95_ms: 430000 } },
      { from_step_hash: "staging_rollout", to_step_hash: "canary_monitor", count: 211, probability: 0.94, timing: { p95_ms: 480000 } },
      { from_step_hash: "canary_monitor", to_step_hash: "production_rollout", count: 187, probability: 0.89, timing: { p95_ms: 640000 } },
      { from_step_hash: "production_rollout", to_step_hash: "customer_confirmed", count: 168, probability: 0.9, timing: { p95_ms: 310000 } },
      { from_step_hash: "workaround_shared", to_step_hash: "customer_confirmed", count: 122, probability: 0.62, timing: { p95_ms: 260000 } },
      { from_step_hash: "customer_confirmed", to_step_hash: "postmortem_queued", count: 141, probability: 0.84, timing: { p95_ms: 520000 } }
    ],
    bottlenecks: [{ from_step_hash: "qa_regression", p95_ms: 910000 }, { from_step_hash: "review_round_1", p95_ms: 710000 }, { from_step_hash: "canary_monitor", p95_ms: 640000 }]
  },
  {
    process_key: "sales:action=handoff",
    title: "Sales-to-Delivery Handoff",
    description: "Opportunity-to-project handoff across sales, solution engineering, PMO, and delivery squads.",
    company_size: 50,
    team_count: 5,
    monthly_traces: 512,
    labels: {
      __START__: "Lead Qualified",
      discovery_call: "Discovery Call",
      solution_fit: "Solution Fit Scored",
      commercial_review: "Commercial Review",
      scope_draft: "Scope Drafted",
      legal_review: "Legal Review",
      contract_signed: "Contract Signed",
      kickoff_scheduled: "Kickoff Scheduled",
      delivery_owner_assigned: "Delivery Owner Assigned",
      implementation_plan: "Implementation Plan",
      customer_onboarding: "Customer Onboarding",
      go_live_ready: "Go-Live Ready"
    },
    patterns: [{ pattern_id: "demo-sales-01", process_key: "sales:action=handoff", distinct_user_count: 34, distinct_trace_count: 512, title: "Sales-to-Delivery Handoff" }],
    variants: [
      { rank: 1, frequency: 0.46, steps: [{ hash: "discovery_call" }, { hash: "solution_fit" }, { hash: "commercial_review" }, { hash: "scope_draft" }, { hash: "legal_review" }, { hash: "contract_signed" }, { hash: "kickoff_scheduled" }, { hash: "delivery_owner_assigned" }, { hash: "implementation_plan" }, { hash: "customer_onboarding" }, { hash: "go_live_ready" }] },
      { rank: 2, frequency: 0.29, steps: [{ hash: "discovery_call" }, { hash: "solution_fit" }, { hash: "scope_draft" }, { hash: "contract_signed" }, { hash: "kickoff_scheduled" }, { hash: "delivery_owner_assigned" }, { hash: "implementation_plan" }, { hash: "go_live_ready" }] }
    ],
    edges: [
      { from_step_hash: "__START__", to_step_hash: "discovery_call", count: 512, probability: 1, timing: { p95_ms: 1400 } },
      { from_step_hash: "discovery_call", to_step_hash: "solution_fit", count: 486, probability: 0.95, timing: { p95_ms: 86000 } },
      { from_step_hash: "solution_fit", to_step_hash: "commercial_review", count: 303, probability: 0.62, timing: { p95_ms: 370000 } },
      { from_step_hash: "solution_fit", to_step_hash: "scope_draft", count: 154, probability: 0.31, timing: { p95_ms: 290000 } },
      { from_step_hash: "commercial_review", to_step_hash: "scope_draft", count: 281, probability: 0.93, timing: { p95_ms: 510000 } },
      { from_step_hash: "scope_draft", to_step_hash: "legal_review", count: 238, probability: 0.55, timing: { p95_ms: 690000 } },
      { from_step_hash: "scope_draft", to_step_hash: "contract_signed", count: 182, probability: 0.42, timing: { p95_ms: 430000 } },
      { from_step_hash: "legal_review", to_step_hash: "contract_signed", count: 221, probability: 0.93, timing: { p95_ms: 740000 } },
      { from_step_hash: "contract_signed", to_step_hash: "kickoff_scheduled", count: 401, probability: 0.92, timing: { p95_ms: 160000 } },
      { from_step_hash: "kickoff_scheduled", to_step_hash: "delivery_owner_assigned", count: 387, probability: 0.96, timing: { p95_ms: 92000 } },
      { from_step_hash: "delivery_owner_assigned", to_step_hash: "implementation_plan", count: 366, probability: 0.95, timing: { p95_ms: 260000 } },
      { from_step_hash: "implementation_plan", to_step_hash: "customer_onboarding", count: 329, probability: 0.89, timing: { p95_ms: 410000 } },
      { from_step_hash: "customer_onboarding", to_step_hash: "go_live_ready", count: 301, probability: 0.91, timing: { p95_ms: 520000 } }
    ],
    bottlenecks: [{ from_step_hash: "legal_review", p95_ms: 740000 }, { from_step_hash: "scope_draft", p95_ms: 690000 }, { from_step_hash: "customer_onboarding", p95_ms: 520000 }]
  },
  {
    process_key: "support:action=escalation",
    title: "Customer Escalation to Engineering",
    description: "Support escalations routed into engineering triage, patching, and customer closure.",
    company_size: 50,
    team_count: 4,
    monthly_traces: 438,
    labels: {
      __START__: "Customer Ticket",
      l1_triage: "L1 Triage",
      severity_set: "Severity Set",
      escalation_manager: "Escalation Manager",
      eng_triage: "Engineering Triage",
      root_cause: "Root Cause Isolated",
      patch_branch: "Patch Branch",
      review_patch: "Patch Review",
      hotfix_release: "Hotfix Release",
      customer_validation: "Customer Validation",
      case_closed: "Case Closed"
    },
    patterns: [{ pattern_id: "demo-escalation-eng-01", process_key: "support:action=escalation", distinct_user_count: 29, distinct_trace_count: 438, title: "Customer Escalation to Engineering" }],
    variants: [
      { rank: 1, frequency: 0.51, steps: [{ hash: "l1_triage" }, { hash: "severity_set" }, { hash: "escalation_manager" }, { hash: "eng_triage" }, { hash: "root_cause" }, { hash: "patch_branch" }, { hash: "review_patch" }, { hash: "hotfix_release" }, { hash: "customer_validation" }, { hash: "case_closed" }] },
      { rank: 2, frequency: 0.24, steps: [{ hash: "l1_triage" }, { hash: "severity_set" }, { hash: "eng_triage" }, { hash: "root_cause" }, { hash: "hotfix_release" }, { hash: "customer_validation" }, { hash: "case_closed" }] }
    ],
    edges: [
      { from_step_hash: "__START__", to_step_hash: "l1_triage", count: 438, probability: 1, timing: { p95_ms: 1200 } },
      { from_step_hash: "l1_triage", to_step_hash: "severity_set", count: 426, probability: 0.97, timing: { p95_ms: 48000 } },
      { from_step_hash: "severity_set", to_step_hash: "escalation_manager", count: 258, probability: 0.61, timing: { p95_ms: 180000 } },
      { from_step_hash: "severity_set", to_step_hash: "eng_triage", count: 149, probability: 0.35, timing: { p95_ms: 150000 } },
      { from_step_hash: "escalation_manager", to_step_hash: "eng_triage", count: 238, probability: 0.92, timing: { p95_ms: 260000 } },
      { from_step_hash: "eng_triage", to_step_hash: "root_cause", count: 341, probability: 0.88, timing: { p95_ms: 420000 } },
      { from_step_hash: "root_cause", to_step_hash: "patch_branch", count: 287, probability: 0.84, timing: { p95_ms: 510000 } },
      { from_step_hash: "patch_branch", to_step_hash: "review_patch", count: 265, probability: 0.92, timing: { p95_ms: 620000 } },
      { from_step_hash: "review_patch", to_step_hash: "hotfix_release", count: 241, probability: 0.91, timing: { p95_ms: 470000 } },
      { from_step_hash: "root_cause", to_step_hash: "hotfix_release", count: 48, probability: 0.14, timing: { p95_ms: 330000 } },
      { from_step_hash: "hotfix_release", to_step_hash: "customer_validation", count: 256, probability: 0.89, timing: { p95_ms: 210000 } },
      { from_step_hash: "customer_validation", to_step_hash: "case_closed", count: 233, probability: 0.91, timing: { p95_ms: 260000 } }
    ],
    bottlenecks: [{ from_step_hash: "review_patch", p95_ms: 620000 }, { from_step_hash: "patch_branch", p95_ms: 510000 }, { from_step_hash: "eng_triage", p95_ms: 420000 }]
  }
];

const DEFAULT_STORY = DEMO_STORIES[3];

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function hashSeed(input: string): number {
  let hash = 2166136261;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) / 4294967295;
}

function compact(id: string): string {
  if (id === "__START__") return "START";
  return id.length > 10 ? id.slice(0, 8) : id;
}

function pickStory(processKey: string): DemoStory {
  const key = processKey.toLowerCase();
  if (key.includes("sales")) return DEMO_STORIES[4];
  if (key.includes("escalation") || key.includes("engineering") || key.includes("support")) return DEMO_STORIES[5];
  if (key.includes("org50") || key.includes("company") || key.includes("delivery")) return DEMO_STORIES[3];
  if (key.includes("merge") || key.includes("code")) return DEMO_STORIES[1];
  if (key.includes("ticket") || key.includes("status")) return DEMO_STORIES[2];
  return DEMO_STORIES[0];
}

function fallbackEdges(variants: Variant[]): Edge[] {
  const map = new Map<string, { count: number; from: string; to: string }>();
  for (const variant of variants) {
    for (let i = 1; i < variant.steps.length; i += 1) {
      const from = variant.steps[i - 1]?.hash;
      const to = variant.steps[i]?.hash;
      if (!from || !to) continue;
      const key = `${from}|${to}`;
      const found = map.get(key);
      if (found) found.count += Math.max(1, Math.round(variant.frequency * 100));
      else map.set(key, { from, to, count: Math.max(1, Math.round(variant.frequency * 100)) });
    }
  }
  const outgoing = new Map<string, number>();
  for (const row of map.values()) outgoing.set(row.from, (outgoing.get(row.from) ?? 0) + row.count);
  return Array.from(map.values()).map((row) => ({
    from_step_hash: row.from,
    to_step_hash: row.to,
    count: row.count,
    probability: row.count / Math.max(outgoing.get(row.from) ?? 1, 1),
    timing: { p95_ms: Math.round((1 + row.count / 20) * 120000) }
  }));
}

function strongestPath(edges: Edge[]): string[] {
  const outgoing = new Map<string, Edge[]>();
  for (const edge of edges) {
    if (!outgoing.has(edge.from_step_hash)) outgoing.set(edge.from_step_hash, []);
    outgoing.get(edge.from_step_hash)?.push(edge);
  }
  for (const list of outgoing.values()) list.sort((a, b) => b.probability - a.probability || b.count - a.count);
  let cursor = outgoing.has("__START__") ? "__START__" : Array.from(outgoing.keys())[0] ?? "";
  if (!cursor) return [];
  const seen = new Set<string>([cursor]);
  const path: string[] = [];
  for (let i = 0; i < 10; i += 1) {
    const next = outgoing.get(cursor)?.find((row) => !seen.has(row.to_step_hash));
    if (!next) break;
    path.push(`${next.from_step_hash}-${next.to_step_hash}`);
    cursor = next.to_step_hash;
    if (seen.has(cursor)) break;
    seen.add(cursor);
  }
  return path;
}

function buildModel(rawEdges: Edge[], variants: Variant[], hints: Record<string, string>, seed: string): GraphModel {
  const edges = rawEdges.length > 0 ? rawEdges : fallbackEdges(variants);
  if (edges.length === 0) return { nodes: [], edges: [], labels: {}, strongestPath: [], avgProbability: 0, maxDelayMs: 0 };
  const labels: Record<string, string> = { ...hints, __START__: "Start" };
  const ids = new Set<string>();
  const incoming = new Map<string, number>();
  const outgoing = new Map<string, number>();
  for (const edge of edges) {
    ids.add(edge.from_step_hash);
    ids.add(edge.to_step_hash);
    outgoing.set(edge.from_step_hash, (outgoing.get(edge.from_step_hash) ?? 0) + edge.count);
    incoming.set(edge.to_step_hash, (incoming.get(edge.to_step_hash) ?? 0) + edge.count);
  }
  const ordered = Array.from(ids).sort((a, b) => {
    const aFlow = (incoming.get(a) ?? 0) + (outgoing.get(a) ?? 0);
    const bFlow = (incoming.get(b) ?? 0) + (outgoing.get(b) ?? 0);
    return bFlow - aFlow || a.localeCompare(b);
  });
  let stepIndex = 1;
  for (const id of ordered) {
    if (!labels[id]) {
      labels[id] = `Step ${stepIndex.toString().padStart(2, "0")}`;
      stepIndex += 1;
    }
  }

  const depths = new Map<string, number>([["__START__", 0]]);
  for (let iter = 0; iter < 12; iter += 1) {
    for (const edge of edges) {
      const fromDepth = depths.get(edge.from_step_hash);
      if (fromDepth === undefined) continue;
      const current = depths.get(edge.to_step_hash);
      const nextDepth = fromDepth + 1;
      if (current === undefined || nextDepth < current) depths.set(edge.to_step_hash, nextDepth);
    }
  }
  let fallbackDepth = 1;
  for (const id of ordered) {
    if (depths.get(id) === undefined) {
      depths.set(id, fallbackDepth);
      fallbackDepth += 1;
    }
  }
  const maxDepth = Math.max(...Array.from(depths.values()));
  const buckets = new Map<number, string[]>();
  for (const id of ordered) {
    const depth = depths.get(id) ?? 0;
    if (!buckets.has(depth)) buckets.set(depth, []);
    buckets.get(depth)?.push(id);
  }
  const maxFlow = Math.max(1, ...ordered.map((id) => (incoming.get(id) ?? 0) + (outgoing.get(id) ?? 0)));
  const nodes: GraphNode[] = [];
  for (let depth = 0; depth <= maxDepth; depth += 1) {
    const bucket = buckets.get(depth) ?? [];
    const x = ((depth + 0.7) / (maxDepth + 1.4)) * GRAPH_WIDTH;
    for (let i = 0; i < bucket.length; i += 1) {
      const id = bucket[i];
      const flow = (incoming.get(id) ?? 0) + (outgoing.get(id) ?? 0);
      const activity = flow / maxFlow;
      const yBase = ((i + 1) / (bucket.length + 1)) * GRAPH_HEIGHT;
      const jitter = (hashSeed(`${seed}-${id}`) - 0.5) * 52;
      nodes.push({
        id,
        label: labels[id],
        x,
        y: clamp(yBase + jitter, 48, GRAPH_HEIGHT - 48),
        activity,
        radius: 8 + activity * 15
      });
    }
  }
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));
  const critical = new Set(strongestPath(edges));
  const maxCount = Math.max(1, ...edges.map((edge) => edge.count));
  const maxDelayMs = Math.max(1, ...edges.map((edge) => edge.timing.p95_ms ?? 0));
  const mappedEdges: GraphEdge[] = edges.flatMap((edge) => {
    const from = nodeMap.get(edge.from_step_hash);
    const to = nodeMap.get(edge.to_step_hash);
    if (!from || !to) return [];
    const id = `${edge.from_step_hash}-${edge.to_step_hash}`;
    return [{
      id,
      from,
      to,
      probability: edge.probability,
      weight: Math.max(edge.probability, edge.count / maxCount),
      delayMs: edge.timing.p95_ms ?? 0,
      isCritical: critical.has(id)
    }];
  });
  const avgProbability = mappedEdges.reduce((sum, edge) => sum + edge.probability, 0) / Math.max(mappedEdges.length, 1);
  return { nodes, edges: mappedEdges, labels, strongestPath: Array.from(critical), avgProbability, maxDelayMs };
}

function pathFor(edge: GraphEdge): string {
  const x1 = edge.from.x;
  const y1 = edge.from.y;
  const x2 = edge.to.x;
  const y2 = edge.to.y;
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.hypot(dx, dy) || 1;
  const bend = (hashSeed(edge.id) - 0.5) * 92;
  const cx = mx - (dy / dist) * bend;
  const cy = my + (dx / dist) * bend;
  return `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`;
}

function strokeColor(edge: GraphEdge, maxDelay: number): string {
  const heat = clamp(edge.delayMs / Math.max(maxDelay, 1), 0, 1);
  const hue = 208 - heat * 170;
  const sat = 45 + heat * 20;
  const light = 66 - heat * 19;
  return `hsl(${hue} ${sat}% ${light}%)`;
}

export default function AnalyticsPage() {
  const [processKey, setProcessKey] = useState(DEFAULT_STORY.process_key);
  const [story, setStory] = useState(DEFAULT_STORY);
  const [origin, setOrigin] = useState<"live" | "demo">("demo");
  const [loadState, setLoadState] = useState<"idle" | "loading" | "ready" | "error">("ready");
  const [statusText, setStatusText] = useState(`Demo scenario: ${DEFAULT_STORY.title}. Load live data at any time.`);
  const [errorText, setErrorText] = useState("");
  const [patterns, setPatterns] = useState<Pattern[]>(DEFAULT_STORY.patterns);
  const [variants, setVariants] = useState<Variant[]>(DEFAULT_STORY.variants);
  const [edges, setEdges] = useState<Edge[]>(DEFAULT_STORY.edges);
  const [bottlenecks, setBottlenecks] = useState<Array<{ from_step_hash: string; p95_ms: number }>>(DEFAULT_STORY.bottlenecks);
  const [selectedPatternId, setSelectedPatternId] = useState(DEFAULT_STORY.patterns[0]?.pattern_id ?? "");
  const [hoverNodeId, setHoverNodeId] = useState<string | null>(null);
  const [hoverEdgeId, setHoverEdgeId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [criticalOnly, setCriticalOnly] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [graphKey, setGraphKey] = useState(0);
  const drag = useRef({ active: false, startX: 0, startY: 0, originX: 0, originY: 0 });

  const graph = useMemo(() => buildModel(edges, variants, origin === "demo" ? story.labels : {}, processKey), [edges, variants, origin, story, processKey]);
  const visibleEdges = useMemo(() => (criticalOnly ? graph.edges.filter((edge) => edge.isCritical) : graph.edges), [graph.edges, criticalOnly]);
  const selectedNode = selectedNodeId ? graph.nodes.find((node) => node.id === selectedNodeId) : null;
  const selectedEdge = selectedEdgeId ? graph.edges.find((edge) => edge.id === selectedEdgeId) : null;
  const zoomLabel = `${Math.round(zoom * 100)}%`;
  const panLabel = `${Math.round(pan.x)},${Math.round(pan.y)}`;

  function resetGraphView() {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }

  function applyStory(next: DemoStory, reason: string) {
    setStory(next);
    setOrigin("demo");
    setProcessKey(next.process_key);
    setPatterns(next.patterns);
    setVariants(next.variants);
    setEdges(next.edges);
    setBottlenecks(next.bottlenecks);
    setSelectedPatternId(next.patterns[0]?.pattern_id ?? "");
    setStatusText(reason);
    setLoadState("ready");
    setErrorText("");
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
    resetGraphView();
    setGraphKey((prev) => prev + 1);
  }

  async function loadPatternDetails(patternId: string) {
    const [variantsRes, edgesRes, bottlenecksRes] = await Promise.all([
      fetch(`${API_BASE}/api/v1/analytics/patterns/${patternId}/variants`, { headers: HEADERS }),
      fetch(`${API_BASE}/api/v1/analytics/patterns/${patternId}/edges`, { headers: HEADERS }),
      fetch(`${API_BASE}/api/v1/analytics/patterns/${patternId}/bottlenecks`, { headers: HEADERS })
    ]);
    if (!variantsRes.ok || !edgesRes.ok || !bottlenecksRes.ok) throw new Error("pattern details unavailable");
    const variantsBody = (await variantsRes.json()) as { variants: Variant[] };
    const edgesBody = (await edgesRes.json()) as { edges: Edge[] };
    const bottlenecksBody = (await bottlenecksRes.json()) as { bottlenecks: Array<{ from_step_hash: string; p95_ms: number }> };
    setVariants(variantsBody.variants);
    setEdges(edgesBody.edges);
    setBottlenecks(bottlenecksBody.bottlenecks);
    setSelectedPatternId(patternId);
  }

  async function loadPatterns(event: FormEvent) {
    event.preventDefault();
    setLoadState("loading");
    setErrorText("");
    const fallback = pickStory(processKey);
    try {
      const response = await fetch(`${API_BASE}/api/v1/analytics/processes/${encodeURIComponent(processKey)}/patterns`, { headers: HEADERS });
      if (!response.ok) throw new Error(`http ${response.status}`);
      const body = (await response.json()) as { patterns: Pattern[] };
      if (!body.patterns.length) {
        applyStory(fallback, "No published live patterns found. Showing curated demo story.");
        return;
      }
      setOrigin("live");
      setStory(fallback);
      setPatterns(body.patterns);
      await loadPatternDetails(body.patterns[0].pattern_id);
      setStatusText("Live analytics loaded.");
      setLoadState("ready");
      setSelectedNodeId(null);
      setSelectedEdgeId(null);
      resetGraphView();
      setGraphKey((prev) => prev + 1);
    } catch {
      applyStory(fallback, "Live API unavailable. Demo story activated.");
      setLoadState("error");
      setErrorText("Live endpoint is unavailable. Demo data is currently displayed.");
    }
  }

  async function selectPattern(pattern: Pattern) {
    if (origin === "demo") {
      setSelectedPatternId(pattern.pattern_id);
      setStatusText(`Demo pattern selected: ${pattern.title ?? pattern.pattern_id}`);
      setGraphKey((prev) => prev + 1);
      return;
    }
    try {
      setLoadState("loading");
      await loadPatternDetails(pattern.pattern_id);
      setStatusText("Live pattern updated.");
      setLoadState("ready");
      setGraphKey((prev) => prev + 1);
    } catch {
      setLoadState("error");
      setErrorText("Could not load pattern details.");
    }
  }

  function onWheel(event: WheelEvent<HTMLDivElement>) {
    event.preventDefault();
    const delta = event.deltaY > 0 ? -0.1 : 0.1;
    setZoom((prev) => clamp(prev + delta, 0.55, 2.7));
  }

  function onPointerDown(event: PointerEvent<HTMLDivElement>) {
    drag.current = { active: true, startX: event.clientX, startY: event.clientY, originX: pan.x, originY: pan.y };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event: PointerEvent<HTMLDivElement>) {
    if (!drag.current.active) return;
    const dx = event.clientX - drag.current.startX;
    const dy = event.clientY - drag.current.startY;
    setPan({ x: drag.current.originX + dx, y: drag.current.originY + dy });
  }

  function onPointerUp(event: PointerEvent<HTMLDivElement>) {
    drag.current.active = false;
    event.currentTarget.releasePointerCapture(event.pointerId);
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const scenario = params.get("scenario");
    if (scenario) {
      const normalized = scenario.toLowerCase();
      const mapped =
        normalized.startsWith("sal")
          ? DEMO_STORIES[4]
          : normalized.startsWith("cust") || normalized.startsWith("eng") || normalized.startsWith("sup")
            ? DEMO_STORIES[5]
            : normalized.startsWith("org") || normalized.includes("50")
          ? DEMO_STORIES[3]
          : normalized.startsWith("rel")
          ? DEMO_STORIES[1]
          : normalized.startsWith("esc")
            ? DEMO_STORIES[2]
            : normalized.startsWith("inc")
              ? DEMO_STORIES[0]
              : pickStory(scenario);
      applyStory(mapped, `Demo scenario: ${mapped.title}`);
    }

    const focus = params.get("focus");
    if (focus === "1" || focus === "true") {
      setCriticalOnly(true);
    }

    const zoomParam = Number(params.get("zoom"));
    if (Number.isFinite(zoomParam) && zoomParam > 0) {
      setZoom(clamp(zoomParam, 0.55, 2.7));
    }

    const panX = Number(params.get("panx"));
    const panY = Number(params.get("pany"));
    if (Number.isFinite(panX) || Number.isFinite(panY)) {
      setPan({
        x: Number.isFinite(panX) ? panX : 0,
        y: Number.isFinite(panY) ? panY : 0
      });
    }
    // Run only on first client render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section className="stack">
      <header className="section-intro reveal">
        <p className="eyebrow">Process Mining</p>
        <h1 className="headline">Process Explorer</h1>
        <p className="subtitle">Neuron-style context graph with curated demo stories, richer interaction, and critical-flow insights.</p>
      </header>

      <div className="process-presets">
        {DEMO_STORIES.map((item) => (
          <button className="button ghost preset-chip" key={item.process_key} onClick={() => applyStory(item, `Demo scenario: ${item.title}`)} type="button">
            {item.title}
          </button>
        ))}
      </div>

      <form className="panel form-card reveal" onSubmit={loadPatterns}>
        <label className="form-row">
          <span>Process key</span>
          <input value={processKey} onChange={(event) => setProcessKey(event.currentTarget.value)} />
        </label>
        <div className="form-actions">
          <button className="button accent" type="submit">{loadState === "loading" ? "Loading..." : "Load live process"}</button>
          <button className="button ghost" onClick={() => applyStory(pickStory(processKey), "Demo scenario selected by process key.")} type="button">Use demo</button>
        </div>
      </form>

      <div className={`status-strip ${origin}`}>{origin === "live" ? "LIVE DATA" : "DEMO DATA"} · {statusText}</div>
      {errorText ? <p className="status-error">{errorText}</p> : null}

      <div className="analytics-stage">
        <article className="panel reveal">
          <div className="panel-head">
            <h2 className="panel-title">Neural Context Graph</h2>
            <div className="row-actions">
              <span className="badge">{graph.nodes.length} nodes / {graph.edges.length} links</span>
              <button className="button ghost" onClick={() => setCriticalOnly((value) => !value)} type="button">{criticalOnly ? "Show all links" : "Focus critical path"}</button>
              <button className="button ghost" onClick={resetGraphView} type="button">Reset view</button>
            </div>
          </div>
          <p className="kicker">Pan with drag, zoom with wheel, hover for details. Strong links pulse and warmer colors reveal bottlenecks.</p>
          <div className="graph-status-row">
            <span className="badge view-badge">View {zoomLabel}</span>
            <span className="badge view-badge">Pan {panLabel}</span>
            {criticalOnly ? <span className="critical-indicator">Critical Path Active</span> : null}
          </div>

          <div className={`neural-wrap interactive ${loadState === "loading" ? "is-loading" : ""}`} onWheel={onWheel} onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerLeave={() => { drag.current.active = false; }}>
            {loadState === "loading" ? (
              <div className="neural-skeleton">Building process neurons...</div>
            ) : graph.nodes.length === 0 ? (
              <div className="neural-empty">No transitions available for this process.</div>
            ) : (
              <svg className="neural-canvas" role="img" viewBox={`0 0 ${GRAPH_WIDTH} ${GRAPH_HEIGHT}`}>
                <g key={graphKey} className="graph-stage" transform={`translate(${pan.x} ${pan.y}) scale(${zoom})`}>
                  {visibleEdges.map((edge) => {
                    const relatedToNode = hoverNodeId ? edge.from.id === hoverNodeId || edge.to.id === hoverNodeId : true;
                    const relatedToEdge = hoverEdgeId ? edge.id === hoverEdgeId : true;
                    const dim = !(relatedToNode && relatedToEdge);
                    const pulse = edge.isCritical || edge.delayMs > graph.maxDelayMs * 0.72;
                    return (
                      <path
                        className={`neural-link ${pulse ? "pulse" : ""} ${edge.isCritical ? "critical" : ""} ${dim ? "dim" : ""}`}
                        d={pathFor(edge)}
                        key={edge.id}
                        onMouseEnter={() => { setHoverEdgeId(edge.id); setSelectedEdgeId(edge.id); }}
                        onMouseLeave={() => setHoverEdgeId(null)}
                        stroke={strokeColor(edge, graph.maxDelayMs)}
                        strokeOpacity={dim ? 0.14 : edge.isCritical ? 0.92 : 0.56}
                        strokeWidth={1.1 + edge.weight * 5.2 + (edge.isCritical ? 1 : 0)}
                      >
                        <title>{`${graph.labels[edge.from.id]} -> ${graph.labels[edge.to.id]} (${(edge.probability * 100).toFixed(1)}%, p95 ${Math.round(edge.delayMs / 1000)}s)`}</title>
                      </path>
                    );
                  })}
                  {graph.nodes.map((node) => {
                    const connected = hoverNodeId
                      ? node.id === hoverNodeId || visibleEdges.some((edge) => edge.from.id === hoverNodeId && edge.to.id === node.id) || visibleEdges.some((edge) => edge.to.id === hoverNodeId && edge.from.id === node.id)
                      : true;
                    const dim = !connected;
                    const selected = selectedNodeId === node.id;
                    const showLabel = selected || node.activity > 0.62 || hoverNodeId === node.id || node.id === "__START__";
                    return (
                      <g className={`neural-node-group ${dim ? "dim" : ""}`} key={node.id} onClick={() => setSelectedNodeId(node.id)} onMouseEnter={() => setHoverNodeId(node.id)} onMouseLeave={() => setHoverNodeId(null)} transform={`translate(${node.x} ${node.y})`}>
                        <circle className={`neural-node-halo ${node.activity > 0.65 ? "hot" : ""}`} r={node.radius + 10} />
                        <circle className={`neural-node ${selected ? "selected" : ""}`} r={node.radius} />
                        {showLabel ? <text className="neural-label" y={node.radius + 16}>{node.label}</text> : null}
                        <title>{node.label}</title>
                      </g>
                    );
                  })}
                </g>
              </svg>
            )}
          </div>
        </article>

        <aside className="panel reveal insight-panel">
          <h2 className="panel-title">Insights</h2>
          <div className="insight-row"><span>Scenario</span><strong>{origin === "live" ? "Live process" : story.title}</strong></div>
          {origin === "demo" && story.company_size ? <div className="insight-row"><span>Sim org size</span><strong>{story.company_size} employees</strong></div> : null}
          {origin === "demo" && story.team_count ? <div className="insight-row"><span>Teams in flow</span><strong>{story.team_count}</strong></div> : null}
          {origin === "demo" && story.monthly_traces ? <div className="insight-row"><span>Monthly traces</span><strong>{story.monthly_traces}</strong></div> : null}
          <div className="insight-row"><span>Avg confidence</span><strong>{(graph.avgProbability * 100).toFixed(1)}%</strong></div>
          <div className="insight-row"><span>Max p95 delay</span><strong>{Math.round(graph.maxDelayMs / 1000)}s</strong></div>
          <div className="insight-row"><span>Top bottleneck</span><strong>{bottlenecks[0] ? graph.labels[bottlenecks[0].from_step_hash] ?? compact(bottlenecks[0].from_step_hash) : "n/a"}</strong></div>

          <h3 className="panel-title insight-subtitle">Critical Flow</h3>
          <div className="critical-list">
            {graph.strongestPath.length === 0 ? <p className="muted">No critical flow available.</p> : null}
            {graph.strongestPath.map((item) => {
              const [from, to] = item.split("-");
              return <p className="critical-item" key={item}>{`${graph.labels[from] ?? compact(from)} -> ${graph.labels[to] ?? compact(to)}`}</p>;
            })}
          </div>

          <h3 className="panel-title insight-subtitle">Selection</h3>
          {selectedNode ? <p className="metric"><strong>Node:</strong> {selectedNode.label}</p> : null}
          {selectedEdge ? <p className="metric"><strong>Edge:</strong> {graph.labels[selectedEdge.from.id]} {" -> "} {graph.labels[selectedEdge.to.id]} ({(selectedEdge.probability * 100).toFixed(1)}%, p95 {Math.round(selectedEdge.delayMs / 1000)}s)</p> : <p className="muted">Hover/click nodes or links for details.</p>}
        </aside>
      </div>

      <div className="panel-grid">
        <article className="panel reveal">
          <h2 className="panel-title">Published Patterns</h2>
          <div className="list">
            {patterns.length === 0 ? <p className="muted">No patterns loaded yet.</p> : null}
            {patterns.map((pattern) => (
              <button className={`row-line pattern-row ${pattern.pattern_id === selectedPatternId ? "active" : ""}`} key={pattern.pattern_id} onClick={() => void selectPattern(pattern)} type="button">
                <span>
                  <span className="row-title">{pattern.title ?? pattern.pattern_id}</span>
                  <span className="metric mono">{pattern.pattern_id}</span>
                </span>
                <span className="badge">{pattern.distinct_user_count} users</span>
              </button>
            ))}
          </div>
        </article>
        <article className="panel reveal">
          <h2 className="panel-title">Top Variants</h2>
          <div className="list">
            {variants.length === 0 ? <p className="muted">No variant data yet.</p> : null}
            {variants.map((variant) => (
              <div className="row-line" key={variant.rank}>
                <div>
                  <p className="row-title">Rank {variant.rank}</p>
                  <p className="metric">{variant.steps.length} steps</p>
                </div>
                <span className="badge">{(variant.frequency * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </article>
        <article className="panel reveal">
          <h2 className="panel-title">Bottlenecks</h2>
          <div className="list">
            {bottlenecks.length === 0 ? <p className="muted">No bottlenecks detected.</p> : null}
            {bottlenecks.map((item) => (
              <div className="row-line" key={`${item.from_step_hash}-${item.p95_ms}`}>
                <p className="row-title">{graph.labels[item.from_step_hash] ?? compact(item.from_step_hash)}</p>
                <span className="badge">{Math.round(item.p95_ms / 1000)}s p95</span>
              </div>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}

