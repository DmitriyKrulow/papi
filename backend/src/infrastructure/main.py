# src/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse  # ← ДОБАВЛЕНО
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import psycopg2
import os
import asyncio

from backend.src.presentation.http.routers.assets import router as assets
from backend.src.presentation.http.routers.users import router as users
from backend.src.presentation.http.routers.auth import router as auth
from backend.src.presentation.http.routers.repairs import router as repairs
from backend.src.presentation.http.routers.documents import router as documents
from backend.src.presentation.http.routers.asset_photos import router as asset_photos
from backend.src.presentation.http.routers.reports import router as reports
from backend.src.presentation.http.routers.admin import router as admin
from backend.src.use_cases.admin.initial_setup import ensure_initial_admin

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# ========== Создание приложения ==========
app = FastAPI(
    title="PAPI - Управление активами",
    description="Система для управления основными средствами и активами",
    version="1.0.0",
)


@app.on_event("startup")
async def on_startup():
    """Инициализация при старте: создание начального администратора"""
    try:
        await ensure_initial_admin()
    except Exception as e:
        print(f"Warning: Failed to create initial admin: {e}")

# ========== Настройка CORS (для React-фронтенда) ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite (React)
        "http://localhost:3000",  # Альтернативный порт
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ========== API Роутеры (ваша бизнес-логика) ==========
app.include_router(assets, prefix="/api/assets", tags=["assets"])
app.include_router(users, prefix="/api/users", tags=["users"])
app.include_router(auth, prefix="/api/auth", tags=["auth"])
app.include_router(admin, prefix="/api", tags=["admin"])
app.include_router(repairs, prefix="/api/repairs", tags=["repairs"])
app.include_router(documents, prefix="/api/documents", tags=["documents"])
app.include_router(asset_photos, prefix="/api", tags=["asset-photos"])
app.include_router(reports, prefix="/api/reports", tags=["reports"])

# ========== Проверка БД ==========
@app.get("/api/db-check")
def check_db_connection():
    """Проверка подключения к базе данных"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {"status": "disconnected", "error": "DATABASE_URL not set"}
        conn = psycopg2.connect(database_url)
        conn.close()
        return {"status": "connected", "database": "papiDB"}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}

# ========== Веб-страницы (для админки/дашборда) ==========
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    """Главная страница"""
    return templates.TemplateResponse(
        request=request, 
        name="index.html",
        context={
            "title": "PAPI - Управление активами",
            "version": "1.0.0",
        }
    )

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    """Дашборд"""
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "title": "Дашборд",
        }
    )

@app.get("/assets", response_class=HTMLResponse)
def assets_page(request: Request):
    """Страница со списком активов"""
    return templates.TemplateResponse(
        request=request,
        name="assets.html",
        context={
            "title": "Активы",
        }
    )

# ========== Health Check ==========
@app.get("/health")
def health_check():
    """Проверка работоспособности"""
    return {"status": "ok", "service": "papi"}

# ========== Запуск ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
    )