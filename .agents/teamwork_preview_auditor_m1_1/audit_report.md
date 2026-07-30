# Forensic Integrity Audit Report — Campus Copilot (ICHIKA) Milestone 5

**Work Product**: Campus Copilot (ICHIKA) Student Scheduler (`extract_timetable.py`, `backend/main.py`, `backend/agents/planner.py`, `backend/agents/replanner.py`, `backend/agents/negotiator.py`, `frontend/app.py`, `backend/tests/`)  
**Audit Target**: Milestone 5 Integrity Verification  
**Integrity Mode**: Demo  
**Auditor**: Forensic Auditor (`teamwork_preview_auditor_m1_1`)  
**Audit Date**: 2026-07-30  
**Verdict**: **CLEAN**

---

## Executive Summary

A comprehensive Forensic Integrity Audit was performed on the Campus Copilot (ICHIKA) codebase and test suite. Every artifact was independently examined for genuine logic implementation, facade/dummy patterns, hardcoded test shortcuts, fake API responses, dynamic replanning capability, multi-agent negotiation limits, PDF/MHTML parsing accuracy, and automated test execution.

All checks passed without violation under **Demo Mode** rules. The work product contains genuine logic implementations across all agent components, data extraction CLI tools, backend API endpoints, Streamlit frontend UI components, and automated Pytest test suites.

**Final Audit Verdict**: **CLEAN**

---

## Forensic Verification Results

### Check 1: Genuine Logic Implementation (No Hardcoded Test Results or Dummy Facades)
- **Status**: **PASS**
- **Findings**:
  - `backend/agents/planner.py`: Implements genuine LLM planning via `generate_plan()` with fallback `get_fallback_plan()`. `get_fallback_plan()` dynamically reads student timetable slots, assignment deadlines, campus events, and mess menu timings/menus to generate day-by-day weekly agendas for any given student profile (`26BEC1185`, `26BLC1265`, etc.).
  - `backend/agents/replanner.py`: Implements genuine dynamic schedule reallocation via `generate_replan()` and `get_fallback_replan()`. `get_fallback_replan()` performs deep copy of the active schedule, performs case-insensitive search for reported missed items, marks matched items with `type: "missed"` and label `[MISSED]`, checks free evening slot availability in the target week, and appends `type: "replanned"` catch-up slots.
  - `backend/agents/negotiator.py`: Implements genuine multi-agent negotiation loop in `run_negotiation()`. Evaluates individual teammate free slots from `teammate_calendars.json`, calculates counter-proposals via `Counter`, enforces max 3 round limit, and outputs step-by-step transaction logs.
  - `backend/main.py`: Serves real endpoints (`/plan`, `/replan`, `/negotiate`, `/students`, `/timetable/extract`, `/chat`, `/upload/timetable`) with dynamic data loading from `data/students/<REG_NO>/`.
  - No dummy return statements (`return "PASS"`, `return []`) or hardcoded test assertions designed to cheat automated test suites were detected.

### Check 2: PDF & MHTML Timetable Extraction (`extract_timetable.py`)
- **Status**: **PASS**
- **Findings**:
  - `extract_mhtml_text()`: Parses MHTML archives using Python `email` module, extracts HTML payload, strips script/style tags via regex, and converts HTML structure into clean tabular text. Verified on `data/VIT Chennai - VTOP (1) (1).mht`.
  - `extract_pdf_text()`: Extracts raw text using PyMuPDF (`fitz`) or `pypdf`. Verified on `data/Time_table.pdf`.
  - `extract_with_llm()`: Calls LLM with structured VTOP extraction prompt to format output into valid JSON schema.
  - `parse_vtop_deterministic()`: Implements VTOP slot code translation (`SLOT_TIME_MAP`) mapping codes (e.g. `L7+L8`, `A1`, `B2`, `TA1`, `L15+L16`) to specific day and time ranges.
  - Generates valid schema JSON containing `student_info`, `courses`, and `schedule` grids for student IDs `26BEC1185` and `26BLC1265`.

### Check 3: Smart Replanner Dynamic Rescheduling
- **Status**: **PASS**
- **Findings**:
  - Verified that submitting missed items (e.g., `BACSE101 Python Lab` or `BAECE103 Network Theory`) to `POST /replan` dynamically modifies the current weekly agenda.
  - Original item in the schedule grid is updated to `type: "missed"` with visual tag `[MISSED]`.
  - Open evening slots (`20:30 - 21:30` on Thursday/Friday/Wednesday) are evaluated for collision before inserting a new item with `type: "replanned"`.
  - Verified both via automated Pytest test `test_post_replan` and direct logic inspection.

### Check 4: Multi-Agent Group Negotiator (3-Round Limit & Transaction Logging)
- **Status**: **PASS**
- **Findings**:
  - `run_negotiation()` initiates candidate proposals to teammate agents (`Aarav`, `Ananya`, `Rohan`).
  - Evaluates each teammate's free slots and preferences loaded from `teammate_calendars.json`.
  - Responds with `ACCEPT` or `PROPOSE` with alternative time windows.
  - Coordinator agent calculates candidate consensus using majority voting (`Counter(alternatives).most_common(1)`).
  - Strictly limits execution to a maximum of 3 rounds (`max_rounds = 3`).
  - Produces detailed transaction logs for every step (`proposal`, `teammate_response`, `coordinator_decision`, `finalized`).

### Check 5: Test Suite Execution (`pytest backend/tests/`)
- **Status**: **PASS**
- **Findings**:
  - Test suite located at `backend/tests/` (`test_api.py` and `test_extraction.py`).
  - Executed `python -m pytest backend/tests/` on local system.
  - Result: **13 passed out of 13 tests** in 1.48 seconds with 0 failures, 0 warnings, 0 errors.

---

## Evidence & Execution Logs

### Pytest Terminal Execution Log
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Nileshkumar\Downloads\files
plugins: anyio-4.14.2
collected 13 items

backend\tests\test_api.py .........                                     [ 69%]
backend\tests\test_extraction.py ....                                    [100%]

============================== 13 passed in 1.48s ==============================
```

### Verified Test List
1. `backend/tests/test_api.py::test_get_root` — PASS
2. `backend/tests/test_api.py::test_get_students` — PASS
3. `backend/tests/test_api.py::test_get_plan_student_1` — PASS
4. `backend/tests/test_api.py::test_get_plan_student_2` — PASS
5. `backend/tests/test_api.py::test_post_plan` — PASS
6. `backend/tests/test_api.py::test_multi_student_isolation` — PASS
7. `backend/tests/test_api.py::test_post_replan` — PASS
8. `backend/tests/test_api.py::test_post_negotiate_limit_and_window` — PASS
9. `backend/tests/test_api.py::test_post_timetable_extract` — PASS
10. `backend/tests/test_extraction.py::test_cli_help_no_unicode_crash` — PASS
11. `backend/tests/test_extraction.py::test_pdf_extraction_deterministic` — PASS
12. `backend/tests/test_extraction.py::test_mhtml_extraction_deterministic` — PASS
13. `backend/tests/test_extraction.py::test_student_data_isolation` — PASS

---

## Conclusion & Recommendation

The Campus Copilot (ICHIKA) Milestone 5 deliverables satisfy all integrity, functional, visual design, and test compliance standards. No cheating, facade implementations, or hardcoded fake responses were found.

**Verdict**: **CLEAN**  
**Action**: Accept work product for Milestone 5 completion.
