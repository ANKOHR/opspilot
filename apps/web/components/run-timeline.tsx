import { runTrace } from "../lib/demo-data";
import { Icon } from "./icons";

export function RunTimeline({ compact = false }: { compact?: boolean }) {
  const items = compact ? runTrace.slice(0, 5) : runTrace;
  return <div className="run-timeline">{items.map((item, index) => <div className="trace-row" key={item.id}><div className={`trace-icon ${item.tone}`}><Icon name={item.icon as Parameters<typeof Icon>[0]["name"]} size={16} /></div><div className="trace-line">{index < items.length - 1 && <span />}</div><div className="trace-copy"><div className="trace-heading"><strong>{item.title}</strong><span>{item.time}</span></div><p>{item.detail}</p><div className="trace-meta"><span className={`trace-dot ${item.tone}`} />{item.step}<i>·</i>{item.duration}</div></div></div>)}</div>;
}

