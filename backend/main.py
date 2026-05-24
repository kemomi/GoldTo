"""
GoldTo Backend — FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from api.routes import router
from config import settings

app = FastAPI(
    title="GoldTo API",
    description="群体智能预测引擎 — Swarm Intelligence Prediction Engine",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "GoldTo",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "llm_model": settings.llm_model_name,
        "llm_configured": settings.llm_api_key != "sk-placeholder",
        "zep_enabled": bool(settings.zep_api_key),
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "llm_mode": "mock" if settings.is_mock else "real",
        "model": settings.llm_model_name,
        "zep_enabled": bool(settings.zep_api_key),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)
