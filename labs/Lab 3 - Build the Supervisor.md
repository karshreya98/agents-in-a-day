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
| Genie Agent (from DAID) | Machine telemetry, fault history, sales data |
| Maintenance Genie | Fault reports, machine registry, extracted PDF content |
| you.com web search | Manufacturer service bulletins, repair procedures, part numbers |

> [!IMPORTANT]
> **Prerequisites:**
> - Lab 0 setup job has run successfully (`fault_reports_structured` exists)
> - you.com MCP service is registered in the Unity AI Gateway (Lab 1 — Step 4b)

---

## Instructions

### Step 1 — Open Agent Bricks (1 min)

1. In the workspace left sidebar click **Agents**
2. Click **New agent** → **Supervisor Agent**

---

### Step 2 — Name and describe the Supervisor (1 min)

| Field | Value |
|---|---|
| **Name** | `Marc Maintenance Supervisor` |
| **Description** | `Field maintenance assistant for Sunny Bay Roastery technicians. Combines machine telemetry, fault reports, and web search into a single field-ready briefing.` |

---

### Step 3 — Add sub-agents (10 min)

Add each sub-agent one at a time using **Add agent**.

---

**Sub-agent 1 — Sunny Bay Sales Genie (from DAID)**

1. Click **Add agent** → **Genie Space**
2. Select the **Sunny Bay Sales Genie** space created by DAID
3. Set the description:

```
Answers questions about Sunny Bay machine telemetry, fault history, uptime,
and sales data using the governed metric view. Use this for all structured
data questions about machines, locations, and fault events.
```

---

**Sub-agent 2 — Maintenance Genie**

1. Click **Add agent** → **Genie Space**
2. Select the **Sunny Bay Maintenance** Genie space (created by the Lab 0 setup job)
3. Set the description:

```
Answers questions about fault reports, machine registry, and structured data
extracted from PDF fault report submissions. Use this to find what the location
manager reported about a specific machine — fault code, issue description,
pressure readings, and technician notes.
```

---

**Sub-agent 3 — you.com web search (MCP service)**

1. Click **Add agent** → **MCP Server** and select the **you.com** MCP service you
   registered in the Unity AI Gateway in Lab 1 (Step 4b).

> [!NOTE]
> If it doesn't appear, confirm the MCP service is registered under **AI Gateway →
> MCPs** and that you have **EXECUTE** on it (Lab 1, Step 4b). See
> [Register an MCP service](https://docs.databricks.com/aws/en/ai-gateway/register-mcp-service).

2. Set the description:

```
Live web search. Use this to look up manufacturer service bulletins, fault code
definitions, recommended repair procedures, and part numbers for commercial
espresso machines. Do not use for internal Sunny Bay data — use the Genie
agents for that.
```

---

### Step 4 — Set Supervisor instructions (3 min)

In the **Instructions** field paste:

```
You are Marc's field maintenance assistant at Sunny Bay Roastery.
Marc is a field technician who visits all 12 locations.

When Marc asks about a machine:
1. Use the Maintenance Genie to get the fault report and machine details.
2. Use the Sunny Bay Sales Genie to get fault event history and telemetry.
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

- **Maintenance Genie** → Sara's fault report (3× E-07, pressure at 7.5 bar, unresolved)
- **Sunny Bay Sales Genie** → fault event history, last service date, machine age
- **you.com** → Siemens EQ.9 pressure fault bulletin, pump replacement procedure

The final response should be a single field-ready briefing.

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

---

## 💡 Key takeaways

- The Supervisor **routes automatically** — you describe what each sub-agent knows,
  it decides which to call
- **Descriptions are routing rules** — the more specific you are, the better the routing
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
