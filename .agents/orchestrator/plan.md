# Orchestration Plan — Campus Copilot (ICHIKA)

## Iteration Status
Current iteration: 1 / 32

## Objectives
1. Multi-student VTOP timetable parsing (PDF & MHTML) into `data/students/<REG_NO>/` isolated JSON configs (26BEC1185, 26BLC1265). CLI script schema-validated.
2. Custom Visual UI matching thumbnail reference image: Prussian Blue (`#002147`), Gold (`#FFA500`), Charcoal text. High contrast tables & dropdowns. No AI buzzwords/emoji clutter.
3. Weekly Agenda & Smart Replanner Agent: Merges courses, meals, events, deadlines; marks missed courses visually, reschedules into remaining free slots.
4. Multi-Agent Group Negotiator: Aarav, Ananya, Rohan over max 3 rounds to select consensus study slot with transaction log.
5. 100% backend API test suite pass & Forensic Integrity Verification CLEAN.

## Workflow Phases
- **Phase 1: Exploration & Audit**: Dispatch Explorers to inspect existing codebase (`extract_timetable.py`, `backend/main.py`, `frontend/app.py`, `data/`) and test infrastructure.
- **Phase 2: Milestone Execution (Iterative Loop)**:
  - Sub-milestone 1: VTOP Timetable Parsing & CLI Script (MHTML + PDF support, Schema validation, Multiple students).
  - Sub-milestone 2: Backend API & Replanner / Negotiator Agents (3 rounds max, transaction log, slot merging & rescheduling).
  - Sub-milestone 3: High-Contrast Visual UI (Prussian Blue, Gold, Charcoal, thumbnail layout compliance, no AI buzzwords/emoji).
  - Sub-milestone 4: E2E Testing & Forensic Audit.

## Verification Checklist
- [ ] `python extract_timetable.py` parses both PDF and MHTML and validates schema.
- [ ] `data/students/26BEC1185` and `data/students/26BLC1265` populated with valid timetable & deadline JSONs.
- [ ] Backend API endpoints (`/plan`, `/replan`, `/negotiate`, `/students`) tested and returning 200 OK.
- [ ] Unit & E2E test suites pass 100%.
- [ ] UI rendered with Prussian Blue `#002147`, Gold `#FFA500`, Charcoal text, high contrast, matching reference layout.
- [ ] Forensic Auditor verdict CLEAN.
