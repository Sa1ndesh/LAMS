# National Land Acquisition & Management System (LAMS) - Backend API

## 1. Overview
The **LAMS Backend** is a high-performance RESTful API service built with **Python 3.11+**, **FastAPI**, **Pydantic v2**, and **SQLAlchemy 2.0 (AsyncPG)**.

---

## 2. AI Decision Support Engine Architecture (Phase 12)

> **Important Disclosure:** This is an explainable rule-based decision-support system, not a trained black-box machine-learning model.

### Risk Scoring Formula (0 to 100 Points)
The risk scoring model evaluates project health dynamically across 6 weighted operational dimensions (maximum total 100 points):

1. **Milestone Schedule Adherence (Max 30 pts):** Evaluates max delay days and overdue milestones.
   - Delay ≥ 60 days: `+30 pts` (CRITICAL)
   - Delay 31–59 days: `+22 pts` (HIGH)
   - Delay 8–30 days: `+14 pts` (MEDIUM)
   - Delay 1–7 days / Overdue: `+7 pts` (LOW)
2. **Declared Project Health Status (Max 20 pts):**
   - Status `CRITICAL`: `+20 pts`
   - Status `DELAYED`: `+12 pts`
   - Status `ON_TRACK`: `0 pts`
3. **Land Acquisition Progress Lag (Max 15 pts):**
   - Advanced stage with land completion < 50%: `+15 pts`
   - Mid stage with land completion < 30%: `+10 pts`
   - Overall land completion < 15%: `+6 pts`
4. **Compensation Disbursement Bottlenecks (Max 15 pts):**
   - Pending approved compensation > ₹1 Cr: `+15 pts`
   - Disbursement rate < 50%: `+10 pts`
   - Assessed but unapproved: `+6 pts`
5. **Workflow & Administrative Approvals (Max 10 pts):**
   - Rejected stage transition requests: `+10 pts`
   - Pending approval requests: `+5 pts`
6. **Rehabilitation & Resettlement (R&R) Progress (Max 10 pts):**
   - Displaced families with 0 resettled: `+10 pts`
   - Resettlement completion < 50%: `+6 pts`

### Risk Level Thresholds
- **0 – 24 pts:** `LOW`
- **25 – 49 pts:** `MEDIUM`
- **50 – 74 pts:** `HIGH`
- **75 – 100 pts:** `CRITICAL`

### Confidence Score Calculation (0.0 to 1.0)
Calculated dynamically based on data completeness:
- `0.40` base rating
- `+0.15` for milestone record presence
- `+0.15` for land footprint data
- `+0.15` for compensation assessment data
- `+0.13` for affected family census data
- Maximum confidence capped at `0.98`.

---

## 3. Setup & Execution Instructions

### 3.1 Environment Setup
```bash
cd backend
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

### 3.2 Install Dependencies
```bash
pip install -r requirements.txt
```

### 3.3 Run Development Server
```bash
python -m uvicorn app.main:app --reload --port 8000
```

---

## 4. API Endpoints & Verification
- **Root Status:** `GET http://localhost:8000/`
- **Health Check:** `GET http://localhost:8000/api/health`
- **AI Risk Analysis:** `GET http://localhost:8000/api/ai/projects/{id}/risk`
- **AI Project Insights:** `GET http://localhost:8000/api/ai/projects/{id}/insights`
- **AI National Overview:** `GET http://localhost:8000/api/ai/overview`
- **AI High Risk Ranking:** `GET http://localhost:8000/api/ai/projects/high-risk`
- **Swagger Interactive Docs:** `GET http://localhost:8000/docs`
- **ReDoc API Documentation:** `GET http://localhost:8000/redoc`

---

## 5. Running Automated Tests
```bash
python -m pytest
```
