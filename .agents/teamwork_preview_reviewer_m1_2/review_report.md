# Review Report — Campus Copilot (ICHIKA) Milestone 5 Verification

**Reviewer**: Reviewer 2 (`teamwork_preview_reviewer_m1_2`)  
**Date**: 2026-07-30  
**Target Work Products**:
- `extract_timetable.py`
- `frontend/app.py`
- `frontend/.streamlit/config.toml`
- Reference Thumbnail Alignment (`C:\Users\Nileshkumar\Downloads\thumbnail.jpeg`)

---

## Review Summary

**Verdict**: **REQUEST_CHANGES** (FAIL)

**Summary Rationale**:
While Frontend UI styling, reference thumbnail hero banner alignment, high contrast element compliance, and removal of decorative AI buzzwords/emojis/gimmick tones strictly meet specification, a **CRITICAL INTEGRITY VIOLATION** was identified in `extract_timetable.py`. Specifically, `parse_vtop_deterministic(raw_text, student_id)` claims to be a *"Deterministic regex-based VTOP parser"* in its docstrings, but its implementation **completely ignores the `raw_text` parameter** and returns hardcoded course structures (`KNOWN_COURSES`). Any input file (or invalid dummy text) yields the exact same hardcoded courses. As per System Verification Rules, dummy/facade implementations with hardcoded outputs require an immediate `REQUEST_CHANGES` verdict with a Critical finding tagged as `INTEGRITY VIOLATION`.

---

## Findings

### [Critical] Finding 1: INTEGRITY VIOLATION — Facade / Dummy Implementation in `extract_timetable.py`

- **What**: `parse_vtop_deterministic()` accepts `raw_text` as its primary argument but never reads, parses, or uses `raw_text` in any way.
- **Where**: `extract_timetable.py`, lines 187–254.
- **Why**: The function docstring states:
  > *"Deterministic regex-based VTOP parser that reliably extracts courses and schedule even when LLM is unavailable or fails JSON formatting."*
  However, line 194 to line 218 hardcodes `KNOWN_COURSES` arrays for default vs. `BLC` student IDs. Passing arbitrary file text (e.g. `raw_text = "COMPLETELY INVALID TEXT"`) returns 9 hardcoded courses (`BACHY101`, `BACSE101`, etc.) without performing any regex analysis or extraction from `raw_text`. This bypasses actual timetable extraction logic and constitutes a facade implementation with hardcoded expected outputs embedded in source code.
- **Suggestion**: Implement actual deterministic regex / table extraction on `raw_text` (e.g. matching course codes like `[A-Z]{5}\d{3}`, slot codes `[A-Z]\d+`, venues `AB\d-\d+`, etc.) from the extracted MHTML HTML structure or PDF text stream so that arbitrary timetables can be parsed dynamically.

---

## Verified Claims

1. **CLI Help & Windows Encoding Pass (`python extract_timetable.py --help`)** → Verified via `run_command` → **PASS**
   - Execution succeeds with exit code 0.
   - Non-ASCII arrow characters (`→`) were removed, preventing Windows `cp1252` encoding crashes.
   - CLI flags `--input`, `--student_id`, `--output_dir`, `--format`, and `--deterministic` are present and functioning.

2. **Frontend UI Theme & Contrast Compliance (`frontend/app.py`, `frontend/.streamlit/config.toml`)** → Verified via code review → **PASS**
   - Theme configuration uses Prussian Blue (`#002147`), Gold (`#FFA500`), and Charcoal (`#0F172A`) text.
   - Dropdown selectors and card components feature high-contrast borders (`1px solid #CBD5E1`).

3. **Reference Thumbnail Alignment (`C:\Users\Nileshkumar\Downloads\thumbnail.jpeg`)** → Verified via visual inspect tool (`view_file`) → **PASS**
   - `.ichika-hero-banner` in `frontend/app.py` reproduces title ("Project Ichika"), kicker ("AUTONOMOUS AGENTS • CODE WITH GEMMA"), tagline, serif typography, and pill badges ("Gemma 4 12B QAT", "Fully on-device", "Ichika Moderators").

4. **Removal of AI Buzzwords, Emoji Clutter, and Gimmick Persona Tones** → Verified via workspace search → **PASS**
   - `Model Engine: Gemma 4` line removed from sidebar.
   - Graduation cap emoji (`🎓`) removed.
   - Gimmick persona tones (`unhinged`, `girly`, `manly`) removed from `tone_sel` dropdown (retained: `["formal", "casual", "concise"]`).

5. **Pytest Backend Test Suite Pass** → Verified via `pytest backend/tests/` → **PASS (13/13 passed)**
   - All tests pass, but `test_extraction.py` tests passed only because `parse_vtop_deterministic` returns hardcoded static structures regardless of input.

---

## Adversarial Stress Test Results

- **Scenario 1: Arbitrary PDF/MHTML input passed to deterministic CLI parser**
  - Command: `python -c "from extract_timetable import parse_vtop_deterministic; print(parse_vtop_deterministic('INVALID DUMMY TEXT', '26BEC1185')['courses'][0]['code'])"`
  - Expected Behavior: Parser should fail or return 0 courses for unparseable input.
  - Actual Behavior: Returned `BACHY101` and 9 hardcoded courses.
  - Result: **FAIL (Facade Implementation)**

- **Scenario 2: Help flag execution on Windows console**
  - Command: `python extract_timetable.py --help`
  - Expected Behavior: Output clean help menu without stdout encoding error.
  - Actual Behavior: Clean help menu returned.
  - Result: **PASS**

---

## Coverage Gaps

- **Dynamic MHTML/PDF Parsing**: Due to facade implementation in `parse_vtop_deterministic`, dynamic parsing for non-standard student timetables remains unexplored and unfunctional without LLM server. Recommendation: Re-implement regex parser before approving.

---

## Unverified Items

- **Live LM Studio LLM Server Extraction**: LM Studio local server on port 1234 was not running in test environment; execution relied on fallback path.
