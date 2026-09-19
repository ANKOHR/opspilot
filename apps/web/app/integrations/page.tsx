import { AppShell } from "../../components/app-shell";
import { Icon } from "../../components/icons";
import { integrations } from "../../lib/demo-data";
import { Button, PageIntro, SectionTitle, StatusPill } from "../../components/ui";

export default function IntegrationsPage() {
  return <AppShell><PageIntro eyebrow="Connect your stack" title="Integrations" description="Give workflows scoped access to the tools your team already uses." action={<Button icon="plus">Add integration</Button>} /><div className="integration-notice"><div className="notice-icon"><Icon name="shield" size={18} /></div><div><strong>Credentials stay server-side</strong><span>OpsPilot never exposes refresh tokens to the browser. External actions remain approval-gated.</span></div><StatusPill status="Protected" /></div><section className="panel integrations-panel"><SectionTitle title="Connected tools" subtitle="4 connector slots · 2 active" /><div className="integration-grid">{integrations.map((integration) => <div className="integration-card" key={integration.name}><div className="integration-card-head"><div className={`integration-logo ${integration.name.toLowerCase().replace(" ", "-")}`}><Icon name={integration.icon as Parameters<typeof Icon>[0]["name"]} size={19} /></div><StatusPill status={integration.status} /></div><h3>{integration.name}</h3><p>{integration.description}</p><div className="integration-card-foot"><span>{integration.detail}</span><button className="more-button" aria-label={`Configure ${integration.name}`}><Icon name="more" size={16} /></button></div></div>)}</div></section></AppShell>;
}

