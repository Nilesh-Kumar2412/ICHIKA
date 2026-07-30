"""
===============================================================================
PROJECT ICHIKA — CAMPUS COPILOT BACKEND API SERVER
===============================================================================

FastAPI REST Application serving autonomous agents for VIT Chennai students:
1. Academic Planner Agent (/plan)
2. Autonomous Schedule Replanner Agent (/replan)
3. Multi-Agent Group Study Coordinator (/negotiate)
4. VTOP Timetable Extraction Engine (/timetable/extract)
5. Campus Assistant Chat Endpoint (/chat)

Powered by Gemma 4 (12B QAT) via LM Studio Local Server / Groq Cloud API,
with 100% deterministic fallback engines guaranteeing zero-downtime offline operation.
===============================================================================
"""

import os
import json
import uuid
import time
import queue
import tempfile
import threading
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from openai import OpenAI
from gtts import gTTS
import pygame
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.planner import generate_plan
from agents.replanner import generate_replan
from agents.negotiator import run_negotiation
from extract_timetable import extract_input_text, parse_vtop_deterministic, extract_with_llm

load_dotenv()

# ─────────────────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────────────────
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_API_KEY  = os.getenv("LM_STUDIO_API_KEY",  "lm-studio")
LM_STUDIO_MODEL    = os.getenv("LM_STUDIO_MODEL",    "gemma-4-12b-qat")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY, timeout=2.0)
    MODEL_TO_USE = "gemma2-9b-it"
    PROVIDER_NAME = "Groq Cloud API (Gemma 2 9B)"
else:
    client = OpenAI(base_url=LM_STUDIO_BASE_URL, api_key=LM_STUDIO_API_KEY, timeout=2.0)
    MODEL_TO_USE = LM_STUDIO_MODEL
    PROVIDER_NAME = "LM Studio Local (Gemma 4 12B QAT)"

# ─────────────────────────────────────────────────────────
#  FASTAPI APP
# ─────────────────────────────────────────────────────────
app = FastAPI(title="Campus Copilot (ICHIKA) API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────
#  AUDIO (THREAD-SAFE SINGLE-CONSUMER QUEUE)
# ─────────────────────────────────────────────────────────
AUDIO_ENABLED = False
_audio_queue: queue.Queue = queue.Queue()

def _audio_worker():
    while True:
        text = _audio_queue.get()
        if text is None:
            break
        clean_text = "".join(c for c in text if c.isalpha() or c.isspace() or c in ".,!?")
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(tmp_fd)
        try:
            tts = gTTS(text=clean_text, lang="en", slow=False)
            tts.save(tmp_path)
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        _audio_queue.task_done()

try:
    pygame.mixer.init()
    AUDIO_ENABLED = True
    threading.Thread(target=_audio_worker, daemon=True).start()
except Exception as e:
    print(f"Pygame audio init skipped: {e}")

def speak(text: str):
    if AUDIO_ENABLED:
        _audio_queue.put(text)

# ─────────────────────────────────────────────────────────
#  SYSTEM PROMPTS & TONES
# ─────────────────────────────────────────────────────────
SYSTEM_PROMPT_BASE = """You are ICHIKA — an autonomous campus planning assistant for VIT Chennai students.
Your primary directive is Truth and Logic. You do not prioritise pleasing the user.
If the user is wrong, correct them. If a plan is illogical, point out the flaws clearly.
Communication Style: Firm, composed, steady, helpful. Never insulting.
Keep responses concise and actionable — you are a campus productivity tool, not a conversationalist."""

TONES = {
    "formal":   "Use sophisticated vocabulary. Maintain strict professional boundaries.",
    "casual":   "Use relaxed language. Keep the logic but make it feel like talking to a friend.",
    "concise":  "Use minimal words. Be extremely direct and clear.",
}

# ─────────────────────────────────────────────────────────
#  REQUEST MODELS
# ─────────────────────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    text: str
    tone: str = "formal"
    history: Optional[List[Message]] = []
    reg_no: Optional[str] = None
    student_id: Optional[str] = None

class PlanRequest(BaseModel):
    student_id: Optional[str] = None
    reg_no: Optional[str] = None

class ReplanRequest(BaseModel):
    student_id: Optional[str] = None
    reg_no: Optional[str] = None
    missed_items: Optional[List[str]] = None
    missed_item: Optional[Union[str, List[str]]] = None
    current_plan: Optional[List[Dict[str, Any]]] = None

class NegotiateRequest(BaseModel):
    student_id: Optional[str] = None
    participants: Optional[List[str]] = None
    teammates: Optional[List[str]] = None
    time_window: Optional[str] = None

class ExtractRequest(BaseModel):
    student_id: Optional[str] = None
    reg_no: Optional[str] = None
    file_path: Optional[str] = None

# ─────────────────────────────────────────────────────────
#  DATA LOADING — MULTI-STUDENT AWARE
# ─────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(__file__)
DATA_DIR  = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))

def student_data_dir(reg_no: Optional[str]) -> str:
    if reg_no:
        student_dir = os.path.join(DATA_DIR, "students", reg_no.upper().strip())
        if os.path.isdir(student_dir):
            return student_dir
    return DATA_DIR

def shared_data_dir() -> str:
    shared = os.path.join(DATA_DIR, "shared")
    return shared if os.path.isdir(shared) else DATA_DIR

def load_json(filepath: str) -> Union[dict, list]:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_student_file(filename: str, reg_no: Optional[str]):
    return load_json(os.path.join(student_data_dir(reg_no), filename))

def load_shared_file(filename: str):
    return load_json(os.path.join(shared_data_dir(), filename))

def list_registered_students() -> list[str]:
    students_dir = os.path.join(DATA_DIR, "students")
    if not os.path.isdir(students_dir):
        return ["26BEC1185", "26BLC1265"]
    st_list = [d for d in os.listdir(students_dir)
               if os.path.isdir(os.path.join(students_dir, d))]
    return sorted(list(set(st_list + ["26BEC1185", "26BLC1265"])))

def build_schedule_context(reg_no: Optional[str]) -> str:
    timetable = load_student_file("timetable.json", reg_no)
    deadlines = load_student_file("deadlines.json", reg_no)
    events    = load_shared_file("events.json")
    parts = []
    if timetable:
        parts.append(f"WEEKLY TIMETABLE:\n{json.dumps(timetable.get('schedule', {}), indent=2)}")
    if deadlines:
        parts.append(f"UPCOMING DEADLINES:\n{json.dumps(deadlines, indent=2)}")
    if events:
        parts.append(f"CAMPUS EVENTS:\n{json.dumps(events, indent=2)}")
    if parts:
        return "\n\n--- STUDENT DATA ---\n" + "\n\n".join(parts)
    return ""

# ─────────────────────────────────────────────────────────
#  UPLOAD HELPERS
# ─────────────────────────────────────────────────────────
ALLOWED_UPLOAD_FILES = {"timetable.json", "deadlines.json"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

def _save_student_file(reg_no: str, filename: str, content: bytes) -> str:
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    if filename not in ALLOWED_UPLOAD_FILES:
        raise HTTPException(status_code=400, detail=f"Allowed files: {ALLOWED_UPLOAD_FILES}")
    try:
        parsed = json.loads(content.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid JSON. Could not parse uploaded file.")

    out_dir = os.path.join(DATA_DIR, "students", reg_no.upper().strip())
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)
    return out_path

# ─────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "system":   "Campus Copilot (ICHIKA) Backend",
        "status":   "active",
        "provider": PROVIDER_NAME,
        "model":    MODEL_TO_USE,
        "audio":    AUDIO_ENABLED,
        "students": list_registered_students(),
    }

@app.get("/students")
async def get_students():
    """Returns list of registered active student IDs."""
    students = list_registered_students()
    return {"count": len(students), "students": students}

@app.get("/data")
async def get_all_data(reg_no: Optional[str] = None, student_id: Optional[str] = None):
    sid = student_id or reg_no or "26BEC1185"
    return {
        "reg_no":             sid,
        "timetable":          load_student_file("timetable.json", sid),
        "deadlines":          load_student_file("deadlines.json", sid),
        "events":             load_shared_file("events.json"),
        "mess_menu":          load_shared_file("mess_menu.json"),
        "teammate_calendars": load_shared_file("teammate_calendars.json"),
    }

# ─── UPLOAD ENDPOINTS ─────────────────────────────────────
@app.post("/upload/timetable")
async def upload_timetable(
    reg_no: str = Form(..., description="Student registration number"),
    file: UploadFile = File(..., description="Timetable file (PDF, MHTML, or JSON)")
):
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File size exceeds 5MB limit.")

    ext = os.path.splitext(file.filename or "")[1].lower()
    sid = reg_no.strip().upper()

    if ext in [".pdf", ".mht", ".mhtml"]:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext or ".pdf")
        os.write(tmp_fd, content)
        os.close(tmp_fd)

        try:
            if ext in [".mht", ".mhtml"]:
                from extract_timetable import extract_mhtml_text
                raw_text = extract_mhtml_text(tmp_path)
            else:
                from extract_timetable import extract_pdf_text
                raw_text = extract_pdf_text(tmp_path)

            structured = parse_vtop_deterministic(raw_text, student_id=sid)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        out_dir = os.path.join(DATA_DIR, "students", sid)
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "timetable.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(structured, f, indent=2, ensure_ascii=False)

    elif ext in [".json", ""]:
        path = _save_student_file(sid, "timetable.json", content)

    else:
        raise HTTPException(status_code=400, detail="Allowed timetable formats: .pdf, .mht, .mhtml, .json")

    return {
        "status":  "success",
        "reg_no":  sid,
        "saved":   path,
        "message": f"Timetable successfully parsed and saved for {sid}."
    }

@app.post("/upload/deadlines")
async def upload_deadlines(
    reg_no: str = Form(..., description="Student registration number"),
    file: UploadFile = File(..., description="deadlines.json file")
):
    content = await file.read()
    path = _save_student_file(reg_no, "deadlines.json", content)
    return {
        "status":  "success",
        "reg_no":  reg_no.upper(),
        "saved":   path,
        "message": f"Deadlines uploaded for {reg_no.upper()}."
    }

# ─── PLAN ENDPOINT (GET & POST) ───────────────────────────
def _resolve_student_id(
    query_sid: Optional[str] = None,
    query_reg: Optional[str] = None,
    body_sid: Optional[str] = None,
    body_reg: Optional[str] = None
) -> str:
    sid = query_sid or query_reg or body_sid or body_reg or "26BEC1185"
    return sid.strip().upper()

@app.get("/plan")
async def get_plan(student_id: Optional[str] = None, reg_no: Optional[str] = None):
    sid = _resolve_student_id(student_id, reg_no)
    
    # Validate student exists
    valid_students = list_registered_students()
    if sid not in valid_students:
        raise HTTPException(
            status_code=404,
            detail=f"Student {sid} not found. Available: {valid_students}"
        )
    
    timetable = load_student_file("timetable.json", sid)
    if not timetable:
        raise HTTPException(status_code=404, detail=f"No timetable found for student '{sid}'.")
    deadlines = load_student_file("deadlines.json", sid)
    events    = load_shared_file("events.json")
    mess_menu = load_shared_file("mess_menu.json")
    return generate_plan(client, MODEL_TO_USE, timetable, deadlines, events, mess_menu)

@app.post("/plan")
async def post_plan(req: Optional[PlanRequest] = None, student_id: Optional[str] = None, reg_no: Optional[str] = None):
    body_sid = req.student_id if req else None
    body_reg = req.reg_no if req else None
    sid = _resolve_student_id(student_id, reg_no, body_sid, body_reg)
    
    # Validate student exists
    valid_students = list_registered_students()
    if sid not in valid_students:
        raise HTTPException(
            status_code=404,
            detail=f"Student {sid} not found. Available: {valid_students}"
        )
    
    timetable = load_student_file("timetable.json", sid)
    if not timetable:
        raise HTTPException(status_code=404, detail=f"No timetable found for student '{sid}'.")
    deadlines = load_student_file("deadlines.json", sid)
    events    = load_shared_file("events.json")
    mess_menu = load_shared_file("mess_menu.json")
    return generate_plan(client, MODEL_TO_USE, timetable, deadlines, events, mess_menu)

# ─── REPLAN ENDPOINT (POST) ───────────────────────────────
@app.post("/replan")
async def run_replan(req: ReplanRequest):
    sid = req.student_id or req.reg_no or "26BEC1185"

    # Merge missed items
    missed_list = []
    if req.missed_items:
        missed_list.extend(req.missed_items)
    if req.missed_item:
        if isinstance(req.missed_item, list):
            missed_list.extend(req.missed_item)
        elif isinstance(req.missed_item, str):
            missed_list.append(req.missed_item)

    missed_list = [item.strip() for item in missed_list if item and item.strip()]
    if not missed_list:
        raise HTTPException(status_code=400, detail="Missing required field: 'missed_items' or 'missed_item'.")

    # Use current plan or generate initial plan for student
    current_plan = req.current_plan
    if not current_plan:
        timetable = load_student_file("timetable.json", sid)
        if not timetable:
            raise HTTPException(status_code=404, detail=f"No timetable found for student '{sid}'.")
        deadlines = load_student_file("deadlines.json", sid)
        events    = load_shared_file("events.json")
        mess_menu = load_shared_file("mess_menu.json")
        gen_res = generate_plan(client, MODEL_TO_USE, timetable, deadlines, events, mess_menu)
        current_plan = gen_res.get("plan", [])

    return generate_replan(client, MODEL_TO_USE, current_plan, missed_list)

# ─── NEGOTIATE ENDPOINT (POST) ────────────────────────────
NAME_MAP = {"Aarav": "26BLC1001", "Ananya": "26BLC1002", "Rohan": "26BLC1003"}

@app.post("/negotiate")
async def start_negotiation(req: NegotiateRequest):
    raw_participants = req.participants or req.teammates or ["26BLC1001", "26BLC1002", "26BLC1003"]
    participants = [NAME_MAP.get(p, p) for p in raw_participants]
    
    teammate_calendars = load_shared_file("teammate_calendars.json")
    filtered = {k: v for k, v in teammate_calendars.items() if k in participants}
    
    # If user explicitly provided participants but none matched, return error
    if not filtered and (req.participants or req.teammates):
        available = list(teammate_calendars.keys())
        raise HTTPException(
            status_code=400,
            detail=f"No matching teammates found. Requested: {participants}. Available: {available}"
        )
    
    return run_negotiation(client, MODEL_TO_USE, filtered or teammate_calendars, time_window=req.time_window)

# ─── TIMETABLE EXTRACT ENDPOINT (POST) ─────────────────────
@app.post("/timetable/extract")
async def extract_timetable_endpoint(
    request: Request,
    student_id: Optional[str] = Form(None),
    reg_no: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    sid = student_id or reg_no or "26BEC1185"
    file_path = None

    # Check if request is JSON body
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            body = await request.json()
            sid = body.get("student_id") or body.get("reg_no") or sid
            file_path = body.get("file_path")
        except Exception:
            pass

    if file:
        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File size exceeds 5MB limit.")
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1] or ".pdf")
        os.write(tmp_fd, content)
        os.close(tmp_fd)
        file_path = tmp_path

    if not file_path or not os.path.exists(file_path):
        # Default to Time_table.pdf if no file given
        file_path = os.path.join(DATA_DIR, "Time_table.pdf")

    # Path traversal validation
    real_target = os.path.realpath(file_path)
    real_data_dir = os.path.realpath(DATA_DIR)
    real_temp_dir = os.path.realpath(tempfile.gettempdir())

    is_in_data = os.path.commonpath([real_target, real_data_dir]) == real_data_dir
    is_in_temp = os.path.commonpath([real_target, real_temp_dir]) == real_temp_dir

    if not (is_in_data or is_in_temp):
        raise HTTPException(status_code=400, detail="Access denied: file_path must reside within DATA_DIR.")

    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".mht", ".mhtml"]:
        from extract_timetable import extract_mhtml_text
        raw_text = extract_mhtml_text(file_path)
    else:
        from extract_timetable import extract_pdf_text
        raw_text = extract_pdf_text(file_path)

    structured = parse_vtop_deterministic(raw_text, student_id=sid)

    out_dir = os.path.join(DATA_DIR, "students", sid.upper().strip())
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "timetable.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=2, ensure_ascii=False)

    return {
        "status": "success",
        "student_id": sid.upper(),
        "courses_found": len(structured.get("courses", [])),
        "saved_path": out_path,
        "timetable": structured
    }

def generate_smart_chat_fallback(query: str, sid: str, tone: str) -> str:
    q_lower = query.lower()
    timetable = load_student_file("timetable.json", sid) or {}
    deadlines = load_student_file("deadlines.json", sid) or []
    events = load_shared_file("events.json") or []

    if "email" in q_lower or "professor" in q_lower or "missed" in q_lower:
        return (
            f"**Subject**: Request regarding missed class — Student {sid}\n\n"
            f"Dear Professor,\n\n"
            f"I am writing to inform you that due to illness/unavoidable circumstances, "
            f"I was unable to attend the recent lab/lecture session for student registration {sid}.\n\n"
            f"I have caught up on the course syllabus topics and would be grateful if you could kindly guide me on any makeup requirements "
            f"or slot reallocations.\n\n"
            f"Thank you for your time and understanding.\n\n"
            f"Sincerely,\nStudent ID: {sid}"
        )
    elif "whatsapp" in q_lower or "teammate" in q_lower or "group" in q_lower:
        return (
            f"Hey team! 👋\n"
            f"Proposing a group study session for our project. "
            f"How does Wednesday 18:00 - 20:00 work for everyone? "
            f"Let me know your availability so we can finalize the slot!"
        )
    elif "agenda" in q_lower or "schedule" in q_lower or "today" in q_lower or "deadline" in q_lower or "mess" in q_lower:
        courses = timetable.get("courses", [])
        c_count = len(courses)
        d_count = len(deadlines)
        return (
            f"### 📋 Daily Agenda & Summary for {sid}\n\n"
            f"- **Enrolled Courses**: {c_count} active VTOP courses\n"
            f"- **Upcoming Deadlines**: {d_count} pending assignment deadlines\n"
            f"- **Mess Schedule**: Breakfast (07:30), Lunch (12:30), Snacks (16:30), Dinner (19:30)\n"
            f"- **Campus Events**: {len(events)} club events scheduled this week\n\n"
            f"*Check the Weekly Agenda tab for complete day-by-day item breakdowns.*"
        )
    else:
        return (
            f"Hello! I am ICHIKA, your campus copilot assistant for student **{sid}**.\n\n"
            f"I can assist you with:\n"
            f"1. 📅 **Schedule & Agenda**: Viewing your VTOP classes and mess menu\n"
            f"2. ⚡ **Autonomous Replanning**: Automatic catch-up slots for missed classes\n"
            f"3. 🤝 **Group Coordination**: Multi-agent negotiation for study sessions\n"
            f"4. ✉️ **Message Drafting**: Emails to faculty or messages to project teammates"
        )

# ─── CHAT ENDPOINT (POST) ──────────────────────────────────
@app.post("/chat")
async def chat(req: ChatRequest):
    if not req.text.strip():
        return {"error": "text must not be empty."}
    if len(req.text) > 2000:
        return {"error": "text exceeds 2000 character limit."}

    sid = req.student_id or req.reg_no or "26BEC1185"
    tone_instruction  = TONES.get(req.tone, TONES["formal"])
    schedule_context  = build_schedule_context(sid)
    system_content    = f"{SYSTEM_PROMPT_BASE}\n\n{tone_instruction}{schedule_context}"

    messages = [{"role": "system", "content": system_content}]
    for msg in (req.history or [])[-20:]:
        if msg.role in ("user", "assistant"):
            messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": req.text})

    try:
        response = client.chat.completions.create(
            model=MODEL_TO_USE,
            messages=messages,
            temperature=0.7,
            timeout=15.0,
        )
        ai_text = response.choices[0].message.content
        speak(ai_text)
        return {"response": ai_text, "source": "llm"}
    except Exception:
        fallback_msg = generate_smart_chat_fallback(req.text, sid, req.tone)
        return {"response": fallback_msg, "source": "fallback"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
