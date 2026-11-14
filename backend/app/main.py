import hmac
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .config import ACCESS_CODE, CORS_ORIGINS, STATIC_DIR
from .routers import catalog, play, profiles

app = FastAPI(title="Révisions 10VP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def access_code(request: Request, call_next):
    """With ACCESS_CODE set, every API call needs the X-Access-Code header (the app shell stays public)."""
    path = request.url.path
    if ACCESS_CODE and path.startswith("/api/") and path not in ("/api/health", "/api/access"):
        given = request.headers.get("x-access-code", "").strip()
        if not hmac.compare_digest(given.lower(), ACCESS_CODE.lower()):
            return JSONResponse({"detail": "access_code"}, status_code=403)
    return await call_next(request)


app.include_router(catalog.router)
app.include_router(profiles.router)
app.include_router(play.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/access")
def access(request: Request):
    """Does this server need an access code, and is the one sent right?"""
    given = request.headers.get("x-access-code", "").strip()
    return {"required": bool(ACCESS_CODE),
            "ok": not ACCESS_CODE or hmac.compare_digest(given.lower(), ACCESS_CODE.lower())}


# Production: serve the built frontend; unknown paths return index.html (client-side routes)
if STATIC_DIR and Path(STATIC_DIR, "index.html").exists():
    static = Path(STATIC_DIR).resolve()

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        file = (static / path).resolve()
        if path and file.is_file() and static in file.parents:
            # hashed asset names never change: cache them; index.html must always be fresh
            cache = "public, max-age=31536000, immutable" if path.startswith("assets/") else "no-cache"
            return FileResponse(file, headers={"Cache-Control": cache})
        return FileResponse(static / "index.html", headers={"Cache-Control": "no-cache"})
