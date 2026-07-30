import pytest
import json
import os
import sys
from typing import List, Dict, Any

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from agents.replanner import get_fallback_replan, generate_replan
from agents.negotiator import run_negotiation, evaluate_teammate_fallback, coordinator_fallback

SAMPLE_PLAN = [
    {
        "day": "Monday",
        "items": [
            {"time": "08:00 - 08:50", "type": "class", "label": "MAT101 Discrete Mathematics", "priority": "High"},
            {"time": "09:00 - 09:50", "type": "class", "label": "PHY101 Physics Lecture", "priority": "High"},
            {"time": "10:00 - 10:50", "type": "class", "label": "CS101 Programming in C", "priority": "High"},
            {"time": "11:00 - 11:50", "type": "class", "label": "ENG101 Technical English", "priority": "Medium"},
            {"time": "12:00 - 13:00", "type": "meal", "label": "Lunch Break", "priority": "Low"},
            {"time": "14:00 - 14:50", "type": "class", "label": "EEE101 Electrical Eng", "priority": "Medium"}
        ]
    },
    {
        "day": "Tuesday",
        "items": [
            {"time": "08:00 - 08:50", "type": "class", "label": "CSE1002 Data Structures", "priority": "High"},
            {"time": "12:00 - 13:00", "type": "meal", "label": "Lunch Break", "priority": "Low"}
        ]
    },
    {
        "day": "Wednesday",
        "items": [
            {"time": "08:00 - 08:50", "type": "class", "label": "ECE1001 Digital Logic", "priority": "High"},
            {"time": "12:00 - 13:00", "type": "meal", "label": "Lunch Break", "priority": "Low"}
        ]
    },
    {
        "day": "Thursday",
        "items": [
            {"time": "08:00 - 08:50", "type": "class", "label": "HUM101 Ethics", "priority": "Low"},
            {"time": "12:00 - 13:00", "type": "meal", "label": "Lunch Break", "priority": "Low"}
        ]
    },
    {
        "day": "Friday",
        "items": [
            {"time": "08:00 - 08:50", "type": "class", "label": "CHY101 Chemistry Lab", "priority": "Medium"},
            {"time": "12:00 - 13:00", "type": "meal", "label": "Lunch Break", "priority": "Low"}
        ]
    }
]

# --- SMART REPLANNER STRESS TESTS ---

def test_replanner_single_missed_course():
    """Verify single missed course marking and rescheduling."""
    missed = ["MAT101 Discrete Mathematics"]
    replanned = get_fallback_replan(SAMPLE_PLAN, missed)
    
    missed_count = 0
    replanned_count = 0
    for day in replanned:
        for item in day["items"]:
            if item.get("type") == "missed":
                missed_count += 1
                assert item["label"].startswith("[MISSED]")
            elif item.get("type") == "replanned":
                replanned_count += 1
                assert "MAT101" in item["label"]
                
    assert missed_count == 1
    assert replanned_count == 1

def test_replanner_multiple_missed_courses():
    """Verify handling of multiple missed courses in a single request."""
    missed = ["MAT101 Discrete Mathematics", "PHY101 Physics Lecture", "CS101 Programming in C"]
    replanned = get_fallback_replan(SAMPLE_PLAN, missed)
    
    missed_labels = []
    replanned_labels = []
    for day in replanned:
        for item in day["items"]:
            if item.get("type") == "missed":
                missed_labels.append(item["label"])
            elif item.get("type") == "replanned":
                replanned_labels.append(item["label"])
                
    assert len(missed_labels) == 3
    assert len(replanned_labels) == 3

def test_replanner_missing_all_courses_in_a_day():
    """Verify missing all 5 courses in a single day (Monday)."""
    monday_courses = ["MAT101 Discrete Mathematics", "PHY101 Physics Lecture", "CS101 Programming in C", "ENG101 Technical English", "EEE101 Electrical Eng"]
    replanned = get_fallback_replan(SAMPLE_PLAN, monday_courses)
    
    missed_count = 0
    replanned_count = 0
    for day in replanned:
        for item in day["items"]:
            if item.get("type") == "missed":
                missed_count += 1
            elif item.get("type") == "replanned":
                replanned_count += 1
                
    assert missed_count == 5
    assert replanned_count == 5

def test_replanner_slot_overlap_check():
    """Stress test: Check for time slot overlap when rescheduling multiple courses."""
    monday_courses = ["MAT101 Discrete Mathematics", "PHY101 Physics Lecture", "CS101 Programming in C", "ENG101 Technical English", "EEE101 Electrical Eng"]
    replanned = get_fallback_replan(SAMPLE_PLAN, monday_courses)
    
    overlaps = []
    for day_obj in replanned:
        day_name = day_obj["day"]
        times_seen = set()
        for item in day_obj["items"]:
            t = item["time"]
            if t in times_seen:
                overlaps.append((day_name, t, item["label"]))
            times_seen.add(t)
            
    print("Detected Overlaps:", overlaps)
    # Highlight failure mode for report
    if len(overlaps) > 0:
        pytest.fail(f"CRITICAL FAIL: Slot overlap detected in replanned schedule: {overlaps}")

def test_replanner_preoccupied_evening_slots():
    """Stress test: When evening slots are already occupied in current_plan."""
    preoccupied_plan = json.loads(json.dumps(SAMPLE_PLAN))
    for day_obj in preoccupied_plan:
        if day_obj["day"] == "Thursday":
            day_obj["items"].append({"time": "20:30 - 21:30", "type": "study", "label": "Existing Study"})
        elif day_obj["day"] == "Friday":
            day_obj["items"].append({"time": "20:30 - 21:30", "type": "study", "label": "Existing Study 1"})
            day_obj["items"].append({"time": "18:00 - 19:00", "type": "study", "label": "Existing Study 2"})
        elif day_obj["day"] == "Wednesday":
            day_obj["items"].append({"time": "20:30 - 21:30", "type": "study", "label": "Existing Study 3"})

    missed = ["MAT101 Discrete Mathematics"]
    replanned = get_fallback_replan(preoccupied_plan, missed)
    
    friday_times = [i["time"] for i in replanned[-1]["items"]]
    print("Friday times with pre-occupied slots:", friday_times)
    if friday_times.count("20:30 - 21:30") > 1:
        pytest.fail(f"CRITICAL FAIL: Duplicate 20:30 - 21:30 slot placed on Friday despite slot being occupied!")

def test_replanner_empty_inputs():
    """Boundary test: Empty missed items list and empty current plan."""
    # When current_plan is empty but missed_items provided, 
    # the function creates a default plan structure with the missed item
    res_empty_plan = get_fallback_replan([], ["MAT101"])
    # Should NOT be empty - it should contain a default plan with the missed item marked
    assert len(res_empty_plan) == 5  # Returns 5-day default plan
    has_missed = any(item.get("type") == "missed" for day in res_empty_plan for item in day.get("items", []))
    assert has_missed is True  # The missed item should be marked

    res_empty_missed = get_fallback_replan(SAMPLE_PLAN, [])
    assert res_empty_missed == SAMPLE_PLAN

# --- MULTI-AGENT NEGOTIATOR STRESS TESTS ---

def test_negotiator_3_round_cap_enforcement():
    """Stress test: Ensure negotiation strictly caps at 3 rounds even with complete conflict."""
    conflicting_calendars = {
        "Aarav": {"free_slots": [{"day": "Monday", "time": "08:00 - 10:00"}], "preferences": "Mornings only"},
        "Ananya": {"free_slots": [{"day": "Tuesday", "time": "14:00 - 16:00"}], "preferences": "Afternoons only"},
        "Rohan": {"free_slots": [{"day": "Friday", "time": "18:00 - 20:00"}], "preferences": "Evenings only"}
    }
    
    res = run_negotiation(client=None, model=None, teammate_calendars=conflicting_calendars, time_window="Sunday 10:00 - 12:00")
    
    assert res["status"] == "success"
    assert res["rounds"] <= 3
    assert res["final_slot"] is not None
    
    rounds_in_transcript = [t["round"] for t in res["transcript"]]
    assert max(rounds_in_transcript) <= 3

def test_negotiator_transaction_log_completeness():
    """Verify transaction log completeness (proposal, teammate_response, coordinator_decision, finalized)."""
    calendars = {
        "Aarav": {"free_slots": [{"day": "Wednesday", "time": "17:30 - 19:30"}], "preferences": ""},
        "Ananya": {"free_slots": [{"day": "Wednesday", "time": "17:30 - 19:30"}], "preferences": ""},
        "Rohan": {"free_slots": [{"day": "Wednesday", "time": "17:30 - 19:30"}], "preferences": ""}
    }
    
    res = run_negotiation(client=None, model=None, teammate_calendars=calendars, time_window="Wednesday 17:30 - 19:30")
    transcript = res["transcript"]
    
    types = [t["type"] for t in transcript]
    assert "proposal" in types
    assert "teammate_response" in types
    assert "coordinator_decision" in types
    assert "finalized" in types
    
    for entry in transcript:
        if entry["type"] == "teammate_response":
            assert "round" in entry
            assert "agent" in entry
            assert "message" in entry
            assert "decision" in entry

def test_negotiator_custom_time_window_handling():
    """Verify custom time_window parameter is honored in initial proposal."""
    calendars = {
        "Aarav": {"free_slots": [{"day": "Friday", "time": "16:00 - 18:00"}], "preferences": ""},
        "Ananya": {"free_slots": [{"day": "Friday", "time": "16:00 - 18:00"}], "preferences": ""}
    }
    
    custom_window = "Friday 16:00 - 18:00"
    res = run_negotiation(client=None, model=None, teammate_calendars=calendars, time_window=custom_window)
    
    first_proposal = res["transcript"][0]
    assert first_proposal["type"] == "proposal"
    assert custom_window in first_proposal["message"]

def test_negotiator_teammate_consensus_aarav_ananya_rohan():
    """Verify consensus slot generation for Aarav, Ananya, and Rohan using actual shared json."""
    calendar_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "shared", "teammate_calendars.json")
    with open(calendar_path, "r") as f:
        calendars = json.load(f)
        
    res = run_negotiation(client=None, model=None, teammate_calendars=calendars)
    
    assert res["status"] == "success"
    assert res["rounds"] <= 3
    assert res["final_slot"] is not None
    print(f"Final Agreed Slot for Aarav, Ananya, Rohan: {res['final_slot']}")

def test_negotiator_time_matching_flaw():
    """Stress test: Check whether teammate fallback incorrectly accepts mismatched time on matching day."""
    cal = {"free_slots": [{"day": "Wednesday", "time": "17:30 - 19:30"}], "preferences": ""}
    
    eval_res = evaluate_teammate_fallback("Aarav", cal, "Wednesday 03:00 - 05:00")
    
    print("Evaluation result for Wednesday 03:00 - 05:00:", eval_res)
    if eval_res["response"] == "ACCEPT":
        pytest.fail("HIGH RISK BUG: Teammate fallback accepts proposed slot at 3:00 AM because day matches, ignoring time window!")
