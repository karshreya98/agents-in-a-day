# 🗣️ Part 1 — Sara: From Dashboard to Action

## 🎯 Learning Objectives

By the end of Part 1, you will be able to:

- Use Genie One as a business-user interface to a governed Databricks dataset.
- Connect an external MCP tool (you.com) to enrich Genie One conversations with live web knowledge.
- Schedule a standing question so the agent does the work automatically each week.

## Introduction

Sara is the Mission location manager at Sunny Bay Roastery. She never opens the Lakehouse. She acts through Genie One — the conversational face of the Genie Agent the data team built in Dashboard in a Day.

This part is **facilitator-led with participant follow-along**. No code to write. Just conversations.

---

## Instructions

### **Step 1: Open Genie One and ask manager questions (5 min)**

1. Open your browser and navigate to your workspace URL, then add `/one` at the end:
   `https://<your-workspace>.cloud.databricks.com/one`

2. You should see the Genie One interface. The **Sunny Bay Sales Genie** agent (built in Dashboard in a Day Lab 4) is available here.

3. Start a conversation. Type each question and observe the response:

   ```
   Which of my machines should I be worried about this week?
   ```

   ```
   How does the Mission location compare to the others on uptime?
   ```

   ```
   Were there more fault events than usual last month?
   ```

> [!NOTE]
> Genie interprets "my machines" and "my location" from your user profile — the
> semantic layer in the metric view handles this automatically. Sara did not configure anything.

4. Observe the SQL Genie generates behind each answer. Click **Show Code** beneath any result.

---

### **Step 2: Connect you.com for live web knowledge (20 min)**

The telemetry tells Sara *what* is happening. It cannot tell her *why*, or what the manufacturer recommends. We fix that now.

**Step 2a — Get your you.com API key**

1. Open a new browser tab and go to [https://you.com](https://you.com).

2. Click **Sign up** — you can use Google or GitHub. The free tier is sufficient.

3. After signing in, go to [https://you.com/settings/api](https://you.com/settings/api).

4. Click **Create API key** → copy the key (it looks like `yk_...`).

> [!TIP]
> No credit card required. The free plan gives 100 web-search calls/day — more
> than enough for this workshop. You keep this key after the session.

**Step 2b — Wire you.com into Genie One**

1. Back in Genie One, click the **gear icon ⚙️** (Settings) in the top-right corner.

2. Select **Connections** → **Add connection**.

3. Choose **you.com Web Search**.

4. Paste your API key in the field provided. Click **Save**.

5. The connection icon turns green ✅.

> [!IMPORTANT]
> This takes about 2 minutes. If you run short on time, the facilitator will
> demonstrate on the main screen — you can configure your own key as homework and
> your Genie One history is preserved.

**Step 2c — Ask enriched questions**

Now in the same conversation, ask:

```
What is the typical uptime benchmark for commercial Siemens espresso machines —
are our numbers normal?
```

```
Are there any known service bulletins for pressure faults on Nespresso Pro
commercial machines?
```

```
What does Siemens recommend when a repeated E-07 pressure error appears on
their commercial coffee machines?
```

> [!NOTE]
> Internal telemetry and live web knowledge in the same conversation. Unity
> Catalog data never moved — context just got richer.

---

### **Step 3: Schedule a standing question (15 min)**

Sara has explored and built trust. Now she defines a standing question — not a
dashboard, not a report — just a question Genie One will re-ask on her behalf every Monday.

1. In the active Genie One conversation, type:

   ```
   Save this as a weekly scheduled briefing.
   ```

2. Genie One prompts for a name and cadence. Type:

   ```
   Monday Morning Machine Check — every Monday at 7am
   ```

3. Genie confirms: *"I'll run this every Monday at 7am and send results to your Genie One inbox."*

4. That's it. Sara defined the question. Genie runs it.

> [!NOTE]
> **Facilitator check:** Confirm this feature is available in your Free Edition
> workspace before the session. Fallback: demonstrate the schedule dialog without
> completing the send.

**What arrives Monday at 7am:**
- Which machines logged fault codes in the last 7 days
- Any machines with scheduled maintenance visits this week
- Any open service bulletins from you.com for those machine models

---

## Bridge to Marc's Arc

Sara's Monday briefing just flagged **CBM-003: pressure anomaly, two fault codes in the last week**.

She can *see* it. But who *acts* on it?

Marc drives between all 12 locations every day without knowing what he is walking into. The fault history is already in Unity Catalog — the same Genie Agent Sara queried knows it. The question is not whether the data exists. It is whether Marc has something that *acts* on it.

**Today you build that.**

---

## What Happens Next?

You have seen Databricks data speak to a business user in plain language, enriched
with live web knowledge, and scheduled to run on its own.

➡️ Continue to **[Lab 1 — Document Intelligence](./Lab%201%20-%20Document%20Intelligence.md)**
   to start building Marc's Maintenance Agent.
