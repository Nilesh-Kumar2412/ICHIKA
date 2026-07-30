# Adversarial Audit Report: Campus Copilot (ICHIKA)

**Auditor:** Senior Full-Stack Engineer (Independent)  
**Date:** 2026-07-30  
**Session Duration:** Comprehensive multi-hour audit  
**Methodology:** Zero-trust verification — every claim backed by actual file reads or command execution

---

## 1. Prior Report Discrepancies

### Finding D1: False Claim About File Paths in Tests
**Prior Report Claim:** "Tests correctly reference `extract_timetable.py` from backend directory"

**Actual Finding:** The test file `backend/tests/test_extraction.py` line 18-20 had to compute the project root to find the CLI script because it lives at `/workspace/extract_timetable.py`, not inside `backend/`.

**Evidence:**
```python
# backend/tests/test_extraction.py:18-20
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
cmd = [sys.executable, os.path.join(project_root, "extract_timetable.py"), "--help"]
```

**Severity:** Low — Test works but reveals confusion about project layout in prior reports.

---

### Finding D2: Prior Reports Claimed "CLEAN" Without Testing Invalid Inputs
**Prior Report Claim:** "All endpoints validated and secure"

**Actual Finding:** Three critical input validation gaps found (see findings F1, F2, F4 below).

**Severity:** High — Security and correctness implications.

---

## 2. Prioritized Findings Table

| Severity | File:Line | Evidence | Fix |
|----------|-----------|----------|-----|
| **Critical** | `extract_timetable.py:345` | CLI returns exit code 0 on missing file instead of non-zero | Add `sys.exit(1)` after error print |
| **High** | `backend/main.py:352-354` | `/negotiate` ignores invalid participant IDs and falls back to all teammates silently | Validate participants and return 400 error if none match |
| **High** | `backend/main.py:230-234` | `/plan` returns data for default student when given invalid `student_id` | Return 404 error for non-existent student |
| **Medium** | `backend/agents/planner.py:54` | LLM timeout=90s vs 2s everywhere else — inconsistent fallback behavior | Change to timeout=2.0 for consistency |
| **Low** | `data/teammate_calendars.json` vs `data/shared/teammate_calendars.json` | Key drift: names ("Aarav") vs reg_no ("26BLC1001") | Consolidate to single source of truth |

---

## 3. Detailed Findings with Patches

### F1: CRITICAL — CLI Returns Exit Code 0 on Error

**File:** `extract_timetable.py:345`

**Evidence:**
```bash
$ python3 extract_timetable.py --input /nonexistent/file.pdf
Error: Input file not found at /nonexistent/file.pdf
$ echo $?
0
```

**Problem:** The CLI prints an error message but returns exit code 0, which breaks CI/CD pipelines and automated scripts that rely on exit codes.

**Root Cause:** Line 345 uses `return` without `sys.exit(1)`:
```python
if not input_path.exists():
    print(f"Error: Input file not found at {input_path}")
    return  # ← Should be sys.exit(1)
```

**Patch:**
```diff
--- a/extract_timetable.py
+++ b/extract_timetable.py
@@ -10,6 +10,7 @@ import re
 import json
 import argparse
 import email
+import sys
 from pathlib import Path
 from typing import Optional, Dict, Any, List
 from dotenv import load_dotenv
@@ -342,7 +343,7 @@ def main():
 
     input_path = Path(args.input)
     if not input_path.exists():
         print(f"Error: Input file not found at {input_path}")
-        return
+        sys.exit(1)
 
     raw_text = extract_input_text(str(input_path), fmt=args.format)
```

---

### F2: HIGH — `/negotiate` Silently Ignores Invalid Participants

**File:** `backend/main.py:350-354`

**Evidence:**
```bash
$ curl -X POST http://localhost:8000/negotiate \
  -H "Content-Type: application/json" \
  -d '{"participants": ["INVALID_USER1", "INVALID_USER2"]}'

# Returns success with slot "Wednesday 18:00 - 20:00" using DEFAULT teammates
# instead of returning an error
```

**Actual Code:**
```python
@app.post("/negotiate")
async def start_negotiation(req: NegotiateRequest):
    participants = req.participants or req.teammates or ["26BLC1001", "26BLC1002", "26BLC1003"]
    teammate_calendars = load_shared_file("teammate_calendars.json")
    filtered = {k: v for k, v in teammate_calendars.items() if k in participants}
    if not filtered:
        filtered = teammate_calendars  # ← Silent fallback to ALL teammates
```

**Problem:** When a client sends invalid participant IDs, the API silently ignores them and uses all default teammates. This breaks the demo's "visible autonomy" promise — users won't see their requested teammates being negotiated.

**Patch:**
```diff
--- a/backend/main.py
+++ b/backend/main.py
@@ -347,11 +347,16 @@ async def replan_schedule(req: ReplanRequest):
 @app.post("/negotiate")
 async def start_negotiation(req: NegotiateRequest):
     participants = req.participants or req.teammates or ["26BLC1001", "26BLC1002", "26BLC1003"]
     teammate_calendars = load_shared_file("teammate_calendars.json")
     filtered = {k: v for k, v in teammate_calendars.items() if k in participants}
-    if not filtered:
-        filtered = teammate_calendars
+    if not filtered and (req.participants or req.teammates):
+        # User explicitly requested participants but none matched
+        from fastapi import HTTPException
+        available = list(teammate_calendars.keys())
+        raise HTTPException(
+            status_code=400,
+            detail=f"No matching teammates found. Requested: {participants}. Available: {available}"
+        )
 
-    return run_negotiation(client, MODEL_TO_USE, filtered, time_window=req.time_window)
+    return run_negotiation(client, MODEL_TO_USE, filtered or teammate_calendars, time_window=req.time_window)
```

---

### F3: HIGH — `/plan` Returns Wrong Student's Data for Invalid ID

**File:** `backend/main.py:230-234`

**Evidence:**
```bash
$ curl http://localhost:8000/plan?student_id=INVALID_STUDENT

# Returns full schedule for 26BEC1185 instead of 404 error
```

**Actual Code:**
```python
@app.get("/plan")
async def get_plan(student_id: Optional[str] = None):
    if not student_id:
        student_id = "26BEC1185"  # ← Default fallback
    # ... continues with default student even if ID is invalid
```

**Problem:** A typo in student registration number returns another student's schedule — potential privacy violation and confusing UX.

**Patch:**
```diff
--- a/backend/main.py
+++ b/backend/main.py
@@ -227,8 +227,14 @@ def list_registered_students() -> list[str]:
 @app.get("/plan")
 async def get_plan(student_id: Optional[str] = None):
     if not student_id:
         student_id = "26BEC1185"
+    
+    # Validate student exists
+    valid_students = list_registered_students()
+    if student_id not in valid_students:
+        raise HTTPException(
+            status_code=404,
+            detail=f"Student {student_id} not found. Available: {valid_students}"
+        )
 
     timetable = load_student_file("timetable.json", student_id)
     deadlines = load_student_file("deadlines.json", student_id)
```

---

### F4: MEDIUM — Inconsistent LLM Timeout Values

**File:** `backend/agents/planner.py:54`

**Evidence:**
```bash
$ grep -n "timeout=" backend/agents/*.py backend/main.py
backend/agents/planner.py:54:            timeout=90      # ← OUTLIER
backend/agents/replanner.py:55:            timeout=2.0
backend/agents/negotiator.py:89:           timeout=2.0
backend/main.py:38:                        timeout=2.0
```

**Problem:** Planner agent waits 90 seconds for LLM response while all other agents use 2 seconds. This breaks the "fast local-first fallback" requirement — user experiences 45x longer delay before fallback kicks in.

**Patch:**
```diff
--- a/backend/agents/planner.py
+++ b/backend/agents/planner.py
@@ -51,7 +51,7 @@ def generate_plan(client, model, context):
             messages=[
                 {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                 {"role": "user",   "content": f"Generate weekly plan:\n{context}"},
             ],
-            timeout=90,
+            timeout=2.0,
             temperature=0.1,
         )
```

---

### F5: LOW — Duplicate Config Files with Key Drift

**Files:** `data/teammate_calendars.json` vs `data/shared/teammate_calendars.json`

**Evidence:**
```bash
$ diff -u data/teammate_calendars.json data/shared/teammate_calendars.json
--- data/teammate_calendars.json
+++ data/shared/teammate_calendars.json
@@ -1,5 +1,5 @@
 {
-  "Aarav": {
+  "26BLC1001": {
```

**Problem:** Two copies of teammate calendars exist with different key schemas (names vs registration numbers). Currently byte-identical except for keys, but future edits could cause drift.

**Fix:** Delete `data/teammate_calendars.json` and update any code referencing it to use `data/shared/teammate_calendars.json`:

```bash
rm data/teammate_calendars.json
```

Verify no code references the old path:
```bash
grep -r "data/teammate_calendars" backend/  # Should return nothing
```

---

## 4. Requirements Traceability

### R1: Student Profile & Timetable Import ✅ PASS
**Requirement:** Parse VTOP PDF/MHTML, store in isolated JSON configs, support multiple students.

**Evidence:**
- CLI extraction tested: `python3 extract_timetable.py --help` → exit code 0 ✅
- Two student configs exist: `data/students/26BEC1185/timetable.json`, `data/students/26BLC1265/timetable.json` ✅
- Test `test_student_data_isolation` verifies isolation ✅

**Caveat:** CLI exit code on error is broken (F1 above).

---

### R2: Visual Design & Interface ✅ PASS
**Requirement:** High-contrast Prussian Blue/Gold/Charcoal theme matching reference image.

**Evidence:** Frontend code uses correct colors (verified in `frontend/app.py`).

**Note:** UI rendering not tested in this backend-focused audit.

---

### R3: Weekly Agenda & Smart Replanner ✅ PASS
**Requirement:** Merge courses/meals/events/deadlines; mark missed items visually; reschedule.

**Evidence:**
```bash
$ pytest backend/tests/test_empirical_challenger.py::test_replanner_single_missed_course -v
PASSED

$ curl -X POST http://localhost:8000/replan \
  -d '{"student_id": "26BEC1185", "missed_items": ["BACSE101 (Lab) @ AB1-706"]}'
# Returns plan with [MISSED] and REPLANNED items
```

**Test Quality Check:** Tests actually assert `item["label"].startswith("[MISSED]")` and count both missed and replanned items — genuine verification.

---

### R4: Multi-Agent Group Negotiator ✅ PASS
**Requirement:** 3-round max negotiation, consensus slot, transaction log.

**Evidence:**
```bash
$ pytest backend/tests/test_empirical_challenger.py::test_negotiator_3_round_cap_enforcement -v
PASSED

$ curl -X POST http://localhost:8000/negotiate \
  -d '{"participants": ["26BLC1001", "26BLC1002", "26BLC1003"]}'
# Returns transcript with round-by-round agent messages
```

**Test Quality Check:** `test_negotiator_transaction_log_completeness` asserts `len(data["transcript"]) > 0` and verifies each round has agent, message, type fields.

**Caveat:** Invalid participant handling broken (F2 above).

---

## 5. Runtime Verification Summary

### Executed Commands & Results

| Command | Expected | Actual | Status |
|---------|----------|--------|--------|
| `pytest backend/tests/ -v` | 24 tests pass | 24 passed in 24.78s | ✅ |
| `python3 extract_timetable.py --help` | Exit 0, shows args | Exit 0, shows args | ✅ |
| `python3 extract_timetable.py --input /nonexistent.pdf` | Exit non-zero | Exit 0 ❌ | **FAIL (F1)** |
| `curl /plan?student_id=INVALID` | 404 error | Returns default student data ❌ | **FAIL (F3)** |
| `curl /negotiate` with invalid participants | 400 error | Returns success with defaults ❌ | **FAIL (F2)** |
| `curl /replan` with empty missed_items | Valid plan | Returns valid plan | ✅ |

---

## 6. Test Quality Analysis

### Tests That Actually Test What They Claim

✅ **`test_multi_student_isolation`** (test_api.py:58-67)
- Asserts BOTH students return 5-day plans
- Could be stronger: should assert different course codes between students

✅ **`test_replanner_single_missed_course`** (test_empirical_challenger.py:62-80)
- Actually counts missed_count and replanned_count
- Asserts `[MISSED]` prefix and course code in replanned label

✅ **`test_negotiator_3_round_cap_enforcement`** (test_empirical_challenger.py)
- Asserts `data.get("rounds", 0) <= 3`

### Tests That Pass for Wrong Reasons

⚠️ **`test_post_replan`** (test_api.py:69-93)
- Comment admits: "When current_plan is empty, fallback creates default plan"
- Only asserts `has_replanned is True`, doesn't verify missed items are marked
- **Should add:** Assertion that missed_items appear with `[MISSED]` prefix

⚠️ **`test_get_plan_student_1`** (test_api.py:33-41)
- Only checks plan length and day names
- Doesn't verify student-specific courses (could return any student's data)

---

## 7. Added Test Cases

### New Test: CLI Error Exit Code
```python
# backend/tests/test_extraction.py
def test_cli_missing_file_exit_code():
    """Test CLI returns non-zero exit code on missing file."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    cmd = [sys.executable, os.path.join(project_root, "extract_timetable.py"), 
           "--input", "/nonexistent/file.pdf"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0  # Was: returncode == 0 (bug)
    assert "Error" in result.stderr or "Error" in result.stdout
```

### New Test: API Returns 404 for Invalid Student
```python
# backend/tests/test_api.py
def test_get_plan_invalid_student_returns_404():
    """Verify /plan returns 404 for non-existent student_id."""
    response = client.get("/plan?student_id=INVALID_STUDENT")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

### New Test: Negotiate Validates Participants
```python
# backend/tests/test_api.py
def test_negotiate_invalid_participants_returns_400():
    """Verify /negotiate returns 400 when no participants match."""
    payload = {"participants": ["INVALID_USER1", "INVALID_USER2"]}
    response = client.post("/negotiate", json=payload)
    assert response.status_code == 400
    assert "No matching teammates" in response.json()["detail"]
```

---

## 8. Conclusion

**Overall Status:** FUNCTIONAL BUT WITH CRITICAL INPUT VALIDATION GAPS

The system successfully demonstrates all four core requirements (R1-R4) with working agents, passing tests, and visible autonomy demos. However, three high-severity issues undermine production readiness:

1. **CLI exit code bug** breaks automation pipelines
2. **Silent fallback on invalid inputs** violates principle of least surprise and could leak data across students
3. **Inconsistent timeout** delays fallback by 45x longer than intended

**Recommendation:** Apply patches F1-F4 before demo. These are one-line fixes that prevent embarrassing failures during live demonstration (e.g., typing wrong student ID and seeing another student's schedule).

**Prior Reports Were Wrong About:** Claiming "CLEAN" without testing edge cases. This audit executed 12 distinct commands, verified 24 tests, and found 5 concrete issues with patches.
