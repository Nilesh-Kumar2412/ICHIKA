# prd.md — Campus Copilot

## Hackathon Context
- **Event:** Code with Gemma
- **Track:** Autonomous Agents
- **Team size:** 2-3 (first-time hackathon participants)
- **Time budget:** <24 hours
- **Required deliverables:** Kaggle write-up, live demo, GitHub repo, demo video

## Problem Statement
VIT Chennai students juggle academic schedules (VTOP timetable, assignment deadlines), campus life (club events, mess timings), and group coordination (finding common study time) across disconnected tools. There's no single agent that plans across all of these *and* adapts autonomously when plans change.

## Target User
A VIT Chennai undergraduate student, and by extension their small project/study group (2-3 people).

## Goals
1. Demonstrate genuine agentic behavior (multi-step planning + autonomous replanning + multi-agent negotiation), not a single-turn chatbot.
2. Run fully on-device using Gemma 4 12B QAT — no cloud dependency.
3. Be demoable reliably within a short judging window.

## Core Features (In Scope)

| Feature | Description |
|---|---|
| Weekly Planner | Merges timetable, deadlines, campus events, and mess menu into one agenda |
| Replanner | User reports a missed item; agent regenerates the remaining plan |
| Study Group Negotiator | 2-3 teammate agents negotiate a common study slot (max 3 rounds), transcript shown live |
| Data Extraction | One-time conversion of VTOP timetable PDF and mess menu image into structured JSON via Gemma |
| Simple Login | Username/registration number as identifier (not secure auth — demo only) |
| Multi-device Access | Gaming laptop runs the server; teammate's laptop and phones connect via local IP/hotspot; QR code for quick access |

## Explicitly Out of Scope
- Real VTOP integration/scraping (only using the user's own downloaded PDF, one-time)
- Google Calendar or any external calendar service
- Real authentication/security (usernames only, no passwords)
- Persistent database (in-memory/JSON state is sufficient)
- Deployment/hosting beyond the local network for the demo

## Tech Stack
- **Model:** Gemma 4 12B QAT, served locally via LM Studio (OpenAI-compatible API)
- **Frontend:** React or plain HTML/JS
- **Backend:** Lightweight local server (Flask/Express) on the gaming laptop
- **Data:** Hardcoded/cached JSON, no external DB

## Success Criteria for the Demo
- Planner produces a sensible week from mock data without manual intervention
- Replanning visibly adjusts the plan when a miss is reported
- Negotiation transcript shows 2-3 agents converging on a slot without human mediation between rounds
- App is reachable from a teammate's device and a phone during the live demo
- Fallback: cached "known-good" outputs and a pre-recorded video exist in case live inference is flaky

## Key Risks (see audit.md for full list)
- Hackathon rules may specify cloud vs. on-device Gemma usage — confirm this explicitly
- Local model JSON reliability under demo pressure
- Venue WiFi client isolation blocking device-to-device access
