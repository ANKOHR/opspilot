export type RunStatus = "succeeded" | "waiting_for_approval" | "running" | "failed" | "rejected";

export type TraceItem = {
  id: string;
  step: string;
  title: string;
  detail: string;
  time: string;
  duration?: string;
  tone: "green" | "blue" | "amber" | "red" | "violet";
  icon: string;
};

export type Approval = {
  id: string;
  title: string;
  subtitle: string;
  recipient: string;
  subject: string;
  body: string;
  score: number;
  created: string;
  runId: string;
};

export type Workflow = {
  id: string;
  name: string;
  description: string;
  trigger: string;
  status: "live" | "draft";
  runs: number;
  success: string;
  steps: { id: string; label: string; kind: string; state: "complete" | "approval" | "next" }[];
};

