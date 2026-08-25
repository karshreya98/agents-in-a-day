---
name: dispatch-plan
description: "Build Marc's weekly dispatch plan by hand — a ranked shortlist of which machines to service, from the structured fault reports plus store revenue. Use when the user says 'build a dispatch plan', 'dispatch plan analysis', 'which machines should Marc service this week', 'rank the machines', or 'preview the dispatch agent'. This is Lab 2 · Bonus: a scoring policy in the same spirit as Marc's Lab 3 dispatch agent, run once by hand over the table Lab 2 just built."
---

# Build Marc's dispatch plan (Lab 2 · Bonus)

**Goal:** turn the structured fault data into a **ranked dispatch plan** — for each machine
worth servicing this week, its location, unresolved-fault count, fault code, revenue at risk,
a priority score, and a short draft message to that store's manager.

This is a **hand-run preview** of what Marc's Lab 3 custom agent automates: it weighs how broken
a machine is against how much store revenue is at risk. Here you run it once, yourself; in Lab 3
it becomes a deployed, approval-gated agent.

> This analysis is **read-only**. It ranks and drafts — it **writes nothing** and raises no
> service order. The write-back (and the human approval gate in front of it) is Lab 3.

## Inputs (Unity Catalog, replace `<catalog>`)

- `<catalog>.coffee_maintenance.fault_reports_structured` — the table Lab 2 built
  (`machine_id`, `machine_model`, `fault_code`, `issue_description`, `location_name`,
  `contact_name`, `report_date`).
- `<catalog>.coffee_maintenance.service_orders` — tells you which faults are still
  **unresolved** (a machine with no `status = 'completed'` order). In a fresh workshop this
  table is often **empty**, in which case *every* fault report counts as unresolved.
- `<catalog>.gold.fact_coffee_sales` + `<catalog>.gold.dim_store` — sales by store; use them to
  compute each store's **weekly revenue** (the "revenue at risk" if that store's machine is
  down). The governed metric view `<catalog>.gold.sm_fact_coffee_sales_genie` exposes the same
  measure if you'd rather query that.

> [!IMPORTANT]
> Confirm the exact columns first (`DESCRIBE` each table). Table shapes can differ per workshop
> catalog — discover, then adapt the SQL. Two things to expect in the seeded data:
> - **Not every fault location has a sales store.** The maintenance data covers ~12 SF
>   neighborhoods; the sales data has fewer named "Sunny Bay – …" stores. Match `location_name`
>   to `store_name` on the neighborhood keyword (e.g. `LIKE '%Mission%'`); a machine at a
>   location with **no matching store carries $0 revenue at risk** and ranks on faults alone.
> - **Weekly revenue is modest** — tens to low-hundreds of dollars per store — which is why the
>   scoring below weights revenue per $100 (not per $1,000).

## The scoring policy

A machine's priority blends how broken it is with how much money is on the line:

```
priority = 5 · unresolved_faults  +  revenue_at_risk_per_week / 100

  FAULT_WEIGHT       = 5    points per unresolved fault              (primary signal)
  REVENUE_WEIGHT     = 1    point per $100/week of revenue at risk   (secondary)
  DISPATCH_THRESHOLD = 6    a machine makes the plan at priority ≥ 6
```

Read plainly, that threshold means: **always dispatch a machine with 2+ unresolved faults**
(repeat faults score ≥ 10 on their own), and for a **single** fault, dispatch only where the
store has **meaningful revenue at risk** (≈ $100+/week). Faults dominate; revenue breaks ties
and pulls high-value stores up.

> These weights are tuned to the workshop's seeded data. Lab 3's agent uses its own constants in
> `app/agent_server/dispatch.py` — the *idea* is the same (unresolved faults + revenue-at-risk,
> with a dispatch threshold); the exact numbers differ. This skill doesn't have to match it.

## Steps

1. **Unresolved faults per machine.** From `fault_reports_structured`, count reports per
   `machine_id` with **no completed `service_orders` row** for that machine. That count is
   `unresolved_faults`. (If `service_orders` is empty, every report is unresolved.)

2. **Revenue at risk per machine.** Compute each store's weekly revenue from
   `fact_coffee_sales` × `dim_store` (e.g. `sum(gross_revenue_usd)` over the weeks of data),
   then match the machine's `location_name` to a `store_name` on the neighborhood keyword. No
   matching store ⇒ `revenue_at_risk_per_week = 0`.

3. **Score and rank.** Compute `priority` with the formula above. Keep machines with
   `unresolved_faults > 0` **and** `priority ≥ 6`. Sort by `priority` descending.

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

Close by pointing out the parallel: *this ranked plan is what Marc's Lab 3 agent produces — but
there the agent gathers the same signals through the Genies, applies its own scoring in
`dispatch.py`, and pauses at a human-in-the-loop approval gate before it raises the real service
order. You just did the agent's "brain" by hand.*
