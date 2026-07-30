# tasks.md — Task Execution Status

## Setup (Hour 0-1)
- [x] Install LM Studio, download Gemma 4 12B QAT
- [x] Start local server, confirm test API call works
- [x] Get gaming laptop's local IP address
- [x] Test 2nd laptop connecting to `http://<ip>:1234`
- [x] Test phone connecting to the same address
- [x] Hotspot / local network access verified with mobile QR code rendering
- [x] Mask registration numbers and ensure multi-student profile isolation

## Data Prep (Hour 1-3)
- [x] Extract raw text from VTOP timetable PDF
- [x] Run extraction prompt against Gemma / deterministic parser, verify JSON output
- [x] Extract mess menu & schedule into JSON, verify output, cache in `data/shared/mess_menu.json`
- [x] Write assignment deadlines JSON (`data/deadlines.json`)
- [x] Write campus events JSON (`data/shared/events.json`)
- [x] Write teammate calendars JSON (`data/shared/teammate_calendars.json`)

## Planner Agent (Hour 3-7)
- [x] Write backend `/plan` route
- [x] Implement Gemma call with planner system prompt
- [x] Implement JSON parse + fallback
- [x] Render agenda in high-contrast Streamlit UI
- [x] Test with real extracted student data

## Replanner (Hour 7-10)
- [x] Add "mark as missed" UI trigger
- [x] Write backend `/replan` route
- [x] Implement replanner prompt & course regex matching fallback

## Negotiator (Hour 10-15)
- [x] Write backend `/negotiate` route
- [x] Implement per-teammate agent calls (sequential, distinct system prompts)
- [x] Implement coordinator reconciliation logic
- [x] Cap at 3 rounds, implement graceful fallback if no consensus
- [x] Log every round's message for transcript display
- [x] Test full negotiation flow with test suite assertions

## UI Polish (Hour 15-18)
- [x] Student Registration / Switch profile UI
- [x] Styled high-contrast Prussia Blue & Gold agenda view
- [x] Negotiation transcript view (chat-log style)
- [x] Generate QR code linking to local frontend server
- [x] Responsive check & CSS drop-down contrast fixes

## Testing & Hardening (Hour 18-20)
- [x] Full run-through of the entire demo flow
- [x] Verify fallback/cached paths work if live LLM call times out (2.0s threshold)
- [x] 24/24 Pytest suite passing 100%

## Deliverables (Hour 20-24)
- [x] Push clean GitHub repo with README (setup steps, architecture diagram)
- [x] MIT License added
- [x] Path safety (`os.path.realpath`) and CLI exit codes hardened
