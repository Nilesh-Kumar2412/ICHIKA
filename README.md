# Project Ichika — Campus Copilot

> **Autonomous On-Device Academic Planner for VIT Chennai Students**  
> Powered by Gemma 4 (12B QAT) • 100% Local Privacy • Zero Cloud Dependencies

[![License: MIT](https://img.shields.io/badge/License-MIT-amber.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.60%2B-red.svg)](https://streamlit.io/)
[![Gemma 4](https://img.shields.io/badge/LLM-Gemma%204%2012B-purple.svg)](https://ai.google.dev/gemma)
[![Tests: Passing](https://img.shields.io/badge/Tests-25%2F25%20Passing-brightgreen.svg)](backend/tests/)

---

## 💡 Overview

**Campus Copilot (ICHIKA)** is an intelligent, autonomous academic scheduling assistant engineered specifically for students at **Vellore Institute of Technology (VIT), Chennai**. 

It parses complex student timetables (PDFs and MHTML VTOP web exports), integrates mess menus, campus events, and assignment deadlines, and provides real-time intelligent replanning and multi-agent group study coordination—all running locally on-device.

---

## ✨ Core Autonomous Agents

### 1. 📅 Academic Planner Agent
- **Inputs**: VTOP timetables, assignment deadlines, mess schedules, and campus events.
- **Autonomous Replanning**: High-visibility autonomy demo. Reporting a missed class (e.g., *"I missed BACSE101 Python Lab"*) visually tags the original item as `[MISSED]` in grey and dynamically re-allocates a `REPLANNED` study slot into open evening windows without overlapping core classes or meals.
- **Drafting Messages & Reminders**: 1-click prompt triggers for drafting formal emails to faculty regarding missed labs or reminder messages to teammates.

### 2. 🤝 Multi-Agent Study Group Coordinator
- **Multi-Agent Negotiation Protocol**: Autonomous agents representing each teammate (`26BLC1001`, `26BLC1002`, `26BLC1003`) evaluate proposed study windows against their availability and preferences over up to 3 rounds.
- **Visible Negotiation Logs**: Real-time, color-coded negotiation logs showing each agent accepting, proposing alternatives, and reaching final coordinator consensus.

### 3. 🍱 Campus Life Concierge Agent
- **Unified Daily Agenda**: Merges mess menus (`mess_menu.json`), campus club events (`events.json`), VTOP timetables, and assignment deadlines into a single high-contrast weekly schedule.
- **Persona Tone Customization**: Toggle between `formal`, `casual`, or `concise` assistant personas.

---

## 🌐 Backend REST API Endpoints

| Method | Endpoint | Description | Query / Body Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | System health check & active student list | None |
| `GET` | `/students` | List registered active student IDs | None |
| `GET` | `/plan` | Generate weekly schedule for student | `student_id` (e.g. `26BEC1185`) |
| `POST` | `/plan` | Generate weekly schedule via JSON body | `{"student_id": "26BEC1185"}` |
| `POST` | `/replan` | Autonomous rescheduling for missed items | `{"student_id": "...", "missed_items": [...]}` |
| `POST` | `/negotiate` | Multi-agent group study coordination | `{"participants": [...], "time_window": "..."}` |
| `POST` | `/timetable/extract` | Extract VTOP PDF or MHTML to JSON | Multipart file or `{"student_id": "..."}` |
| `POST` | `/chat` | Interactive assistant query & email drafting | `{"text": "...", "tone": "formal"}` |

---

## 🛠️ Architecture

```mermaid
graph TD
    A[Student VTOP PDF / MHTML] -->|CLI / API Upload| B[extract_timetable.py Parser]
    B --> C[(data/students/<REG_NO>/timetable.json)]
    
    D[Streamlit Frontend App :8501] -->|REST Calls| E[FastAPI Backend Server :8000]
    
    E --> F[Planner Agent]
    E --> G[Replanner Agent]
    E --> H[Multi-Agent Negotiator]
    
    F -->|2.0s Fast Timeout| I[LM Studio / Groq API (Gemma 4)]
    G -->|Fallback| J[Deterministic Heuristic Engine]
    H -->|Consensus Protocol| K[Teammate Calendar Schedules]
```

---

## 🚀 Quick Setup & Run

### Prerequisites
- Python 3.9 or higher
- (Optional) [LM Studio](https://lmstudio.ai/) running locally on `http://localhost:1234/v1` with `google/gemma-4-12b-qat` loaded.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Nilesh-Kumar2412/ICHIKA.git
   cd ICHIKA
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

3. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   ```

---

## 🏃 Running the Application

### 1. Start the Backend API Server
```bash
python backend/main.py
```
*API running at `http://localhost:8000` (Swagger docs available at `http://localhost:8000/docs`).*

### 2. Start the Frontend Web UI
```bash
streamlit run frontend/app.py --server.port 8501
```
*UI running at `http://localhost:8501`.*

---

## 🧪 Test Suite Execution

Run the complete 25-test suite covering API endpoints, empirical replanning, multi-agent negotiation caps, and parser isolation:

```bash
python -m pytest backend/tests/ -v
```

---

## 📁 Repository Structure

```text
ICHIKA/
├── backend/
│   ├── main.py               # FastAPI backend routes (/plan, /replan, /negotiate, etc.)
│   ├── agents/               # Autonomous agent implementations
│   │   ├── planner.py        # Weekly agenda generation agent
│   │   ├── replanner.py      # Rescheduling & slot reallocation agent
│   │   └── negotiator.py     # Multi-agent negotiation agent
│   ├── tests/                # Comprehensive Pytest test suite (25 tests)
│   └── requirements.txt      # Backend Python dependencies
├── frontend/
│   ├── app.py                # Streamlit high-contrast UI
│   ├── .streamlit/           # Custom Streamlit config & theme settings
│   └── requirements.txt      # Frontend dependencies
├── data/
│   ├── shared/               # Shared events, mess menu, & teammate calendars
│   └── students/             # Isolated per-student timetable profiles
├── extract_timetable.py      # CLI extraction script for PDF & MHTML parsing
├── .env.example              # Environment variables template
├── LICENSE                   # MIT License
└── README.md                 # Technical documentation
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
