export interface Manager {
  name: string;
  email: string;
}

export interface PlanRow {
  machine_id: string;
  location: string;
  manager: Manager;
  unresolved_faults: number;
  fault_code: string | null;
  revenue_at_risk: number;
  priority_score: number;
  bulletin?: string;
  draft_message?: string;
  needs_approval?: boolean;
}

export interface DispatchPlan {
  ranked: PlanRow[];
  actions: PlanRow[];
  summary: string;
  thread_id: string;
  executed: Record<string, unknown>[];
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  intent: string;
  reply: string;
  plan?: DispatchPlan;
}

export async function chat(message: string, history: ChatTurn[]): Promise<ChatResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) throw new Error(`chat failed: ${res.status}`);
  return res.json();
}

export async function getDispatchPlan(): Promise<DispatchPlan> {
  const res = await fetch("/api/dispatch-plan", { method: "POST" });
  if (!res.ok) throw new Error(`dispatch-plan failed: ${res.status}`);
  return res.json();
}

export async function approve(
  machineId: string,
  threadId: string
): Promise<Record<string, unknown>> {
  const res = await fetch("/api/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ machine_id: machineId, thread_id: threadId }),
  });
  if (!res.ok) throw new Error(`approve failed: ${res.status}`);
  return res.json();
}
