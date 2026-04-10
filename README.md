<div align="center">
  <h1>FRAUDA — AI Trust Intelligence</h1>
  <p><strong>"Think Before You Act"</strong></p>
  <p>A web-based AI deepfake video detection system for social media users in Malaysia.</p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.11-blue" />
    <img src="https://img.shields.io/badge/React-18-61DAFB" />
    <img src="https://img.shields.io/badge/Flask-3.0-black" />
    <img src="https://img.shields.io/badge/Supabase-green" />
    <img src="https://img.shields.io/badge/Hackaton_2026-League_4-orange" />
  </p>
</div>

---

## What is Frauda?

Frauda analyzes videos from social media and detects whether they are likely AI-generated or deepfakes.
It uses a **4-signal detection engine** examining motion, facial stability, lighting, and visual artifacts —
then returns an explainable risk score with actionable recommendations.

Built for **Hackaton 2026** — League 4, Team AF (Aurea Fabrica).

---

## Features

- Upload a video or paste a social media link
- 4-signal AI detection: brightness, motion, blur, facial stability
- AI likelihood score (0–100%) with confidence level
- Risk classification: Low / Moderate / High
- Plain-language explanation of detection results
- Actionable next steps (verify, do not share, report)
- Downloadable analysis report

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Tailwind CSS |
| Backend | Python 3.11 + Flask + Flask-CORS |
| Computer Vision | OpenCV + NumPy |
| Database / Storage | Supabase |
| Deployment | Railway (backend) + Vercel (frontend) |

---

## Project Structure

```
AI SCAM DETECTOR/
├── backend/
│   ├── ml/
│   │   ├── models/          # Download separately — see ML Models section below
│   │   └── evaluate.py
│   ├── routes/              # Flask API routes
│   ├── services/            # Detection logic (4-signal engine)
│   ├── tmp_videos/          # Temp storage, auto-deleted after analysis
│   ├── app.py               # Flask entry point
│   ├── debug_signals.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.example
├── sample video/
├── .gitignore
└── README.md
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Free Supabase account → https://supabase.com

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/YOURUSERNAME/frauda.git
cd frauda
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
# Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Open .env and fill in your Supabase credentials
```

### 3. Frontend Setup

```bash
cd frontend
npm install

cp .env.example .env
# Open .env and fill in your Supabase credentials
```

### 4. ML Models

Models are not included due to file size. Download and place in `backend/ml/models/`:

```
backend/ml/models/
├── FF++_c23.pth
└── FF++_c40.pth
```

Download link: [https://drive.google.com/drive/folders/1GNtk3hLq6sUGZCGx8fFttvyNYH8nrQS8]

### 5. Run Locally

Start backend first:
```bash
cd backend
source venv/bin/activate
python app.py
# Running on http://localhost:5000
```

Then start frontend:
```bash
cd frontend
npm run dev
# Running on http://localhost:5173
```

---

## Supabase Setup

Run this SQL in your Supabase SQL editor:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    media_type TEXT DEFAULT 'video',
    file_name TEXT,
    source_url TEXT,
    content_type TEXT DEFAULT 'general',
    risk_score INTEGER NOT NULL,
    trust_score INTEGER NOT NULL,
    confidence INTEGER NOT NULL,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'moderate', 'high')),
    risk_label TEXT NOT NULL,
    analysis_time DECIMAL(6,2),
    frames_analyzed INTEGER,
    faces_detected INTEGER,
    signal_breakdown JSONB,
    detection_metrics JSONB,
    explainable_findings TEXT[],
    detection_timeline JSONB,
    risk_impact JSONB,
    what_to_do JSONB
);

CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for demo" ON analyses FOR ALL USING (true);
```

---

## Detection Engine

| Signal | What It Checks | Threshold |
|--------|---------------|-----------|
| Signal 1 — Brightness | Frame brightness std deviation | std > 40 |
| Signal 2 — Temporal | Frame-to-frame pixel change | diff > 15 or < 2 |
| Signal 3 — Blur | Laplacian variance (skin texture) | variance < 100 |
| Signal 4 — Facial Stability | Face count variation across frames | std > 0.5 |
| Signal 5 — XceptionNet | Deep learning face crop classification | Optional |

**Score Formula**: `AI_SCORE = signals_triggered × 25` (0–100)

**Risk Levels**: 0–30 Low · 31–60 Moderate · 61–100 High

---

## ML Evaluation

```bash
cd backend
python ml/evaluate.py
```

Place test videos in:
- `backend/ml/test_videos/real/` — authentic videos (label = real)
- `backend/ml/test_videos/fake/` — deepfake videos (label = fake)

---

## Deployment

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| Railway | Backend (Flask) | Yes |
| Vercel | Frontend (React) | Yes |
| Supabase | Database + Storage | Yes |

---

## Disclaimer

This tool is for informational purposes only. AI-based detection has limitations and should be used alongside human verification. Always verify through official sources.

---

*Built with by Team AF (Aurea Fabrica) — Hackaton 2026, League 4*
