# Product Notes — Travel Disruption Operations Copilot

## Project Context

Travel disruptions create time-sensitive operational workflows. Agents need to understand passenger impact, provider reliability, available recovery options, policy constraints, and approval requirements before taking action.

This project explores how to design a product-grade operations console for disrupted travel bookings where:

- agents can prioritize work
- external dependency health is visible
- deterministic policy governs allowed actions
- AI reduces cognitive load
- supervisors handle high-risk decisions
- human decisions create audit and feedback records

The goal is not to build a complete travel rebooking platform. The goal is to demonstrate how product, workflow, AI, and system design can work together in a realistic operational product.

---

## Product Thesis

Travel disruption handling is not just customer support. It is an operational workflow involving:

- passenger urgency
- provider uncertainty
- SLA pressure
- policy constraints
- cost and refund risk
- role-based approvals
- human judgment
- feedback loops

The system follows this principle:

> AI summarizes and drafts.  
> Deterministic systems govern.  
> Humans decide.  
> Audit and feedback records improve the workflow.

---

## Target Users

### Operations Agent

Primary user responsible for handling disrupted bookings.

Needs to:

- identify which cases need attention
- understand disruption context quickly
- evaluate provider-supplied recovery options
- select a policy-valid action
- provide rationale
- capture feedback after action

### Operations Supervisor

Responsible for reviewing high-risk or approval-required cases.

Needs to:

- see cases requiring supervisor review
- inspect agent decisions and rationale
- approve, reject, or request more information
- preserve auditability of review decisions

### Product / Operations Lead

Secondary stakeholder who needs aggregate insight.

Needs to understand:

- recommendation usefulness
- provider data quality
- common override reasons
- passenger response patterns
- provider-level operational issues

---

## Core User Workflows

### Agent Workflow

```text
Open Agent View
→ review prioritized disruption queue
→ filter by provider, severity, status, action needed, disruption type
→ open a case
→ inspect passenger and disruption context
→ review provider dependency status
→ review weather enrichment
→ optionally generate AI operational brief and passenger message draft
→ review deterministic policy evaluation
→ select a policy-valid action
→ enter rationale
→ submit decision
→ case status updates
→ audit trail records action
→ submit workflow feedback
```

### Supervisor Workflow

```text
Open Supervisor View
→ review cases pending supervisor approval
→ inspect case context
→ review provider status, AI brief, policy evaluation, decision history, and audit trail
→ approve, reject, or request more information
→ submit supervisor rationale
→ case status updates
→ supervisor decision is persisted and audited
```

### Analytics Workflow

```text
Open Analytics View
→ inspect feedback KPIs
→ review recommendation usefulness
→ review provider data quality
→ identify override and escalation patterns
→ inspect passenger response / outcome distribution
→ review provider-level and disruption-type patterns
```

---

## Lifecycle States

The system models case state explicitly.

Key states include:

```text
NEW
WAITING_PROVIDER
CUSTOMER_CONTACT_PENDING
PENDING_SUPERVISOR_APPROVAL
APPROVED_PENDING_EXECUTION
REJECTED_BY_SUPERVISOR
NEEDS_AGENT_FOLLOW_UP
RESOLVED_REBOOKED
RESOLVED_REFUNDED
RESOLVED
ESCALATED
```

State transitions are triggered by agent or supervisor decisions.

Examples:

| Action | Resulting State |
|---|---|
| Rebook passenger | RESOLVED_REBOOKED |
| Issue refund | RESOLVED_REFUNDED |
| Wait for provider update | WAITING_PROVIDER |
| Escalate to supervisor | PENDING_SUPERVISOR_APPROVAL |
| Prepare customer update | CUSTOMER_CONTACT_PENDING |
| Supervisor approves | APPROVED_PENDING_EXECUTION |
| Supervisor rejects | REJECTED_BY_SUPERVISOR |
| Supervisor requests more information | NEEDS_AGENT_FOLLOW_UP |

---

## AI Boundaries

AI is intentionally assistive, not authoritative.

### AI Can

- summarize case context
- explain operational considerations
- draft passenger-facing communication
- reduce agent cognitive load
- operate in fallback mode when unavailable

### AI Cannot

- approve refunds
- approve rebookings
- override deterministic policy
- execute workflow actions
- change case state
- invent unavailable recovery options
- bypass supervisor review

This keeps the system aligned with the product principle:

> AI helps agents understand and communicate. Deterministic policy governs what actions are allowed.

---

## Deterministic Policy Boundaries

The policy engine governs:

- allowed actions
- blocked actions
- supervisor-required actions
- provider-data freshness constraints
- high-value refund thresholds
- high-cost rebooking thresholds
- critical-case handling
- sensitive passenger-impact flags

Policy output is visible in the UI so the agent can understand why an action is allowed, blocked, or requires approval.

---

## External Dependency Strategy

The system uses two types of external dependency modeling.

### Mocked Travel Provider Dependency

The travel provider dependency is mocked to simulate realistic states:

- success
- partial response
- stale data
- provider unavailable
- timeout
- no options available

This gives the prototype controlled, repeatable failure modes.

### Real Weather API Dependency

Weather enrichment uses the Open-Meteo API.

Weather is treated as contextual enrichment, not as the authoritative workflow control.

If weather data is unavailable, the system degrades gracefully and continues to rely on provider status and deterministic policy.

---

## Demo Controls

The app includes sidebar demo controls for dependency fallback.

Demo controls allow the user to simulate:

- AI healthy mode
- AI forced fallback
- weather healthy mode
- weather forced degraded mode

This makes failure behavior visible and testable without relying on real outages.

---

## Feedback Loop

The system captures case-level workflow feedback.

Feedback includes:

- recommendation usefulness
- provider data quality
- override or escalation reason
- passenger response / outcome
- internal learning note

Feedback is persisted and shown in analytics.

The goal is not model retraining. The goal is to show a product learning loop:

```text
human decision
→ feedback capture
→ aggregate analytics
→ product and operations insight
```

---

## Product UX Improvements Introduced

This project intentionally improves on earlier portfolio weaknesses around workflow UX.

Key UX improvements include:

- prioritized queue
- action-needed labels
- SLA status indicators
- role-specific views
- policy-aware action selection
- feedback capture
- analytics view
- visible dependency health
- demo-friendly fallback controls
- local success acknowledgements after submissions

The product is designed to reduce cognitive load for agents rather than simply display raw backend outputs.

---

## Current Limitations

This remains a prototype.

Known limitations:

- provider recovery options are mocked rather than integrated with a real travel provider
- weather context is not yet used in deterministic policy
- AI output is not persisted
- passenger messages are drafted but not sent
- refunds and rebookings are not executed
- no authentication or permission model
- no production-grade concurrency handling
- no policy version management UI
- limited synthetic dataset
- SQLite is used for local persistence only

---

## Future Improvements

Potential future improvements:

- add real provider or mobility API integration
- persist AI-generated summaries and drafts
- add policy versioning and policy audit
- add provider-level incident clustering
- add case lookup for non-active supervisor cases
- add recently reviewed supervisor cases
- add real notification or messaging integration
- add richer SLA breach handling
- add role-based permissions
- add production database such as Postgres
- add automated tests for policy and state transitions
- add clearer screenshot-based walkthroughs in README