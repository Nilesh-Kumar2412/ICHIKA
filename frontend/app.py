import streamlit as st
import requests
import json
import html
import socket
import io
try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

st.set_page_config(
    page_title="VIT Chennai — Campus Copilot (Ichika)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if "backend_url" not in st.session_state:
    st.session_state["backend_url"] = "http://localhost:8000"

if "selected_reg_no" not in st.session_state:
    st.session_state["selected_reg_no"] = "26BEC1185"

if "plan_data" not in st.session_state:
    st.session_state.plan_data = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "replan_data" not in st.session_state:
    st.session_state.replan_data = None

if "neg_result" not in st.session_state:
    st.session_state.neg_result = None

# ─────────────────────────────────────────────────────────
#  HIGH-CONTRAST PRUSSIAN BLUE / GOLD / CHARCOAL STYLING
# ─────────────────────────────────────────────────────────
st.html("""
<style>

/* Global Cyber-Violet Dark Theme Overrides matching thumbnail.jpeg */
body, .stApp {
    color: #F8FAFC !important;
    background-color: #120F24 !important;
}

/* Sidebar styling - Dark Cyber Violet background */
section[data-testid="stSidebar"] {
    background-color: #0C0A19 !important;
    border-right: 1px solid #2E2656 !important;
}
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3 {
    color: #F8FAFC !important;
}
section[data-testid="stSidebar"] label {
    color: #C084FC !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] label p,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
    color: #CBD5E1 !important;
}

/* Sidebar inputs & selectboxes */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] div[data-baseweb="select"] {
    background-color: #16122C !important;
    color: #F8FAFC !important;
    border: 1px solid #C084FC !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] div {
    color: #F8FAFC !important;
}

/* Dropdown listbox popups - Dark panel with vibrant text */
div[role="listbox"],
div[role="listbox"] *,
div[role="option"],
div[role="option"] *,
ul[role="listbox"] li,
ul[role="listbox"] li * {
    color: #F8FAFC !important;
    background-color: #1C173B !important;
}

div[data-baseweb="select"] {
    border: 1px solid #3B3363 !important;
    border-radius: 6px !important;
}

/* Thumbnail Reference Visual Layout Banner */
.ichika-hero-banner {
    background: linear-gradient(135deg, #0F0C21 0%, #1A1536 60%, #120E29 100%);
    border: 1px solid #3B3363;
    border-bottom: 3px solid #C084FC;
    padding: 24px 32px;
    border-radius: 10px;
    margin-bottom: 24px;
    color: #F8FAFC;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}
.ichika-hero-kicker {
    color: #C084FC;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.ichika-hero-title {
    font-family: Georgia, serif;
    font-size: 2.3rem;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0 0 8px 0;
    letter-spacing: 0.5px;
    text-shadow: 0 0 20px rgba(192, 132, 252, 0.3);
}
.ichika-hero-sub {
    color: #CBD5E1;
    font-size: 0.95rem;
    line-height: 1.5;
    max-width: 800px;
    margin-bottom: 16px;
}
.ichika-pill-container {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}
.ichika-pill-badge {
    background: rgba(192, 132, 252, 0.12);
    border: 1px solid #C084FC;
    color: #E879F9;
    padding: 4px 14px;
    border-radius: 16px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* Custom Header Bar */
.vtop-navbar {
    background-color: #1A1536;
    border: 1px solid #3B3363;
    border-bottom: 2px solid #38BDF8;
    padding: 14px 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.vtop-title {
    color: #FFFFFF !important;
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0;
}
.vtop-sub {
    color: #38BDF8 !important;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.vtop-user-pill {
    background: #120E29;
    border: 1px solid #C084FC;
    color: #F8FAFC !important;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 600;
}

/* Page Section Titles */
.page-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #F8FAFC !important;
    margin-bottom: 2px;
}
.page-sub {
    font-size: 0.85rem;
    color: #94A3B8 !important;
    margin-bottom: 16px;
}

/* Cyber-Violet Schedule Item Card */
.schedule-item {
    background-color: #181434;
    border: 1px solid #2E2656;
    border-left: 5px solid #C084FC;
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}
.schedule-item-class    { border-left-color: #38BDF8; }
.schedule-item-meal     { border-left-color: #4ADE80; }
.schedule-item-deadline { border-left-color: #F87171; }
.schedule-item-event    { border-left-color: #FBBF24; }
.schedule-item-study    { border-left-color: #C084FC; }
.schedule-item-replanned{ border-left-color: #0EA5E9; }
.schedule-item-missed   { border-left-color: #64748B; opacity: 0.65; background-color: #120E27; }

.schedule-time-badge {
    min-width: 120px;
    font-size: 0.85rem;
    font-weight: 700;
    color: #F8FAFC !important;
}
.schedule-type-tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    min-width: 85px;
    text-align: center;
}
.tag-class     { background: rgba(56, 189, 248, 0.15); color: #38BDF8 !important; border: 1px solid #38BDF8; }
.tag-meal      { background: rgba(74, 222, 128, 0.15); color: #4ADE80 !important; border: 1px solid #4ADE80; }
.tag-deadline  { background: rgba(248, 113, 113, 0.15); color: #F87171 !important; border: 1px solid #F87171; }
.tag-event     { background: rgba(251, 191, 36, 0.15); color: #FBBF24 !important; border: 1px solid #FBBF24; }
.tag-study     { background: rgba(192, 132, 252, 0.15); color: #C084FC !important; border: 1px solid #C084FC; }
.tag-replanned { background: rgba(14, 165, 233, 0.2); color: #38BDF8 !important; border: 1px solid #38BDF8; }
.tag-missed    { background: rgba(148, 163, 184, 0.15); color: #94A3B8 !important; border: 1px solid #475569; }

.schedule-label-text {
    flex: 1;
    font-size: 0.92rem;
    font-weight: 600;
    color: #F8FAFC !important;
}
.schedule-meta-text {
    font-size: 0.8rem;
    color: #CBD5E1 !important;
    font-weight: 600;
}

/* Day Strip Header */
.day-strip {
    background-color: #1A1536;
    border: 1px solid #3B3363;
    color: #FFFFFF !important;
    font-weight: 700;
    font-size: 0.88rem;
    padding: 8px 16px;
    border-radius: 6px;
    margin-top: 16px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.day-strip span {
    color: #FFFFFF !important;
}

/* Negotiation Log Items */
.log-card {
    background-color: #181434;
    border: 1px solid #2E2656;
    border-left: 4px solid #38BDF8;
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 8px;
    font-size: 0.88rem;
    color: #F8FAFC !important;
}
.log-card-teammate { border-left-color: #C084FC; }
.log-card-final    { border-left-color: #4ADE80; background-color: rgba(74, 222, 128, 0.1); }

</style>
""")

# ─────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### VIT CHENNAI")
    st.markdown("Academic Portal · Campus Copilot")
    st.markdown("---")

    BACKEND_URL = st.text_input("API Base Endpoint", key="backend_url")

    available_students = ["26BEC1185", "26BLC1265"]
    try:
        res = requests.get(f"{BACKEND_URL}/students", timeout=5)
        if res.status_code == 200:
            server_students = res.json().get("students", [])
            if server_students:
                available_students = server_students
    except Exception:
        pass

    st.markdown("##### Student Profile")
    reg_choice = st.selectbox(
        "Select Active Student",
        options=available_students + ["+ Upload New Profile"],
        index=0 if st.session_state["selected_reg_no"] not in available_students else available_students.index(st.session_state["selected_reg_no"])
    )

    if reg_choice != "+ Upload New Profile":
        if st.session_state["selected_reg_no"] != reg_choice:
            st.session_state["selected_reg_no"] = reg_choice
            st.session_state.plan_data = None
            st.session_state.replan_data = None
    else:
        st.markdown("##### Register New Profile")
        new_reg = st.text_input("Registration No.", key="sidebar_new_reg_no")
        new_file = st.file_uploader("Upload Timetable (PDF, MHTML, or JSON)", type=["json", "pdf", "mht", "mhtml"], key="sidebar_new_file")
        if st.button("Register & Switch", type="primary", width="stretch"):
            if not new_reg.strip():
                st.warning("Please enter a registration number.")
            elif not new_file:
                st.warning("Please select a timetable file.")
            else:
                try:
                    mime = "application/pdf" if new_file.name.endswith(".pdf") else ("message/rfc822" if new_file.name.endswith((".mht", ".mhtml")) else "application/json")
                    files = {"file": (new_file.name, new_file.getvalue(), mime)}
                    data = {"reg_no": new_reg.strip().upper()}
                    res = requests.post(f"{BACKEND_URL}/upload/timetable", data=data, files=files, timeout=30)
                    if res.status_code == 200:
                        st.success(f"Registered {new_reg.upper()}!")
                        st.session_state["selected_reg_no"] = new_reg.upper()
                        st.session_state.plan_data = None
                        st.session_state.replan_data = None
                        st.rerun()
                    else:
                        st.error(f"Registration failed: {res.text}")
                except Exception as e:
                    st.error(f"Registration error: {e}")

    st.markdown("---")
    st.markdown("##### System Status")
    st.markdown("""
    • Status: Active & Operational<br>
    • Backend Port: 8000<br>
    • Network: Local IP / Hotspot
    """)

    st.markdown("---")
    st.markdown("##### Local Network Access")
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "localhost"
    frontend_url = f"http://{local_ip}:8501"
    st.code(frontend_url, language="text")

    if QR_AVAILABLE:
        try:
            qr = qrcode.QRCode(version=1, box_size=3, border=1)
            qr.add_data(frontend_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="#002147", back_color="white")
            buf = io.BytesIO()
            qr_img.save(buf, format="PNG")
            buf.seek(0)
            st.image(buf, caption="Mobile Web Access QR", width="stretch")
        except Exception:
            pass

# ─────────────────────────────────────────────────────────
#  HERO BANNER (MATCHING THUMBNAIL REFERENCE LAYOUT)
# ─────────────────────────────────────────────────────────
st.html("""
<div class="ichika-hero-banner">
  <div class="ichika-hero-kicker">AUTONOMOUS AGENTS • CODE WITH GEMMA</div>
  <div class="ichika-hero-title">Project Ichika</div>
  <div class="ichika-hero-sub">
    Plans your week. Replans on the fly. Negotiates with your teammates — an autonomous agent running fully on-device, no cloud in sight.
  </div>
  <div class="ichika-pill-container">
    <span class="ichika-pill-badge">Gemma 4 12B QAT</span>
    <span class="ichika-pill-badge">Fully on-device</span>
    <span class="ichika-pill-badge">Ichika Moderators</span>
  </div>
</div>
""")

# ─────────────────────────────────────────────────────────
#  NAVBAR
# ─────────────────────────────────────────────────────────
st.html(f"""
<div class="vtop-navbar">
  <div>
    <div class="vtop-title">VELLORE INSTITUTE OF TECHNOLOGY</div>
    <div class="vtop-sub">Chennai Campus · Campus Copilot Assistant</div>
  </div>
  <div class="vtop-user-pill">
    Active Student: <strong>{html.escape(st.session_state['selected_reg_no'])}</strong>
  </div>
</div>
""")

# ─────────────────────────────────────────────────────────
#  RENDER HELPERS
# ─────────────────────────────────────────────────────────
TAG_CLASSES = {
    "class": "tag-class", "meal": "tag-meal", "deadline": "tag-deadline",
    "event": "tag-event", "study": "tag-study", "replanned": "tag-replanned",
    "missed": "tag-missed"
}
ITEM_CLASSES = {
    "class": "schedule-item-class", "meal": "schedule-item-meal", "deadline": "schedule-item-deadline",
    "event": "schedule-item-event", "study": "schedule-item-study", "replanned": "schedule-item-replanned",
    "missed": "schedule-item-missed"
}

def render_schedule_item(item):
    itype = item.get("type", "class").lower()
    tag_cls = TAG_CLASSES.get(itype, "tag-class")
    item_cls = ITEM_CLASSES.get(itype, "schedule-item-class")
    safe_label = html.escape(item.get("label", ""))
    safe_time = html.escape(item.get("time", ""))
    priority = html.escape(str(item.get("priority", "Low")))

    st.html(f"""
    <div class="schedule-item {item_cls}">
      <div class="schedule-time-badge">{safe_time}</div>
      <div><span class="schedule-type-tag {tag_cls}">{itype.upper()}</span></div>
      <div class="schedule-label-text">{safe_label}</div>
      <div class="schedule-meta-text">Priority: {priority}</div>
    </div>
    """)

# ─────────────────────────────────────────────────────────
#  MAIN TABS
# ─────────────────────────────────────────────────────────
tab_agenda, tab_replan, tab_negotiate, tab_upload, tab_chat = st.tabs([
    "Weekly Agenda",
    "Replanner",
    "Group Negotiator",
    "Data Upload",
    "Assistant Chat",
])

# ══════════════════════════════════════════════════════════
#  TAB 1 — WEEKLY AGENDA
# ══════════════════════════════════════════════════════════
with tab_agenda:
    col_hdr, col_act = st.columns([3, 1])
    with col_hdr:
        st.html(f"""
        <div class="page-title">Weekly Schedule Overview</div>
        <div class="page-sub">Integrated VTOP schedule and deadlines for <strong>{html.escape(st.session_state["selected_reg_no"])}</strong></div>
        """)
    with col_act:
        st.write("")
        gen_btn = st.button("Generate Schedule", type="primary", width="stretch")

    if gen_btn:
        with st.spinner("Fetching schedule data..."):
            try:
                res = requests.get(f"{BACKEND_URL}/plan?student_id={st.session_state['selected_reg_no']}", timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.plan_data = data.get("plan", [])
                    st.success("Schedule generated successfully.")
                else:
                    st.error(f"Error fetching schedule: {res.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")

    if st.session_state.plan_data:
        for day_obj in st.session_state.plan_data:
            day_name = day_obj.get("day", "")
            items = day_obj.get("items", [])

            st.html(f"""
            <div class="day-strip">
                <span>{html.escape(day_name)}</span>
                <span style="font-weight:400;font-size:0.78rem;">{len(items)} items</span>
            </div>
            """)
            if items:
                for item in items:
                    render_schedule_item(item)
            else:
                st.caption("No items scheduled for this day.")
    else:
        st.info(f"Click **Generate Schedule** above to load the weekly schedule for {st.session_state['selected_reg_no']}.")

# ══════════════════════════════════════════════════════════
#  TAB 2 — REPLANNER
# ══════════════════════════════════════════════════════════
with tab_replan:
    st.html("""
    <div class="page-title">Schedule Replanner</div>
    <div class="page-sub">Report missed items to automatically re-allocate tasks into open slots later in the week.</div>
    """)

    col_in, col_act2 = st.columns([3, 1])
    with col_in:
        missed_input = st.text_input("Missed Course / Lab / Activity", placeholder="e.g. BACSE101 Python Lab")
    with col_act2:
        st.write("")
        replan_btn = st.button("Reschedule Item", type="primary", width="stretch")

    if replan_btn:
        if not missed_input.strip():
            st.warning("Please enter a description of the missed item.")
        else:
            if not st.session_state.plan_data:
                try:
                    res = requests.get(f"{BACKEND_URL}/plan?student_id={st.session_state['selected_reg_no']}", timeout=30)
                    if res.status_code == 200:
                        st.session_state.plan_data = res.json().get("plan", [])
                except Exception:
                    pass

            with st.spinner("Reallocating schedule..."):
                try:
                    payload = {
                        "student_id": st.session_state["selected_reg_no"],
                        "current_plan": st.session_state.plan_data or [],
                        "missed_items": [missed_input]
                    }
                    res = requests.post(f"{BACKEND_URL}/replan", json=payload, timeout=30)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.plan_data = data.get("plan", [])
                        st.success(f"Rescheduled item: {missed_input}")
                    else:
                        st.error(f"Replanner error: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    if st.session_state.plan_data:
        st.markdown("---")
        st.markdown("##### Active Schedule State")
        for day_obj in st.session_state.plan_data:
            day_name = day_obj.get("day", "")
            items = day_obj.get("items", [])
            with st.expander(f"{day_name} ({len(items)} items)", expanded=True):
                for item in items:
                    render_schedule_item(item)

# ══════════════════════════════════════════════════════════
#  TAB 3 — GROUP NEGOTIATOR
# ══════════════════════════════════════════════════════════
with tab_negotiate:
    st.html("""
    <div class="page-title">Group Study Negotiator</div>
    <div class="page-sub">Automated schedule coordination between teammate calendars (max 3 rounds).</div>
    """)

    # Fetch teammate registration numbers dynamically
    teammate_options = ["26BLC1001", "26BLC1002", "26BLC1003"]
    try:
        data_res = requests.get(f"{BACKEND_URL}/data?student_id={st.session_state['selected_reg_no']}", timeout=5)
        if data_res.status_code == 200:
            tcals = data_res.json().get("teammate_calendars", {})
            if tcals:
                teammate_options = list(tcals.keys())
    except Exception:
        pass

    col_tm, col_win, col_act3 = st.columns([2, 2, 1])
    with col_tm:
        selected_teammates = st.multiselect(
            "Select Teammates",
            teammate_options,
            default=teammate_options
        )
    with col_win:
        time_win_input = st.text_input("Proposed Window (Optional)", placeholder="e.g. Wednesday 18:00 - 20:00")
    with col_act3:
        st.write("")
        start_neg = st.button("Start Coordination", type="primary", width="stretch")

    if start_neg:
        if not selected_teammates:
            st.warning("Select at least one teammate.")
        else:
            with st.spinner("Negotiating study slot..."):
                try:
                    payload = {"participants": selected_teammates}
                    if time_win_input.strip():
                        payload["time_window"] = time_win_input.strip()
                    res = requests.post(f"{BACKEND_URL}/negotiate", json=payload, timeout=30)
                    if res.status_code == 200:
                        st.session_state.neg_result = res.json()
                    else:
                        st.error(f"Negotiation error: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    if "neg_result" in st.session_state:
        neg = st.session_state.neg_result
        final_slot = neg.get("final_slot")
        rounds = neg.get("rounds", 0)

        if final_slot:
            st.success(f"Agreed Study Slot: **{final_slot}** (Resolved in {rounds} round(s))")
        else:
            st.warning("No complete consensus reached. Review log entries below.")

        st.markdown("##### Negotiation Log")
        for log in neg.get("transcript", []):
            agent = html.escape(str(log.get("agent", "")))
            message = html.escape(str(log.get("message", "")))
            rnd = log.get("round", 1)
            msg_type = log.get("type", "")

            item_class = "log-card-final" if msg_type == "finalized" else ("log-card-teammate" if "Teammate" in agent else "log-card")
            st.html(f"""
            <div class="log-card {item_class}">
                <strong>[Round {rnd}] {agent}:</strong> {message}
            </div>
            """)

# ══════════════════════════════════════════════════════════
#  TAB 4 — DATA UPLOAD
# ══════════════════════════════════════════════════════════
with tab_upload:
    st.html("""
    <div class="page-title">VTOP Timetable & Data Upload</div>
    <div class="page-sub">Upload parsed timetable JSON or view CLI extraction instructions.</div>
    """)

    col_u1, col_u2 = st.columns(2)
    with col_u1:
        st.markdown("##### File Upload Form")
        target_reg = st.text_input("Registration No.", value="26BLC1265", key="upload_reg_no")
        tt_file = st.file_uploader("Upload Timetable (PDF, MHTML, or JSON)", type=["json", "pdf", "mht", "mhtml"], key="tt_file_uploader")

        if st.button("Upload Timetable Data", width="stretch"):
            if not tt_file or not target_reg.strip():
                st.warning("Provide both Registration Number and file.")
            else:
                try:
                    mime = "application/pdf" if tt_file.name.endswith(".pdf") else ("message/rfc822" if tt_file.name.endswith((".mht", ".mhtml")) else "application/json")
                    files = {"file": (tt_file.name, tt_file.getvalue(), mime)}
                    data = {"reg_no": target_reg.strip()}
                    res = requests.post(f"{BACKEND_URL}/upload/timetable", data=data, files=files, timeout=30)
                    if res.status_code == 200:
                        st.success(f"Successfully uploaded & parsed data for {target_reg.upper()}")
                        st.session_state["selected_reg_no"] = target_reg.upper()
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {res.text}")
                except Exception as e:
                    st.error(f"Upload error: {e}")

    with col_u2:
        st.markdown("##### CLI Extraction Instructions")
        st.code("""
# PDF Extraction Command
python extract_timetable.py --input data/Time_table.pdf --student_id 26BEC1185 --out data/students/26BEC1185/timetable.json

# MHTML Web Export Command
python extract_timetable.py --input "data/VIT Chennai - VTOP (1) (1).mht" --student_id 26BLC1265 --out data/students/26BLC1265/timetable.json
        """, language="bash")

# ══════════════════════════════════════════════════════════
#  TAB 5 — ASSISTANT CHAT
# ══════════════════════════════════════════════════════════
with tab_chat:
    st.html(f"""
    <div class="page-title">Campus Assistant Chat</div>
    <div class="page-sub">Query schedule details or request assistance for <strong>{html.escape(st.session_state["selected_reg_no"])}</strong>.</div>
    """)

    tone_sel = st.selectbox("Persona Tone", ["formal", "casual", "concise"])

    st.markdown("##### Quick Demo Prompts")
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    preset_prompt = None
    with c_btn1:
        if st.button("Draft Missed Lab Email", width="stretch"):
            preset_prompt = "Draft a formal email to my professor explaining I missed BACSE101 lab due to illness and requesting a make-up slot."
    with c_btn2:
        if st.button("Draft Teammate Message", width="stretch"):
            preset_prompt = "Draft a WhatsApp message to my project teammates proposing a study session on Wednesday 18:00 - 20:00."
    with c_btn3:
        if st.button("Summarize Daily Agenda", width="stretch"):
            preset_prompt = "Summarize my core class schedule, mess menu, and upcoming deadlines for today."

    st.markdown("---")

    for msg in st.session_state.messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        with st.chat_message(role):
            st.markdown(content)

    chat_input_val = st.chat_input("Ask a question about your timetable or deadlines...")
    chat_prompt = preset_prompt or chat_input_val
    if chat_prompt:
        st.session_state.messages.append({"role": "user", "content": chat_prompt})
        with st.chat_message("user"):
            st.markdown(chat_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processing request..."):
                try:
                    history_payload = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                    ]
                    res = requests.post(
                        f"{BACKEND_URL}/chat",
                        json={
                            "text": chat_prompt,
                            "tone": tone_sel,
                            "history": history_payload,
                            "student_id": st.session_state["selected_reg_no"]
                        },
                        timeout=30
                    )
                    if res.status_code == 200:
                        data = res.json()
                        if "error" in data:
                            st.error(f"Error: {data['error']}")
                        else:
                            ai_resp = data.get("response", "")
                            st.markdown(ai_resp)
                            st.session_state.messages.append({"role": "assistant", "content": ai_resp})
                    else:
                        st.error(f"Backend error: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    if st.session_state.messages:
        if st.button("Clear Chat History", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()
