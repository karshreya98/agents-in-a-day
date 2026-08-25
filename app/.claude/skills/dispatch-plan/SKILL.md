---
name: dispatch-plan
description: "Build Marc's weekly dispatch plan by hand — a ranked shortlist of which machines to service, from the structured fault reports plus store revenue. Use when the user says 'build a dispatch plan', 'dispatch plan analysis', 'which machines should Marc service this week', 'rank the machines', or 'preview the dispatch agent'. This is Lab 2 · Bonus: the SAME deterministic scoring Marc's Lab 3 agent runs in code (agent_server/dispatch.py), run once by hand over the table Lab 2 just built."
---

# Build Marc's dispatch plan (Lab 2 · Bonus)

**Goal:** turn the structured fault data into a **ranked dispatch plan** — for each machine
worth servicing this week, its location, unresolved-fault count, fault code, revenue at risk,
a priority score, and a short draft message to that store's manager.

This is a **hand-run preview** of what Marc's Lab 3 custom agent automates. The scoring below
is exactly the policy in `app/agent_server/dispatch.py` (`_priority`, `DISPATCH_THRESHOLD`).
Here you run it once, yourself; in Lab 3 it becomes a deployed, approval-gated agent.

> This analysis is **read-only**. It ranks and drafts — it **writes nothing** and raises no
> service order. The write-back (and the human approval gate in front of it) is Lab 3.

## Inputs (Unity Catalog, replace `<catalog>`)

- `<catalog>.coffee_maintenance.fault_reports_structured` — the table Lab 2 built
  (`machine_id`, `machine_model`, `fault_code`, `issue_description`, `location_name`,
  `contact_name`, `report_date`).
- `<catalog>.coffee_maintenance.service_orders` — used to tell which faults are still
  **unresolved** (no `status = 'completed'` order for that machine).
- `<catalog>.gold.sm_fact_coffee_sales_genie` — governed sales **metric view**; use it for each
  store's **weekly revenue** (the "revenue at risk" if that store's machine is down).

> [!IMPORTANT]
> Confirm the exact column names first (`DESCRIBE` each table / the metric view). Table shapes
> can differ per workshop catalog — discover, then adapt the SQL. The **scoring policy below is
> fixed**; only the joins/column names adapt.

## The scoring policy — do NOT change these numbers

Matches `dispatch.py` exactly:

```
priority = 4 · unresolved_faults + (revenue_at_risk_per_week / 1000)

  FAULT_WEIGHT       = 4     points per unresolved fault
  REVENUE_WEIGHT     = 1     point per $1,000/week of revenue at risk
  DISPATCH_THRESHOLD = 10    a machine must score ≥ 10 to make the plan
```

## Steps

1. **Unresolved faults per machine.** From `fault_reports_structured`, count reports per
   `machine_id` that have **no completed `service_orders` row** for that machine. That count is
   `unresolved_faults`.

2. **Revenue at risk per machine.** Join each machine's `location_name` to its store's **weekly
   revenue** from the sales metric view. A down machine risks its store's weekly revenue — that
   figure is `revenue_at_risk_per_week`.

3. **Score and filter.** Compute `priority` with the formula above. Keep only machines that have
   `unresolved_faults > 0` **and** `priority ≥ 10`. Sort by `priority` descending.

4. **Draft a manager message** for each machine that made the cut — one or two sentences to the
   store contact (`contact_name`), naming the machine, the `fault_code`, the `issue_description`,
   and any recommended part, e.g.:

   > *"Hi {contact_name} — CBM-003 at {location_name} has logged {n} unresolved {fault_code}
   > pressure faults. Recommend dispatching a technician this week; the reports flag the pump
   > seal. This store is ~${revenue}/wk of revenue at risk."*

5. **Return the plan** as a ranked table (machine, location, unresolved faults, fault code,
   revenue at risk, priority score) **plus** the draft messages. Show your SQL so the user can
   see the scoring is deterministic, not a guess.

## Tie it back to Lab 3

Close by pointing out the parallel: *this ranked plan is exactly what Marc's Lab 3 agent
produces — but there the agent gathers the same signals through the Genies, applies this same
formula in `dispatch.py`, and pauses at a human-in-the-loop approval gate before it raises the
real service order. You just did the agent's "brain" by hand.*
