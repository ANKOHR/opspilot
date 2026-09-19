import type { ReactNode } from "react";

export type IconName =
  | "activity"
  | "arrow"
  | "calendar"
  | "chart"
  | "check"
  | "chevron"
  | "coin"
  | "edit"
  | "file"
  | "globe"
  | "inbox"
  | "link"
  | "mail"
  | "message"
  | "more"
  | "play"
  | "plus"
  | "refresh"
  | "search"
  | "settings"
  | "shield"
  | "spark"
  | "workflow"
  | "x";

const stroke = { fill: "none", stroke: "currentColor", strokeLinecap: "round" as const, strokeLinejoin: "round" as const, strokeWidth: 1.8 };

function glyph(name: IconName): ReactNode {
  switch (name) {
    case "activity": return <><path {...stroke} d="M3 12h3l2-7 4 14 2-7h7" /></>;
    case "arrow": return <><path {...stroke} d="M5 12h14M13 6l6 6-6 6" /></>;
    case "calendar": return <><rect {...stroke} x="3" y="4" width="18" height="17" rx="3" /><path {...stroke} d="M7 2v4M17 2v4M3 9h18" /></>;
    case "chart": return <><path {...stroke} d="M4 19V5M4 19h17" /><path {...stroke} d="m7 15 3-4 3 2 5-7" /></>;
    case "check": return <><path {...stroke} d="m5 12 4 4L19 6" /></>;
    case "chevron": return <><path {...stroke} d="m8 10 4 4 4-4" /></>;
    case "coin": return <><circle {...stroke} cx="12" cy="12" r="8" /><path {...stroke} d="M14.5 8.8c-.6-.6-1.5-.9-2.5-.9-1.3 0-2.3.6-2.3 1.5 0 2.3 4.9 1 4.9 3.6 0 1-.9 1.6-2.5 1.6-1.1 0-2-.3-2.7-1M12 6.5v11" /></>;
    case "edit": return <><path {...stroke} d="m4 16.8-.7 3.2 3.2-.7L18 7.8l-2.5-2.5L4 16.8Z" /><path {...stroke} d="m14 6.3 2.5 2.5" /></>;
    case "file": return <><path {...stroke} d="M6 3h8l4 4v14H6z" /><path {...stroke} d="M14 3v5h5M9 12h6M9 16h6" /></>;
    case "globe": return <><circle {...stroke} cx="12" cy="12" r="9" /><path {...stroke} d="M3 12h18M12 3c2.2 2.4 3.3 5.4 3.3 9s-1.1 6.6-3.3 9c-2.2-2.4-3.3-5.4-3.3-9S9.8 5.4 12 3Z" /></>;
    case "inbox": return <><path {...stroke} d="M4 4h16l2 11H2L4 4Z" /><path {...stroke} d="M2 15h5l2 3h6l2-3h5M8 8h8" /></>;
    case "link": return <><path {...stroke} d="M10 13.8 8.4 15.4a3.5 3.5 0 0 1-5-5l2.2-2.2a3.5 3.5 0 0 1 5 0" /><path {...stroke} d="m14 10.2 1.6-1.6a3.5 3.5 0 0 1 5 5l-2.2 2.2a3.5 3.5 0 0 1-5 0" /><path {...stroke} d="m8.5 15.5 7-7" /></>;
    case "mail": return <><rect {...stroke} x="3" y="5" width="18" height="14" rx="3" /><path {...stroke} d="m4 7 8 6 8-6" /></>;
    case "message": return <><path {...stroke} d="M4 5h16v11H9l-5 4V5Z" /><path {...stroke} d="M8 9h8M8 12h5" /></>;
    case "more": return <><circle fill="currentColor" cx="5" cy="12" r="1.5" /><circle fill="currentColor" cx="12" cy="12" r="1.5" /><circle fill="currentColor" cx="19" cy="12" r="1.5" /></>;
    case "play": return <><path {...stroke} d="m8 5 10 7-10 7V5Z" /></>;
    case "plus": return <><path {...stroke} d="M12 5v14M5 12h14" /></>;
    case "refresh": return <><path {...stroke} d="M20 11a8 8 0 0 0-14.7-3.8L3 10M3 5v5h5M4 13a8 8 0 0 0 14.7 3.8L21 14M21 19v-5h-5" /></>;
    case "search": return <><circle {...stroke} cx="10.8" cy="10.8" r="6.8" /><path {...stroke} d="m16 16 5 5" /></>;
    case "settings": return <><path {...stroke} d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" /><path {...stroke} d="m19.4 15 .1.1a2 2 0 0 1-2.8 2.8l-.1-.1a2 2 0 0 0-3.4 1.4v.2a2 2 0 0 1-4 0v-.2A2 2 0 0 0 5.8 18l-.1.1a2 2 0 0 1-2.8-2.8l.1-.1a2 2 0 0 0-1.4-3.4h-.2a2 2 0 0 1 0-4h.2A2 2 0 0 0 3 4.4l-.1-.1a2 2 0 0 1 2.8-2.8l.1.1a2 2 0 0 0 3.4-1.4V0a2 2 0 0 1 4 0v.2A2 2 0 0 0 16.6 1l.1-.1a2 2 0 0 1 2.8 2.8l-.1.1a2 2 0 0 0 1.4 3.4h.2a2 2 0 0 1 0 4h-.2a2 2 0 0 0-1.4 3.4Z" transform="translate(1 1) scale(.83)" /></>;
    case "shield": return <><path {...stroke} d="M12 3 19 6v5c0 4.6-2.8 8-7 10-4.2-2-7-5.4-7-10V6l7-3Z" /><path {...stroke} d="m9 12 2 2 4-4" /></>;
    case "spark": return <><path {...stroke} d="m12 3 1.4 5.6L19 10l-5.6 1.4L12 17l-1.4-5.6L5 10l5.6-1.4L12 3ZM19 16l.6 2.4L22 19l-2.4.6L19 22l-.6-2.4L16 19l2.4-.6L19 16Z" /></>;
    case "workflow": return <><circle {...stroke} cx="6" cy="6" r="2.5" /><circle {...stroke} cx="18" cy="6" r="2.5" /><circle {...stroke} cx="12" cy="18" r="2.5" /><path {...stroke} d="M8.5 6h7M7.7 8.2l2.8 7.2M16.3 8.2l-2.8 7.2" /></>;
    case "x": return <><path {...stroke} d="m6 6 12 12M18 6 6 18" /></>;
  }
}

export function Icon({ name, size = 18, strokeWidth }: { name: IconName; size?: number; strokeWidth?: number }) {
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" style={strokeWidth ? { strokeWidth } : undefined}>{glyph(name)}</svg>;
}

