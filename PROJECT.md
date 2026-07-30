# Project: Campus Copilot (ICHIKA) Student Scheduler

## Architecture
- **Backend**: FastAPI / Flask application serving `/plan`, `/replan`, `/negotiate`, `/students`, `/timetable/extract` APIs.
- **Frontend**: Streamlit / Web UI with Prussian Blue (`#002147`), Gold (`#FFA500`), and Charcoal high-contrast theme.
- **CLI Extraction**: `extract_timetable.py` supporting PDF and MHTML VTOP timetable extraction to schema-validated JSON.
- **Agents**: Smart Replanner Agent (merging slots, meal, deadlines, visual miss marking & rescheduling) and Multi-Agent Negotiator (3-round consensus negotiation with Aarav, Ananya, Rohan + transaction log).
- **Data Isolation**: Student-specific JSON configurations in `data/students/<REG_NO>/` (supporting `26BEC1185` and `26BLC1265`).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Architecture & Codebase Exploration | Comprehensive code & requirement audit | None | IN_PROGRESS |
| 2 | Data Prep & CLI Timetable Parsing | VTOP PDF/MHTML CLI script & isolated JSON configs | M1 | PLANNED |
| 3 | Backend API & Agents | Smart Replanner & Multi-Agent Negotiator API | M2 | PLANNED |
| 4 | Visual Layout & High Contrast UI | Prussian Blue/Gold/Charcoal UI, tables, dropdowns | M3 | PLANNED |
| 5 | E2E Testing & Forensic Audit | Verification of 100% test pass, UI layout & non-cheating audit | M4 | PLANNED |

## Code Layout
- `backend/main.py`: Main API server
- `backend/agents/`: Replanner & Negotiator agent logic
- `frontend/app.py`: Streamlit frontend application & UI components
- `extract_timetable.py`: CLI script for PDF & MHTML parsing
- `data/students/`: Isolated student directories (`26BEC1185`, `26BLC1265`)

## Interface Contracts
- `POST /plan`: Takes `student_id`, returns merged weekly agenda JSON.
- `POST /replan`: Takes `student_id`, `missed_items`, returns updated weekly agenda with visual flags and rescheduled tasks.
- `POST /negotiate`: Takes `student_id`, `participants`, `time_window`, returns consensus slot & max 3 round transaction log.
- CLI: `python extract_timetable.py --input <file> --student_id <id> --output <path>` -> validates JSON output schema.
