"use client";

import { useEffect, useState } from "react";

import { approvals as fallbackApprovals } from "../lib/demo-data";
import type { Approval } from "../lib/types";
import { ApprovalCard } from "./approval-card";

type ApiApproval = {
  id: string;
  run_id: string;
  title: string;
  summary: string;
  proposed_action: { to?: string; subject?: string; body?: string };
  status: string;
  created_at: string;
};

export function ApprovalInbox() {
  const [items, setItems] = useState<Approval[]>(fallbackApprovals);

  useEffect(() => {
    const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    fetch(`${api}/api/approvals`)
      .then(async (response) => (response.ok ? response.json() as Promise<ApiApproval[]> : []))
      .then((records) => {
        const pending = records.filter((record) => record.status === "pending");
        if (pending.length) {
          setItems(pending.map((record) => ({
            id: record.id,
            title: record.title,
            subtitle: record.summary,
            recipient: record.proposed_action.to ?? "sandbox recipient",
            subject: record.proposed_action.subject ?? "Proposed external action",
            body: record.proposed_action.body ?? record.summary,
            score: 94,
            created: "live",
            runId: record.run_id,
          })));
        }
      })
      .catch(() => undefined);
  }, []);

  return <>{items.map((approval) => <ApprovalCard key={approval.id} approval={approval} onResolved={(id) => setItems((current) => current.filter((item) => item.id !== id))} />)}</>;
}

