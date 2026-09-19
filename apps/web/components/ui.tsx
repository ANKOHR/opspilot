import type { ReactNode } from "react";

import { Icon, type IconName } from "./icons";

export function PageIntro({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="page-intro"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>{action && <div className="intro-action">{action}</div>}</div>;
}

export function MetricCard({ label, value, change, note, tone, icon }: { label: string; value: string; change: string; note: string; tone: string; icon: IconName }) {
  return <div className={`metric-card tone-${tone}`}><div className="metric-top"><span>{label}</span><span className="metric-icon"><Icon name={icon} size={16} /></span></div><div className="metric-value">{value}</div><div className="metric-foot"><strong>{change}</strong><span>{note}</span></div></div>;
}

export function SectionTitle({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return <div className="section-title"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{action}</div>;
}

export function StatusPill({ status }: { status: string }) {
  const normalized = status.toLowerCase().replaceAll("_", " ");
  const tone = normalized.includes("success") || normalized === "live" || normalized === "connected" ? "green" : normalized.includes("wait") || normalized.includes("sandbox") || normalized.includes("review") || normalized.includes("draft") ? "amber" : normalized.includes("fail") || normalized.includes("reject") || normalized.includes("attention") ? "red" : "blue";
  return <span className={`status-pill ${tone}`}><i />{status.replaceAll("_", " ")}</span>;
}

export function Button({ children, variant = "primary", icon, onClick, disabled, type = "button" }: { children: ReactNode; variant?: "primary" | "secondary" | "ghost" | "danger"; icon?: IconName; onClick?: () => void; disabled?: boolean; type?: "button" | "submit" }) {
  return <button type={type} className={`button ${variant}`} onClick={onClick} disabled={disabled}>{icon && <Icon name={icon} size={16} />}{children}</button>;
}

export function SparkBars({ values }: { values: number[] }) {
  const max = Math.max(...values);
  return <div className="spark-bars" aria-label="Seven day activity chart">{values.map((value, index) => <span key={index} style={{ height: `${Math.max(12, (value / max) * 100)}%` }} />)}</div>;
}

export function EmptyState({ icon, title, text }: { icon: IconName; title: string; text: string }) {
  return <div className="empty-state"><div className="empty-icon"><Icon name={icon} size={23} /></div><h3>{title}</h3><p>{text}</p></div>;
}

