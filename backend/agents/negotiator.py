import json
import re
from typing import Dict, Any, List, Optional
from collections import Counter

SYSTEM_PROMPT_TEAMMATE = """You are an autonomous AI agent representing teammate '{teammate_name}'.
Your free schedule slots are: {free_slots}.
Your preferences: {preferences}.

A study slot proposal has been made: "{proposed_slot}".

Analyze if this proposed slot works with your free slots.
Respond ONLY with JSON:
{{
  "response": "ACCEPT|PROPOSE",
  "reason": "Brief explanation of why accept or alternative suggestion",
  "alternative_slot": "Day HH:MM - HH:MM (only if response is PROPOSE, else null)"
}}
"""

SYSTEM_PROMPT_COORDINATOR = """You are the Group Study Coordinator Agent.
You are evaluating responses from {num_teammates} teammates for proposed slot: "{proposed_slot}".

Round: {round_num} of 3.

Responses from teammates:
{responses_json}

Rules:
- If ALL teammates responded "ACCEPT", set status to "FINALIZED" with that slot.
- If any teammate responded "PROPOSE", find the most commonly proposed alternative slot among all responses.
  Set status to "REPROPOSING" and set final_slot to that most-common alternative.
- If there is a tie in proposed alternatives, pick the earliest one in the week (Mon before Tue etc).
- Respond ONLY with JSON:
{{
  "status": "FINALIZED|REPROPOSING",
  "final_slot": "Day HH:MM - HH:MM",
  "summary": "One sentence coordinator decision summary"
}}
"""

def run_negotiation(
    client,
    model,
    teammate_calendars: Dict[str, Any],
    target_duration: str = "2 Hours",
    time_window: Optional[str] = None
) -> Dict[str, Any]:
    transcript = []
    rounds_run = 0
    max_rounds = 3

    # Initial candidate slot from coordinator (use custom time_window if provided)
    current_proposed_slot = time_window or "Wednesday 18:00 - 20:00"
    final_agreed_slot = None

    teammate_names = list(teammate_calendars.keys())

    for round_num in range(1, max_rounds + 1):
        rounds_run = round_num
        transcript.append({
            "round": round_num,
            "agent": "Coordinator",
            "message": f"Proposing study slot: '{current_proposed_slot}' to {', '.join(teammate_names)}.",
            "type": "proposal"
        })

        round_responses = {}
        all_accepted = True

        # === TEAMMATE AGENT CALLS ===
        for name in teammate_names:
            cal = teammate_calendars[name]
            prompt = SYSTEM_PROMPT_TEAMMATE.format(
                teammate_name=name,
                free_slots=json.dumps(cal.get("free_slots", [])),
                preferences=cal.get("preferences", ""),
                proposed_slot=current_proposed_slot
            )

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": f"Evaluate the proposed study slot: {current_proposed_slot}"}
                    ],
                    temperature=0.2,
                    timeout=15.0
                )
                raw_text = response.choices[0].message.content
                cleaned = re.sub(r"```[\w]*", "", raw_text).strip()
                cleaned = re.sub(r"```", "", cleaned).strip()
                res = json.loads(cleaned)
            except Exception as e:
                res = evaluate_teammate_fallback(name, cal, current_proposed_slot)

            round_responses[name] = res

            if res.get("response") == "ACCEPT":
                msg = f"Accepted proposal '{current_proposed_slot}'. {res.get('reason', '')}"
            else:
                all_accepted = False
                alt = res.get("alternative_slot", "Thursday 18:00 - 20:00")
                msg = f"Cannot attend '{current_proposed_slot}'. Proposing alternative: {alt}. {res.get('reason', '')}"

            transcript.append({
                "round": round_num,
                "agent": f"Teammate ({name})",
                "message": msg,
                "decision": res.get("response"),
                "type": "teammate_response"
            })

        # === COORDINATOR CALL ===
        coordinator_prompt = SYSTEM_PROMPT_COORDINATOR.format(
            num_teammates=len(teammate_names),
            proposed_slot=current_proposed_slot,
            responses_json=json.dumps(round_responses, indent=2),
            round_num=round_num
        )

        try:
            coord_response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": coordinator_prompt},
                    {"role": "user", "content": f"Round {round_num}: Evaluate teammate responses and decide next action."}
                ],
                temperature=0.1,
                timeout=15.0
            )
            raw_coord = coord_response.choices[0].message.content
            cleaned_coord = re.sub(r"```[\w]*", "", raw_coord).strip()
            cleaned_coord = re.sub(r"```", "", cleaned_coord).strip()
            coord_decision = json.loads(cleaned_coord)
        except Exception:
            coord_decision = coordinator_fallback(round_responses, current_proposed_slot, all_accepted)

        coord_status = coord_decision.get("status", "REPROPOSING")
        coord_slot = coord_decision.get("final_slot", current_proposed_slot)
        coord_summary = coord_decision.get("summary", "")

        transcript.append({
            "round": round_num,
            "agent": "Coordinator",
            "message": f"[{coord_status}] {coord_summary} -> Slot: {coord_slot}",
            "type": "coordinator_decision"
        })

        if coord_status == "FINALIZED" or round_num == max_rounds:
            final_agreed_slot = coord_slot
            if round_num == max_rounds and coord_status != "FINALIZED":
                transcript.append({
                    "round": round_num,
                    "agent": "Coordinator",
                    "message": f"Maximum {max_rounds} rounds reached. Best available consensus slot selected: {final_agreed_slot}",
                    "type": "finalized"
                })
            else:
                transcript.append({
                    "round": round_num,
                    "agent": "Coordinator",
                    "message": f"Consensus reached on {final_agreed_slot}.",
                    "type": "finalized"
                })
            break
        else:
            current_proposed_slot = coord_slot
            transcript.append({
                "round": round_num,
                "agent": "Coordinator",
                "message": f"No full consensus in Round {round_num}. Re-proposing: '{current_proposed_slot}' in Round {round_num + 1}.",
                "type": "reproposal"
            })

    return {
        "status": "success",
        "rounds": rounds_run,
        "final_slot": final_agreed_slot,
        "transcript": transcript
    }

def coordinator_fallback(round_responses, current_proposed_slot, all_accepted):
    if all_accepted:
        return {
            "status": "FINALIZED",
            "final_slot": current_proposed_slot,
            "summary": "All teammates accepted the proposed slot."
        }

    alternatives = [
        res.get("alternative_slot")
        for res in round_responses.values()
        if res.get("response") == "PROPOSE" and res.get("alternative_slot")
    ]

    if alternatives:
        counter = Counter(alternatives)
        best_alt = counter.most_common(1)[0][0]
    else:
        best_alt = "Thursday 18:00 - 20:00"

    return {
        "status": "REPROPOSING",
        "final_slot": best_alt,
        "summary": f"Not all teammates accepted. Re-proposing most common alternative: {best_alt}."
    }

def parse_day_and_time(slot_str: str):
    if not slot_str or not isinstance(slot_str, str):
        return None, None, None
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    found_day = None
    for d in days:
        if d.lower() in slot_str.lower():
            found_day = d
            break

    time_match = re.search(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", slot_str)
    if time_match:
        h1, m1 = map(int, time_match.group(1).split(":"))
        h2, m2 = map(int, time_match.group(2).split(":"))
        start_min = h1 * 60 + m1
        end_min = h2 * 60 + m2
        return found_day, start_min, end_min
    return found_day, None, None

def evaluate_teammate_fallback(name, cal, proposed_slot):
    p_day, p_start, p_end = parse_day_and_time(proposed_slot)
    free_slots = cal.get("free_slots", [])

    for slot in free_slots:
        f_day = slot.get("day")
        f_time_str = slot.get("time", "")
        _, f_start, f_end = parse_day_and_time(f_time_str)

        if p_day and f_day and p_day.lower() == f_day.lower():
            if p_start is not None and p_end is not None and f_start is not None and f_end is not None:
                overlap = max(0, min(p_end, f_end) - max(p_start, f_start))
                if overlap >= 30:
                    return {
                        "response": "ACCEPT",
                        "reason": f"Proposed slot '{proposed_slot}' fits within free window ({f_time_str}) on {f_day}.",
                        "alternative_slot": None
                    }
            else:
                return {
                    "response": "ACCEPT",
                    "reason": f"Proposed slot '{proposed_slot}' matches free day {f_day}.",
                    "alternative_slot": None
                }

    if free_slots:
        alt = free_slots[0]
        alt_str = f"{alt.get('day')} {alt.get('time')}"
    else:
        alt_str = "Thursday 18:00 - 20:00"

    return {
        "response": "PROPOSE",
        "reason": f"Schedule conflict: proposed time slot '{proposed_slot}' is outside available free windows.",
        "alternative_slot": alt_str
    }
