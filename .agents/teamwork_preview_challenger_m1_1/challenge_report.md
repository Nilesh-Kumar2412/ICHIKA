# Adversarial Challenge Report — Campus Copilot (ICHIKA) Milestone 5

**Evaluator**: Challenger 1 (`teamwork_preview_challenger_m1_1`)  
**Target Components**: `backend/agents/replanner.py` & `backend/agents/negotiator.py`  
**Test Suite**: `backend/tests/test_empirical_challenger.py`  
**Date**: 2026-07-30  

---

## Challenge Summary

**Overall Risk Assessment**: **HIGH**  
**Empirical Verdict**: **FAIL** (3 failed stress test scenarios out of 11 executed tests).

While basic functionalities (single-item replanning, 3-round cap enforcement, transaction logging, custom time window initialization, and standard consensus generation) passed successfully, empirical stress-testing uncovered critical edge-case failures in slot overlap management during replanning and flawed time matching logic in the negotiator fallback.

---

## Detailed Challenges & Vulnerabilities

### [HIGH] Challenge 1: Replanner Slot Overlap on Available Slot Exhaustion
- **Assumption Challenged**: Replanner schedules all missed items into free evening slots without creating overlapping time slots.
- **Attack Scenario**: Missing 5 or more courses in a single request (e.g. missing an entire day of 5 classes: MAT101, PHY101, CS101, ENG101, EEE101).
- **Empirical Result**: The fallback replanner has 4 pre-designated available evening slots. The 5th course exhausts `available_slots` and falls through to `updated_plan[-1]["items"].append({"time": "20:30 - 21:30", "type": "replanned", ...})`. Because Friday 20:30 - 21:30 was ALREADY assigned to missed course #2, Friday ends up with TWO separate items scheduled at `"20:30 - 21:30"`.
- **Blast Radius**: Student schedule corruption with overlapping replanned items on the last day of the week.
- **Suggested Defense**: Dynamically find unassigned evening time slots per day rather than relying on a static array, and check whether the fallback slot is already occupied before appending.

### [HIGH] Challenge 2: Replanner Slot Overlap on Pre-occupied Evening Slots
- **Assumption Challenged**: Replanner safely handles cases where designated evening slots are already occupied by existing user events.
- **Attack Scenario**: A student already has study sessions or classes scheduled at `Thursday 20:30 - 21:30`, `Friday 20:30 - 21:30`, `Friday 18:00 - 19:00`, and `Wednesday 20:30 - 21:30`. A missed course replan is requested.
- **Empirical Result**: All designated slots are skipped as occupied. The replanner falls through to `updated_plan[-1]["items"].append({"time": "20:30 - 21:30", ...})` without checking if `"20:30 - 21:30"` on Friday is already occupied by the pre-existing event, producing duplicate `"20:30 - 21:30"` entries.
- **Blast Radius**: Overlapping items scheduled directly over user's existing events.
- **Suggested Defense**: Maintain a pool of alternate time windows (e.g. 19:00 - 20:00, 21:30 - 22:30) or shift days dynamically if all evening slots are full.

### [MEDIUM] Challenge 3: Negotiator Teammate Fallback Ignores Proposed Time Range
- **Assumption Challenged**: Teammate agent fallback evaluates whether proposed slot time range actually falls within the teammate's free window.
- **Attack Scenario**: Coordinator proposes a slot at 3:00 AM on Wednesday (`"Wednesday 03:00 - 05:00"`).
- **Empirical Result**: `evaluate_teammate_fallback(name, cal, proposed_slot)` in `backend/agents/negotiator.py` checks `if slot.get("day") and slot.get("day") in proposed_slot: return {"response": "ACCEPT", ...}`. Because `"Wednesday"` is in `"Wednesday 03:00 - 05:00"`, it returns `ACCEPT` even though the teammate's free slot is `17:30 - 19:30`.
- **Blast Radius**: False consensus reached on invalid times (e.g., middle-of-the-night or conflicting hours) whenever the day name matches.
- **Suggested Defense**: Parse start and end times from `proposed_slot` and verify overlap with `slot["time"]` interval before returning `ACCEPT`.

---

## Stress Test Results Matrix

| # | Scenario / Test Case | Expected Behavior | Actual Behavior | Result |
|---|----------------------|-------------------|-----------------|--------|
| 1 | Single missed course replanning | Mark `[MISSED]`, append `replanned` slot | Marked `[MISSED]`, added replanned evening slot | **PASS** |
| 2 | Multiple missed courses (3 items) | Mark all 3 `[MISSED]`, add 3 distinct replanned slots | All 3 marked and rescheduled into distinct slots | **PASS** |
| 3 | Missing all 5 courses in a day | Mark all 5 `[MISSED]`, reschedule all 5 | All 5 marked `[MISSED]` and rescheduled | **PASS** |
| 4 | Slot overlap check for 5 missed items | Zero overlapping time slots on any day | Overlap detected: 2 items at Friday 20:30 - 21:30 | **FAIL** |
| 5 | Pre-occupied evening slots handling | No collision with existing events | Collision detected: Friday 20:30 - 21:30 duplicated | **FAIL** |
| 6 | Replanner empty inputs handling | Graceful fallback without crash | Returns empty plan or unchanged plan | **PASS** |
| 7 | Negotiator 3-round cap enforcement | Strictly <= 3 rounds under total conflict | Terminates at Round 3 with fallback selection | **PASS** |
| 8 | Transaction log completeness | Log all proposals, responses, decisions | Complete log with rounds, agents, decisions | **PASS** |
| 9 | Custom time window handling | Start Round 1 with custom `time_window` | Proposal 1 uses specified `time_window` | **PASS** |
| 10 | Consensus slot for Aarav, Ananya, Rohan | Generate valid consensus slot | Agreed slot: `Wednesday 18:00 - 20:00` | **PASS** |
| 11 | Negotiator time window boundary check | Reject mismatched time on matching day | Accepted 3:00 AM slot because day matched | **FAIL** |

---

## Unchallenged Areas

- **LLM API Live Completion**: Live OpenAI/Groq API calls were not tested live due to environment configuration (CODE_ONLY mode / offline local execution), but rule-based fallback paths were fully stress-tested.
- **Frontend Streamlit Interactivity**: Web UI state rendering was out of scope for backend agent logic testing.
