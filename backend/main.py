"""
FastAPI application entrypoint.
Registers middleware, routers, lifespan events, and exception handlers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import get_settings
from db.session import create_tables
from services.inference import load_champion_model

settings = get_settings()


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables + load ML model. Shutdown: nothing to clean."""
    print("🚀 Starting up...")
    await create_tables()
    load_champion_model()
    yield
    print("👋 Shutting down...")


# ── App factory ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Student Performance & Dropout Risk Prediction API",
    description="AI-powered system to predict student performance and dropout risk.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Pass through Starlette/FastAPI HTTPExceptions
    if isinstance(exc, (StarletteHTTPException, RequestValidationError)):
        raise exc
    
    # Log the full traceback for everything else
    import traceback
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc),
            "status_code": 500,
        },
    )


# ── Routers ────────────────────────────────────────────────────────────────────
from api.v1 import auth, model, predict, students, upload  # noqa: E402

API_PREFIX = "/api/v1"
app.include_router(auth.router,     prefix=API_PREFIX)
app.include_router(predict.router,  prefix=API_PREFIX)
app.include_router(students.router, prefix=API_PREFIX)
app.include_router(upload.router,   prefix=API_PREFIX)
app.include_router(model.router,    prefix=API_PREFIX)


# ── Health Check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "version": "1.0.0"}
