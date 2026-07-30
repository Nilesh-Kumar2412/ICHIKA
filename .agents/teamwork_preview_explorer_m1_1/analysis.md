# Milestone 1 Analysis Report: Timetable Extraction & Data Directory Audit

**Author**: Explorer 1 (Campus Copilot / ICHIKA)  
**Working Directory**: `c:/Users/Nileshkumar/Downloads/files/.agents/teamwork_preview_explorer_m1_1`  
**Target Files**: `extract_timetable.py`, `data/`, `data/students/26BEC1185/`, `data/students/26BLC1265/`  
**Date**: 2026-07-30  

---

## 1. Executive Summary

This report presents a comprehensive technical audit of `extract_timetable.py` and the `data/` directory structure for Campus Copilot (ICHIKA) Milestone 1.

### Key Discoveries:
1. **MHTML Parsing Gap**: `extract_timetable.py` only implements PDF parsing via PyMuPDF (`fitz`). It has **zero support** for parsing VTOP MHTML web archives (`VIT Chennai - VTOP (1) (1).mht`), despite `.mht` files being present in `data/`.
2. **CLI Parameter & Pathing Gap**: `extract_timetable.py` does **not** accept `--student_id` or `--reg_no` or `--input` arguments. It defaults output to `data/timetable.json` (flat legacy path) instead of student-isolated paths (`data/students/<REG_NO>/timetable.json` and `deadlines.json`).
3. **Windows CLI Unicode Crash**: Executing `python extract_timetable.py --help` crashes on Windows terminals (`cp1252` encoding) due to an unencoded unicode right arrow character (`→`, `\u2192`) in the `ArgumentParser` description.
4. **Schema Inconsistencies**: While both student data folders (`26BEC1185` and `26BLC1265`) load successfully into `backend/main.py` and `backend/agents/planner.py`, there are notable schema variations:
   - `26BEC1185` is missing `display_name` and `branch` in `student_info`, missing `credits` in `courses`, and missing `description` in `deadlines.json`.
   - `26BLC1265` includes `display_name`, `branch`, course `credits`, and deadline `description`.
   - Privacy masking uses `"26BECXXXX"` in `26BEC1185` vs `"MASKED_FOR_PRIVACY"` in `26BLC1265`.
5. **Context Window & Resilience Limits**: `extract_timetable.py` truncates raw input text to 6000 characters before calling the LLM (`raw_text[:6000]`), which risks dropping late-week schedule items for dense timetables. It also lacks a non-LLM regex/heuristic fallback parser.

---

## 2. Deep Dive: `extract_timetable.py` Inspection

### 2.1 PDF Parsing Pipeline (`Time_table.pdf`)
- **Mechanism**: Lines 108–121 define `extract_pdf_text(pdf_path: str)` using PyMuPDF (`import fitz`). It opens the PDF and concatenates raw page text (`page.get_text("text")`).
- **LLM Pipeline**: Lines 126–166 define `extract_with_llm(raw_text)`. It constructs a prompt using `EXTRACTION_SYSTEM_PROMPT` (lines 60–103) and sends `raw_text[:6000]` to either Groq (`gemma2-9b-it`) or LM Studio (`gemma-4-12b-qat`).
- **Flaw — Hard Truncation**: Line 133 truncates input at 6000 characters:
  ```python
  RAW TEXT:
  {raw_text[:6000]}
  ```
  A full VTOP PDF page text stream often exceeds 6000 characters when headers, course tables, and slot tables are included. Truncation can cut off Friday/Saturday classes or course listings.

### 2.2 MHTML Parsing Gap (`VIT Chennai - VTOP (1) (1).mht`)
- **Observation**: `extract_timetable.py` contains no MHTML/HTML extraction logic.
- **Dataset Reality**: The `data/` directory contains two MHTML files:
  - `data/VIT Chennai - VTOP (1) (1).mht`
  - `data/VIT Chennai - VTOP (1).mht`
  And intermediate plain-text extractions: `mht_parsed.txt`, `mht_parsed2.txt`, `mht_slots.txt`, `mht_slots2.txt`.
- **Impact**: Passing `.mht` to `extract_timetable.py` raises a PyMuPDF file error (`fitz.FileDataError`) because PyMuPDF cannot process MIME HTML archives.

### 2.3 CLI & Execution Defects
1. **Unicode Crash on Help**: Line 172:
   ```python
   parser = argparse.ArgumentParser(
       description="Extract VTOP timetable PDF → structured JSON via Gemma"
   )
   ```
   The `→` symbol fails under Windows `cp1252` encoding during `--help`:
   `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 101`.
2. **Eager LLM Client Instantiation**: Lines 39–55 instantiate the `OpenAI` client at top-level module load. Importing `extract_timetable.py` or running `--help` executes network/client setup code and prints `Using LLM provider: ...` before argument parsing happens.

---

## 3. Data Directory & CLI Verification

### 3.1 CLI Contract Comparison

| Parameter / Feature | Required by PROJECT.md / Task | Implemented in `extract_timetable.py` | Status |
|---|---|---|---|
| Input File Flag | `--input <path>` | `--pdf <path>` (only) | ❌ Incomplete |
| Student Identification | `--student_id <id>` or `--reg_no <id>` | None | ❌ Missing |
| MHTML Support | Parse `.mht` / `.mhtml` | None | ❌ Missing |
| Output Directory Pathing | `data/students/<REG_NO>/timetable.json` | `data/timetable.json` (default) | ❌ Legacy only |
| Deadline JSON Output | Save `deadlines.json` | None | ❌ Missing |
| Stdin Mode | `--text-only` | `--text-only` | ✅ Supported |

### 3.2 Student Data Directory Audit (`data/students/`)

Directories present:
- `data/students/26BEC1185/`
  - `timetable.json` (4,224 bytes, 9 courses)
  - `deadlines.json` (553 bytes, 3 deadlines)
- `data/students/26BLC1265/`
  - `timetable.json` (3,972 bytes, 9 courses)
  - `deadlines.json` (1,195 bytes, 4 deadlines)

---

## 4. Schema Validation Analysis: 26BEC1185 vs 26BLC1265

### 4.1 `timetable.json` Schema Comparison

| Schema Field | 26BEC1185 | 26BLC1265 | Standardized Target Schema |
|---|---|---|---|
| `student_info.reg_no` | `"26BECXXXX"` | `"MASKED_FOR_PRIVACY"` | `"MASKED_FOR_PRIVACY"` |
| `student_info.display_name` | ❌ Missing | `"Student 2 (BLC)"` | `"Student <ID>"` |
| `student_info.branch` | ❌ Missing | `"B.Tech"` | `"B.Tech"` |
| `student_info.semester` | `"Fall Semester 2026-27"` | `"Fall Semester 2026-27"` | `"Fall Semester 2026-27"` |
| `student_info.total_credits` | `20.0` | `20.0` | `20.0` (float) |
| `courses[].code` | `"BACSE101"` | `"BACSE101"` | Required string |
| `courses[].title` | `"Problem Solving Using Python"` | `"Problem Solving Using Python"` | Required string |
| `courses[].type` | `"Lab Only"` / `"Theory Only"` | `"Lab Only"` / `"Theory Only"` | `"Theory"`, `"Lab"`, `"Online Course"`, `"Embedded Theory"`, `"Embedded Lab"`, `"Theory Only"`, `"Lab Only"` |
| `courses[].slot` | `"L7+L8+L25+L26"` | `"L13+L14+L27+L28"` | Required slot string |
| `courses[].venue` | `"AB1-706"` | `"AB4-409"` | Required venue string |
| `courses[].faculty` | `"JITENDRA TAHALYANI"` | `"RENIKUNTA MALLAIAH"` | Required faculty string |
| `courses[].credits` | ❌ Missing | `2.0` (float) | `credits` float |
| `schedule.<Day>[]` | `[{"time": "08:00 - 09:40", "type": "class", ...}]` | `[{"time": "14:00 - 14:50", "type": "class", ...}]` | Standard schedule item format |

### 4.2 `deadlines.json` Schema Comparison

| Schema Field | 26BEC1185 | 26BLC1265 | Standardized Target Schema |
|---|---|---|---|
| `id` | `"D1"`, `"D2"`, `"D3"` | `"DL-BLC-1"`, `"DL-BLC-2"` | String (`"D1"` or `"DL-1"`) |
| `title` | `"Python Problem Solving Lab Assignment 2"` | `"BACSE101 Python Lab Report — Experiment 3"` | Required string |
| `course_code` | `"BACSE101"` | `"BACSE101"` | Required string |
| `due_day` | `"Wednesday"` | `"Thursday"` | Standard day name |
| `due_time` | `"23:59"` | `"23:59"` | HH:MM 24-hr time |
| `priority` | `"High"` / `"Medium"` | `"High"` / `"Medium"` | `"High"`, `"Medium"`, `"Low"` |
| `description` | ❌ Missing | `"Submit completed code..."` | Optional string |

### 4.3 Backend Compatibility
Both student datasets were verified against `backend/main.py` and `backend/agents/planner.py`:
- `list_registered_students()` correctly discovers `['26BEC1185', '26BLC1265']`.
- `build_schedule_context()` builds prompt context for both students without error.
- `get_fallback_plan()` successfully generates 5-day agendas (Monday to Friday) for both students.

---

## 5. Identified Gaps, Bugs & Vulnerabilities

1. **Bug 1: CLI Help Unicode Crash**
   - Location: `extract_timetable.py:172`
   - Cause: Arrow symbol `→` in `ArgumentParser` description.
   - Severity: High (CLI fails on Windows).
2. **Bug 2: Eager Execution at Import Time**
   - Location: `extract_timetable.py:39-55`
   - Cause: `OpenAI()` client creation and `print()` statements outside functions.
   - Severity: Medium (side effects on import/help).
3. **Gap 1: Missing MHTML Input Handler**
   - Location: `extract_timetable.py:108-121`
   - Cause: Only `extract_pdf_text` implemented; no MHTML MIME/HTML decoder.
   - Severity: High (cannot parse VTOP `.mht` files).
4. **Gap 2: Missing `--student_id` / `--reg_no` CLI flags & Automatic Path Routing**
   - Location: `extract_timetable.py:170-186`
   - Cause: Hardcoded default output `data/timetable.json`.
   - Severity: High (violates multi-student isolated data architecture).
5. **Gap 3: Input Truncation at 6000 Characters**
   - Location: `extract_timetable.py:133`
   - Cause: `raw_text[:6000]` slices raw text.
   - Severity: Medium (potential data loss for large timetables).
6. **Gap 4: No Deadlines Parsing/Extraction**
   - Location: `extract_timetable.py`
   - Cause: Script only handles timetable data.
   - Severity: Medium (requires manual creation of `deadlines.json`).
7. **Gap 5: Absence of Heuristic/Regex Fallback Parser**
   - Location: `extract_timetable.py:126-166`
   - Cause: Entire extraction relies on LLM API availability.
   - Severity: High (script fails completely if LLM is offline or invalid JSON returned).

---

## 6. Recommended Concrete Fix Strategies

### Strategy 1: Add Dual PDF + MHTML Parser
Implement `extract_input_text(file_path: str) -> str`:
- Detect extension:
  - `.pdf`: Use `fitz` (PyMuPDF) or `pdfplumber` / `pypdf`.
  - `.mht` / `.mhtml`: Use Python's built-in `email` package (`email.message_from_file`) + `html2text` or `BeautifulSoup` to parse HTML tables into clean structured text.

```python
import email
from bs4 import BeautifulSoup

def extract_mhtml_text(mht_path: str) -> str:
    with open(mht_path, "rb") as f:
        msg = email.message_from_binary_file(f)
    parts = []
    for part in msg.walk():
        if part.get_content_type() in ("text/html", "text/plain"):
            payload = part.get_payload(decode=True)
            if payload:
                soup = BeautifulSoup(payload, "html.parser")
                parts.append(soup.get_text(separator="\n"))
    return "\n".join(parts)
```

### Strategy 2: Support CLI Flags and Student Isolation Pathing
Update `main()` in `extract_timetable.py`:
- Add arguments: `--input` (or `--pdf`), `--student_id` (or `--reg_no`), `--out`.
- Automatic output path logic:
  ```python
  if args.student_id:
      reg_no = args.student_id.upper().strip()
      out_dir = Path("data/students") / reg_no
      out_dir.mkdir(parents=True, exist_ok=True)
      out_timetable = out_dir / "timetable.json"
      out_deadlines = out_dir / "deadlines.json"
  ```

### Strategy 3: Remove Unicode Characters & Defer LLM Setup
- Replace `→` with `->` in `ArgumentParser` description.
- Move `OpenAI` client instantiation inside `extract_with_llm()` or a getter function `get_llm_client()`.

### Strategy 4: Standardize JSON Schema
Ensure both `26BEC1185` and `26BLC1265` adhere to:
1. `student_info`: include `reg_no` (`"MASKED_FOR_PRIVACY"`), `display_name`, `branch`, `semester`, `total_credits`.
2. `courses`: include `code`, `title`, `type`, `slot`, `venue`, `faculty`, `credits`.
3. `deadlines.json`: include `id`, `title`, `course_code`, `due_day`, `due_time`, `priority`, `description`.

### Strategy 5: Add Regex/Deterministic Fallback Parser
Implement heuristic regex extraction for VTOP course tables so that even if the LLM API is unavailable, standard VTOP timetable text patterns (e.g. `BACSE101`, `L7+L8`, `AB1-706`) are parsed into valid timetable JSON.

---
