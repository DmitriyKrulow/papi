# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.db.init_db import init_db, get_or_create_admin

# Создаем необходимые папки
import os
os.makedirs("uploads/documents", exist_ok=True)
os.makedirs("uploads/reports", exist_ok=True)
os.makedirs("uploads/inventory", exist_ok=True)

app = FastAPI(title="PAPI Backend")


@app.get("/")
def root():
    return {"message": "Welcome to PAPI Backend API"}


@app.get("/api/db-check")
def db_check():
    try:
        from sqlalchemy import text
        from src.infrastructure.db.session import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "connected", "database": "sqlite"}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}


def register_routers():
    from src.presentation.http.routers.assets import router as assets_router
    from src.presentation.http.routers.users import router as users_router
    from src.presentation.http.routers.auth import router as auth_router
    from src.presentation.http.routers.repairs import router as repairs_router
    from src.presentation.http.routers.documents import router as documents_router
    from src.presentation.http.routers.asset_photos import router as asset_photos_router
    from src.presentation.http.routers.reports import router as reports_router
    from src.presentation.http.routers.admin import router as admin_router

    app.include_router(assets_router, prefix="/api")
    app.include_router(users_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(repairs_router, prefix="/api")
    app.include_router(documents_router, prefix="/api")      # ✅ Роутер документов
    app.include_router(asset_photos_router, prefix="/api")
    app.include_router(reports_router, prefix="/api")        # ✅ Роутер отчетов
    app.include_router(admin_router, prefix="/api")


@app.on_event("startup")
def startup_event():
    init_db()
    get_or_create_admin()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routers()