import { AppShell } from "../../components/app-shell";
import { ApprovalInbox } from "../../components/approval-inbox";
import { PageIntro, SectionTitle } from "../../components/ui";

export default function ApprovalsPage() {
  return <AppShell><PageIntro eyebrow="Human control" title="Approval inbox" description="Review the actions your AI workflows want to take outside the system." /><div className="approval-summary"><div className="approval-summary-main"><div className="approval-summary-icon"><span className="live-dot" /></div><div><strong>12 actions need your attention</strong><span>External and high-impact actions are paused until a human decides.</span></div></div><div className="approval-summary-stats"><div><strong>8</strong><span>external</span></div><div><strong>4</strong><span>finance</span></div></div></div><section className="approval-section"><SectionTitle title="Needs review" subtitle="Sorted by confidence and age" /><ApprovalInbox /></section></AppShell>;
}
