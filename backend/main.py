"""
===============================================================================
PROJECT ICHIKA — CAMPUS COPILOT BACKEND API SERVER
===============================================================================

FastAPI REST Application serving autonomous AI agents for university students:
1. Academic Planner Agent (/plan)
2. Autonomous Schedule Replanner Agent (/replan)
3. Multi-Agent Group Study Coordinator (/negotiate)
4. VTOP Timetable Extraction Engine (/timetable/extract)
5. All-Purpose AI Assistant Chat (/chat) with JARVIS voice mode

Powered by Gemma via Google AI Studio (cloud) / Groq / LM Studio (local),
with 100% deterministic fallback engines guaranteeing zero-downtime operation.
Supports: VIT Chennai, VIT Vellore, VIT Bhopal, VIT AP, and any university.
===============================================================================
"""

import os
import re
import json
import time
import queue
import tempfile
import threading
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from openai import OpenAI
from dotenv import load_dotenv

# Optional TTS dependencies (not available on cloud deployment)
try:
    from gtts import gTTS
    import pygame
    _TTS_AVAILABLE = True
except ImportError:
    _TTS_AVAILABLE = False

import sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.planner import generate_plan
from agents.replanner import generate_replan
from agents.negotiator import run_negotiation
from extract_timetable import parse_vtop_deterministic

backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
load_dotenv(os.path.join(root_dir, ".env"))
load_dotenv(os.path.join(backend_dir, ".env"))
load_dotenv()

# ─────────────────────────────────────────────────────────
#  CONFIGURATION — 3-tier LLM Provider Fallback
#  Priority: Google AI Studio (Gemini API) > Groq > LM Studio Local
# ─────────────────────────────────────────────────────────
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_API_KEY  = os.getenv("LM_STUDIO_API_KEY",  "lm-studio")
LM_STUDIO_MODEL    = os.getenv("LM_STUDIO_MODEL",    "gemma-4-12b-qat")

if GEMINI_API_KEY and GEMINI_API_KEY not in ("", "your_gemini_api_key_here"):
    # ─── Tier 1: Google AI Studio (free Gemma via OpenAI-compatible endpoint) ───
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=GEMINI_API_KEY,
        timeout=45.0,
    )
    MODEL_TO_USE = "gemini-3.5-flash"
    PROVIDER_NAME = "Google AI Studio (Gemini 3.5 Flash)"
elif GROQ_API_KEY and GROQ_API_KEY not in ("", "your_groq_api_key_here"):
    # ─── Tier 2: Groq Cloud (fast inference) ───
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY, timeout=30.0)
    MODEL_TO_USE = "gemma2-9b-it"
    PROVIDER_NAME = "Groq Cloud API (Gemma 2 9B)"
else:
    # ─── Tier 3: LM Studio Local (requires laptop running) ───
    client = OpenAI(base_url=LM_STUDIO_BASE_URL, api_key=LM_STUDIO_API_KEY, timeout=30.0)
    MODEL_TO_USE = LM_STUDIO_MODEL
    PROVIDER_NAME = f"LM Studio Local ({LM_STUDIO_MODEL})"

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

if _TTS_AVAILABLE:
    try:
        pygame.mixer.init()
        AUDIO_ENABLED = True
        threading.Thread(target=_audio_worker, daemon=True).start()
    except Exception as e:
        print(f"Pygame audio init skipped (normal on cloud): {e}")
else:
    print("TTS dependencies not installed — voice handled client-side via JARVIS mode.")

def speak(text: str):
    if AUDIO_ENABLED:
        _audio_queue.put(text)

# ─────────────────────────────────────────────────────────
#  CHAT SYSTEM PROMPT & PERSONA CONFIGURATION
# ─────────────────────────────────────────────────────────
SYSTEM_PROMPT_BASE = """You are ICHIKA — a highly capable, general-purpose AI assistant powered by Gemma.

You are intelligent, knowledgeable, and helpful across ALL domains — science, math, programming, history, literature, philosophy, creative writing, career advice, exam preparation, general knowledge, reasoning puzzles, and more. You think step-by-step when solving complex problems.

CAMPUS CONTEXT (use when relevant, ignore when not):
You also serve as an autonomous campus copilot for university students (primarily VIT Chennai, but also VIT Vellore, VIT Bhopal, VIT AP, and other institutions). When the user asks about schedules, timetables, deadlines, mess menus, campus events, group study coordination, or email/message drafting — use the student context data provided below to give precise, personalized answers.

CORE PRINCIPLES:
1. Answer ONLY what the user asks. Do not give unsolicited intros, bio dumps, or feature bullet lists.
2. For simple greetings (e.g. "hi", "hii", "hello", "hey"), reply with a brief, natural 1-sentence greeting (e.g. "Hey there! How can I help you today?").
3. For math/science/coding problems: show step-by-step reasoning and clear explanations.
4. For creative tasks: write stories, poems, essays, or brainstorm ideas naturally.
5. For coding: write clean, well-commented code in any language.
6. For campus-specific queries: use the student's timetable, deadlines, and events data.
7. Be honest. If you don't know something, say so. Never fabricate facts.
8. Use markdown formatting (headers, bold, code blocks) for readability.
9. Keep responses natural, direct, and conversational."""

TONES = {
    "formal":   "Respond with professional, sophisticated language. Use proper structure and academic tone.",
    "casual":   "Respond like a friendly, smart peer. Keep the depth but make it conversational and approachable.",
    "concise":  "Be extremely direct and brief. Minimum words, maximum clarity. Skip pleasantries.",
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

class CodeCompareRequest(BaseModel):
    code_a: str
    code_b: str
    language: Optional[str] = "python"
    problem_title: Optional[str] = "Algorithm Optimization Benchmark"

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
    # Try student-specific dir first, then shared, then root data dir
    student_path = os.path.join(student_data_dir(reg_no), filename)
    if os.path.exists(student_path):
        return load_json(student_path)
    shared_path = os.path.join(shared_data_dir(), filename)
    if os.path.exists(shared_path):
        return load_json(shared_path)
    root_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(root_path):
        return load_json(root_path)
    return {}

def load_shared_file(filename: str, default=None):
    result = load_json(os.path.join(shared_data_dir(), filename))
    if not result and default is not None:
        return default
    return result

def list_registered_students() -> list[str]:
    students_dir = os.path.join(DATA_DIR, "students")
    if not os.path.isdir(students_dir):
        return ["26BEC1185", "26BLC1265", "26BLC1001", "26BLC1002", "26BLC1003"]
    st_list = [d for d in os.listdir(students_dir)
               if os.path.isdir(os.path.join(students_dir, d))]
    return sorted(list(set(st_list))) if st_list else ["26BEC1185", "26BLC1265", "26BLC1001", "26BLC1002", "26BLC1003"]

def build_schedule_context(reg_no: Optional[str]) -> str:
    timetable = load_student_file("timetable.json", reg_no)
    deadlines = load_student_file("deadlines.json", reg_no)
    events    = load_shared_file("events.json", default=[])
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
    clean_reg = re.sub(r'[^A-Z0-9]', '', reg_no.upper().strip())
    if not clean_reg:
        clean_reg = "26BEC1185"
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    if filename not in ALLOWED_UPLOAD_FILES:
        raise HTTPException(status_code=400, detail=f"Allowed files: {ALLOWED_UPLOAD_FILES}")
    try:
        parsed = json.loads(content.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid JSON. Could not parse uploaded file.")

    out_dir = os.path.join(DATA_DIR, "students", clean_reg)
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

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return {"status": "healthy", "provider": PROVIDER_NAME, "model": MODEL_TO_USE}

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
        "events":             load_shared_file("events.json", default=[]),
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
    events    = load_shared_file("events.json", default=[])
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
    events    = load_shared_file("events.json", default=[])
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
        events    = load_shared_file("events.json", default=[])
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
    
    # If no matching participants found in calendar (regardless of whether they were
    # explicitly specified or came from the default fallback list), return 400.
    if not filtered:
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
    events = load_shared_file("events.json", default=[])

    # --- Campus-specific fallbacks ---
    if "email" in q_lower or "professor" in q_lower or ("missed" in q_lower and ("class" in q_lower or "lab" in q_lower)):
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
    elif "whatsapp" in q_lower or ("teammate" in q_lower and "message" in q_lower):
        return (
            f"Hey team! 👋\n"
            f"Proposing a group study session for our project. "
            f"How does Wednesday 18:00 - 20:00 work for everyone? "
            f"Let me know your availability so we can finalize the slot!"
        )
    elif any(k in q_lower for k in ["agenda", "schedule", "timetable", "deadline", "mess", "class today"]):
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

    # --- General-purpose fallback: attempt to give a useful answer ---
    # Math & calculations
    if any(k in q_lower for k in ["calculate", "solve", "integral", "derivative", "equation", "math", "formula"]):
        return (
            "I'd love to help with this math problem! However, I'm currently running in **offline fallback mode** "
            "(the Gemma LLM server is unreachable right now). Once the LM Studio server is back online, "
            "I'll be able to solve equations, integrals, derivatives, and more step-by-step.\n\n"
            "**Tip**: Make sure LM Studio is running on `http://localhost:1234/v1` with the Gemma 4 model loaded."
        )

    # Coding
    if any(k in q_lower for k in ["code", "program", "function", "algorithm", "python", "java", "debug", "error", "bug"]):
        return (
            "I can write and debug code in Python, Java, C++, JavaScript, and more! "
            "However, I'm currently in **offline fallback mode** (the Gemma LLM is unreachable). "
            "Once the LM Studio server is back online, I'll generate clean, commented code for you.\n\n"
            "**Tip**: Make sure LM Studio is running on `http://localhost:1234/v1` with the Gemma 4 model loaded."
        )

    # General knowledge / explain
    if any(k in q_lower for k in ["explain", "what is", "who is", "how does", "why", "define", "tell me about", "history"]):
        return (
            "Great question! I'm a general-purpose AI and can explain concepts across science, history, philosophy, "
            "technology, and more. However, I'm currently in **offline fallback mode** (the Gemma LLM is unreachable). "
            "Once the LM Studio server is back online, I'll give you a thorough, well-structured explanation.\n\n"
            "**Tip**: Make sure LM Studio is running on `http://localhost:1234/v1` with the Gemma 4 model loaded."
        )

    # Creative writing
    if any(k in q_lower for k in ["write", "story", "poem", "essay", "creative", "letter", "blog"]):
        return (
            "I'd be happy to write that for you! Here is a starting outline:\n\n"
            "1. **Introduction**: Introduce the core theme and setting.\n"
            "2. **Body**: Develop key arguments or narrative progression.\n"
            "3. **Conclusion**: Summarize insights and final thoughts.\n\n"
            "*(If you want a full customized text, ask me again and I will generate it instantly!)*"
        )

    # Simple Greetings
    if any(q_lower == g or q_lower.startswith(g + " ") for g in ["hi", "hii", "hiii", "hello", "hey", "heyy", "greetings", "good morning", "good evening"]):
        return "Hey there! I am ICHIKA, your Campus Copilot. How can I help you today?"

    # Default: brief helpful response
    return f"I'm processing your request. Please ask your question again or try a quick prompt!"


def call_gemini_native_failover(prompt: str, system_prompt: str = "", history: list = None):
    if not GEMINI_API_KEY or GEMINI_API_KEY in ("", "your_gemini_api_key_here"):
        raise ValueError("GEMINI_API_KEY not configured")

    models = ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash", "gemma-4-26b-a4b-it"]
    contents = []
    if history:
        for m in history:
            role = "user" if (getattr(m, "role", "") == "user" or (isinstance(m, dict) and m.get("role") == "user")) else "model"
            text = getattr(m, "content", "") if hasattr(m, "content") else (m.get("content", "") if isinstance(m, dict) else "")
            if text:
                contents.append({"role": role, "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {"contents": contents}
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    encoded_data = json.dumps(payload).encode("utf-8")

    import urllib.request
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        req = urllib.request.Request(url, data=encoded_data, headers={"Content-Type": "application/json"})
        try:
            res = urllib.request.urlopen(req, timeout=12.0)
            data = json.loads(res.read().decode("utf-8"))
            txt = data["candidates"][0]["content"]["parts"][0]["text"]
            return txt.strip(), model
        except Exception as e:
            print(f"[GEMINI NATIVE FAILOVER] Model '{model}' failed: {e}. Trying next...")
            continue

    raise TimeoutError("All Gemini native models exhausted")


# ─── CHAT ENDPOINT (POST) ──────────────────────────────────
@app.post("/chat")
async def chat(req: ChatRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty.")
    if len(req.text) > 2000:
        raise HTTPException(status_code=400, detail="text exceeds 2000 character limit.")

    sid = req.student_id or req.reg_no or "26BEC1185"
    tone_instruction = TONES.get(req.tone, TONES["formal"])
    
    # Selective context: only attach heavy schedule context if query is campus-related
    q_lower = req.text.lower()
    campus_keywords = ["schedule", "timetable", "class", "deadline", "mess", "menu", "today", "agenda", "event", "professor", "vtop", "lab", "assignment", "exam", "course"]
    schedule_context = build_schedule_context(sid) if any(k in q_lower for k in campus_keywords) else ""
    
    system_content = f"{SYSTEM_PROMPT_BASE}\n\n{tone_instruction}{schedule_context}"

    # Tier 1: Try Native Gemini REST Failover Chain (sub-second fast)
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        ai_text, used_model = await asyncio.wait_for(
            loop.run_in_executor(None, call_gemini_native_failover, req.text, system_content, req.history),
            timeout=15.0
        )
        clean_ai_text = re.sub(r'<thought>.*?</thought>', '', ai_text, flags=re.DOTALL)
        clean_ai_text = re.sub(r'<think>.*?</think>', '', clean_ai_text, flags=re.DOTALL).strip()
        if not clean_ai_text:
            clean_ai_text = ai_text.strip()
        return {"response": clean_ai_text, "source": f"llm_native ({used_model})"}
    except Exception as e:
        print(f"[CHAT NATIVE LLM FAILOVER] {e}. Trying OpenAI compatibility client...")

    # Tier 2: Try OpenAI Compatibility Client (Groq / LM Studio)
    messages = [{"role": "system", "content": system_content}]
    for msg in (req.history or [])[-20:]:
        if msg.role in ("user", "assistant"):
            messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": req.text})

    try:
        import asyncio
        loop = asyncio.get_running_loop()
        
        def _call_llm():
            return client.chat.completions.create(
                model=MODEL_TO_USE,
                messages=messages,
                temperature=0.7,
                timeout=15.0,
            )

        response = await asyncio.wait_for(loop.run_in_executor(None, _call_llm), timeout=15.0)
        ai_text = response.choices[0].message.content or ""
        clean_ai_text = re.sub(r'<thought>.*?</thought>', '', ai_text, flags=re.DOTALL)
        clean_ai_text = re.sub(r'<think>.*?</think>', '', clean_ai_text, flags=re.DOTALL).strip()
        if not clean_ai_text:
            clean_ai_text = ai_text.strip()

        return {"response": clean_ai_text, "source": "llm_openai"}
    except Exception as e:
        import traceback
        print(f"[CHAT ERROR] LLM Call failed or timed out: {e}\n{traceback.format_exc()}")
        fallback_msg = generate_smart_chat_fallback(req.text, sid, req.tone)
        return {"response": fallback_msg, "source": "fallback"}

# ─── BACKEND SPEECH-TO-TEXT (STT) ENDPOINT ─────────────────
@app.post("/stt")
async def stt_transcribe(file: UploadFile = File(...)):
    try:
        import speech_recognition as sr
        contents = await file.read()
        
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        with os.fdopen(tmp_fd, 'wb') as f:
            f.write(contents)
            
        r = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
            
        try:
            os.remove(tmp_path)
        except Exception:
            pass
            
        return {"text": text, "status": "success"}
    except Exception as e:
        print(f"[STT ENDPOINT ERROR] {e}")
        return {"text": "", "status": "error", "detail": str(e)}

# ─── BACKEND TEXT-TO-SPEECH (TTS) ENDPOINT ─────────────────
@app.get("/tts")
def tts_stream(text: str):
    if not text.strip():
        raise HTTPException(status_code=400, detail="text parameter is required.")
    
    clean_text = "".join(c for c in text if c.isalnum() or c.isspace() or c in ".,!?")
    if not clean_text.strip():
        clean_text = "System active."

    try:
        from gtts import gTTS
        import io
        mp3_buffer = io.BytesIO()
        tts = gTTS(text=clean_text[:600], lang="en", slow=False)
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)
        return Response(content=mp3_buffer.read(), media_type="audio/mpeg")
    except Exception as e:
        print(f"[TTS ENDPOINT ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

# ─── COMPARATIVE CODING ENDPOINT (POST) ─────────────────────
def analyze_code_comparison_fallback(code_a: str, code_b: str, language: str, problem_title: str) -> dict:
    def estimate_complexity(code: str):
        lines = [l.strip() for l in code.splitlines() if l.strip() and not l.strip().startswith("#")]
        nested_loop = False
        loop_count = 0
        in_loop = False
        for l in lines:
            if any(k in l for k in ["for ", "while "]):
                if in_loop:
                    nested_loop = True
                in_loop = True
                loop_count += 1
        
        if nested_loop:
            t_comp = "O(N²)"
            score = 65
        elif loop_count > 0:
            if "log" in code.lower() or "// 2" in code or ">> 1" in code or "bisect" in code:
                t_comp = "O(N log N)"
                score = 88
            else:
                t_comp = "O(N)"
                score = 82
        elif any(k in code for k in ["binary_search", "bisect", "mid ="]):
            t_comp = "O(log N)"
            score = 95
        else:
            t_comp = "O(1)"
            score = 98

        s_comp = "O(N)" if ("append(" in code or "new " in code or "[" in code) else "O(1)"
        return t_comp, s_comp, score

    t_a, s_a, score_a = estimate_complexity(code_a)
    t_b, s_b, score_b = estimate_complexity(code_b)

    winner = "Solution A" if score_a >= score_b else "Solution B"
    margin = abs(score_a - score_b)

    return {
        "status": "success",
        "source": "deterministic_evaluator",
        "problem_title": problem_title,
        "language": language,
        "solution_a": {
            "time_complexity": t_a,
            "space_complexity": s_a,
            "efficiency_score": score_a,
            "summary": f"Evaluated as {t_a} time complexity with {s_a} auxiliary space."
        },
        "solution_b": {
            "time_complexity": t_b,
            "space_complexity": s_b,
            "efficiency_score": score_b,
            "summary": f"Evaluated as {t_b} time complexity with {s_b} auxiliary space."
        },
        "comparison": {
            "winner": winner,
            "verdict": f"{winner} is more optimal by {margin} efficiency points.",
            "recommendation": f"For VIT lab evaluations, prefer {winner} due to lower algorithmic overhead and cleaner memory allocation."
        }
    }

@app.post("/compare-code")
async def compare_code(req: CodeCompareRequest):
    if not req.code_a.strip() or not req.code_b.strip():
        raise HTTPException(status_code=400, detail="Both code_a and code_b must be provided.")

    lang = req.language or "python"
    title = req.problem_title or "Algorithm Benchmark"

    try:
        import asyncio
        loop = asyncio.get_running_loop()

        system_prompt = (
            "You are an expert algorithm evaluator and competitive programming mentor for VIT students.\n"
            "Compare two code implementations for efficiency, asymptotic time/space complexity, and code readability.\n"
            "Return ONLY valid JSON matching this schema:\n"
            "{\n"
            '  "status": "success",\n'
            '  "problem_title": "Title",\n'
            '  "language": "python",\n'
            '  "solution_a": {"time_complexity": "O(...)", "space_complexity": "O(...)", "efficiency_score": 85, "summary": "..."},\n'
            '  "solution_b": {"time_complexity": "O(...)", "space_complexity": "O(...)", "efficiency_score": 92, "summary": "..."},\n'
            '  "comparison": {"winner": "Solution B", "verdict": "...", "recommendation": "..."}\n'
            "}"
        )
        user_prompt = f"PROBLEM: {title}\nLANGUAGE: {lang}\n\n=== CODE SOLUTION A ===\n{req.code_a}\n\n=== CODE SOLUTION B ===\n{req.code_b}"

        def _call_compare():
            return client.chat.completions.create(
                model=MODEL_TO_USE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                timeout=10.0,
            )

        response = await asyncio.wait_for(loop.run_in_executor(None, _call_compare), timeout=10.0)
        raw_text = response.choices[0].message.content
        cleaned = re.sub(r"```[\w]*", "", raw_text).strip()
        cleaned = re.sub(r"```", "", cleaned).strip()
        parsed = json.loads(cleaned)
        parsed["source"] = "llm"
        return parsed
    except Exception:
        return analyze_code_comparison_fallback(req.code_a, req.code_b, lang, title)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
