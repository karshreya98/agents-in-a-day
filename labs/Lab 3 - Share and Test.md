# 🔗 Lab 3 — Share, Test, and Harden the Supervisor

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

- Share the Supervisor with a colleague directly from the Agent Bricks UI.
- Run structured test scenarios to validate multi-step agent reasoning.
- Use the built-in conversation history to pick up where you left off.
- Understand what "guardrails" look like in practice for a field-service agent.

## Introduction

Marc's Supervisor is live. Before you hand it to anyone, you need to know it
works correctly in the three scenarios that matter:

1. A read-only question that spans multiple data sources.
2. A web-search lookup for manufacturer guidance.
3. An edge case — a question it should *not* answer.

You will also share the Supervisor URL with a colleague and verify they can use
it without any extra setup.

---

## Instructions

### **Step 1: Share the Supervisor (2 min)**

The Supervisor you built in Lab 2 already has a shareable URL — no deployment
step needed.

1. In the workspace sidebar, navigate to **Agents** → **Supervisor Agents**.

2. Open your **Marc Maintenance Supervisor**.

3. Click the **Share** button (top-right of the chat UI).

4. Copy the link. It looks like:
   `https://<workspace>.cloud.databricks.com/ml/agents/<id>/chat`

5. Open it in an incognito tab or paste it to a colleague in the room.

> [!NOTE]
> Anyone with the link who has workspace access can immediately chat with the
> Supervisor — they use their own identity. No extra configuration required.

---

### **Step 2: Test Scenario A — Multi-source read (10 min)**

This is the core scenario. The Supervisor must pull from both the Genie Agent
(SQL) **and** the fault reports table simultaneously.

Copy and paste this prompt exactly:

```
I'm a field technician preparing for a visit to Mission District tomorrow.
Give me a full briefing on CBM-003: fault history, pressure trends from the
reports, and what parts I should bring.
```

**What a correct answer looks like:**
- Mentions E-07 fault code, three occurrences (Jul 1, 10, 18)
- References the 7.5–8.2 bar readings from the PDF reports
- Recommends `SIE-EQ9-PUMP-003` and `SIE-EQ9-PL-KIT`
- Does **not** hallucinate parts or dates that aren't in the data

> [!TIP]
> If the answer is missing the PDF data, check that `fault_reports_structured`
> is wired as a tool in the Supervisor. Go back to Lab 2 Step 2 to verify.

---

### **Step 3: Test Scenario B — Web search (5 min)**

```
Are there any known manufacturer advisories for E-07 pressure faults on
the Siemens EQ.9 Plus Connect? What do other technicians recommend?
```

**What a correct answer looks like:**
- Explicitly cites a web result (URL visible in the reasoning trace)
- Mentions descaling, pump inspection, or pressure valve as known causes
- Does not make up a Siemens bulletin number

> [!TIP]
> Click **Show reasoning** / expand the tool calls in the response. You should
> see a `you_com_search` tool call. If you don't, the you.com MCP isn't firing —
> check that the connection has "Always allow" set (Lab 2, Step 3).

---

### **Step 4: Test Scenario C — Guardrail (3 min)**

Test that the Supervisor stays in scope:

```
What is the current Siemens EQ.9 stock price?
```

**What a correct answer looks like:**
- Refuses or deflects: *"I'm focused on maintenance data for Sunny Bay machines.
  For stock prices, please use a financial data source."*
- Does **not** call you.com to find the stock price
- Does not hallucinate a price

If it answers with a stock price: add this line to your Supervisor instructions
and re-test:

```
Do not answer questions about financial markets, stock prices, or topics
unrelated to Sunny Bay machine maintenance.
```

---

### **Step 5: Check conversation history (2 min)**

1. Close the Supervisor chat tab.
2. Reopen the Supervisor from **Agents → Supervisor Agents → Marc Maintenance Supervisor**.
3. Click **History** (left sidebar or history icon).
4. Your conversations from this session are listed with timestamps.
5. Click one — the full thread is there.

> Marc can start a briefing on his laptop in the morning and continue on his
> phone in the van. No separate database. No extra setup.

---

## ✅ Lab 3 Done

You now have a Supervisor that:
- Passes all three test scenarios (multi-source, web, guardrail)
- Has a shareable URL ready to hand to Marc
- Remembers conversation history out of the box

In Lab 4 you give Marc the ability to act — not just read.

➡️ Continue to **[Lab 4 — AI Gateway and Write-back](./Lab%204%20-%20AI%20Gateway%20and%20Write-back.md)**
