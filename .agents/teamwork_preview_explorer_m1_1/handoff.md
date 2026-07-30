# Handoff Report: Milestone 1 Explorer Analysis

**Agent**: Explorer 1 (`teamwork_preview_explorer_m1_1`)  
**Target Milestone**: Milestone 1 (Architecture & Codebase Exploration)  
**Parent Conversation ID**: `b9129f4c-2875-4303-851e-40d2ff34b89b`  
**Report Path**: `c:/Users/Nileshkumar/Downloads/files/.agents/teamwork_preview_explorer_m1_1/handoff.md`  

---

## 1. Observation

Direct, verified observations from code and environment inspection:

1. **`extract_timetable.py` CLI Crash**:
   - Running `python extract_timetable.py --help` failed with exit code 1:
     `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 101`
   - Location: `extract_timetable.py:172`:
     `description="Extract VTOP timetable PDF → structured JSON via Gemma"`

2. **PyMuPDF Dependency & PDF Extraction**:
   - Lines 28–34 import PyMuPDF (`fitz`).
   - Line 113 calls `fitz.open(pdf_path)` to extract PDF pages text.
   - PyMuPDF is currently not installed in the execution environment, triggering:
     `WARNING: PyMuPDF not installed. Run: pip install pymupdf`

3. **Absence of MHTML Parsing**:
   - `extract_timetable.py` contains 0 calls or helper functions for `.mht` or `.mhtml` files.
   - `data/` contains two MHTML files: `data/VIT Chennai - VTOP (1) (1).mht` and `data/VIT Chennai - VTOP (1).mht`.

4. **CLI Argument & Output Pathing Limitations**:
   - Lines 171–186 define arguments `--pdf`, `--out`, and `--text-only`.
   - Arguments `--student_id`, `--reg_no`, and `--input` are absent.
   - `--out` defaults to `data/timetable.json` (legacy flat structure), not `data/students/<REG_NO>/timetable.json`.

5. **LLM Context Window Truncation**:
   - Line 133 truncates raw extracted text: `raw_text[:6000]`.

6. **Student Data Isolation Audit (`data/students/`)**:
   - Directory `26BEC1185/`:
     - `timetable.json`: contains `student_info`, 9 `courses` (lacking `credits` field), 5 days `schedule`. `student_info.reg_no` = `"26BECXXXX"`. Missing `display_name` and `branch`.
     - `deadlines.json`: contains 3 items (`D1`, `D2`, `D3`), lacking `description` key.
   - Directory `26BLC1265/`:
     - `timetable.json`: contains `student_info` (with `display_name` = `"Student 2 (BLC)"`, `branch` = `"B.Tech"`), 9 `courses` (with `credits` field = `2.0`), 5 days `schedule`. `student_info.reg_no` = `"MASKED_FOR_PRIVACY"`.
     - `deadlines.json`: contains 4 items (`DL-BLC-1` .. `DL-BLC-4`), includes `description` field.

7. **Backend Data Integration**:
   - Running `list_registered_students()` from `backend/main.py` returns `['26BEC1185', '26BLC1265']`.
   - Running `get_fallback_plan()` from `backend/agents/planner.py` succeeds for both `26BEC1185` and `26BLC1265`.

---

## 2. Logic Chain

1. **CLI Unicode & Eager Setup**:
   - *Observation*: `python extract_timetable.py --help` threw `UnicodeEncodeError` due to `\u2192` (`→`) and printed LLM client init logs.
   - *Deduction*: Non-ASCII characters in stdout break default Windows encodings (`cp1252`). Top-level instantiation of LLM client forces unnecessary setup before CLI argument parsing.

2. **MHTML & File Extraction Deficit**:
   - *Observation*: `extract_timetable.py` only imports `fitz` for PDFs, while `data/` has `.mht` files.
   - *Deduction*: When users provide VTOP web page exports (`.mht`), the CLI script cannot read them. Adding an MHTML parser using Python's `email` + `html.parser` modules will bridge this gap.

3. **Data Isolation vs. CLI Output**:
   - *Observation*: `PROJECT.md` specifies isolated storage under `data/students/<REG_NO>/`, but `extract_timetable.py` defaults to `data/timetable.json`.
   - *Deduction*: To align CLI with architecture contracts, `--student_id` / `--reg_no` must automatically create and target `data/students/<REG_NO>/timetable.json` and `deadlines.json`.

4. **Schema Inconsistency Impact**:
   - *Observation*: `26BEC1185` lacks `credits` in `courses` and `description` in `deadlines.json`, while `26BLC1265` includes them. `reg_no` masking string varies (`"26BECXXXX"` vs `"MASKED_FOR_PRIVACY"`).
   - *Deduction*: Backend planner works because it accesses `.get("schedule", {})` and `.get("due_day")`, which are present in both. However, standardized schemas are required to ensure uniform UI rendering and validation.

---

## 3. Caveats

- **No Source Code Changes Made**: In accordance with Explorer read-only investigation rules, no code modifications were applied to `extract_timetable.py` or project files. Concrete fix strategies are documented in `analysis.md`.
- **LLM Provider Availability**: Live LLM calls depend on local LM Studio running `gemma-4-12b-qat` or Groq API key set in `.env`. Non-LLM fallback parser logic is currently absent in `extract_timetable.py`.

---

## 4. Conclusion

1. **`extract_timetable.py` requires 5 essential fixes**:
   - Fix Unicode help crash (`→` -> `->`) and defer LLM client creation.
   - Add MHTML (`.mht` / `.mhtml`) input decoder.
   - Add `--student_id` / `--reg_no` CLI flags and automatic output routing to `data/students/<REG_NO>/`.
   - Remove 6000-character input truncation.
   - Add regex/deterministic fallback extraction parser.
2. **Student datasets (`26BEC1185` and `26BLC1265`) are functional**:
   - Both datasets load correctly into `backend/main.py` and generate 5-day schedules via `planner.py`.
   - Schema properties (`credits`, `display_name`, `description`, `reg_no`) should be harmonized across student files.

---

## 5. Verification Method

To independently verify these observations:

1. **Test CLI help crash**:
   ```bash
   python extract_timetable.py --help
   ```
   *Expected result*: UnicodeEncodeError on Windows terminals using `cp1252`.

2. **Verify Student Data Loading**:
   ```bash
   python -c "import sys; sys.path.append('backend'); from main import load_student_file, list_registered_students; print(list_registered_students()); print(load_student_file('timetable.json', '26BEC1185')['student_info']); print(load_student_file('timetable.json', '26BLC1265')['student_info'])"
   ```
   *Expected output*: `['26BEC1185', '26BLC1265']` and student info dicts displaying schema differences.

3. **Verify Fallback Planner Execution**:
   ```bash
   python -c "import sys; sys.path.append('backend'); from main import load_student_file, load_shared_file; from agents.planner import get_fallback_plan; print(len(get_fallback_plan(load_student_file('timetable.json', '26BEC1185'), load_student_file('deadlines.json', '26BEC1185'), load_shared_file('events.json'), load_shared_file('mess_menu.json'))))"
   ```
   *Expected output*: `5` (five days of agenda).

---
