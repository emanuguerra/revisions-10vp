from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .routers import catalog, play, profiles

app = FastAPI(title="Révisions 10VP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(profiles.router)
app.include_router(play.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
