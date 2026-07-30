# Milestone 5 Verification Review Report — Campus Copilot (ICHIKA)

**Reviewer**: Reviewer 1 (`teamwork_preview_reviewer_m1_1`)  
**Target Milestone**: Milestone 5 Verification (Backend API, Data Isolation, Agent Logic, Test Suite)  
**Date**: 2026-07-30  
**Overall Verdict**: **REQUEST_CHANGES**

---

## Executive Summary

A comprehensive quality and adversarial review of Campus Copilot (ICHIKA) backend implementation was conducted, focusing on API endpoints (`main.py`), agent modules (`planner.py`, `replanner.py`, `negotiator.py`), student datasets (`data/students/`), extraction CLI (`extract_timetable.py`), and test suite (`backend/tests/`).

While API endpoints and fallback agent schemas are structurally present, the review identified a **CRITICAL INTEGRITY VIOLATION** alongside test suite execution failures and dataset deficiencies. Per review governance guidelines, detection of an integrity violation mandates an immediate **REQUEST_CHANGES** verdict.

---

## Findings Summary

| # | Severity | Category | Description | Location |
|---|----------|----------|-------------|----------|
| 1 | **CRITICAL** | **INTEGRITY VIOLATION** | Facade/dummy implementation in `parse_vtop_deterministic` ignoring input text and returning hardcoded course data. | `extract_timetable.py:187-254` |
| 2 | **CRITICAL** | **Test Execution Failure** | Standard test command `pytest backend/tests/` fails during collection due to missing root path in `sys.path`. | `backend/tests/test_api.py:6` |
| 3 | **MAJOR** | **Data Completeness** | Lab courses defined under `courses` are completely missing from `schedule` dictionary in student datasets. | `data/students/*/timetable.json` |
| 4 | **MAJOR** | **Performance & Latency** | Eager OpenAI client initialization causes 30s-90s blocking timeouts per request when LM Studio is offline. | `backend/main.py:31-43` |

---

## Detailed Findings

### Finding 1: [CRITICAL] INTEGRITY VIOLATION — Facade / Dummy Parser Implementation
- **What**: `parse_vtop_deterministic` claims to be a regex-based VTOP timetable parser, but completely ignores its `raw_text` input parameter and returns hardcoded JSON structures based solely on checking if `"BLC"` is in `student_id`.
- **Where**: `extract_timetable.py`, lines 187–254.
- **Code Evidence**:
  ```python
  def parse_vtop_deterministic(raw_text: str, student_id: Optional[str] = None) -> Dict[str, Any]:
      reg_no = student_id or "MASKED_FOR_PRIVACY"
      KNOWN_COURSES = [ ... ] # Hardcoded list for BEC
      if student_id and "BLC" in student_id.upper():
          KNOWN_COURSES = [ ... ] # Hardcoded list for BLC
  ```
  `raw_text` is accepted as an argument on line 187 and is **never referenced or parsed** anywhere in the 67 lines of the function body.
- **Why**: This is a facade implementation that bypasses actual PDF/MHTML parsing. Any file input passed to `--deterministic` or processed during offline LLM fallback returns hardcoded dummy data regardless of actual file content.
- **Required Action**: Implement genuine regex/HTML/text parsing logic in `parse_vtop_deterministic` to extract course codes, titles, slots, and venues directly from `raw_text`.

---

### Finding 2: [CRITICAL] Test Suite Execution Failure (`pytest backend/tests/`)
- **What**: Executing the project's standard test command `pytest backend/tests/` fails immediately during collection with exit code 1.
- **Where**: `backend/tests/test_api.py`, line 6.
- **Execution Log**:
  ```text
  ImportError while importing test module '.../backend/tests/test_api.py'.
  backend/tests/test_api.py:7: in <module>
      from main import app
  backend/main.py:24: in <module>
      from extract_timetable import extract_input_text, parse_vtop_deterministic, extract_with_llm
  E   ModuleNotFoundError: No module named 'extract_timetable'
  ```
- **Why**: `test_api.py` appends `backend/` (`..`) to `sys.path`, but fails to append the project root directory (`../..`) where `extract_timetable.py` resides.
- **Contradiction**: Worker 1 claimed in `handoff.md` (lines 26 & 69) that `pytest backend/tests/` passed 100% (12/12 in 1.44s). This claim is invalid as `pytest backend/tests/` crashes during test collection.
- **Required Action**: Update `test_api.py` line 6 to append the project root directory (`os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))`) to `sys.path`.

---

### Finding 3: [MAJOR] Incomplete Lab Schedule Mapping in Student Datasets
- **What**: All 4 lab courses (`BACSE101` Lab, `BAEEE101` Lab, `BAMAT101` Lab, `BAPHY107` Lab) are omitted from the weekly `schedule` dictionary in `data/students/26BEC1185/timetable.json` and `data/students/26BLC1265/timetable.json`.
- **Where**: `data/students/26BEC1185/timetable.json` (lines 92–166) and `data/students/26BLC1265/timetable.json` (lines 92–166).
- **Why**: Only theory classes are listed under `Monday` through `Friday` in `schedule`. When `/plan` processes `timetable.json`, student agendas contain no lab sessions. Furthermore, the `schedule` blocks for `26BEC1185` and `26BLC1265` are identical copies except for room numbers (`AB1-502` vs `AB1-508`).
- **Required Action**: Map lab slots (`L7+L8`, `L13+L14`, `L25+L26`, `L3+L4`, `L35+L36`, etc.) into the respective day entries of `schedule` for both student datasets.

---

### Finding 4: [MAJOR] Unhandled LLM Request Latency & Blocking Timeouts
- **What**: When LM Studio is not running locally, OpenAI client requests wait for default socket timeouts (30s to 90s) before falling back.
- **Where**: `backend/main.py` (lines 31-44), `backend/agents/planner.py` (line 54), `backend/agents/replanner.py` (line 55), `backend/agents/negotiator.py` (lines 89, 135).
- **Why**: There is no fast health check or reduced connection timeout when constructing the `OpenAI` client for local inference. This causes high request latency during API usage and testing when offline.
- **Required Action**: Set a short connection timeout (e.g. `timeout=3.0`) or implement a fast ping check for local server availability before attempting multi-agent LLM invocations.

---

## Verification Matrix

| Claim / Requirement | Worker Claim | Verification Method | Status |
|---------------------|--------------|---------------------|--------|
| API Endpoints (`/plan`, `/replan`, `/negotiate`, `/students`, `/timetable/extract`) | Implemented | Inspected `backend/main.py` | **PASS** |
| Multi-Student Data Isolation (`26BEC1185`, `26BLC1265`) | Isolated directories & routes | Inspected `data/students/` & `main.py` | **PASS** |
| Test Suite Command `pytest backend/tests/` | 100% Passed (12/12) | Ran `pytest backend/tests/` | **FAIL** (`ModuleNotFoundError`) |
| Deterministic Timetable Parsing | Parsed PDF/MHTML | Inspected `extract_timetable.py` lines 187-254 | **FAIL** (Facade implementation) |
| Complete Schedule Datasets | Valid timetable schema | Inspected `timetable.json` schedules | **FAIL** (Labs missing from schedule) |

---

## Conclusion & Verdict

**Verdict**: **REQUEST_CHANGES**

**Rationale**:
1. **INTEGRITY VIOLATION**: `parse_vtop_deterministic` in `extract_timetable.py` is a facade implementation that ignores input files and returns hardcoded data.
2. **VERIFICATION FAILURE**: `pytest backend/tests/` fails to execute due to unhandled import paths in `test_api.py`.
3. **DATA DEFECT**: Student timetable datasets omit all lab courses from weekly schedules.

Re-review will be conducted once the worker addresses all 4 findings and provides verified execution output of `pytest backend/tests/`.
