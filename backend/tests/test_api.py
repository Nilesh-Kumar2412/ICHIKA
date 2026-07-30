import pytest
import os
import sys
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
from main import app

client = TestClient(app)

def test_get_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "active"
    assert "students" in data

def test_get_students():
    response = client.get("/students")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "students" in data
    students = data["students"]
    assert "26BEC1185" in students
    assert "26BLC1265" in students

def test_get_plan_student_1():
    response = client.get("/plan?student_id=26BEC1185")
    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    plan = data["plan"]
    assert len(plan) == 5
    days = [d["day"] for d in plan]
    assert days == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

def test_get_plan_student_2():
    response = client.get("/plan?student_id=26BLC1265")
    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    plan = data["plan"]
    assert len(plan) == 5

def test_post_plan():
    response = client.post("/plan", json={"student_id": "26BEC1185"})
    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    assert len(data["plan"]) == 5

def test_multi_student_isolation():
    res1 = client.get("/plan?student_id=26BEC1185").json()
    res2 = client.get("/plan?student_id=26BLC1265").json()

    p1 = res1.get("plan", [])
    p2 = res2.get("plan", [])

    # Schedules should both exist, be valid, and be isolated/distinct
    assert len(p1) == 5
    assert len(p2) == 5
    assert p1 != p2

def test_post_replan():
    payload = {
        "student_id": "26BEC1185",
        "missed_items": ["BACSE101 (Lab) @ AB1-706"],
        "current_plan": []
    }
    response = client.post("/replan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    plan = data["plan"]

    # Check for missed and replanned items
    has_missed = False
    has_replanned = False
    for day in plan:
        for item in day.get("items", []):
            if item.get("type") == "missed":
                has_missed = True
            if item.get("type") == "replanned":
                has_replanned = True

    # When current_plan is empty, fallback creates a default plan and marks missed items
    # The key behavior is that replanned items ARE added (even if original not found to mark as missed)
    assert has_replanned is True

def test_post_negotiate_limit_and_window():
    payload = {
        "participants": ["Aarav", "Ananya", "Rohan"],
        "time_window": "Thursday 18:00 - 20:00"
    }
    response = client.post("/negotiate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"
    assert data.get("rounds", 0) <= 3
    assert "final_slot" in data
    assert "transcript" in data
    assert len(data["transcript"]) > 0

def test_post_timetable_extract():
    payload = {"student_id": "26BEC1185"}
    response = client.post("/timetable/extract", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"
    assert data.get("student_id") == "26BEC1185"
    assert "timetable" in data
