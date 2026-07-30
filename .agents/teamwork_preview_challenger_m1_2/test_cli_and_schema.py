"""
Empirical test suite for extract_timetable.py CLI and Schema Validation.
Executes CLI commands, tests argument variations, tests cp1252 codepage,
tests PDF and MHTML parsing, and validates JSON schema output.
"""

import sys
import os
import subprocess
import json
import shutil
from pathlib import Path

# Paths
ROOT_DIR = Path("c:/Users/Nileshkumar/Downloads/files").resolve()
CLI_SCRIPT = ROOT_DIR / "extract_timetable.py"
DATA_DIR = ROOT_DIR / "data"
PDF_FILE = DATA_DIR / "Time_table.pdf"
MHTML_FILE = DATA_DIR / "VIT Chennai - VTOP (1) (1).mht"
ALT_MHTML_FILE = DATA_DIR / "VIT Chennai - VTOP (1).mht"

OUTPUT_TEST_DIR = ROOT_DIR / ".agents/teamwork_preview_challenger_m1_2/test_output"

REQUIRED_STUDENT_INFO_KEYS = {"reg_no", "display_name", "branch", "semester", "total_credits"}
REQUIRED_COURSE_KEYS = {"code", "title", "type", "slot", "venue", "faculty", "credits"}
REQUIRED_SCHEDULE_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
REQUIRED_SCHEDULE_ITEM_KEYS = {"time", "type", "course", "slot", "venue"}

results = []

def record_test(name: str, passed: bool, details: str):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "details": details})
    print(f"[{status}] {name}: {details}", flush=True)

def validate_schema(data: dict) -> (bool, str):
    if not isinstance(data, dict):
        return False, "Root JSON is not an object"

    # Check top level keys
    for k in ["student_info", "courses", "schedule"]:
        if k not in data:
            return False, f"Missing top-level key: '{k}'"

    # Check student_info
    s_info = data["student_info"]
    if not isinstance(s_info, dict):
        return False, "student_info is not an object"
    missing_s = REQUIRED_STUDENT_INFO_KEYS - set(s_info.keys())
    if missing_s:
        return False, f"student_info missing keys: {missing_s}"
    if not isinstance(s_info["total_credits"], (int, float)):
        return False, f"student_info.total_credits is not numeric: {type(s_info['total_credits'])}"

    # Check courses
    courses = data["courses"]
    if not isinstance(courses, list):
        return False, "courses is not a list"
    for idx, c in enumerate(courses):
        if not isinstance(c, dict):
            return False, f"course[{idx}] is not an object"
        missing_c = REQUIRED_COURSE_KEYS - set(c.keys())
        if missing_c:
            return False, f"course[{idx}] missing keys: {missing_c}"
        if not isinstance(c["credits"], (int, float)):
            return False, f"course[{idx}].credits is not numeric: {type(c['credits'])}"

    # Check schedule
    sched = data["schedule"]
    if not isinstance(sched, dict):
        return False, "schedule is not an object"
    missing_days = REQUIRED_SCHEDULE_DAYS - set(sched.keys())
    if missing_days:
        return False, f"schedule missing days: {missing_days}"

    for day in REQUIRED_SCHEDULE_DAYS:
        day_items = sched[day]
        if not isinstance(day_items, list):
            return False, f"schedule['{day}'] is not a list"
        for idx, item in enumerate(day_items):
            if not isinstance(item, dict):
                return False, f"schedule['{day}'][{idx}] is not an object"
            missing_item = REQUIRED_SCHEDULE_ITEM_KEYS - set(item.keys())
            if missing_item:
                return False, f"schedule['{day}'][{idx}] missing keys: {missing_item}"

    return True, "Valid Schema"


def run_tests():
    if OUTPUT_TEST_DIR.exists():
        shutil.rmtree(OUTPUT_TEST_DIR)
    OUTPUT_TEST_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # Test 1: CLI --help on Windows cp1252 encoding console
    # -------------------------------------------------------------
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "cp1252"
        env["PYTHONUTF8"] = "0"
        cmd = [sys.executable, str(CLI_SCRIPT), "--help"]
        res = subprocess.run(cmd, capture_output=True, text=False, env=env, timeout=10)
        stdout_text = res.stdout.decode("cp1252", errors="strict")
        stderr_text = res.stderr.decode("cp1252", errors="strict")
        
        if res.returncode == 0 and "--input" in stdout_text:
            record_test("CLI Help CP1252", True, "Successfully ran --help under cp1252 without UnicodeEncodeError")
        else:
            record_test("CLI Help CP1252", False, f"Exit code {res.returncode}. Stderr: {stderr_text}")
    except Exception as e:
        record_test("CLI Help CP1252", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 2: PDF extraction with --deterministic and --student_id 26BEC1185
    # -------------------------------------------------------------
    try:
        out_file = OUTPUT_TEST_DIR / "pdf_26BEC1185.json"
        cmd = [
            sys.executable, str(CLI_SCRIPT),
            "--input", str(PDF_FILE),
            "--student_id", "26BEC1185",
            "--format", "pdf",
            "--output_dir", str(out_file),
            "--deterministic"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid, msg = validate_schema(data)
            if valid and data["student_info"]["reg_no"] == "26BEC1185":
                record_test("PDF Extraction (26BEC1185)", True, f"Schema Valid. Courses: {len(data['courses'])}")
            else:
                record_test("PDF Extraction (26BEC1185)", False, f"Schema validation failed: {msg}")
        else:
            record_test("PDF Extraction (26BEC1185)", False, f"CLI returncode {res.returncode}: {res.stderr}")
    except Exception as e:
        record_test("PDF Extraction (26BEC1185)", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 3: MHTML extraction with --deterministic and --student_id 26BLC1265
    # -------------------------------------------------------------
    try:
        out_file = OUTPUT_TEST_DIR / "mhtml_26BLC1265.json"
        cmd = [
            sys.executable, str(CLI_SCRIPT),
            "-i", str(MHTML_FILE),
            "--reg_no", "26BLC1265",
            "-f", "mhtml",
            "-o", str(out_file),
            "--deterministic"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid, msg = validate_schema(data)
            if valid and data["student_info"]["reg_no"] == "26BLC1265":
                record_test("MHTML Extraction (26BLC1265)", True, f"Schema Valid. Courses: {len(data['courses'])}")
            else:
                record_test("MHTML Extraction (26BLC1265)", False, f"Schema validation failed: {msg}")
        else:
            record_test("MHTML Extraction (26BLC1265)", False, f"CLI returncode {res.returncode}: {res.stderr}")
    except Exception as e:
        record_test("MHTML Extraction (26BLC1265)", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 4: Format = "auto" variation on MHTML file
    # -------------------------------------------------------------
    try:
        out_file = OUTPUT_TEST_DIR / "mhtml_auto.json"
        cmd = [
            sys.executable, str(CLI_SCRIPT),
            "--input", str(MHTML_FILE),
            "--student_id", "26BLC1265",
            "--format", "auto",
            "--out", str(out_file),
            "--deterministic"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid, msg = validate_schema(data)
            if valid:
                record_test("Format 'auto' MHTML", True, "Successfully auto-detected and extracted format mhtml")
            else:
                record_test("Format 'auto' MHTML", False, f"Schema validation failed: {msg}")
        else:
            record_test("Format 'auto' MHTML", False, f"CLI returncode {res.returncode}: {res.stderr}")
    except Exception as e:
        record_test("Format 'auto' MHTML", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 5: Output dir specified as directory path (not ending in .json)
    # -------------------------------------------------------------
    try:
        out_dir_path = OUTPUT_TEST_DIR / "dir_output"
        cmd = [
            sys.executable, str(CLI_SCRIPT),
            "--input", str(PDF_FILE),
            "--student_id", "26BEC1185",
            "--output_dir", str(out_dir_path),
            "--deterministic"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        expected_json = out_dir_path / "timetable.json"
        if res.returncode == 0 and expected_json.exists():
            with open(expected_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid, msg = validate_schema(data)
            if valid:
                record_test("Output Directory Target", True, f"Saved to {expected_json} and schema valid")
            else:
                record_test("Output Directory Target", False, f"Schema validation failed: {msg}")
        else:
            record_test("Output Directory Target", False, f"Expected file {expected_json} missing. Returncode {res.returncode}: {res.stderr}")
    except Exception as e:
        record_test("Output Directory Target", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 6: Default student_id path generation (no --output_dir flag)
    # -------------------------------------------------------------
    try:
        test_student = "26TEST9999"
        expected_path = DATA_DIR / "students" / test_student / "timetable.json"
        if expected_path.exists():
            os.remove(expected_path)

        cmd = [
            sys.executable, str(CLI_SCRIPT),
            "--input", str(PDF_FILE),
            "--student_id", test_student,
            "--deterministic"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and expected_path.exists():
            with open(expected_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid, msg = validate_schema(data)
            if valid and data["student_info"]["reg_no"] == test_student:
                record_test("Default Student Path", True, f"Correctly generated {expected_path}")
            else:
                record_test("Default Student Path", False, f"Schema or reg_no mismatch: {msg}")
            # cleanup
            shutil.rmtree(expected_path.parent)
        else:
            record_test("Default Student Path", False, f"File {expected_path} not created. Returncode {res.returncode}: {res.stderr}")
    except Exception as e:
        record_test("Default Student Path", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 7: Non-existent input file handling
    # -------------------------------------------------------------
    try:
        cmd = [
            sys.executable, str(CLI_SCRIPT),
            "--input", "non_existent_file.pdf"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if "Input file not found" in res.stdout or "Error" in res.stdout:
            record_test("Non-existent input error handling", True, "Gracefully reported missing input file")
        else:
            record_test("Non-existent input error handling", False, f"Unexpected output: stdout={res.stdout}, stderr={res.stderr}")
    except Exception as e:
        record_test("Non-existent input error handling", False, f"Exception: {e}")

    # Write summary
    summary_path = OUTPUT_TEST_DIR / "cli_test_results.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote CLI test results to {summary_path}", flush=True)

if __name__ == "__main__":
    run_tests()
