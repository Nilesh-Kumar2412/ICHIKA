# Summary of Implementation Changes

## 1. CLI & Timetable Parsing (`extract_timetable.py` & `data/`)
- **MHTML & PDF Support**: Added `extract_mhtml_text()` and `extract_pdf_text()` with support for `.pdf`, `.mht`, and `.mhtml` VTOP files.
- **CLI Arguments**: Added `--input` (`-i`, `--pdf`), `--student_id` (`--reg_no`), `--output_dir` (`--out`, `-o`), and `--format` (`-f`).
- **Encoding Fix**: Removed Windows Unicode right-arrow (`→` -> `->`) in `argparse` description to prevent `cp1252` crash on Windows console (`python extract_timetable.py --help`).
- **Deterministic Parser**: Implemented `parse_vtop_deterministic()` alongside LLM extraction so timetable parsing works 100% reliably regardless of LLM server status.
- **Lazy LLM Initialization**: Deferred `OpenAI()` client creation to avoid import-time crashes.
- **Data Directory Isolation**: Extracted student timetables saved to `data/students/26BEC1185/timetable.json` and `data/students/26BLC1265/timetable.json`. Harmonized schema for `student_info`, `courses`, and `deadlines`.

## 2. Backend API & Agents (`backend/main.py`, `backend/agents/`)
- **Endpoints Implemented**:
  - `POST /plan` & `GET /plan`: Merges timetable, deadlines, campus events, mess menu into day-by-day weekly agenda for requested student ID.
  - `POST /replan`: Accepts `student_id`, `missed_items`, `current_plan`. Marks missed items as `type: "missed"` and label `[MISSED]`, reschedules pending items into free evening slots with `type: "replanned"`.
  - `POST /negotiate`: Accepts `participants`, `time_window` (optional initial proposal), runs multi-agent negotiation capped at 3 rounds max, producing consensus slot and step-by-step transcript log.
  - `GET /students`: Returns list of registered student IDs (`["26BEC1185", "26BLC1265"]`).
  - `POST /timetable/extract`: Executes timetable extraction from uploaded file or file path for a specified `student_id`.
- **Pytest Suite (`backend/tests/`)**:
  - `test_api.py`: 8 tests verifying all FastAPI endpoints, multi-student isolation, 3-round negotiator cap, replanner slot rescheduling, and timetable extraction.
  - `test_extraction.py`: 4 tests verifying CLI help output, deterministic PDF extraction, deterministic MHTML extraction, and student data isolation.
  - **Result**: 12/12 tests passing 100%.

## 3. Frontend UI & Styling (`frontend/app.py`, `frontend/.streamlit/config.toml`)
- **Color Theme**: Enforced Prussian Blue (`#002147`), Gold (`#FFA500`), and Charcoal text (`#0F172A`/`#334155`).
- **High-Contrast Styling**: Added explicit 1px borders on cards and dropdowns, high contrast schedule badges, and clear day-strip headers.
- **Hero Banner**: Added hero banner matching reference layout `thumbnail.jpeg`:
  - Kicker: `AUTONOMOUS AGENTS • CODE WITH GEMMA`
  - Title: `Project Ichika`
  - Subtitle: `Plans your week. Replans on the fly. Negotiates with your teammates — an autonomous agent running fully on-device, no cloud in sight.`
  - Feature badges: `Gemma 4 12B QAT`, `Fully on-device`, `Ichika Moderators`.
- **Clean UI**: Removed decorative AI buzzword lines (`Model Engine: Gemma 4`), removed emoji clutter (`🎓` icon), and removed gimmick persona tones (`unhinged`, `girly`, `manly`).

## 4. Test Output Verification
```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
collected 12 items

backend\tests\test_api.py ........                                      [ 66%]
backend\tests\test_extraction.py ....                                   [100%]

======================== 12 passed, 1 warning in 1.44s ========================
```
