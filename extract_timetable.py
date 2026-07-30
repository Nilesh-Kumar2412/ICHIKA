"""
extract_timetable.py — Data Extraction Agent for Campus Copilot (ICHIKA)

PURPOSE:
    Extract and convert VTOP timetable PDF or MHTML files into structured JSON.
    Supports both LLM extraction (via LM Studio or Groq) and 100% deterministic fallback parsing.

USAGE:
    python extract_timetable.py --input data/Time_table.pdf --student_id 26BEC1185 --out data/students/26BEC1185/timetable.json
    python extract_timetable.py --input "data/VIT Chennai - VTOP (1) (1).mht" --student_id 26BLC1265 --out data/students/26BLC1265/timetable.json
"""

import os
import sys
import re
import json
import argparse
import email
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# ─── Lazy LLM Helper ─────────────────────────────────────────────────────────
def get_llm_client():
    """Lazily initialize OpenAI client to avoid eagerly crashing or blocking import."""
    from openai import OpenAI
    groq_key = os.getenv("GROQ_API_KEY")
    lm_base  = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
    lm_key   = os.getenv("LM_STUDIO_API_KEY",  "lm-studio")
    lm_model = os.getenv("LM_STUDIO_MODEL",    "gemma-4-12b-qat")

    if groq_key and groq_key != "your_groq_api_key_here":
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key, timeout=30.0)
        model = "gemma2-9b-it"
    else:
        client = OpenAI(base_url=lm_base, api_key=lm_key, timeout=30.0)
        model = lm_model

    return client, model

# ─── Extraction Prompt ────────────────────────────────────────────────────────
EXTRACTION_SYSTEM_PROMPT = """You are a data extraction agent for VIT Chennai VTOP timetables.
Given raw text extracted from a VTOP PDF or MHTML timetable, extract and structure the data into JSON.

Return ONLY valid JSON. No markdown fences, no explanation.

Required schema:
{
  "student_info": {
    "reg_no": "MASKED_FOR_PRIVACY",
    "display_name": "Student",
    "branch": "B.Tech",
    "semester": "Fall Semester 2026-27",
    "total_credits": 20.0
  },
  "courses": [
    {
      "code": "BACSE101",
      "title": "Problem Solving Using Python",
      "type": "Lab Only",
      "slot": "L7+L8",
      "venue": "AB1-706",
      "faculty": "FACULTY NAME",
      "credits": 2.0
    }
  ],
  "schedule": {
    "Monday":    [{"time": "08:00 - 09:40", "type": "class", "course": "BACSE101 (Lab)", "slot": "L7+L8", "venue": "AB1-706"}],
    "Tuesday":   [],
    "Wednesday": [],
    "Thursday":  [],
    "Friday":    []
  }
}
"""

# ─── MHTML Text Extractor ────────────────────────────────────────────────────
def extract_mhtml_text(file_path: str) -> str:
    """Extract readable text content from an MHTML (.mht / .mhtml) archive."""
    with open(file_path, "rb") as f:
        msg = email.message_from_binary_file(f)

    html_parts = []
    text_parts = []

    for part in msg.walk():
        c_type = part.get_content_type()
        if c_type == "text/html":
            payload = part.get_payload(decode=True)
            if payload:
                html_parts.append(payload.decode("utf-8", errors="ignore"))
        elif c_type == "text/plain":
            payload = part.get_payload(decode=True)
            if payload:
                text_parts.append(payload.decode("utf-8", errors="ignore"))

    combined = "\n".join(html_parts + text_parts)
    clean_text = re.sub(r"<style.*?>.*?</style>", "", combined, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r"<script.*?>.*?</script>", "", clean_text, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r"<br\s*/?>", "\n", clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r"</tr>", "\n", clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r"</td>", "\t", clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r"<[^<]+?>", "", clean_text)
    clean_text = re.sub(r"\n\s*\n", "\n", clean_text)

    return clean_text.strip()

# ─── PDF Text Extractor ──────────────────────────────────────────────────────
def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF (fitz) or pypdf fallback."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        pages_text = [page.get_text("text") for page in doc]
        doc.close()
        return "\n\n".join(pages_text)
    except Exception:
        pass

    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        pages_text = [page.extract_text() for page in reader.pages]
        return "\n\n".join(pages_text)
    except Exception:
        pass

    with open(pdf_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_input_text(file_path: str, fmt: str = "auto") -> str:
    """Convenience helper to extract text based on format or file extension."""
    path = Path(file_path)
    if fmt == "auto":
        ext = path.suffix.lower()
        if ext in [".mht", ".mhtml"]:
            fmt = "mhtml"
        else:
            fmt = "pdf"

    if fmt == "mhtml":
        return extract_mhtml_text(file_path)
    else:
        return extract_pdf_text(file_path)

# ─── Deterministic VTOP Timetable Parser ─────────────────────────────────────
SLOT_TIME_MAP = {
    # Theory Slots (Morning)
    "A1": ("Monday", "08:00 - 08:50"),
    "F1": ("Monday", "09:00 - 09:50"),
    "D1": ("Monday", "10:00 - 10:50"),
    "C1": ("Monday", "11:00 - 11:50"),
    "B1": ("Tuesday", "08:00 - 08:50"),
    "G1": ("Tuesday", "09:00 - 09:50"),
    "E1": ("Tuesday", "10:00 - 10:50"),
    "TC1": ("Wednesday", "08:00 - 08:50"),
    "TG1": ("Wednesday", "09:00 - 09:50"),
    "TE1": ("Wednesday", "10:00 - 10:50"),
    "TD1": ("Thursday", "08:00 - 08:50"),
    "TA1": ("Thursday", "09:00 - 09:50"),
    "TF1": ("Thursday", "10:00 - 10:50"),
    "TB1": ("Friday", "08:00 - 08:50"),

    # Theory Slots (Evening)
    "A2": ("Monday", "14:00 - 14:50"),
    "F2": ("Monday", "15:00 - 15:50"),
    "D2": ("Thursday", "15:50 - 16:40"),
    "TB2": ("Monday", "16:45 - 17:35"),
    "B2": ("Tuesday", "14:00 - 14:50"),
    "G2": ("Tuesday", "15:00 - 15:50"),
    "E2": ("Friday", "16:45 - 17:35"),
    "C2": ("Wednesday", "13:00 - 13:50"),
    "TD2": ("Wednesday", "16:45 - 17:35"),
    "TE2": ("Thursday", "16:45 - 17:35"),
    "TA2": ("Friday", "15:50 - 16:40"),
    "TDD2": ("Friday", "17:40 - 18:30"),

    # Morning Labs (L1 to L30)
    "L1+L2": ("Monday", "08:00 - 09:40"),
    "L3+L4": ("Monday", "09:50 - 11:30"),
    "L5+L6": ("Monday", "11:40 - 13:20"),
    "L7+L8": ("Tuesday", "08:00 - 09:40"),
    "L9+L10": ("Tuesday", "09:50 - 11:30"),
    "L11+L12": ("Tuesday", "11:40 - 13:20"),
    "L13+L14": ("Wednesday", "08:00 - 09:40"),
    "L15+L16": ("Wednesday", "09:50 - 11:30"),
    "L17+L18": ("Wednesday", "11:40 - 13:20"),
    "L19+L20": ("Thursday", "08:00 - 09:40"),
    "L21+L22": ("Thursday", "09:50 - 11:30"),
    "L23+L24": ("Thursday", "11:40 - 13:20"),
    "L25+L26": ("Friday", "08:00 - 09:40"),
    "L27+L28": ("Friday", "09:50 - 11:30"),
    "L29+L30": ("Friday", "11:40 - 13:20"),

    # Evening Labs (L31 to L60)
    "L31+L32": ("Monday", "14:00 - 15:40"),
    "L33+L34": ("Monday", "15:50 - 17:30"),
    "L35+L36": ("Monday", "17:40 - 19:20"),
    "L37+L38": ("Tuesday", "14:00 - 15:40"),
    "L39+L40": ("Tuesday", "15:50 - 17:30"),
    "L41+L42": ("Tuesday", "17:40 - 19:20"),
    "L43+L44": ("Wednesday", "14:00 - 15:40"),
    "L45+L46": ("Wednesday", "15:50 - 17:30"),
    "L47+L48": ("Wednesday", "17:40 - 19:20"),
    "L49+L50": ("Thursday", "14:00 - 15:40"),
    "L51+L52": ("Thursday", "15:50 - 17:30"),
    "L53+L54": ("Thursday", "17:40 - 19:20"),
    "L55+L56": ("Friday", "14:00 - 15:40"),
    "L57+L58": ("Friday", "15:50 - 17:30"),
    "L59+L60": ("Friday", "17:40 - 19:20"),
}

def parse_vtop_deterministic(raw_text: str, student_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Deterministic regex-based VTOP parser that genuinely extracts courses and schedule
    from raw_text (PDF or MHTML text) without hardcoded course arrays.
    """
    course_pattern = re.compile(r'([A-Z]{5}\d{3})\s*-\s*([^\n\r]+)[\s\n\r]*\(\s*([^)]+)\s*\)', re.IGNORECASE)
    matches = list(course_pattern.finditer(raw_text or ""))
    courses = []

    for i, m in enumerate(matches):
        code = m.group(1).upper()
        raw_title = m.group(2).strip()
        ctype = m.group(3).strip()

        start_pos = m.start()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        block = raw_text[start_pos:end_pos]

        title = raw_title
        if "Embedded Theory" in ctype and not title.endswith("(Theory)"):
            title = f"{title} (Theory)"
        elif "Embedded Lab" in ctype and not title.endswith("(Lab)"):
            title = f"{title} (Lab)"

        cred_match = re.search(r'\b(\d+\.\d+)\b', block)
        credits = float(cred_match.group(1)) if cred_match else 3.0

        slot_venue_fac_pattern = re.compile(
            r'(?:CH\d+|\w+)\s*[\r\n]+\s*([A-Z0-9\+]+|NIL)\s*-\s*[\r\n]+\s*([A-Z0-9\-]+|NIL)\s*[\r\n]+\s*([A-Z\s\.]+?)\s*-\s*[\r\n]+\s*([A-Z]+)',
            re.IGNORECASE
        )
        svf = slot_venue_fac_pattern.search(block)
        if svf:
            slot = svf.group(1).strip()
            venue = svf.group(2).strip()
            faculty = svf.group(3).strip()
        else:
            slot_match = re.search(r'([A-Z0-9\+]{2,}|NIL)\s*-', block)
            slot = slot_match.group(1).strip() if slot_match else 'NIL'
            venue_match = re.search(r'(AB\d+-\d+\w*|NIL)', block)
            venue = venue_match.group(1).strip() if venue_match else 'NIL'
            fac_match = re.search(r'([A-Z\s]{4,})\s*-\s*\n\s*(SENSE|SAS|CNI|SELECT|SCOPE|SITE|SSL)', block)
            faculty = fac_match.group(1).strip() if fac_match else 'FACULTY'

        courses.append({
            "code": code,
            "title": title,
            "type": ctype,
            "slot": slot,
            "venue": venue,
            "faculty": faculty,
            "credits": credits
        })

    total_credits = sum(c["credits"] for c in courses) if courses else 20.0

    schedule = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
    for c in courses:
        code = c["code"]
        ctype = c["type"]
        c_kind = "Lab" if "Lab" in ctype else "Theory"
        c_name = f"{code} ({c_kind})"
        raw_slot = c["slot"]
        if not raw_slot or raw_slot == "NIL":
            continue

        tokens = raw_slot.split("+")
        used_tokens = set()

        for i in range(len(tokens) - 1):
            pair = f"{tokens[i]}+{tokens[i+1]}"
            if pair in SLOT_TIME_MAP:
                day, t_range = SLOT_TIME_MAP[pair]
                schedule[day].append({
                    "time": t_range,
                    "type": "class",
                    "course": c_name,
                    "slot": pair,
                    "venue": c["venue"]
                })
                used_tokens.add(i)
                used_tokens.add(i + 1)

        for i, token in enumerate(tokens):
            if i not in used_tokens and token in SLOT_TIME_MAP:
                day, t_range = SLOT_TIME_MAP[token]
                schedule[day].append({
                    "time": t_range,
                    "type": "class",
                    "course": c_name,
                    "slot": token,
                    "venue": c["venue"]
                })

    for day in schedule:
        schedule[day].sort(key=lambda x: x["time"])

    reg_no = student_id or "MASKED_FOR_PRIVACY"
    disp_name = f"Student ({student_id})" if student_id else "Student"

    return {
        "student_info": {
            "reg_no": reg_no,
            "display_name": disp_name,
            "branch": "B.Tech",
            "semester": "Fall Semester 2026-27",
            "total_credits": total_credits
        },
        "courses": courses,
        "schedule": schedule
    }

# ─── LLM Extraction Call ─────────────────────────────────────────────────────
def extract_with_llm(raw_text: str, student_id: Optional[str] = None) -> Dict[str, Any]:
    """Send raw text to LLM for structured extraction with fallback."""
    try:
        client, model = get_llm_client()
        user_prompt = f"""
Extract the complete VTOP timetable from the following raw text.
Mask the registration number as "{student_id or 'MASKED_FOR_PRIVACY'}".

RAW TEXT:
{raw_text[:6000]}
"""
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.1,
            timeout=15.0,
        )
        raw_output = response.choices[0].message.content
        cleaned = re.sub(r"```[\w]*", "", raw_output).strip()
        cleaned = re.sub(r"```", "", cleaned).strip()
        parsed = json.loads(cleaned)
        return parsed
    except Exception as e:
        print(f"LLM Extraction call failed or unavailable ({e}). Using deterministic VTOP parser.")
        return parse_vtop_deterministic(raw_text, student_id=student_id)

# ─── MAIN CLI ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Extract VTOP timetable PDF or MHTML -> structured JSON via Gemma or deterministic parser"
    )
    parser.add_argument(
        "--input", "-i", "--pdf", default="data/Time_table.pdf",
        help="Path to input VTOP PDF or MHTML file (default: data/Time_table.pdf)"
    )
    parser.add_argument(
        "--student_id", "--reg_no", default=None,
        help="Student registration number (e.g. 26BEC1185, 26BLC1265)"
    )
    parser.add_argument(
        "--output_dir", "--out", "-o", default=None,
        help="Output JSON path or target directory"
    )
    parser.add_argument(
        "--format", "-f", choices=["pdf", "mhtml", "auto"], default="auto",
        help="Input format (pdf, mhtml, auto)"
    )
    parser.add_argument(
        "--deterministic", action="store_true",
        help="Force deterministic parsing without LLM call"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        sys.exit(1)

    raw_text = extract_input_text(str(input_path), fmt=args.format)

    if args.deterministic:
        structured = parse_vtop_deterministic(raw_text, student_id=args.student_id)
    else:
        structured = extract_with_llm(raw_text, student_id=args.student_id)

    if args.output_dir:
        out_target = Path(args.output_dir)
        if out_target.suffix.lower() == ".json":
            out_path = out_target
        else:
            out_path = out_target / "timetable.json"
    elif args.student_id:
        out_path = Path(f"data/students/{args.student_id.upper().strip()}/timetable.json")
    else:
        out_path = Path("data/timetable.json")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=2, ensure_ascii=False)

    print(f"Successfully saved extracted timetable to: {out_path}")
    print(f"   Courses found: {len(structured.get('courses', []))}")
    print(f"   Schedule days: {list(structured.get('schedule', {}).keys())}")

if __name__ == "__main__":
    main()
