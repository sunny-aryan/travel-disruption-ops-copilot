# Travel Disruption Operations Copilot

A product-grade operations workflow prototype for managing disrupted travel bookings.

## Product Thesis

Travel disruptions are not just customer support cases. They are time-sensitive operational workflows involving passenger impact, provider uncertainty, policy constraints, SLA pressure, and human judgment.

This system helps operations teams prioritize disrupted bookings, evaluate safe recovery options, draft customer communication, and record human decisions while deterministic rules govern eligibility, approvals, and external execution boundaries.

## Why This Project Exists

This is Project 3 in my product portfolio.

The goal of this project is to demonstrate progression from:

1. AI-assisted decision support
2. Human-in-the-loop operational workflow
3. Product-grade workflow UX with prioritization, external dependency realism, and feedback loops

## Target Users

- Travel operations agents
- Operations supervisors
- Provider operations teams

## Initial Scope

The MVP will include:

- Disruption case queue
- SLA and priority indicators
- Case detail view
- Mock travel provider dependency
- Weather enrichment using the Open-Meteo API
- AI-generated case summaries and customer message drafts
- Deterministic policy checks
- Agent and supervisor workflows
- Decision capture
- Feedback analytics
- Audit trail

## Current Status

Project foundation initialized.

## Planned Stack

- Python
- Streamlit
- SQLite
- OpenAI API
- Open-Meteo API
- Local mock provider API/service

## Core Principle

AI helps agents understand and communicate.  
Deterministic systems govern what actions are allowed.  
Humans decide.  
Audit and feedback records improve the workflow.