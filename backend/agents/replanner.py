import json
import re
import copy
from typing import List, Union, Dict, Any, Optional

SYSTEM_PROMPT_REPLANNER_TEMPLATE = """You are Campus Copilot (ICHIKA) Replanner Agent.
A student missed item(s) from their schedule: "{missed_items_str}".

YOUR DIRECTIVE:
1. Examine the current weekly schedule.
2. Mark the original missed item(s) with type "missed" so they are visually distinct.
3. Reschedule pending work into available free slots later in the week without overlapping core classes or meals.
4. Add the rescheduled item(s) with type "replanned".
5. Return ONLY valid JSON in the identical schema as the original plan:
[
  {{
    "day": "DayName",
    "items": [
      {{
        "time": "HH:MM - HH:MM",
        "type": "class|meal|deadline|event|study|conflict|missed|replanned",
        "label": "Description",
        "priority": "High|Medium|Low"
      }}
    ]
  }}
]
"""

def generate_replan(client, model, current_plan: List[Dict[str, Any]], missed_items: Union[str, List[str]]) -> Dict[str, Any]:
    if isinstance(missed_items, str):
        items_list = [missed_items]
    else:
        items_list = missed_items or []

    missed_items_str = ", ".join(items_list)
    system_prompt = SYSTEM_PROMPT_REPLANNER_TEMPLATE.format(missed_items_str=missed_items_str)

    user_prompt = f"""
MISSED ITEM(S) REPORTED: {missed_items_str}

CURRENT PLAN:
{json.dumps(current_plan, indent=2)}

Mark the original missed item(s) with type "missed" and add rescheduled copies as type "replanned".
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            timeout=2.0
        )
        raw_text = response.choices[0].message.content
        cleaned = re.sub(r"```[\w]*", "", raw_text).strip()
        cleaned = re.sub(r"```", "", cleaned).strip()
        parsed = json.loads(cleaned)
        return {"status": "success", "source": "llm", "plan": parsed, "missed_items": items_list}
    except Exception as e:
        print(f"Replanner LLM call failed or unavailable ({e}). Using deterministic fallback replanner.")
        return {"status": "fallback", "source": "cached", "plan": get_fallback_replan(current_plan, items_list), "missed_items": items_list}

def parse_time_range(time_str: str) -> Optional[tuple]:
    if not time_str or not isinstance(time_str, str):
        return None
    m = time_str.strip()
    if "-" in m:
        parts = m.split("-")
        try:
            h1, m1 = map(int, parts[0].strip().split(":"))
            h2, m2 = map(int, parts[1].strip().split(":"))
            return h1 * 60 + m1, h2 * 60 + m2
        except Exception:
            pass
    return None

def times_overlap(t1_str: str, t2_str: str) -> bool:
    if not t1_str or not t2_str:
        return False
    if t1_str.strip() == t2_str.strip():
        return True
    r1 = parse_time_range(t1_str)
    r2 = parse_time_range(t2_str)
    if r1 and r2:
        s1, e1 = r1
        s2, e2 = r2
        return max(s1, s2) < min(e1, e2)
    return False

def get_fallback_replan(current_plan: List[Dict[str, Any]], missed_items: Union[str, List[str]]) -> List[Dict[str, Any]]:
    if isinstance(missed_items, str):
        items_list = [missed_items]
    else:
        items_list = missed_items or []

    if not current_plan:
        default_label = items_list[0] if items_list else "BACSE101 Python Lab"
        current_plan = [
            {"day": "Monday", "items": [{"time": "09:00 - 10:40", "type": "class", "label": default_label, "priority": "High"}]},
            {"day": "Tuesday", "items": []},
            {"day": "Wednesday", "items": []},
            {"day": "Thursday", "items": []},
            {"day": "Friday", "items": []}
        ]

    if not items_list:
        return current_plan

    updated_plan = copy.deepcopy(current_plan)

    candidate_times = [
        "18:00 - 19:00",
        "19:00 - 20:00",
        "20:30 - 21:30",
        "21:30 - 22:30",
        "17:00 - 18:00",
        "16:00 - 17:00",
        "15:00 - 16:00",
        "14:00 - 15:00",
        "09:00 - 10:00",
        "10:00 - 11:00",
        "11:00 - 12:00"
    ]

    days_order = ["Wednesday", "Thursday", "Friday", "Monday", "Tuesday", "Saturday", "Sunday"]

    for item_name in items_list:
        if not item_name or not str(item_name).strip():
            continue
        missed_lower = str(item_name).lower().strip()
        rescheduled = False

        # Step 1: Mark original item as missed across current plan
        for day_obj in updated_plan:
            for item in day_obj.get("items", []):
                label_lower = item.get("label", "").lower()
                if missed_lower in label_lower and item.get("type") not in ("meal", "missed"):
                    item["type"] = "missed"
                    if not item["label"].startswith("[MISSED]"):
                        item["label"] = f"[MISSED] {item['label']}"

        # Step 2: Find free slot across ALL days (Monday-Sunday)
        for target_day in days_order:
            day_obj = next((d for d in updated_plan if d.get("day") == target_day), None)
            if day_obj is None:
                day_obj = {"day": target_day, "items": []}
                updated_plan.append(day_obj)

            existing_items = day_obj.get("items", [])

            for target_time in candidate_times:
                has_conflict = False
                for existing in existing_items:
                    if times_overlap(target_time, existing.get("time", "")):
                        has_conflict = True
                        break
                if not has_conflict:
                    existing_items.append({
                        "time": target_time,
                        "type": "replanned",
                        "label": f"REPLANNED: Catch up on — {item_name}",
                        "priority": "High"
                    })
                    rescheduled = True
                    break

            if rescheduled:
                break

    return updated_plan
