# tasks.md — Task Breakdown

Assign each task to a teammate before starting. Check off as completed.

## Setup (Hour 0-1)
- [ ] Install LM Studio, download Gemma 4 12B QAT
- [ ] Start local server, confirm test API call works
- [ ] Get gaming laptop's local IP address
- [ ] Test 2nd laptop connecting to `http://<ip>:1234`
- [ ] Test phone connecting to the same address
- [ ] If venue WiFi blocks device-to-device, set up laptop/phone hotspot instead and retest
- [ ] Mask registration number in the shared VTOP PDF before it's used in any public file

## Data Prep (Hour 1-3)
- [ ] Extract raw text from VTOP timetable PDF
- [ ] Run extraction prompt against Gemma, verify JSON output matches actual timetable (spot-check a few entries)
- [ ] Extract mess menu image → Gemma multimodal → JSON, verify output, cache it
- [ ] Write mock assignment deadlines JSON
- [ ] Write mock campus events JSON (2-3 events)
- [ ] Write 2-3 mock teammate calendars JSON

## Planner Agent (Hour 3-7)
- [ ] Write backend `/plan` route
- [ ] Implement Gemma call with planner system prompt
- [ ] Implement JSON parse + fallback
- [ ] Render agenda in basic UI (even unstyled list is fine at this stage)
- [ ] Test with real extracted data

## Replanner (Hour 7-10)
- [ ] Add "mark as missed" UI trigger
- [ ] Write backend `/replan` route
- [ ] Implement replanner prompt, test with a couple of miss scenarios

## Negotiator (Hour 10-15)
- [ ] Write backend `/negotiate` route
- [ ] Implement per-teammate agent calls (sequential, distinct system prompts)
- [ ] Implement coordinator reconciliation logic
- [ ] Cap at 3 rounds, implement graceful "closest option" fallback if no consensus
- [ ] Log every round's message for transcript display
- [ ] Test full negotiation flow 2-3 times

## UI Polish (Hour 15-18)
- [ ] Login screen (reg number input)
- [ ] Agenda view (styled)
- [ ] Negotiation transcript view (chat-log style)
- [ ] Generate QR code linking to the local server address
- [ ] Basic responsive check on phone browser

## Testing & Hardening (Hour 18-20)
- [ ] Full run-through of the entire demo flow, 2-3 times
- [ ] Verify fallback/cached paths work if a live call fails
- [ ] Confirm no leftover LM Studio chat windows competing for GPU during demo
- [ ] Fix any breakages found

## Deliverables (Hour 20-24)
- [ ] Record demo video (2-3 min: problem → planner → replanner → negotiation → close)
- [ ] Push clean GitHub repo with README (setup steps, architecture diagram)
- [ ] Write Kaggle write-up (reuse README + screenshots/GIFs)
- [ ] Final buffer check against audit.md
