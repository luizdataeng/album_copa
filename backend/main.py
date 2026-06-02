from pathlib import Path

import os

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = FastAPI(title="PWA Album Sticker Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UpdatePayload(BaseModel):
    selecao: str
    numero: int
    delta: int


class NewSelectionPayload(BaseModel):
    name: str
    group: str | None = None


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/manifest.json")
def manifest() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "manifest.json")


@app.get("/sw.js")
def service_worker() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "sw.js")


@app.get("/album")
def get_album() -> dict:
    return {"selections": db.fetch_album()}


def require_admin_token(admin_token: str | None = Header(default=None, alias="X-ADMIN-TOKEN")) -> None:
    expected = os.getenv("ADMIN_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_TOKEN not configured",
        )
    if admin_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )


@app.post("/atualizar")
def update_sticker(payload: UpdatePayload) -> dict:
    require_admin_token()
    try:
        quantity = db.update_quantity(payload.selecao, payload.numero, payload.delta)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "selecao": payload.selecao,
        "numero": payload.numero,
        "quantity": quantity,
    }


@app.post("/selecoes/nova")
def create_selection(payload: NewSelectionPayload) -> dict:
    require_admin_token()
    group = payload.group or "Custom"
    changes = db.create_selection(payload.name, group)
    if changes == 0:
        raise HTTPException(status_code=409, detail="Selection already exists")
    return {"created": payload.name, "group": group, "count": changes}


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
