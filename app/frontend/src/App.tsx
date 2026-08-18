import { useEffect, useRef, useState } from "react";
import { approve, chat, ChatTurn, DispatchPlan, PlanRow } from "./api";

interface Msg {
  role: "user" | "assistant";
  text: string;
  plan?: DispatchPlan;
}

const SUGGESTIONS = [
  "Build my dispatch plan",
  "Why is CBM-003 ranked first?",
  "What's the weekly revenue by store?",
  "Approve CBM-003",
];

export default function App() {
  const [msgs, setMsgs] = useState<Msg[]>([
    {
      role: "assistant",
      text: "I'm Marc's operations agent for the 12 Sunny Bay locations. Ask me to build a dispatch plan, explain a ranking, look up data, or approve a service order.",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [approved, setApproved] = useState<Record<string, string>>({});
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, busy]);

  async function send(text: string) {
    if (!text.trim() || busy) return;
    const history: ChatTurn[] = msgs.map((m) => ({ role: m.role, content: m.text }));
    setMsgs((m) => [...m, { role: "user", text }]);
    setInput("");
    setBusy(true);
    try {
      const res = await chat(text, history);
      setMsgs((m) => [...m, { role: "assistant", text: res.reply, plan: res.plan }]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "assistant", text: `⚠️ ${String(e)}` }]);
    } finally {
      setBusy(false);
    }
  }

  async function onApprove(machineId: string, threadId: string) {
    try {
      const res = await approve(machineId, threadId);
      setApproved((s) => ({ ...s, [machineId]: String(res.order_id ?? "created") }));
      setMsgs((m) => [
        ...m,
        { role: "assistant", text: `✅ Raised service order ${res.order_id} for ${machineId}.` },
      ]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "assistant", text: `⚠️ ${String(e)}` }]);
    }
  }

  return (
    <div className="wrap">
      <header>
        <h1>Marc's Manager Agent</h1>
        <p className="sub">Fleet operations across 12 locations — ask, plan, and act.</p>
      </header>

      <div className="chat">
        {msgs.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <div className="bubble">{m.text}</div>
            {m.plan && (
              <div className="cards">
                {m.plan.ranked.map((row) => (
                  <Card
                    key={row.machine_id}
                    row={row}
                    approvedOrder={approved[row.machine_id]}
                    onApprove={() => onApprove(row.machine_id, m.plan!.thread_id)}
                  />
                ))}
              </div>
            )}
          </div>
        ))}
        {busy && <div className="msg assistant"><div className="bubble typing">…</div></div>}
        <div ref={endRef} />
      </div>

      <div className="suggestions">
        {SUGGESTIONS.map((s) => (
          <button key={s} className="chip" onClick={() => send(s)} disabled={busy}>
            {s}
          </button>
        ))}
      </div>

      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Marc's agent…"
          disabled={busy}
        />
        <button type="submit" disabled={busy || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

function Card({
  row,
  approvedOrder,
  onApprove,
}: {
  row: PlanRow;
  approvedOrder?: string;
  onApprove: () => void;
}) {
  return (
    <div className={`card ${row.needs_approval ? "flagged" : ""}`}>
      <div className="card-head">
        <span className="machine">{row.machine_id}</span>
        <span className="score">priority {row.priority_score}</span>
      </div>
      <div className="meta">
        {row.location} · mgr {row.manager.name} · {row.unresolved_faults} unresolved
        {row.fault_code ? ` · ${row.fault_code}` : ""} · ${row.revenue_at_risk.toLocaleString()}/wk
      </div>
      {row.bulletin && <div className="bulletin">🔧 {row.bulletin}</div>}
      {row.draft_message && (
        <div className="draft">
          <div className="draft-label">Draft to {row.manager.name}:</div>
          {row.draft_message}
        </div>
      )}
      {row.needs_approval &&
        (approvedOrder ? (
          <div className="approved">✅ Service order {approvedOrder} created</div>
        ) : (
          <button className="approve" onClick={onApprove}>
            Approve &amp; create service order
          </button>
        ))}
    </div>
  );
}
