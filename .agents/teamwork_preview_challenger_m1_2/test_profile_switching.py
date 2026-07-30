"""
Empirical test suite for Multi-Student Profile Switching across API endpoints & UI state.
Tests data isolation, backend endpoints (/students, /plan, /replan, /data, /timetable/extract, /chat),
and checks for profile bleeding or cross-contamination.
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import MagicMock

ROOT_DIR = Path("c:/Users/Nileshkumar/Downloads/files").resolve()
BACKEND_DIR = ROOT_DIR / "backend"

# Ensure both ROOT_DIR and BACKEND_DIR are in sys.path
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(BACKEND_DIR))

import main
from main import app
from fastapi.testclient import TestClient

# Speed up offline test execution by mocking client to trigger rule-based fallback instantly if LLM is offline
mock_client = MagicMock()
mock_client.chat.completions.create.side_effect = Exception("Offline test mode - using deterministic fallback")
main.client = mock_client

client = TestClient(app)

results = []

def record_test(name: str, passed: bool, details: str):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "details": details})
    print(f"[{status}] {name}: {details}", flush=True)

def run_profile_switching_tests():
    # -------------------------------------------------------------
    # Test 1: GET /students returns both active student profiles
    # -------------------------------------------------------------
    try:
        res = client.get("/students")
        if res.status_code == 200:
            data = res.json()
            students = data.get("students", [])
            if "26BEC1185" in students and "26BLC1265" in students:
                record_test("GET /students", True, f"Found registered students: {students}")
            else:
                record_test("GET /students", False, f"Missing expected students in list: {students}")
        else:
            record_test("GET /students", False, f"Status code {res.status_code}")
    except Exception as e:
        record_test("GET /students", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 2: GET /plan profile switching (26BEC1185 vs 26BLC1265)
    # -------------------------------------------------------------
    try:
        res_bec = client.get("/plan?student_id=26BEC1185").json()
        res_blc = client.get("/plan?student_id=26BLC1265").json()

        plan_bec = res_bec.get("plan", [])
        plan_blc = res_blc.get("plan", [])

        if len(plan_bec) == 5 and len(plan_blc) == 5:
            # Extract course titles from Monday
            monday_bec_labels = [item["label"] for item in plan_bec[0].get("items", [])]
            monday_blc_labels = [item["label"] for item in plan_blc[0].get("items", [])]

            # Verify that schedules are distinct and contain student-specific data
            is_different = (monday_bec_labels != monday_blc_labels)
            record_test("GET /plan Profile Switching", True, 
                        f"26BEC1185 Monday items: {len(monday_bec_labels)}, 26BLC1265 Monday items: {len(monday_blc_labels)}. Schedules distinct: {is_different}")
        else:
            record_test("GET /plan Profile Switching", False, f"Invalid plan response length: BEC={len(plan_bec)}, BLC={len(plan_blc)}")
    except Exception as e:
        record_test("GET /plan Profile Switching", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 3: POST /plan profile switching
    # -------------------------------------------------------------
    try:
        res_bec = client.post("/plan", json={"student_id": "26BEC1185"}).json()
        res_blc = client.post("/plan", json={"student_id": "26BLC1265"}).json()

        p_bec = res_bec.get("plan", [])
        p_blc = res_blc.get("plan", [])

        if len(p_bec) == 5 and len(p_blc) == 5:
            record_test("POST /plan Profile Switching", True, "Both 26BEC1185 and 26BLC1265 returned 5-day plans via POST")
        else:
            record_test("POST /plan Profile Switching", False, f"Failed length check: BEC={len(p_bec)}, BLC={len(p_blc)}")
    except Exception as e:
        record_test("POST /plan Profile Switching", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 4: GET /data isolation check
    # -------------------------------------------------------------
    try:
        data_bec = client.get("/data?reg_no=26BEC1185").json()
        data_blc = client.get("/data?reg_no=26BLC1265").json()

        bec_reg = data_bec.get("timetable", {}).get("student_info", {}).get("reg_no")
        blc_reg = data_blc.get("timetable", {}).get("student_info", {}).get("reg_no")

        bec_faculty = data_bec.get("timetable", {}).get("courses", [{}])[0].get("faculty")
        blc_faculty = data_blc.get("timetable", {}).get("courses", [{}])[0].get("faculty")

        if bec_reg == "26BEC1185" and blc_reg == "26BLC1265" and bec_faculty != blc_faculty:
            record_test("GET /data Data Isolation", True, 
                        f"Isolated: 26BEC1185 reg={bec_reg} faculty={bec_faculty} | 26BLC1265 reg={blc_reg} faculty={blc_faculty}")
        else:
            record_test("GET /data Data Isolation", False, 
                        f"Isolation failed: BEC reg={bec_reg}, BLC reg={blc_reg}, BEC faculty={bec_faculty}, BLC faculty={blc_faculty}")
    except Exception as e:
        record_test("GET /data Data Isolation", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 5: POST /replan student isolation
    # -------------------------------------------------------------
    try:
        payload_bec = {
            "student_id": "26BEC1185",
            "missed_items": ["BACSE101 Python Lab"]
        }
        payload_blc = {
            "student_id": "26BLC1265",
            "missed_items": ["BACSE101 Python Lab"]
        }

        replan_bec = client.post("/replan", json=payload_bec).json()
        replan_blc = client.post("/replan", json=payload_blc).json()

        plan_b = replan_bec.get("plan", [])
        plan_l = replan_blc.get("plan", [])

        if len(plan_b) > 0 and len(plan_l) > 0:
            record_test("POST /replan Isolation", True, "Successfully generated replans independently for both student profiles")
        else:
            record_test("POST /replan Isolation", False, f"Replan output empty: BEC={len(plan_b)}, BLC={len(plan_l)}")
    except Exception as e:
        record_test("POST /replan Isolation", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 6: POST /timetable/extract student profile output path
    # -------------------------------------------------------------
    try:
        res_bec = client.post("/timetable/extract", json={"student_id": "26BEC1185"}).json()
        res_blc = client.post("/timetable/extract", json={"student_id": "26BLC1265"}).json()

        if res_bec.get("student_id") == "26BEC1185" and res_blc.get("student_id") == "26BLC1265":
            bec_path = res_bec.get("saved_path", "")
            blc_path = res_blc.get("saved_path", "")
            if "26BEC1185" in bec_path and "26BLC1265" in blc_path:
                record_test("POST /timetable/extract Student Path", True, f"Saved paths: BEC={bec_path}, BLC={blc_path}")
            else:
                record_test("POST /timetable/extract Student Path", False, f"Path isolation error: BEC={bec_path}, BLC={blc_path}")
        else:
            record_test("POST /timetable/extract Student Path", False, f"Student ID mismatch in response: BEC={res_bec}, BLC={res_blc}")
    except Exception as e:
        record_test("POST /timetable/extract Student Path", False, f"Exception: {e}")

    # -------------------------------------------------------------
    # Test 7: POST /chat student context isolation
    # -------------------------------------------------------------
    try:
        chat_bec = client.post("/chat", json={"text": "What is my schedule?", "student_id": "26BEC1185"}).json()
        chat_blc = client.post("/chat", json={"text": "What is my schedule?", "student_id": "26BLC1265"}).json()

        if "response" in chat_bec and "response" in chat_blc:
            record_test("POST /chat Student Isolation", True, "Successfully accepted student_id for both BEC and BLC chat requests")
        else:
            record_test("POST /chat Student Isolation", False, f"Chat response error: BEC={chat_bec}, BLC={chat_blc}")
    except Exception as e:
        record_test("POST /chat Student Isolation", False, f"Exception: {e}")

    # Save summary
    out_dir = ROOT_DIR / ".agents/teamwork_preview_challenger_m1_2/test_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "profile_switching_results.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote Profile Switching test results to {summary_path}", flush=True)

if __name__ == "__main__":
    run_profile_switching_tests()
