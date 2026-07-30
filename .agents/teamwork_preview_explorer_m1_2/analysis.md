# Campus Copilot (ICHIKA) Backend & Agent Architecture Analysis Report

## Executive Summary
This report provides a comprehensive analysis of the backend API (`backend/main.py`), agent modules (`backend/agents/planner.py`, `backend/agents/replanner.py`, `backend/agents/negotiator.py`), CLI timetable extraction (`extract_timetable.py`), test suite infrastructure, and compliance gaps against project requirements (R3, R4, R5).

---

## 1. Inspection of Backend Endpoints (`backend/main.py`)

### 1.1 Endpoint Audit & Interface Alignment

| Endpoint | HTTP Method Implemented | Interface Contract (PROJECT.md) | Request Payload Model | Status / Key Discrepancies |
|---|---|---|---|---|
| `/plan` | `GET /plan` (line 286) | `POST /plan` | Query param `reg_no: Optional[str]` | **Contract Mismatch**: Implemented as GET instead of POST. Uses `reg_no` query param instead of `student_id` JSON body payload. |
| `/replan` | `POST /replan` (line 293) | `POST /replan` | `ReplanRequest` (`current_plan: list`, `missed_item: str`) | **Contract Mismatch**: Requires `current_plan` in request body. Accepts single `missed_item` (str) instead of `student_id` and `missed_items` (list/plural). |
| `/negotiate` | `POST /negotiate` (line 299) | `POST /negotiate` | `NegotiateRequest` (`teammates: list = ["Aarav", "Ananya", "Rohan"]`) | **Contract Mismatch**: Accepts `teammates` instead of `participants`. Missing `student_id` and `time_window` parameters. |
| `/students` | `GET /students` (line 231) | `GET /students` | None | **Compliant**: Dynamically lists registered student directories (`["26BEC1185", "26BLC1265"]`). |
| `/timetable/extract` | **MISSING** | `POST /timetable/extract` | N/A | **Missing Endpoint**: Listed in `PROJECT.md` lines 4 & 15, but absent from `backend/main.py`. |

### 1.2 Multi-Student Data Isolation Logic (`backend/main.py`, Lines 140–181)
- Student directories are isolated under `data/students/<REG_NO>/` (supporting `26BEC1185` and `26BLC1265`).
- `student_data_dir(reg_no)` checks `data/students/<REG_NO>` first before falling back to `data/`.
- `shared_data_dir()` resolves `data/shared/` for shared assets (`events.json`, `mess_menu.json`, `teammate_calendars.json`).
- `list_registered_students()` inspects subdirectories in `data/students/`.

---

## 2. Smart Replanner Logic Analysis (`backend/agents/planner.py` & `replanner.py`)

### 2.1 Agenda Generation & Slot Merging (`planner.py`)
- **LLM System Prompt (`SYSTEM_PROMPT_PLANNER`)**: Instructs model to merge timetable classes, mess menu meals (Breakfast, Lunch, Snacks, Dinner), campus events, and assignment deadlines (with dedicated study prep slots).
- **Deterministic Fallback (`get_fallback_plan`)**:
  - Iterates over days `Monday` to `Friday`.
  - Merges Breakfast (`timings.breakfast`), Classes (`schedule[day]`), Lunch (`timings.lunch`), Snacks (`timings.snacks`), Campus Events (`events.json` matching day), Deadlines & Study (`deadlines.json` matching day with dedicated 18:00–19:30 prep slot), and Dinner (`timings.dinner`).

### 2.2 Visual Marking & Rescheduling (`replanner.py`)
- **Visual Marking of Missed Items**:
  - LLM System Prompt instructs setting `type: "missed"` for the missed item.
  - Fallback function (`get_fallback_replan`, lines 74–78) performs case-insensitive substring matching against `item['label']` (excluding `meal` and `missed` types), updates `item['type'] = 'missed'`, and prefixes `label` with `[MISSED]`.
- **Rescheduling Logic**:
  - LLM System Prompt instructs finding an available free slot later in the week without overlapping core classes or meals, creating a new item with `type: "replanned"`.
  - Fallback function (`get_fallback_replan`, lines 80–103) checks Thursday/Friday for an unoccupied `20:30 - 21:30` slot and appends:
    `{"time": "20:30 - 21:30", "type": "replanned", "label": "REPLANNED: Catch up on — <missed_item>", "priority": "High"}`.

### 2.3 Replanner Weaknesses & Vulnerabilities
1. **Single-Item Assumption**: `ReplanRequest` only passes a single string (`missed_item`). If a student misses multiple classes/labs in a day, replanning fails or requires sequential requests.
2. **Coarse Substring Matching**: Fallback matching `missed_lower in item.get("label", "").lower()` can match multiple unintended items if the query string is generic (e.g. `"lab"` or `"theory"`).
3. **Hardcoded Fallback Window**: Fallback slot selection is hardcoded to `20:30 - 21:30` without verifying actual class/meal free time gaps.

---

## 3. Multi-Agent Negotiator Logic Analysis (`backend/agents/negotiator.py`)

### 3.1 Teammate & Coordinator Architecture
- **Agents**: Aarav, Ananya, Rohan (loaded from `data/shared/teammate_calendars.json`).
- **Teammate Agent Prompt (`SYSTEM_PROMPT_TEAMMATE`)**: Evaluates a proposed time slot against free schedule slots and preferences. Returns `ACCEPT` or `PROPOSE` with an `alternative_slot`.
- **Coordinator Agent Prompt (`SYSTEM_PROMPT_COORDINATOR`)**: Evaluates responses from all teammates. If all accept, status set to `FINALIZED`. Otherwise selects the most common alternative slot and sets status to `REPROPOSING`.

### 3.2 Maximum 3 Rounds & Transaction Log
- **3-Round Restriction**: Enforced in loop (`for round_num in range(1, max_rounds + 1)` with `max_rounds = 3`). If consensus is reached before round 3, the loop breaks immediately. On round 3, the coordinator picks the best available candidate and finalizes.
- **Transaction Log Format**: Every step appends a structured record to `transcript`:
  - `proposal`: `{round, agent: "Coordinator", message, type: "proposal"}`
  - `teammate_response`: `{round, agent: "Teammate (Name)", message, decision: "ACCEPT|PROPOSE", type: "teammate_response"}`
  - `coordinator_decision`: `{round, agent: "Coordinator", message, type: "coordinator_decision"}`
  - `finalized`: `{round, agent: "Coordinator", message, type: "finalized"}`

### 3.3 Negotiator Weaknesses & Vulnerabilities
1. **Hardcoded Initial Proposal**: `current_proposed_slot = "Wednesday 18:00 - 20:00"` is hardcoded at line 47 of `negotiator.py`, ignoring user-specified `time_window` input.
2. **Primitive Substring Matching in Fallback**: `evaluate_teammate_fallback` uses `slot.get("day") in proposed_slot`, which can accept a slot even if the proposed time range conflicts with a teammate's busy hours on that day.
3. **Parameter Naming Mismatch**: `main.py` expects `teammates` list instead of `participants` and lacks `student_id` or `time_window` parameters in `NegotiateRequest`.

---

## 4. Test Infrastructure Inspection

### 4.1 Findings
- **Zero Test Files**: A comprehensive scan of the repository (`backend/` and project root) revealed **0 test files** (`test_*.py` or `*_test.py`).
- **Missing Dependencies**: `pytest` and `httpx` (required for FastAPI `TestClient`) are absent from `backend/requirements.txt`.

### 4.2 Impact
- Requirement R5 specifies verification of 100% backend test pass.
- Absence of unit and API integration tests creates high regression risk during M2–M4 implementations.

---

## 5. Identified Gaps Against Requirements (R3, R4, R5) & Concrete Fix Strategies

```
+-----------------------------------------------------------------------------------+
| Requirement | Gap Identified                                | Concrete Fix Strategy |
+-----------------------------------------------------------------------------------+
| R3: Backend | 1. /plan is GET instead of POST.               | Update main.py to     |
|     API     | 2. /replan uses current_plan & missed_item.   | support POST /plan    |
|             | 3. /negotiate lacks student_id & time_window.| and standard schema   |
|             | 4. /timetable/extract API is missing.          | for replan & negotiate.|
|             |                                                | Add /timetable/extract|
+-------------+------------------------------------------------+-----------------------+
| R3: Smart   | 1. Fallback replanner uses hardcoded slot.     | Implement dynamic gap |
|  Replanner  | 2. Substring matching is fragile.              | search algorithm &    |
|             | 3. Single-item limitation.                     | accept List[str] for  |
|             |                                                | missed_items.         |
+-------------+------------------------------------------------+-----------------------+
| R3: Multi-  | 1. Initial proposal hardcoded to Wednesday.    | Accept time_window    |
|   Agent     | 2. Fallback teammate check ignores time range. | parameter & parse     |
| Negotiator  | 3. Parameter names mismatch contract.          | exact day/time window |
|             |                                                | for overlap check.    |
+-------------+------------------------------------------------+-----------------------+
| R5: E2E &   | Zero test files exist in the codebase.         | Create pytest suite   |
| Testing     | pytest/httpx missing from requirements.txt.    | under tests/ covering |
|             |                                                | all endpoints/agents. |
+-----------------------------------------------------------------------------------+
```

---

## 6. Recommendations & Action Plan for Milestone 2/3

1. **API Schema Alignment**: Update `backend/main.py` models:
   - `POST /plan`: accept `student_id` (or `reg_no`) in JSON body.
   - `POST /replan`: accept `student_id`, `missed_items: Union[List[str], str]`, and optional `current_plan`.
   - `POST /negotiate`: accept `student_id`, `participants: List[str]`, `time_window: str`.
   - `POST /timetable/extract`: wrap `extract_timetable.py` parsing function into FastAPI endpoint.
2. **Agent Refinement**:
   - `negotiator.py`: accept `initial_slot` argument (from `time_window`).
   - `replanner.py`: support list of missed items and dynamic free-slot search.
3. **Establish Pytest Suite**:
   - Add `pytest` and `httpx` to `backend/requirements.txt`.
   - Create `tests/test_api.py`, `tests/test_planner.py`, `tests/test_replanner.py`, `tests/test_negotiator.py`, `tests/test_extractor.py`.
