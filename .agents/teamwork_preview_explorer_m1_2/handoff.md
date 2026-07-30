# Handoff Report — Explorer 2 (Backend & Agents Exploration)

## 1. Observation

### 1.1 File Locations & Direct Observations
- **`backend/main.py`**:
  - Line 286: `@app.get("/plan") async def create_plan(reg_no: Optional[str] = None)`
  - Line 293: `@app.post("/replan") async def run_replan(req: ReplanRequest)` where `ReplanRequest` (lines 127–129) is:
    ```python
    class ReplanRequest(BaseModel):
        current_plan: list
        missed_item: str
    ```
  - Line 299: `@app.post("/negotiate") async def start_negotiation(req: NegotiateRequest)` where `NegotiateRequest` (lines 131–132) is:
    ```python
    class NegotiateRequest(BaseModel):
        teammates: list = ["Aarav", "Ananya", "Rohan"]
    ```
  - Lines 231–235: `@app.get("/students") async def get_students()` correctly scans `data/students/` directory.
  - Endpoint `/timetable/extract` is **completely absent** from `backend/main.py`.
- **`backend/agents/planner.py`**:
  - Lines 4–28: `SYSTEM_PROMPT_PLANNER` defines JSON schema for Monday–Friday agenda, merging classes, meals (breakfast, lunch, snacks, dinner), deadlines, and events.
  - Lines 69–155: `get_fallback_plan()` constructs a deterministic agenda merging schedule, mess menu, events, and deadlines.
- **`backend/agents/replanner.py`**:
  - Lines 6–28: `SYSTEM_PROMPT_REPLANNER_TEMPLATE` defines replanning schema, visually marking missed items as `type: "missed"` and rescheduled items as `type: "replanned"`.
  - Lines 74–78: `get_fallback_replan()` marks missed items:
    ```python
    if missed_lower in item.get("label", "").lower() and item.get("type") not in ("meal", "missed"):
        item["type"] = "missed"
        item["label"] = f"[MISSED] {item['label']}"
    ```
  - Lines 80–103: Reschedules into Thursday/Friday 20:30–21:30 free slot with `type: "replanned"`.
- **`backend/agents/negotiator.py`**:
  - Line 43: `max_rounds = 3` enforces 3-round cap.
  - Line 47: `current_proposed_slot = "Wednesday 18:00 - 20:00"` hardcodes the starting proposal.
  - Lines 54–155: Loop executes up to 3 rounds, appending structured log objects (`proposal`, `teammate_response`, `coordinator_decision`, `finalized`) to `transcript`.
- **`PROJECT.md` Interface Contracts**:
  - Line 27: `POST /plan`: Takes `student_id`, returns merged weekly agenda JSON.
  - Line 28: `POST /replan`: Takes `student_id`, `missed_items`, returns updated weekly agenda with visual flags and rescheduled tasks.
  - Line 29: `POST /negotiate`: Takes `student_id`, `participants`, `time_window`, returns consensus slot & max 3 round transaction log.
  - Line 4 & 15: Specifies backend API serving `/plan`, `/replan`, `/negotiate`, `/students`, `/timetable/extract`.
- **Test Infrastructure**:
  - File search across workspace (`Pattern: "*test*"`) returned 0 results. No test files (`test_*.py`) exist in `backend/` or root directory.
  - `backend/requirements.txt` contains 7 dependencies (`fastapi`, `uvicorn`, `pydantic`, `openai`, `gTTS`, `pygame-ce`, `python-dotenv`), missing `pytest` and `httpx`.

---

## 2. Logic Chain

1. **Endpoint Contract Divergence**:
   - Observation: `backend/main.py:286` defines `GET /plan`, `main.py:127-132` defines `ReplanRequest` (`current_plan`, `missed_item`) and `NegotiateRequest` (`teammates`), and `/timetable/extract` is missing.
   - Deduction: The current FastAPI endpoint definitions do not align with `PROJECT.md` lines 27–29 interface contracts (`POST /plan` with `student_id`, `POST /replan` with `student_id`/`missed_items`, `POST /negotiate` with `student_id`/`participants`/`time_window`, and `POST /timetable/extract`).
2. **Replanner & Negotiator Agent Behavior**:
   - Observation: `replanner.py:74-78` uses case-insensitive substring matching against a single string `missed_item` and reschedules into a fixed fallback slot (`20:30 - 21:30`). `negotiator.py:47` hardcodes starting proposal `"Wednesday 18:00 - 20:00"`.
   - Deduction: Replanner cannot process multiple missed items concurrently and relies on naive fallback window placement. Negotiator ignores caller-provided `time_window` parameters.
3. **Test Coverage Gap**:
   - Observation: Zero test files exist in the repository, and `pytest` is absent from `backend/requirements.txt`.
   - Deduction: Milestone 1 baseline lacks test infrastructure needed to verify R3/R5 requirements automatically. Test suite must be authored before M3/M5 execution.

---

## 3. Caveats

- **LM Studio Local LLM Execution**: Analysis focused on backend Python code and agent fallback/prompt structures. Actual live LLM behavior depends on LM Studio server availability (`http://localhost:1234/v1`) or Groq fallback API key.
- **Frontend Integration**: Explorer 3 analyzed `frontend/app.py`. Frontend calls `GET /plan?reg_no=...`, `POST /replan`, and `POST /negotiate` matching current `main.py` definitions. Backend API updates must preserve backward compatibility or be synchronized with frontend model calls.

---

## 4. Conclusion

The backend codebase (`backend/main.py`) and agent modules (`backend/agents/`) provide a functional foundation for multi-student schedule merging, visual replanning, and multi-agent negotiation. However, four critical gaps must be resolved:
1. Endpoint contracts (`/plan`, `/replan`, `/negotiate`) must be updated to accept `student_id`, `missed_items`, `participants`, and `time_window`, and `/timetable/extract` must be added.
2. Replanner agent must support multiple missed items and dynamic free slot discovery.
3. Negotiator agent must accept `time_window` as dynamic initial proposal.
4. A complete `pytest` test suite (`tests/`) must be created to satisfy Requirement R5.

---

## 5. Verification Method

### 5.1 Codebase Inspection Verification
- Inspect `backend/main.py` lines 220–306 to verify route definitions.
- Inspect `backend/agents/planner.py`, `backend/agents/replanner.py`, and `backend/agents/negotiator.py` to trace prompt construction and fallback execution.

### 5.2 Test Execution (Once Pytest Suite is Created)
- Install test dependencies: `pip install pytest httpx`
- Run test suite: `pytest` or `python -m pytest backend/`
- Invalidation condition: Any failing test case or endpoint 404/422 status code when posting valid JSON payload contract.
