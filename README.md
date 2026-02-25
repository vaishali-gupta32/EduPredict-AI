# 🎓 Intelligent Student Performance & Dropout Risk Prediction System

An end-to-end AI/ML platform that predicts student academic performance and dropout risk using ensemble ML models, exposing results via a FastAPI backend and React admin dashboard.

---

## Screenshots

<img width="1915" height="907" alt="image" src="https://github.com/user-attachments/assets/f2062d2f-5cf5-42a0-90a7-f11412cc6c56" />

## 🏗️ Architecture

```
├── backend/          # FastAPI Python backend
│   ├── api/v1/       # Route handlers (auth, predict, students, upload, model)
│   ├── core/         # Config, security, dependencies
│   ├── db/           # SQLAlchemy session, seed script
│   ├── ml/           # Training, evaluation, models/
│   ├── models/       # ORM models + Pydantic schemas
│   ├── services/     # Preprocessing, inference, intervention, ingestion
│   └── main.py       # FastAPI entrypoint
├── frontend/         # React + Vite + TailwindCSS dashboard
│   └── src/
│       ├── pages/    # Dashboard, Login, StudentDetail, Upload, ModelHealth
│       ├── components/
│       ├── context/  # AuthContext (JWT)
│       └── api/      # Axios client
├── data/             # Synthetic dataset generator
└── .env              # Local environment variables
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Generate synthetic data & train ML models

```bash
# From project root
python data/generate_dataset.py

# From backend/ directory
python ml/train.py
```

This trains 4 models (Logistic Regression, Random Forest, XGBoost, LightGBM), selects the champion by F1-score, and saves artifacts to `backend/ml/models/`.

### 3. Seed the database

```bash
# From backend/ directory
python db/seed.py
```

Creates two users:
| Email | Password | Role |
|-------|----------|------|
| admin@college.edu | Admin@1234 | admin |
| viewer@college.edu | Viewer@1234 | viewer |

### 4. Start the backend API

```bash
# From backend/ directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 5. Install & start the frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

---

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/login` | Public | Get JWT token |
| GET | `/api/v1/auth/me` | Bearer | Current user profile |
| POST | `/api/v1/predict` | Bearer | Single student prediction |
| POST | `/api/v1/predict/batch` | Bearer | Batch JSON predictions (≤500) |
| GET | `/api/v1/students` | Bearer | Paginated student list with filters |
| GET | `/api/v1/students/{id}` | Bearer | Student detail + history |
| POST | `/api/v1/upload/csv` | Admin | CSV batch upload |
| GET | `/api/v1/model/metrics` | Bearer | Champion model metrics |
| GET | `/health` | Public | Health check |

---

## 🤖 ML Pipeline

- **Models**: Logistic Regression, Random Forest, XGBoost, LightGBM
- **Champion Selection**: Highest F1-score on "At Risk" class
- **Explainability**: SHAP TreeExplainer for top-3 risk factors
- **Drift Detection**: Rule-based (accuracy/AUC < 0.70 threshold)
- **Interventions**: Rule-based mapping to actionable recommendations

### Performance Targets
| Metric | Target |
|--------|--------|
| Accuracy | ≥ 88% |
| ROC-AUC | ≥ 88% |
| F1 (At Risk) | ≥ 82% |

---

## 🛠️ Tech Stack

**Backend**: FastAPI · SQLAlchemy (async) · Pydantic v2 · python-jose · passlib  
**ML**: scikit-learn · XGBoost · LightGBM · SHAP · pandas  
**Database**: SQLite (dev) / PostgreSQL (prod)  
**Frontend**: React 18 · Vite · TailwindCSS · React Query · Recharts · Axios
