# 🧠 Lab 3 — Build the Supervisor Agent

## 🎯 Goal

Marc needs a single assistant that can answer questions across three sources at once:
his machine telemetry, the fault reports Sara submitted, and the wider web.

In this lab you build that assistant — a **Supervisor Agent** in Databricks Agent Bricks.
A Supervisor routes each question to the right sub-agent, collects the answers, and
synthesises one field-ready response. You configure the sub-agents; the Supervisor
decides which to call, in what order, and how to combine the results.

**Marc's three tools:**

| Tool | What it knows |
|---|---|
| Maintenance Genie | Machine registry, fault event history and telemetry, service orders, and extracted PDF fault reports |
| Sales Genie | Sunny Bay coffee sales — governed measures for units, revenue, and profit by store, product, and date |
| you.com web search | Manufacturer service bulletins, repair procedures, part numbers |

> [!IMPORTANT]
> **Prerequisites:**
> - Lab 0 setup job has run successfully (`fault_reports_structured` exists)
> - The **Sunny Bay Maintenance Genie** and **Sunny Bay Sales Genie** agents exist (you build the
>   Maintenance Genie in Lab 1 — Step 1; the setup job pre-builds the Sales Genie over the metric view)
> - you.com MCP service is registered in the Unity AI Gateway (Lab 1 — Step 4b)

---

## Instructions

### Step 1 — Open Agent Bricks (1 min)

1. In the workspace left sidebar click **Agents**
2. Click **New agent** → **Supervisor Agent**

---

### Step 2 — Name and describe the Supervisor (2 min)

Set the **Name**:

```
Marc Maintenance Supervisor
```

Then paste this **Description** — one cumulative description covering all three sources,
so you don't have to write one per sub-agent:

```
Field maintenance assistant for Sunny Bay Roastery technicians. Combines three
sources into a single field-ready briefing:

- Maintenance Genie — fault reports, machine registry, and fields extracted from
  PDF fault report submissions: fault code, issue description, pressure
  readings, technician notes. Use for what the location manager reported about a
  specific machine.
- Sales Genie — Sunny Bay coffee sales: governed measures for units sold, revenue,
  and profit by store, product, and date. Use for sales, revenue, profit, and
  store-performance questions by store, product, and time period.
- you.com web search — manufacturer service bulletins, fault code definitions,
  repair procedures, and part numbers for commercial espresso machines. Use for
  external knowledge only, never for internal Sunny Bay data.
```

> [!TIP]
> **Why one description instead of three.** You *can* describe each sub-agent
> individually, and for a production agent that's the more precise approach — a
> description sits right next to the thing it describes. But it's also three times the
> typing, and the Supervisor routes from this description plus your instructions either
> way. One cumulative description gets you to a working agent faster, which is what you
> want in a 25-minute lab.

---

### Step 3 — Add the three sub-agents (5 min)

Just add them — no descriptions needed, since Step 2 already covers what each one knows.

1. Click **Add agent** → **Genie Space** *(the menu still says "Space" — this is a Genie
   agent)* and select the **Sunny Bay Maintenance Genie** you built in Lab 1.

2. Click **Add agent** → **Genie Space** again and select the **Sunny Bay Sales Genie**
   you built in Lab 1.

3. Click **Add agent** → **MCP Server** and select the **you.com** MCP service from
   Lab 1 (Step 4b).

> [!NOTE]
> If the MCP service doesn't appear, confirm it's registered under **AI Gateway →
> MCPs** and that you have **EXECUTE** on it (Lab 1, Step 4b) — the service sits on top of
> a Unity Catalog **HTTP connection** created once for the metastore. See
> [Register an MCP service](https://docs.databricks.com/aws/en/ai-gateway/register-mcp-service).

---

### Step 4 — Set Supervisor instructions (3 min)

The description told the Supervisor *what each source knows*. The instructions tell it
*how to behave*. In the **Instructions** field paste:

```
You are Marc's field maintenance assistant at Sunny Bay Roastery.
Marc is a field technician who visits all 12 locations.

When Marc asks about a machine:
1. Use the Maintenance Genie to get the machine details, fault event history,
   and what the fault report said.
2. Use the Sunny Bay Sales Genie only for sales or store-performance questions.
3. Use you.com to look up relevant service bulletins or repair procedures.
4. Synthesise a single field-ready briefing: machine status, fault history,
   customer complaint, manufacturer recommendation, and parts to bring.

Be concise and actionable. Marc reads this on his phone while driving.
No walls of text. Lead with what's wrong and what to bring.
```

Click **Save**.

---

### Step 5 — Test the Supervisor (5 min)

In the Supervisor chat, type:

```
I'm visiting CBM-003 tomorrow morning. What should I bring and what am I walking into?
```

Watch the Supervisor work — you will see it call each sub-agent in the reasoning trace:

- **Maintenance Genie** → Sara's fault report and fault event history (3× E-07,
  pressure at 7.5 bar, unresolved), plus last service date and machine age
- **you.com** → Siemens EQ.9 pressure fault bulletin, pump replacement procedure

The final response should be a single field-ready briefing.

> [!NOTE]
> This CBM-003 question is all maintenance, so the Supervisor may not call the Sales
> Genie at all — that's correct routing, not a miss. Ask a sales question (Step 6) to
> see it reach for the Sales Genie.

---

### Step 6 — Try follow-up questions (optional, 5 min)

```
What is the part number for the Siemens EQ.9 pump assembly?
```

```
Has CBM-009 had similar issues to CBM-003?
```

```
Which machines across all locations need attention this week?
```

```
Which store had the highest coffee revenue in 2024? (routes to the Sales Genie)
```

---

## 💡 Key takeaways

- The Supervisor **routes automatically** — you describe what each source knows,
  it decides which to call
- **Descriptions are routing rules** — the more specific you are, the better the routing.
  Same lesson as Genie One in Lab 1: a thin description gets the sub-agent skipped
- **Description vs instructions** — the description says what each source *knows*; the
  instructions say how the Supervisor should *behave*. You described all three sources in
  one place here to save time; per-sub-agent descriptions are the tidier choice for
  something you'll maintain
- The Supervisor has a **built-in chat UI** with conversation history — no app needed
  to start using it
- In Lab 4 you observe it with MLflow traces and collect structured domain-expert
  feedback through a Review App

---

## What Happens Next?

Marc's Supervisor is live. It answers multi-domain questions and keeps conversation
history in the Agent Bricks UI. In Lab 4 you inspect its MLflow traces and set up a
Review App so domain experts can grade its answers before you trust it.

➡️ Continue to **[Lab 4 — Observe and Review](./Lab%204%20-%20Observe%20and%20Review.md)**
