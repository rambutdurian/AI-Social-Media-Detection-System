**Frauda – AI Trust Intelligence**

Frauda AI Trust Intelligence is a **web-based AI detection system** designed to analyze videos and links from social media platforms (TikTok, YouTube, Facebook, LinkedIn, etc.) to identify **fake news, deepfake videos, job scams, and fraudulent endorsements**.  

Guided by the principle **"Think Before You Act"**, Frauda empowers everyday users to evaluate suspicious content with **explainable AI results** and actionable recommendations.

---

**🚩 Problem Statement**
- Deepfake technology enables highly realistic AI-generated scams that are difficult to detect.
- Malaysia has faced **RM2.4B+ losses** due to online scams (PDRM, 2023–24).
- Current detection tools are enterprise-focused, lack explainability, and perform poorly on real-world social media content.
- Victims span all age groups: younger users fall more frequently, older users suffer higher financial losses.

---

**🎯 Our Solution**
Frauda AI Trust Intelligence provides:
- **Video-based analysis** (upload or paste link).
- **Multi-signal detection**:
  - Brightness consistency  
  - Temporal frame differences  
  - Blur / Laplacian sharpness  
  - Facial stability  
- **Explainable results** in English language.
- **AI likelihood score** (0–100, capped at 95%).
- **Risk classification** (Low / Medium / High).
- **Actionable recommendations** (verify, avoid sharing, report).
- **Downloadable PDF report** for evidence or reporting.

---

**🛠️ Tech Stack**
- **Frontend:** React 18 + TypeScript + Tailwind CSS
- **Backend:** Flask (Python 3.11) + Flask-CORS
- **Processing:** OpenCV + NumPy
- **Analysis:** 4-Signal Multi-Analyzer
- **Storage:** Supabase / Local / S3 (temporary auto-deletion)
- **Deployment:** Dockerized, decoupled client-server architecture

---

**⚙️ Setup Instructions**

**Prerequisites**
- Node.js (for frontend build)
- Python 3.11 (for backend)
- GitHub account (for repo management)
- pip (Python package manager)

**Front-end Setup**
- cd frontend
- npm install
- npm run build
- npm start

**Back-end Setup**
- cd backend
- pip install -r requirements.txt
- python app.py

**How to run**
1. Start backend (Flask API)
- python app.py
- Runs on http://localhost:5000.
   
3. Start frontend (React UI)
- npm start
- Runs on http://localhost:3000.

4. Workflow:
- Open the React UI in the browser.
- Upload a suspicious video or paste a social media link.
- Backend analyzes frames (brightness, motion, blur, facial stability).
- Results returned: AI score, confidence, risk type, explanation.
- Optionally download PDF report.

💡 **Market & Impact**
- Over 80% of Malaysians (~33M users) are active on social media, increasing exposure to manipulated content.
- Frauda fills a gap: existing tools (Jumio, iSEM.ai, Sumsub) focus on enterprise, not public users.
- Revenue model: Freemium + API pricing (RM0.20–0.40 per call), subscription plans for consumers, custom pricing for enterprises/regulators.
  
