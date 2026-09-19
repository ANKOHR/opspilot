"use client";

import { useState } from "react";

import { activity, overviewMetrics, workflows } from "../lib/demo-data";
import { Icon } from "./icons";
import { Button, MetricCard, PageIntro, SectionTitle, SparkBars, StatusPill } from "./ui";

export function Dashboard() {
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState("");

  async function runShowcase() {
    setRunning(true);
    setMessage("");
    try {
      const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const response = await fetch(`${api}/api/demo/inbound-lead`, { method: "POST" });
      const payload = await response.json().catch(() => null) as { status?: string } | null;
      if (response.ok) {
        setMessage(payload?.status === "waiting_for_approval" ? "Run created and paused for approval." : `Showcase replay returned ${payload?.status ?? "a result"}.`);
      } else {
        setMessage("Demo is ready in sandbox preview mode.");
      }
    } catch {
      setMessage("Demo is ready in sandbox preview mode.");
    }
    setRunning(false);
  }

  return <>
    <PageIntro eyebrow="Friday · 19 September 2026" title="Good evening, Henry" description="Here’s what your AI operations team has been doing today." action={<Button icon="play" onClick={runShowcase} disabled={running}>{running ? "Starting showcase…" : "Run showcase"}</Button>} />
    {message && <div className="toast"><span className="live-dot" />{message}</div>}
    <div className="metric-grid">{overviewMetrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}</div>
    <div className="dashboard-grid">
      <section className="panel activity-panel"><SectionTitle title="Recent activity" subtitle="Live view across your workflows" action={<a className="text-link" href="/runs">View all <Icon name="arrow" size={14} /></a>} /><div className="activity-list">{activity.map((item) => <div className="activity-row" key={`${item.time}-${item.label}`}><div className={`activity-icon ${item.tone}`}><Icon name={item.icon as Parameters<typeof Icon>[0]["name"]} size={16} /></div><div className="activity-copy"><strong>{item.label}</strong><span>{item.detail}</span></div><StatusPill status={item.status} /><time>{item.time}</time></div>)}</div></section>
      <section className="panel health-panel"><SectionTitle title="System health" subtitle="All systems operational" /><div className="health-hero"><div className="health-score">99.98<span>%</span></div><span className="health-label"><i /> Platform uptime</span></div><div className="health-rows"><div><span>API latency</span><strong>142ms</strong><em className="good">−12ms</em></div><div><span>Queue depth</span><strong>4 jobs</strong><em className="good">Healthy</em></div><div><span>Provider health</span><strong>3 / 3</strong><em className="good">Operational</em></div></div></section>
    </div>
    <section className="panel workflow-overview"><SectionTitle title="Active workflows" subtitle="Your automation fleet at a glance" action={<a className="text-link" href="/workflows">Manage workflows <Icon name="arrow" size={14} /></a>} /><div className="workflow-cards">{workflows.map((workflow) => <div className="workflow-mini" key={workflow.id}><div className="workflow-mini-head"><div className="workflow-symbol"><Icon name="workflow" size={17} /></div><StatusPill status={workflow.status} /><button className="more-button" aria-label="More options"><Icon name="more" size={15} /></button></div><h3>{workflow.name}</h3><p>{workflow.description}</p><div className="workflow-mini-foot"><div><strong>{workflow.runs}</strong><span>runs</span></div><div><strong>{workflow.success}</strong><span>success</span></div><SparkBars values={[4, 7, 5, 9, 8, 6, 10]} /></div></div>)}</div></section>
  </>;
}
