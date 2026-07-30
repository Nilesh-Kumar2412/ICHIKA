# tasks.md — Task Execution Status & Completion Tracker

## Setup (Hour 0-1)
- [x] Install LM Studio, download Gemma 4 12B QAT / Qwen 1.7B
- [x] Start local server, confirm test API call works
- [x] Get local network IP address
- [x] Test cross-device connection to API server
- [x] Test mobile phone connecting to local network
- [x] Hotspot / local network access verified with mobile QR code rendering
- [x] Mask registration numbers and ensure multi-student profile isolation

## Data Prep (Hour 1-3)
- [x] Extract raw text from VTOP timetable PDF and MHTML web exports
- [x] Run extraction prompt against Gemma / deterministic parser, verify JSON output
- [x] Extract mess menu & schedule into JSON, verify output, cache in `data/shared/mess_menu.json`
- [x] Write assignment deadlines JSON (`data/deadlines.json`)
- [x] Write campus events JSON (`data/shared/events.json`)
- [x] Write teammate calendars JSON (`data/shared/teammate_calendars.json`) for 5 students
- [x] Generate mock profiles for 5 students (`26BEC1185`, `26BLC1265`, `26BLC1001`, `26BLC1002`, `26BLC1003`)

## Planner Agent (Hour 3-7)
- [x] Write backend `/plan` route (GET & POST)
- [x] Implement Gemma call with planner system prompt
- [x] Implement JSON parse + 5-day schedule fallback
- [x] Render agenda in high-contrast Cyber-Violet Streamlit UI
- [x] Test with real extracted student data

## Replanner (Hour 7-10)
- [x] Add "mark as missed" UI trigger
- [x] Write backend `/replan` route
- [x] Implement replanner prompt, course code regex matching, and day-name miss handling
- [x] Auto-allocate open evening catch-up slots without meal/class conflicts

## Negotiator (Hour 10-15)
- [x] Write backend `/negotiate` route
- [x] Implement per-teammate agent calls (sequential, distinct system prompts)
- [x] Implement coordinator reconciliation logic with dynamic name mapping
- [x] Cap at 3 rounds, implement graceful fallback if no consensus
- [x] Add LLM circuit-breaker flag for sub-second execution speed
- [x] Log every round's message for transcript display
- [x] Test full negotiation flow with test suite assertions

## Comparative Coding & Benchmarking
- [x] Add `/compare-code` backend endpoint for asymptotic time/space complexity analysis
- [x] Build AST-based deterministic complexity estimator fallback
- [x] Create Tab 6 UI with side-by-side solution benchmarks & VIT lab recommendations

## UI Polish & Theme (Hour 15-18)
- [x] Student Registration / Switch profile UI with automatic cache invalidation
- [x] Styled high-contrast Cyber-Violet dark theme matching `thumbnail.jpeg`
- [x] Dynamic backend model indicator in Hero Banner & sidebar
- [x] Negotiation transcript view (chat-log style)
- [x] Generate QR code linking to local frontend server
- [x] 5MB file upload support for `.pdf`, `.mht`, `.mhtml`, and `.json` files

## Testing & Hardening (Hour 18-20)
- [x] Complete A-to-Z codebase audit (25 issues found & 100% resolved)
- [x] Verify fallback/cached paths work if live LLM call times out
- [x] 25/25 Pytest suite passing 100%

## Deliverables (Hour 20-24)
- [x] Push clean GitHub repo with updated README (setup steps, architecture diagram, 5 profiles)
- [x] MIT License added
- [x] Path safety (`os.path.realpath`) and CLI exit codes hardened
- [x] 2-Minute Video Demo Script created (`video_demo_script.md`)
