## 2026-07-30T10:03:54Z
You are Worker 1 for Campus Copilot (ICHIKA) Milestone 2 & 3 & 4 (Implementation Phase).
Your working directory is: c:/Users/Nileshkumar/Downloads/files/.agents/teamwork_preview_worker_m1_1
Project Scope Document: c:/Users/Nileshkumar/Downloads/files/PROJECT.md
Original Request: c:/Users/Nileshkumar/Downloads/files/ORIGINAL_REQUEST.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Detailed Tasks for Implementation:
1. **CLI & Timetable Parsing (`extract_timetable.py` & `data/`)**:
   - Enhance `extract_timetable.py` to support both PDF and MHTML (`VIT Chennai - VTOP (1) (1).mht`) input files.
   - Add CLI arguments: `--input`, `--student_id` (or `--reg_no`), `--output_dir`, `--format`.
   - Remove Windows Unicode right-arrow character in `argparse` to prevent cp1252 crash on Windows console (`python extract_timetable.py --help`).
   - Implement deterministic MHTML and PDF text/table parsing fallback alongside LLM parsing so extraction works 100% reliably.
   - Save extracted schema-validated timetable and deadlines JSON files into isolated student directories (`data/students/26BEC1185/` and `data/students/26BLC1265/`). Ensure schema consistency (student_info, courses, deadlines).

2. **Backend API & Agents (`backend/main.py`, `backend/agents/`)**:
   - Implement/Update endpoints:
     - `POST /plan` (and `GET /plan`): Takes `student_id`, merges timetable, deadlines, campus events, mess menu into day-by-day weekly agenda.
     - `POST /replan`: Takes `student_id`, `missed_items`, `current_plan`. Marks missed items as `type: "missed"` (visual indicator), dynamically finds remaining free slots later in the week, and reschedules as `type: "replanned"`.
     - `POST /negotiate`: Takes `student_id`, `participants` (Aarav, Ananya, Rohan), optional `time_window`. Runs a multi-agent negotiation over maximum 3 rounds, producing a consensus study slot and a structured step-by-step transaction log.
     - `GET /students`: Returns list of registered active student IDs (`26BEC1185`, `26BLC1265`).
     - `POST /timetable/extract`: Accepts file path or upload + `student_id` and executes extraction.
   - Create complete Pytest backend test suite (`backend/tests/test_api.py` and `tests/test_extraction.py`) verifying all endpoints, schema validation, multi-student isolation, 3-round negotiator limit, and replanner slot rescheduling. Ensure pytest passes 100%.

3. **Frontend UI & High Contrast Styling (`frontend/app.py`, `frontend/.streamlit/config.toml`)**:
   - Ensure color palette is Prussian Blue (`#002147`), Gold (`#FFA500`), and Charcoal text (`#0F172A`/`#334155`).
   - Add high contrast borders (`1px solid #E2E8F0`), high contrast schedule tables, high contrast dropdown menus.
   - Remove decorative AI buzzwords (`Model Engine: Gemma 4`), remove emoji clutter (`🎓` icon), and remove gimmick persona tone dropdown options (`unhinged`, `girly`, `manly`).
   - Match custom visual layout specified in thumbnail reference image (`thumbnail.jpeg`).

4. **Build & Test Verification**:
   - Run `pytest` on backend and CLI test suites.
   - Run `python extract_timetable.py` on PDF and MHTML test files.
   - Document build and test outputs in your handoff report (`handoff.md` and `changes.md` in your working directory).

Communicate completion via `send_message` to parent (conversation ID: b9129f4c-2875-4303-851e-40d2ff34b89b).
