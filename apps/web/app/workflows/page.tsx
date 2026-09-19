import Link from "next/link";

import { AppShell } from "../../components/app-shell";
import { Icon } from "../../components/icons";
import { workflows } from "../../lib/demo-data";
import { Button, PageIntro, SectionTitle, StatusPill } from "../../components/ui";

export default function WorkflowsPage() {
  return <AppShell><PageIntro eyebrow="Automation library" title="Workflows" description="Versioned, observable playbooks that keep humans in control." action={<Button icon="plus">New workflow</Button>} /><div className="summary-strip"><div><span>Active workflows</span><strong>2</strong></div><div><span>Runs this week</span><strong>342</strong></div><div><span>Average success</span><strong>97.1%</strong></div><div><span>Approval gates</span><strong>8</strong></div></div><section className="panel workflow-list-panel"><SectionTitle title="Workflow library" subtitle="Each workflow runs against an immutable versioned definition." /><div className="workflow-list">{workflows.map((workflow) => <Link className="workflow-row" href={`/workflows/${workflow.id}`} key={workflow.id}><div className="workflow-row-icon"><Icon name="workflow" size={19} /></div><div className="workflow-row-copy"><div><h3>{workflow.name}</h3><StatusPill status={workflow.status} /></div><p>{workflow.description}</p><div className="workflow-row-meta"><span><Icon name="inbox" size={14} />{workflow.trigger}</span><span><Icon name="activity" size={14} />{workflow.runs} runs</span><span><Icon name="check" size={14} />{workflow.success} success</span></div></div><div className="workflow-row-arrow"><Icon name="arrow" size={18} /></div></Link>)}</div></section></AppShell>;
}

