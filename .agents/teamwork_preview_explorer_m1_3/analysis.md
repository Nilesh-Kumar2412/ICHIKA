# Comprehensive Frontend & UI Styling Analysis: `frontend/app.py`

## Executive Summary
The Streamlit frontend (`frontend/app.py`) and configuration (`frontend/.streamlit/config.toml`) implement a clean, institutional interface for VIT Chennai's Campus Copilot (ICHIKA). The theme strictly adheres to Prussian Blue (`#002147`), Gold (`#FFA500`), and Charcoal text (`#0F172A`) on light backgrounds with explicit card borders and high-contrast badges. Multi-student profile selection (`26BEC1185`, `26BLC1265`), smart replanner controls, and negotiation transcript rendering are fully functional. Minor areas for improvement include removing emoji clutter (`🎓`) and non-academic AI persona tones (`unhinged`, `girly`, `manly`), and improving UX when "+ Upload New Profile" is selected.

---

## 1. Visual Layout & Institutional Theme Implementation

### 1.1 Configuration (`frontend/.streamlit/config.toml`)
The Streamlit global theme is defined as follows:
```toml
[theme]
primaryColor = "#002147"
backgroundColor = "#F8FAFC"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#0F172A"
font = "sans serif"
```
- **Primary Color (`#002147`)**: Official Prussian Blue.
- **Background Color (`#F8FAFC`)**: Light slate background providing soft contrast.
- **Secondary Background (`#FFFFFF`)**: Pure white container background.
- **Text Color (`#0F172A`)**: Deep charcoal for maximum readability.

### 1.2 Inline CSS Overrides (`frontend/app.py`, Lines 37–203)
The custom CSS strictly enforces the institutional identity:
- **Sidebar Container** (`lines 41–65`):
  ```css
  section[data-testid="stSidebar"] {
      background-color: #002147 !important;
      border-right: 2px solid #CBD5E1 !important;
  }
  section[data-testid="stSidebar"] label {
      color: #FFA500 !important; /* Gold */
      font-weight: 700 !important;
  }
  ```
- **Header Navbar** (`lines 68–100`):
  ```css
  .vtop-navbar {
      background-color: #002147;
      border-bottom: 3px solid #FFA500;
      padding: 16px 24px;
  }
  .vtop-title { color: #FFFFFF !important; }
  .vtop-sub { color: #FFA500 !important; }
  ```
- **Day Header Strips** (`lines 170–186`):
  ```css
  .day-strip {
      background-color: #002147;
      color: #FFFFFF !important;
  }
  ```

---

## 2. High-Contrast Schedule Tables, Dropdowns, & Explicit Borders

### 2.1 Schedule Tables (`frontend/app.py`, Lines 114–169 & 294–310)
- **Schedule Card Structure**:
  ```css
  .schedule-item {
      background-color: #FFFFFF;
      border: 1px solid #E2E8F0; /* Explicit 1px border */
      border-left: 4px solid #002147; /* Prussian Blue default accent */
      padding: 12px 16px;
  }
  ```
- **High-Contrast Type Tags (`.schedule-type-tag`)**:
  - `CLASS`: `#EFF6FF` background, `#1D4ED8` text, `#BFDBFE` explicit border.
  - `MEAL`: `#F0FDF4` background, `#15803D` text, `#BBF7D0` explicit border.
  - `DEADLINE`: `#FEF2F2` background, `#B91C1C` text, `#FECACA` explicit border.
  - `EVENT`: `#FFFBEB` background, `#B45309` text, `#FDE68A` explicit border.
  - `STUDY`: `#F5F3FF` background, `#6D28D9` text, `#DDD6FE` explicit border.
  - `REPLANNED`: `#F0F9FF` background, `#0369A1` text, `#BAE6FD` explicit border.
  - `MISSED`: `#F8FAFC` background, `#64748B` text, `#E2E8F0` explicit border.

### 2.2 Dropdown Options & Control Elements
- **Sidebar Controls**:
  - Sidebar inputs are styled with dark background (`#001530`), white text (`#FFFFFF`), and explicit border (`1px solid #334155`).
  - Selectbox option text inherits global `textColor: #0F172A` on `#FFFFFF` popover background, ensuring no invisible or low-contrast text.
- **Explicit Borders Throughout**:
  - Sidebar right border: `border-right: 2px solid #CBD5E1 !important;`
  - Navbar bottom border: `border-bottom: 3px solid #FFA500;`
  - Schedule item cards: `border: 1px solid #E2E8F0; border-left: 4px solid <color>;`
  - Negotiation log cards: `border: 1px solid #E2E8F0; border-left: 4px solid <color>;`

---

## 3. Review of Decorative AI Buzzwords & Emoji Clutter

| Item Location | Content Observed | Classification | Flag / Recommendation |
|---------------|------------------|----------------|-----------------------|
| `frontend/app.py:16` | `page_icon="🎓"` | Emoji Clutter | **Flagged for Removal**: Remove emoji or replace with standard university logo path. |
| `frontend/app.py:239` | `• Model Engine: Gemma 4` | Decorative AI Mention | **Optional Flag**: Can be simplified to "Engine: Active" to maintain strictly institutional phrasing. |
| `frontend/app.py:531` | `selectbox("Persona Tone", ["formal", "casual", "powerful", "unhinged", "girly", "manly"])` | AI Gimmick / Buzzword Fluff | **Flagged for Removal**: Persona options like `"unhinged"`, `"girly"`, `"manly"` are AI gimmick clutter. Restrict choices to academic/formal tones or eliminate tone selection. |

---

## 4. Multi-Student Profile Support

- **Implementation (`frontend/app.py`, Lines 215–234)**:
  ```python
  available_students = ["26BEC1185", "26BLC1265"]
  try:
      res = requests.get(f"{BACKEND_URL}/students", timeout=2)
      if res.status_code == 200:
          server_students = res.json().get("students", [])
          if server_students:
              available_students = server_students
  except Exception:
      pass

  reg_choice = st.selectbox(
      "Select Active Student",
      options=available_students + ["+ Upload New Profile"],
      index=...
  )
  ```
- **Verification**:
  - Dynamically retrieves registration numbers from `/students` endpoint.
  - Supports switching between `26BEC1185` and `26BLC1265`.
  - State updates `st.session_state["selected_reg_no"]` globally, which propagates to:
    - Navbar active student badge (`line 274`)
    - Tab 1 agenda fetch (`POST /plan?reg_no=...`)
    - Tab 4 timetable upload pre-fill
    - Tab 5 chat payload
- **UX Recommendation**: If user selects `"+ Upload New Profile"`, provide explicit instructions or auto-navigate to Tab 4 ("Data Upload").

---

## 5. Replanner Controls & Negotiation Transcript Rendering

### 5.1 Replanner Controls (`frontend/app.py`, Lines 371–423)
- **Controls**:
  - Input field: `st.text_input("Missed Course / Lab / Activity", placeholder="e.g. BACSE101 Python Lab")`
  - Action button: `st.button("Reschedule Item", type="primary", width="stretch")`
- **Execution & Rendering**:
  - On click, posts payload `{"current_plan": st.session_state.plan_data or [], "missed_item": missed_input}` to `/replan`.
  - Renders daily expanders displaying updated plan.
  - Re-allocated items are rendered with `schedule-item-replanned` styling (sky blue accent border `#0284C7`, badge `REPLANNED`).

### 5.2 Negotiation Transcript Rendering (`frontend/app.py`, Lines 425–480)
- **Controls**:
  - Multiselect: `st.multiselect("Select Teammates", ["Aarav", "Ananya", "Rohan"], default=["Aarav", "Ananya", "Rohan"])`
  - Action button: `st.button("Start Coordination", type="primary", width="stretch")`
- **Transcript Rendering**:
  - Iterates through `neg.get("transcript", [])`.
  - Each log entry is rendered as a custom `.log-card`:
    - `log-card`: White card with Prussian Blue `#002147` left border for main coordinator messages.
    - `log-card-teammate`: Gold `#F59E0B` left border for teammate responses.
    - `log-card-final`: Light green background `#F0FDF4` with `#10B981` border for consensus final agreement.
  - Final consensus banner displayed via `st.success(...)`.

---

## 6. Summary of Proposed UI Code Cleanups

1. **Remove Page Icon Emoji**:
   - `frontend/app.py:16`: Change `page_icon="🎓"` to `page_icon=None` or university logo asset.
2. **Clean Up Persona Tone Dropdown**:
   - `frontend/app.py:531`: Replace `["formal", "casual", "powerful", "unhinged", "girly", "manly"]` with `["formal", "academic", "concise"]`.
3. **Enhance "+ Upload New Profile" Selectbox Handling**:
   - Add notification advising user to switch to Tab 4 ("Data Upload") when `"+ Upload New Profile"` is selected.
