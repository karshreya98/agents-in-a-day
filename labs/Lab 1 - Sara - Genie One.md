# 🗣️ Lab 1 — Sara: From Dashboard to Action

## 🎯 Learning Objectives

By the end of Lab 1, you will be able to:

- Build a **Genie space** over the Sunny Bay maintenance data.
- Use **Genie One** as a business-user interface, driven by that Genie space (an *agent*).
- Connect an external **MCP tool** (you.com) to enrich Genie One conversations with live web knowledge.

## Introduction

Sara is the Mission location manager at Sunny Bay Roastery. Day to day she doesn't
write SQL or dig through tables — she just wants answers. She gets them through
**Genie One**, the conversational front door to Databricks. Behind Genie One sits a
**Genie space**: a governed, natural-language interface to a set of Unity Catalog
tables. In Genie One these spaces show up as **agents** Sara can talk to.

In this lab you'll wear two hats: first you set up the Genie space (a quick,
one-time build), then you step into Sara's shoes and just ask questions.

Dashboard in a Day built a *Sales* Genie. In this lab you build the **Maintenance
Genie** — the one Sara (and later Marc's Supervisor in Lab 3) needs to ask about
machine faults — then talk to *both* of them through Genie One, which routes each
question to the right space.

This lab is **facilitator-led with participant follow-along**. No code to write. Just
one Genie space and a few conversations.

---

## Instructions

### **Step 1: Build the Maintenance Genie space (10 min)**

The Lab 0 setup job already created the maintenance tables and the
`fault_reports_structured` table (parsed and extracted from the fault report PDFs —
you'll see exactly how in Lab 2). Now you'll put a Genie space in front of them.

1. In the workspace left sidebar, click **Genie**.

2. Click **New** (or **+ New Genie space**).

3. When prompted for data, add these four tables from your catalog's
   `coffee_maintenance` schema:

   ```
   <catalog>.coffee_maintenance.machines
   <catalog>.coffee_maintenance.fault_events
   <catalog>.coffee_maintenance.service_orders
   <catalog>.coffee_maintenance.fault_reports_structured
   ```

   > [!NOTE]
   > Replace `<catalog>` with the catalog name you used in Lab 0 (e.g.
   > `sunny_bay_roastery`). If your tables have a prefix (e.g. `sbr_machines`),
   > select the prefixed names.

4. Name the space **`Sunny Bay Maintenance Genie`** and give it a description:

   ```
   Natural-language Q&A over Sunny Bay espresso machine maintenance: machine
   registry, fault event history, service orders, and fields extracted from
   fault report PDFs. Use for questions about a machine's faults, pressure
   readings, parts, and technician notes.
   ```

5. Click **Save**.

> [!TIP]
> You'll reuse this exact Genie space in **Lab 3** as one of Marc's Supervisor
> sub-agents — building it once here means it's ready when you get there.

---

### **Step 2: Ask maintenance questions in the Genie space (5 min)**

1. In the Genie space you just built, start a conversation and try:

   ```
   What fault reports do we have for CBM-003?
   ```

   ```
   Which machines have logged E-07 pressure faults?
   ```

   ```
   Show me the fault event history for the Mission District location
   ```

2. Click **Show code** beneath any answer to see the SQL Genie generated — no one
   wrote it by hand.

> [!NOTE]
> Genie answers from the governed tables only. `fault_reports_structured` holds the
> fields extracted from the PDF fault reports — so Sara can ask about the *contents*
> of those reports in plain language. In Lab 2 you'll see exactly how that table is built.

---

### **Step 3: Talk to your Genie spaces through Genie One (5 min)**

Genie One is the business-user front door. Every Genie space in the workspace shows
up here as an **agent** — including the **Sunny Bay Maintenance Genie** you just built
*and* the **Sunny Bay Sales Genie** from Dashboard in a Day. Sara doesn't pick a
table or an agent; she just asks, and Genie One routes to the right one.

1. Open the **kebab menu** (the ⋮ / grid "waffle" icon in the top navigation bar) and
   select **Genie One**.

2. Ask Sara's manager questions — a mix of **maintenance** and **sales**. Genie One
   routes each to the right Genie space:

   **Maintenance** (routes to the Sunny Bay Maintenance Genie you built):

   ```
   Which of my machines should I be worried about this week?
   ```

   ```
   What did the latest fault report for CBM-003 say?
   ```

   **Sales** (routes to the Sunny Bay Sales Genie from Dashboard in a Day):

   ```
   How do sales at the Sunny Bay – Mission store compare to the other stores?
   ```

   ```
   Which store had the highest coffee sales this year?
   ```

> [!NOTE]
> One conversation, two governed Genie spaces — maintenance *and* sales — with no
> switching. Sara configured nothing; she just asks. Unity Catalog governs what each
> space can see.

---

### **Step 4: Connect you.com for live web knowledge (15 min)**

The telemetry tells Sara *what* is happening. It cannot tell her *why*, or what the
manufacturer recommends. An external **MCP service** (you.com), registered in the Unity
AI Gateway, fixes that.

**Step 4a — Get your you.com API key**

1. Open a new browser tab and go to [https://you.com](https://you.com).

2. Click **Sign up** — you can use Google or GitHub. The free tier is sufficient.

3. After signing in, go to [https://you.com/settings/api](https://you.com/settings/api).

4. Click **Create API key** → copy the key (it looks like `yk_...`).

> [!TIP]
> No credit card required. The free plan gives 100 web-search calls/day — more
> than enough for this workshop. You keep this key after the session.

**Step 4b — Register you.com as an MCP service in the Unity AI Gateway**

You register the you.com MCP server once, in the Unity AI Gateway, so it's governed like
any other Databricks asset. Full reference:
[Register an MCP service](https://docs.databricks.com/aws/en/ai-gateway/register-mcp-service).

> [!NOTE]
> **Prerequisites (admin):** Unity Catalog enabled, and the **Unity AI Gateway** +
> **Managed MCP Servers** previews turned on. You need `CREATE CONNECTION`, `USE CATALOG`,
> `USE SCHEMA`, and `CREATE SERVICE` to complete these steps.

1. **Create an HTTP connection to you.com.** Go to **Catalog → Connections → Create
   connection** and choose type **HTTP**. Enter the you.com MCP server URL and pick an
   authentication method — for you.com use **Bearer token** and paste the API key from
   Step 4a. Save.

2. **Register the MCP service.** Go to **AI Gateway → MCPs → Register MCP Server** (or
   **Catalog → [your schema] → Create → MCP Service**). Set:
   - the **catalog and schema** to register it in,
   - a **service name** (e.g. `you_com_search` — this can't be changed later),
   - the **HTTP connection** you just created,
   - the **tools** to expose under the **Tools** section (the you.com web search tool).

3. **Grant access.** On the service's **Permissions** tab, click **Grant**, add your
   workshop users (or a group), and assign the **EXECUTE** privilege.

> [!IMPORTANT]
> Invoking an MCP service needs **no privilege on the underlying connection** — grant
> **EXECUTE** on the *service*, and do **not** grant `USE CONNECTION` to end users (that
> would bypass governance).

> [!TIP]
> Registering the MCP server is a one-time admin step. If you're short on time, the
> facilitator can register it once and grant the room EXECUTE — participants then just
> use it in the next step.

**Step 4c — Ask enriched questions**

Now in Genie One, ask questions that combine your governed data with the web:

```
What does Siemens recommend when a repeated E-07 pressure error appears on
their commercial coffee machines?
```

```
Are there any known service bulletins for pressure faults on Nespresso Pro
commercial machines?
```

> [!NOTE]
> Internal maintenance data and live web knowledge in the same conversation. Unity
> Catalog data never moved — the context just got richer.

---

### **Step 5: Make it a standing question (optional, 10 min)**

Sara has explored and built trust. A natural next step is a *standing* question — one
Genie re-runs on a cadence so she gets a briefing without asking.

> [!NOTE]
> **Facilitator note:** Scheduled/standing Genie briefings depend on the features
> enabled in your workspace. Confirm availability before the session. If it isn't
> available in your Free Edition workspace, demonstrate the intent instead: Sara would
> save *"Which of my machines logged faults in the last 7 days, and are there any open
> service bulletins for them?"* to run every Monday morning.

The point stands either way: Sara defines the *question*. Genie does the *work*.

---

## Bridge to Marc's Arc

Sara's machine check just flagged **CBM-003: pressure anomaly, repeated E-07 fault
codes**.

She can *see* it. But who *acts* on it?

Marc drives between all 12 locations every day without knowing what he is walking into.
The fault history is already in Unity Catalog — the same Maintenance Genie Sara queried
knows it. The question is not whether the data exists. It is whether Marc has something
that *acts* on it.

**Today you build that.**

---

## What Happens Next?

You have built a Genie space, driven it from Genie One as a business user, and enriched
it with live web knowledge — all on governed data that never left Unity Catalog.

➡️ Continue to **[Lab 2 — Document Intelligence](./Lab%202%20-%20Document%20Intelligence.md)**
   to start building Marc's Maintenance Agent.
