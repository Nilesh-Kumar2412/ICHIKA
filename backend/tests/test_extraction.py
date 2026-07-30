import pytest
import os
import sys
import subprocess
import json
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
from extract_timetable import extract_input_text, parse_vtop_deterministic, extract_mhtml_text, extract_pdf_text

DATA_DIR = Path(__file__).parent.parent.parent / "data"

def test_cli_help_no_unicode_crash():
    """Test CLI help runs from project root (where extract_timetable.py lives)."""
    # The script is at /workspace/extract_timetable.py, not in backend/
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    cmd = [sys.executable, os.path.join(project_root, "extract_timetable.py"), "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "--input" in result.stdout
    assert "--student_id" in result.stdout

def test_pdf_extraction_deterministic():
    pdf_path = DATA_DIR / "Time_table.pdf"
    assert pdf_path.exists()

    raw_text = extract_pdf_text(str(pdf_path))
    assert len(raw_text) > 0

    parsed = parse_vtop_deterministic(raw_text, student_id="26BEC1185")
    assert "student_info" in parsed
    assert "courses" in parsed
    assert "schedule" in parsed
    assert len(parsed["courses"]) > 0
    assert len(parsed["schedule"]["Monday"]) > 0

def test_mhtml_extraction_deterministic():
    mhtml_path = DATA_DIR / "VIT Chennai - VTOP (1) (1).mht"
    assert mhtml_path.exists()

    raw_text = extract_mhtml_text(str(mhtml_path))
    assert len(raw_text) > 0
    assert "BACHY101" in raw_text or "BACSE101" in raw_text

    parsed = parse_vtop_deterministic(raw_text, student_id="26BLC1265")
    assert "student_info" in parsed
    assert "courses" in parsed
    assert "schedule" in parsed
    assert len(parsed["courses"]) > 0

def test_student_data_isolation():
    bec_path = DATA_DIR / "students" / "26BEC1185" / "timetable.json"
    blc_path = DATA_DIR / "students" / "26BLC1265" / "timetable.json"

    assert bec_path.exists()
    assert blc_path.exists()

    with open(bec_path, "r", encoding="utf-8") as f:
        bec_data = json.load(f)

    with open(blc_path, "r", encoding="utf-8") as f:
        blc_data = json.load(f)

    assert bec_data["student_info"]["reg_no"] == "26BEC1185"
    assert blc_data["student_info"]["reg_no"] == "26BLC1265"
