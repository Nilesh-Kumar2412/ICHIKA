# audit.md — Risk & Error Checklist

Go through this before you consider the build "done." Each item includes why it matters.

## Compliance / Rules
- [ ] **Confirm Gemma usage requirement**: does "Code with Gemma" require on-device inference, or the cloud Gemma/Gemini API? Building the wrong one risks disqualification or lost points on the core requirement.
- [ ] **Check AI-assisted code disclosure rules** — some hackathons require you to disclose how much code was AI-generated ("vibe coded"). Confirm there's no restriction.
- [ ] **Team size limits** — confirm 2-3 people is within allowed range.
- [ ] **Submission format confirmed**: Kaggle write-up + live demo + GitHub repo + video — double check nothing else is required (e.g. specific Kaggle dataset/notebook format).

## Data & Privacy
- [ ] **Mask your registration number** in any file, screenshot, or video shared publicly (visible in the VTOP PDF).
- [ ] **No real scraping of VTOP** — only your own downloaded PDF/data used, no live scraping or credential automation.
- [ ] **Mock teammate calendars are clearly fictional/consented** — don't use real people's real schedules without asking them.

## Technical Reliability
- [ ] **JSON parsing has a fallback** for every Gemma call (strip fences, try/catch, fallback to cached state) — build this in from hour 3, not hour 20.
- [ ] **Negotiation rounds are capped** (max 3) so a live demo can't hang in an open-ended loop.
- [ ] **Network access tested at the actual venue**, not just at home — WiFi client isolation can silently block device-to-device connections; have a laptop-hosted hotspot as backup.
- [ ] **GPU not double-loaded** — make sure no leftover LM Studio chat window is competing with the app's calls during the live demo.
- [ ] **Cached "known-good" outputs exist** for planner/replanner/negotiator in case live inference is slow or malformed during judging.
- [ ] **Pre-recorded demo video exists** as a full fallback if live demo fails entirely.

## Product / Pitch
- [ ] **"Why is this autonomous, not a chatbot?"** — have a rehearsed answer: multi-step action without per-step instruction, self-triggered replanning, agents negotiating without human mediation each round.
- [ ] **VTOP-like mock data is plausible** (real-looking course codes/slot structure) so it doesn't look obviously fake to judges who may recognize VIT's actual system.
- [ ] **Real-world scaling note prepared** — a one-line closing point on how this could extend to real VTOP/calendar integration post-hackathon.

## Team Process
- [ ] **Roles assigned**: who owns agent/prompt logic, who owns UI, who owns mock data + pitch/video/write-up — avoid blocking each other in a <24h window.
- [ ] **Video recorded before exhaustion sets in** (hour 20-21, not hour 23).
