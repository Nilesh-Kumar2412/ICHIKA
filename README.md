# Campus Copilot (ICHIKA)

A high-level logic processor for VIT Chennai students, built with Gemma 4 and designed for autonomous planning.

## Features
- **Planner Agent:** Merges schedules, deadlines, and events.
- **Replanner:** Adjusts plans dynamically based on user feedback.
- **Negotiator:** Multi-agent negotiation for study slots.
- **Local Inference:** Runs entirely on-device using LM Studio.

## Setup & Run

### Prerequisites
- LM Studio installed with Gemma 4 12B QAT model loaded.
- Python 3.9+ installed.

### Installation
1. Clone the repository.
2. Create a `.env` file from `.env.example`.
3. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Install frontend dependencies:
   ```bash
   pip install -r frontend/requirements.txt
   ```

### Running the Application
1. **Start LM Studio:** Ensure the local server is running on `http://localhost:1234/v1`.
2. **Start Backend:**
   ```bash
   cd backend
   python main.py
   ```
3. **Start Frontend:**
   ```bash
   cd frontend
   streamlit run app.py
   ```

## Architecture
- **Backend:** FastAPI (Python)
- **Frontend:** Streamlit
- **Model:** Gemma 4 (Local via LM Studio)
