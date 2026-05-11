# Trade-Offs — Travel Disruption Operations Copilot

This document captures key product and system trade-offs made during the project.

---

## 1. Operations Console vs Full Travel Rebooking Platform

### Decision

Build an operations console for disrupted bookings, not a complete rebooking platform.

### Why

The portfolio goal is to demonstrate product-grade workflow thinking:

- prioritization
- policy controls
- role-based review
- external dependency handling
- feedback loops
- auditability

A full rebooking engine would require complex route search, ticketing, settlement, provider contracts, and passenger rights logic.

### Alternative Considered

Build a more complete travel recovery platform with route optimization and real booking execution.

### Why Rejected

Too broad for a 2–3 week portfolio project. It would shift focus from product workflow design to travel domain complexity.

---

## 2. Mock Provider Dependency vs Real Travel Provider API

### Decision

Use mocked provider responses for core travel recovery options.

### Why

The project needs reliable demonstration of multiple external dependency states:

- success
- partial response
- stale data
- timeout
- provider unavailable
- no recovery options

A mock provider allows these scenarios to be tested repeatedly and shown in screenshots.

### Alternative Considered

Use a real travel or mobility API for recovery options.

### Why Rejected

Real provider APIs may be difficult to access, unreliable for repeatable demo scenarios, or unavailable for refund/rebooking flows. They may also create unnecessary implementation overhead.

### Future Improvement

Integrate a real provider or mobility API while keeping mocked fallback scenarios for testing.

---

## 3. Real Weather API as Enrichment, Not Authority

### Decision

Use Open-Meteo as a real external API for weather enrichment.

### Why

Weather can be useful disruption context, but it should not directly determine operational actions in the MVP.

### Alternative Considered

Use weather as an input into policy or priority scoring.

### Why Rejected

That would add complexity and could overstate the reliability of weather as a decision signal. Provider status and deterministic policy should remain the primary controls.

### Product Principle

Weather informs agent caution. It does not approve or block actions.

---

## 4. AI Assistance vs AI Decision-Making

### Decision

Use AI for operational summaries and passenger message drafts only.

### Why

AI is useful for reducing cognitive load, but unsafe as the authority for refund, rebooking, or escalation decisions.

### Alternative Considered

Let AI recommend final actions or choose the best recovery option.

### Why Rejected

The workflow requires deterministic controls, auditability, and human accountability. AI recommendations could be inconsistent or unsupported by policy.

### Product Principle

AI summarizes and drafts. Deterministic policy governs. Humans decide.

---

## 5. Deterministic Policy Engine vs LLM-Based Policy Reasoning

### Decision

Use handcrafted deterministic policy rules.

### Why

For safety-critical workflow actions, deterministic policy is easier to inspect, test, and explain.

The policy engine governs:

- allowed actions
- blocked actions
- supervisor-required actions
- provider-data freshness
- cost thresholds
- sensitive passenger-impact flags

### Alternative Considered

Ask the LLM to evaluate policy eligibility.

### Why Rejected

LLM-based policy evaluation would be harder to audit and could create inconsistent decisions.

### Future Improvement

Add policy configuration files, policy versions, and policy test cases.

---

## 6. SQLite vs Postgres

### Decision

Use SQLite for local persistence.

### Why

SQLite is sufficient for a locally runnable portfolio prototype. It supports persisted decisions, audit events, case states, feedback records, and supervisor decisions without infrastructure setup.

### Alternative Considered

Use Postgres.

### Why Rejected

Postgres would be more production-like but would add setup overhead and make the project harder to run locally.

### Future Improvement

Move to Postgres for multi-user concurrency, production deployment, role-based access, and richer operational reporting.

---

## 7. Case-Level Feedback vs Decision-Level Feedback

### Decision

Capture feedback at the case level.

### Why

Case-level feedback is simpler and still useful for product learning. It connects feedback to concrete operational context without forcing the user to select which exact decision the feedback refers to.

### Alternative Considered

Attach feedback to specific agent decisions, supervisor decisions, AI outputs, or provider responses.

### Why Rejected

More precise, but too complex for the MVP UI and data model.

### Future Improvement

Support decision-level and recommendation-level feedback once workflows become more complex.

---

## 8. Success Acknowledgements vs Immediate Auto-Rerun

### Decision

Show success acknowledgements near the user action and avoid unnecessary automatic reruns.

### Why

Immediate reruns refreshed the page but created a poor experience because the user lost visual context and had to scroll to confirm the action.

### Alternative Considered

Call `st.rerun()` immediately after every decision or feedback submission.

### Why Rejected

It caused UI jumps and made confirmations easy to miss.

### Product Principle

The user should feel confident that the workflow action succeeded.

---

## 9. Active Queue vs Full Case History

### Decision

Default Agent View to active cases only, while allowing terminal cases to be shown through a toggle.

### Why

Operations agents typically need to focus on cases that still require action.

Terminal statuses include:

- RESOLVED
- RESOLVED_REBOOKED
- RESOLVED_REFUNDED
- REJECTED_BY_SUPERVISOR

### Alternative Considered

Show all cases by default.

### Why Rejected

It increases cognitive load and makes the queue less operationally useful.

### Future Improvement

Add dedicated views for active queue, closed cases, and supervisor review history.

---

## 10. Supervisor Queue Only Shows Active Review Cases

### Decision

Supervisor View shows only cases with `PENDING_SUPERVISOR_APPROVAL`.

### Why

The supervisor queue should answer:

> What needs my decision right now?

Already approved, rejected, or returned cases should not remain in the active approval queue.

### Alternative Considered

Show all supervisor-related statuses in the supervisor queue.

### Why Rejected

It blurred the distinction between active review work and historical review records.

### Future Improvement

Add a separate "Recently Reviewed" or case lookup section for supervisors.

---

## 11. Demo Controls for Dependency Degradation

### Decision

Add sidebar demo controls for AI and weather degradation.

### Why

Failure-mode behavior should be easy to test and demonstrate without changing code, deleting environment variables, or relying on real outages.

### Alternative Considered

Only test fallback behavior by breaking API calls manually.

### Why Rejected

Manual failure testing is fragile and not demo-friendly.

### Product Principle

Reliability behavior should be visible, testable, and explainable.

---

## 12. Streamlit vs Custom Frontend

### Decision

Use Streamlit for the UI.

### Why

Streamlit enables fast iteration and keeps the focus on product workflow logic rather than frontend engineering.

### Alternative Considered

Build a custom React frontend.

### Why Rejected

A custom frontend would allow better UX polish but would increase implementation time and shift the project toward software engineering complexity.

### Future Improvement

If this were taken further, a custom frontend could improve table interactions, persistent notifications, role-based navigation, and workflow ergonomics.

---

## Summary

The main trade-off across the project was to prioritize:

- workflow realism
- safety boundaries
- local runnability
- visible degradation
- role-specific decision-making
- feedback loops

over:

- production infrastructure
- full travel-domain completeness
- real rebooking execution
- advanced AI autonomy
- complex frontend engineering