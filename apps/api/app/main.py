from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.briefs import router as briefs_router
from app.routes.chat import router as chat_router
from app.routes.config import router as config_router
from app.routes.events import router as events_router

app = FastAPI(title="Overseas Jewelry Strategy Simulator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(briefs_router)
app.include_router(events_router)
app.include_router(chat_router)
app.include_router(config_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
