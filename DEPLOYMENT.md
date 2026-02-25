# Deployment Guide: Student Performance & Dropout Risk Prediction System

This guide outlines the steps to deploy the Intelligent Student Performance & Dropout Risk Prediction System to a production environment.

## 🏗️ Production Architecture

The system is designed to be deployed as a multi-container application using **Docker** and **Docker Compose**.

- **Backend**: FastAPI running on Gunicorn with Uvicorn workers.
- **Frontend**: React (Vite) built into static files and served by Nginx.
- **Database**: PostgreSQL (recommened for production instead of SQLite).
- **ML Artifacts**: Model binaries and scalers are bundled with the backend container.

---

## 🐋 Containerization (Docker)

### 1. Backend Dockerfile
Create a `backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn uvicorn

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with Gunicorn
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### 2. Frontend Dockerfile
Create a `frontend/Dockerfile`:
```dockerfile
# Build stage
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 🚀 Deployment Steps

### Step 1: Prepare Environment Variables
Configure your production `.env` file for the backend:
```env
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/edupredict
SECRET_KEY=your_production_secret_key_here
CORS_ORIGINS=https://your-domain.com
```

### Step 2: Orchestrate with Docker Compose
Create a `docker-compose.yml` in the project root:
```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: edupredict
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@db:5432/edupredict
      - SECRET_KEY=prod_secret
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

### Step 3: Run the System
```bash
docker-compose up -d --build
```

---

## 🌐 Recommended Hosting Options

1. **Managed Containers**: Render, Railway, or Google Cloud Run.
2. **Virtual Private Servers (VPS)**: DigitalOcean, Linode, or AWS EC2 (requires manual Docker setup).
3. **PaaS**: Heroku (supports Docker deployments).

> [!IMPORTANT]
> Ensure that `ml/models/` artifacts (champion_model.pkl, etc.) are included in your git repository or part of your CI/CD horizontal scaling strategy.
