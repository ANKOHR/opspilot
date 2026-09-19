import Link from "next/link";

import { AppShell } from "../../../components/app-shell";
import { Icon } from "../../../components/icons";
import { RunTimeline } from "../../../components/run-timeline";
import { runs } from "../../../lib/demo-data";
import { Button, PageIntro, SectionTitle, StatusPill } from "../../../components/ui";

export default async function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const run = runs.find((item) => item.id === id) ?? runs[0];
  return <AppShell><div className="detail-breadcrumb"><Link href="/runs"><Icon name="arrow" size={14} /> Back to runs</Link><span>/</span><strong>{run.id}</strong></div><PageIntro eyebrow="Run trace · Inbound Revenue Agent · version 7" title={run.id} description="A complete, replayable trace of the inbound revenue workflow." action={<div className="button-row"><Button variant="secondary" icon="refresh">Replay run</Button><Button variant="ghost" icon="more">More</Button></div>} /><div className="run-banner"><div className="run-banner-status"><StatusPill status={run.status} /><span>Started 2 min ago</span></div><div className="run-banner-metrics"><div><span>Runtime</span><strong>{run.duration}</strong></div><div><span>Steps</span><strong>7 / 10</strong></div><div><span>LLM cost</span><strong>$0.0036</strong></div><div><span>Trace ID</span><strong className="mono">{run.id}</strong></div></div></div><div className="detail-grid run-detail-grid"><section className="panel trace-panel"><SectionTitle title="Execution trace" subtitle="Chronological events with inputs, outputs and latency" /><RunTimeline /></section><aside className="detail-side"><section className="panel"><SectionTitle title="Current state" /><div className="state-card amber"><div className="state-icon"><Icon name="shield" size={20} /></div><div><strong>Waiting for approval</strong><p>The proposed email is ready for a human decision.</p></div></div><Link className="approval-shortcut" href="/approvals"><span><Icon name="inbox" size={15} /> Open approval inbox</span><Icon name="arrow" size={15} /></Link></section><section className="panel"><SectionTitle title="Run context" /><div className="context-list"><div><span>Workflow version</span><strong>v7 · immutable</strong></div><div><span>Trigger</span><strong>gmail.email_received</strong></div><div><span>Organisation</span><strong>Northstar Demo</strong></div><div><span>Policy budget</span><strong>12 / 15 tool calls</strong></div></div></section></aside></div></AppShell>;
}

