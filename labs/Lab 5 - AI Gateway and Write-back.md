# 🔒 Lab 5 — AI Gateway and Write-back

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

- Inspect the full AI Gateway audit trail from today's session.
- Understand the `create_service_order` UC function that was registered in Lab 0.
- Add the UC function as a tool to the Supervisor.
- Trigger a real write-back: the agent creates a service order in a governed Delta table.
- Swap the model behind the endpoint without changing any agent code.

---

## Introduction

Everything the Supervisor called today — Genie Agent queries, you.com lookups,
`ai_extract()` from Lab 2 — has been flowing through the **AI Gateway**.
You were not thinking about governance while you were building. It was tracking
everything anyway.

In this final lab you:
1. Open the audit dashboard and see the full trail.
2. Inspect the `create_service_order` UC function (the code is below).
3. Wire it into the Supervisor so Marc can create real tickets with two words.

---

## Background: the UC function

The `create_service_order` function was registered in Unity Catalog during Lab 0
(Step 7). Here is the full Python source so you can understand what the agent
will call:

```python
# Unity Catalog function: catalog.coffee_maintenance.create_service_order
# Language: PYTHON
# Registered in: Lab 0 - Setup.py, Step 7

import random
import requests
import os

def create_service_order(
    machine_id: str,        # e.g. "CBM-003"
    fault_code: str,        # e.g. "E-07"
    part_id: str,           # e.g. "SIE-EQ9-PUMP-003"
    technician_notes: str,  # free-text summary for the technician
) -> str:
    """
    Creates a service order row in the service_orders Delta table.
    Returns the new order ID (e.g. "SO-47231").
    """
    order_id = f"SO-{random.randint(10000, 99999)}"
    sql = (
        f"INSERT INTO `{catalog}`.`coffee_maintenance`.`service_orders` "
        "(order_id, machine_id, created_ts, fault_code, part_id, technician_notes, status) "
        f"VALUES ('{order_id}', '{machine_id}', current_timestamp(), "
        f"'{fault_code}', '{part_id}', '{technician_notes}', 'pending')"
    )
    requests.post(
        f"{os.environ['DATABRICKS_HOST']}/api/2.0/sql/statements",
        headers={"Authorization": f"Bearer {os.environ['DATABRICKS_TOKEN']}",
                 "Content-Type": "application/json"},
        json={"statement": sql, "wait_timeout": "10s"},
        timeout=15,
    )
    return order_id
```

> [!NOTE]
> The function uses the Databricks SQL Statements API to execute the INSERT.
> This is the standard pattern for UC Python functions that need to write back
> to Delta — they can't use `spark.sql()` directly inside a UC function context.

---

## Instructions

### **Step 1: Review the AI Gateway audit trail (5 min)**

1. In the workspace sidebar, navigate to **AI Gateway**
   (under **AI** or **Machine Learning**).

2. Open the dashboard for your gateway endpoint.

3. You should see:
   - Every Supervisor call from Labs 2–3 (model, tokens, latency, user).
   - Every `ai_extract()` call from Lab 2.
   - Timestamps and cost per call.

4. Filter by **User** to see only your calls.

> *"You were not thinking about governance while you were building.
>  It was tracking everything anyway."*

---

### **Step 2: Inspect the UC function in Unity Catalog (3 min)**

Before wiring the function to the Supervisor, confirm it exists and
understand its signature.

**Option A — UC Explorer (UI):**

1. Go to **Catalog** → navigate to your catalog → `coffee_maintenance` schema.
2. Click **Functions**.
3. Open `create_service_order`.
4. The **Columns** tab shows the 4 input parameters and the return type (`STRING`).
5. Read the **Comment** field — this is what the Supervisor sees when deciding
   whether to call the function.

**Option B — SQL (notebook or query editor):**

```sql
DESCRIBE FUNCTION EXTENDED <your_catalog>.coffee_maintenance.create_service_order;
```

You should see the 4 parameters: `machine_id`, `fault_code`, `part_id`, `technician_notes`.

---

### **Step 3: Test the UC function directly (optional, 5 min)**

Before trusting the agent to call it, verify it works with a manual call.

Open a new notebook (Serverless, SQL), then run:

```sql
-- Replace <your_catalog> with your catalog name
SELECT <your_catalog>.coffee_maintenance.create_service_order(
  'CBM-TEST',
  'E-00',
  'TEST-PART-001',
  'Manual test call from Lab 5'
) AS order_id
```

Then verify the row landed:

```sql
SELECT * FROM <your_catalog>.coffee_maintenance.service_orders
ORDER BY created_ts DESC
LIMIT 5
```

You should see `CBM-TEST` in the table with status `pending`.

> [!TIP]
> Delete the test row before running the real demo:
> ```sql
> DELETE FROM <your_catalog>.coffee_maintenance.service_orders
> WHERE machine_id = 'CBM-TEST';
> ```

---

### **Step 4: Add the UC function to the Supervisor (8 min)**

1. In the workspace sidebar, navigate to **Agents → Supervisor Agents**.

2. Open your **Marc Maintenance Supervisor** from Lab 3.

3. Click **Add tool** → **Unity Catalog function**.

4. Search for and select:
   `<your_catalog>.coffee_maintenance.create_service_order`

5. Set the tool description to:

   ```
   Creates a service order in the Sunny Bay service_orders Delta table.
   Use this ONLY when Marc explicitly asks to book, raise, or create a
   service order for a specific machine. Required: machine_id, fault_code,
   part_id, technician_notes. Returns a service order ID (e.g. SO-47231).
   ```

> [!IMPORTANT]
> The phrase "ONLY when Marc explicitly asks" prevents the Supervisor from
> creating orders unprompted during read-only queries.

6. Update the Supervisor instructions — add this at the end:

   ```
   When the user explicitly says "book it", "raise a service order", or
   "create a ticket", call create_service_order with the machine_id,
   fault_code, part_id you identified from the data, and a brief technician
   note. Confirm the order ID in your response.
   ```

7. Click **Save** → **Update endpoint**.

---

### **Step 5: Close the loop — Marc creates a service order (10 min)**

Start a new conversation in the Supervisor. Run the full Marc scenario:

**Turn 1:**
```
I'm visiting CBM-003 tomorrow. What should I bring?
```
The Supervisor gives the same multi-source briefing as Lab 3/3.

**Turn 2:**
```
Book it.
```

The Supervisor calls `create_service_order` and responds:

> *"Service order created: **SO-47231** — Pump assembly + pressure line kit
>  dispatched for CBM-003. Fault: E-07. Status: pending."*

**Verify the write-back:**

```sql
SELECT order_id, machine_id, fault_code, part_id, status, created_ts
FROM <your_catalog>.coffee_maintenance.service_orders
ORDER BY created_ts DESC
LIMIT 5
```

**Turn 3 (same conversation or new one):**
```
What is the status of CBM-003?
```

The Genie Agent now sees the pending service order in the Delta table.
The agent wrote something. Its next answer reflects what it wrote.

> *"One estate, both ends."*

---

### **Step 6: Swap the model (facilitator demo, 3 min)**

1. Ask your facilitator to change the model behind the AI Gateway endpoint —
   for example from `claude-3-5-haiku` to `llama-3-3-70b-instruct-awq`.
   This is two fields in the Gateway UI.

2. Ask the same CBM-003 question again.

3. Check AI Gateway — same audit trail, different model in the log.

> *"Your agent does not know what model it is running on.
>  You do. And so does compliance."*

---

## 🎉 Workshop Complete

**What you built today, on Free Edition, zero infrastructure to provision:**

| | |
|---|---|
| **Sara** | Gets a machine-health briefing from Genie One without touching the Lakehouse. |
| **Marc** | Asks one question, gets a multi-source briefing from SQL + PDFs + web, creates a service order with two words. |
| **Your workspace** | Has a governed audit trail of every AI call — model-swap-proof. |

**What you take home:**

- The Supervisor shareable URL — live and usable right now.
- The Agent Bricks config — point it at your own data next week.
- The UC function pattern — governed write-back, any domain.
- The DAB in this repo — packaged, reproducible, your architecture to keep.

---

## What Happens Next?

- Drop a new PDF into `/Volumes/<catalog>/coffee_maintenance/fault_reports/`
  and watch it appear in `fault_reports_structured` automatically
  (SDP pipeline deployed in Lab 0).

- Swap Sunny Bay data for your own — same Supervisor, same pattern, your domain.

> [!TIP]
> The Dashboard in a Day team runs follow-up deep-dive sessions on **Lakebase**
> and **Databricks Apps** — ask your facilitator for the schedule.
