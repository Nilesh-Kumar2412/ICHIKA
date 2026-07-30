import json
import re

SYSTEM_PROMPT_PLANNER = """You are Campus Copilot (ICHIKA), an autonomous planner for VIT Chennai students.
Given the student's timetable, assignment deadlines, campus events, and mess menu, produce a day-by-day weekly schedule for Monday to Friday.

RULES:
1. Return ONLY valid JSON in the specified schema. No markdown fences, no explanatory text.
2. Schema:
[
  {
    "day": "Monday",
    "items": [
      {
        "time": "08:00 - 09:40",
        "type": "class|meal|deadline|event|study|conflict",
        "label": "BAMAT101 (Lab) @ AB1-607B",
        "priority": "High|Medium|Low"
      }
    ]
  }
]
3. Include meals from the mess menu (Breakfast, Lunch, Snacks, Dinner).
4. Include all scheduled classes from the timetable.
5. Include assignment deadlines on their specified days with dedicated study/prep slots before the due time.
6. Include campus events without conflicting with core classes.
7. Flag any unresolvable timing overlap with type "conflict".
"""

def generate_plan(client, model, timetable, deadlines, events, mess_menu):
    user_prompt = f"""
TIMETABLE:
{json.dumps(timetable, indent=2)}

DEADLINES:
{json.dumps(deadlines, indent=2)}

CAMPUS EVENTS:
{json.dumps(events, indent=2)}

MESS MENU:
{json.dumps(mess_menu, indent=2)}

Generate the complete Monday to Friday agenda.
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_PLANNER},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            timeout=8.0
        )
        raw_text = response.choices[0].message.content
        # Robust fence stripping: handles ```json, ```JSON, ~~~json, etc.
        cleaned = re.sub(r"```[\w]*", "", raw_text).strip()
        cleaned = re.sub(r"```", "", cleaned).strip()
        parsed = json.loads(cleaned)
        return {"status": "success", "source": "llm", "plan": parsed}
    except json.JSONDecodeError as e:
        print(f"Planner JSON parse failed (LLM call succeeded): {e}. Using fallback.")
        return {"status": "fallback", "source": "cached", "plan": get_fallback_plan(timetable, deadlines, events, mess_menu)}
    except Exception as e:
        print(f"Planner LLM Call failed: {e}. Using deterministic fallback plan.")
        return {"status": "fallback", "source": "cached", "plan": get_fallback_plan(timetable, deadlines, events, mess_menu)}

def get_fallback_plan(timetable, deadlines, events, mess_menu):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    plan = []

    schedule = timetable.get("schedule", {})
    menu = mess_menu.get("menu", {})
    timings = mess_menu.get("timings", {})

    breakfast_time = timings.get("breakfast", "07:30 - 09:00")
    lunch_time     = timings.get("lunch",     "12:30 - 14:00")
    snacks_time    = timings.get("snacks",    "16:30 - 17:30")
    dinner_time    = timings.get("dinner",    "19:30 - 21:00")

    for day in days:
        day_items = []

        # Breakfast
        day_items.append({
            "time": breakfast_time,
            "type": "meal",
            "label": f"Breakfast: {menu.get(day, {}).get('breakfast', 'Mess Breakfast')}",
            "priority": "Low"
        })

        # Classes (already roughly time-sorted in JSON)
        for cls in schedule.get(day, []):
            day_items.append({
                "time": cls["time"],
                "type": "class",
                "label": f"{cls['course']} @ {cls['venue']}",
                "priority": "High"
            })

        # Lunch
        day_items.append({
            "time": lunch_time,
            "type": "meal",
            "label": f"Lunch: {menu.get(day, {}).get('lunch', 'Mess Lunch')}",
            "priority": "Low"
        })

        # Snacks (previously missing)
        day_items.append({
            "time": snacks_time,
            "type": "meal",
            "label": f"Snacks: {menu.get(day, {}).get('snacks', 'Mess Snacks')}",
            "priority": "Low"
        })

        # Events on this day
        for ev in events:
            if ev.get("day") == day:
                day_items.append({
                    "time": ev["time"],
                    "type": "event",
                    "label": f"Event: {ev['title']} @ {ev['venue']}",
                    "priority": "Medium"
                })

        # Deadlines on this day — use 18:00-19:30 study slot to avoid dinner overlap
        if not isinstance(deadlines, list):
            deadlines = []
        for dl in deadlines:
            if dl.get("due_day") == day:
                day_items.append({
                    "time": f"Before {dl['due_time']}",
                    "type": "deadline",
                    "label": f"DUE: {dl['title']} ({dl['course_code']})",
                    "priority": dl.get("priority", "High")
                })
                # Study prep at 18:00-19:30 (before dinner at 19:30, no overlap)
                day_items.append({
                    "time": "18:00 - 19:30",
                    "type": "study",
                    "label": f"Focus Session: Finalize {dl['title']}",
                    "priority": "High"
                })

        # Dinner
        day_items.append({
            "time": dinner_time,
            "type": "meal",
            "label": f"Dinner: {menu.get(day, {}).get('dinner', 'Mess Dinner')}",
            "priority": "Low"
        })

        plan.append({"day": day, "items": day_items})

    return plan
