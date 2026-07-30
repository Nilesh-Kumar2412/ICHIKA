# implementation_plan.md — Campus Copilot (24h Build)

## Architecture Overview

```
[Gaming Laptop]
  ├── LM Studio (Gemma 4 12B QAT) — local server on port 1234
  ├── Backend (Flask/Express) — local server on a chosen port
  │     ├── /login (reg number → session/user state)
  │     ├── /plan (calls Planner agent)
  │     ├── /replan (calls Replanner agent)
  │     ├── /negotiate (runs Negotiator rounds)
  │     └── /data (serves cached timetable/mess menu/events JSON)
  └── Frontend (React or HTML/JS) — served to any device on the network

[2nd Laptop] ──┐
[Phone(s)]  ───┼──> connect to http://<gaming-laptop-ip>:<port>
[Judges' phone]┘     (same WiFi or laptop-hosted hotspot)
```

## Pre-Build Checklist (do before hour 0)
- [ ] Confirm hackathon rules: on-device vs. cloud Gemma requirement (see audit.md)
- [ ] LM Studio installed, Gemma 4 12B QAT downloaded
- [ ] Test hotspot/WiFi device-to-device reachability (client isolation check)
- [ ] Mask registration number in any shared files/screenshots

## Hour-by-Hour Plan

| Hours | Task | Owner (assign) |
|---|---|---|
| 0–1 | LM Studio server running, test call confirmed working; networking (hotspot/WiFi) tested with 2nd laptop + phone | |
| 1–3 | Extract timetable JSON from VTOP PDF (validated prompt); extract/cache mess menu JSON from image; write mock deadlines, campus events, and 2-3 teammate calendars | |
| 3–7 | Build Planner agent end-to-end: backend route → Gemma call → JSON → basic UI render | |
| 7–10 | Build Replanner flow (same call pattern, "miss" trigger) | |
| 10–15 | Build Negotiator: sequential calls with per-teammate prompts, round cap at 3, transcript logging | |
| 15–18 | UI polish: agenda view, negotiation transcript view, login by reg number, QR code generation for phone access | |
| 18–20 | Full run-through 2-3x on the actual demo network setup; fix breakages; verify fallback/cached data path works | |
| 20–21 | Record demo video (do this before fatigue sets in) | |
| 21–22 | Clean GitHub repo + README (setup instructions, architecture diagram, how to run) | |
| 22–23 | Write Kaggle write-up (reuse README + screenshots) | |
| 23–24 | Buffer / final checks | |

## File/Folder Structure (suggested)

```
campus-copilot/
├── backend/
│   ├── server.js (or app.py)
│   ├── agents/
│   │   ├── planner.js
│   │   ├── replanner.js
│   │   └── negotiator.js
│   └── data/
│       ├── timetable.json
│       ├── deadlines.json
│       ├── events.json
│       ├── mess_menu.json
│       └── teammate_calendars.json
├── frontend/
│   └── (React or plain HTML/JS)
├── agent.md
├── prd.md
├── implementation_plan.md
├── audit.md
├── tasks.md
└── README.md
```

## Demo Script (for judging + video)
1. Show login by reg number
2. Show generated weekly plan (Planner agent)
3. Report a missed item live → show Replanner adjust the plan
4. Trigger study group negotiation → show live transcript of 2-3 agents converging on a slot
5. Close with: fully offline, powered by Gemma 4 12B QAT, no cloud cost, privacy-preserving
