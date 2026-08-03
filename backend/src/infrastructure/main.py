# src/main.py
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.infrastructure.db.init_db import init_db, get_or_create_admin
from src.infrastructure.db.session import SessionLocal
from src.infrastructure.db.models.asset_type_config import seed_asset_types
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем необходимые папки
import os
os.makedirs("uploads/documents", exist_ok=True)
os.makedirs("uploads/reports", exist_ok=True)
os.makedirs("uploads/inventory", exist_ok=True)
os.makedirs("uploads/asset_photos", exist_ok=True)

app = FastAPI(title="PAPI Backend", redirect_slashes=False)


@app.get("/")
def root():
    return {"message": "Welcome to PAPI Backend API"}


@app.get("/api/db-check")
def db_check():
    try:
        from sqlalchemy import text
        from src.infrastructure.db.session import SessionLocal, engine
        db = SessionLocal()
        result = db.execute(text("SELECT current_database(), current_user, version()")).fetchone()
        db.close()
        return {
            "status": "connected",
            "database": result[0] if result else "unknown",
            "user": result[1] if result else "unknown",
            "version": str(result[2])[:60] if result else "unknown",
        }
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}


def register_routers():
    from src.presentation.http.routers.assets import router as assets_router
    from src.presentation.http.routers.assets_export import router as assets_export_router
    from src.presentation.http.routers.assets_restore import router as assets_restore_router
    from src.presentation.http.routers.users import router as users_router
    from src.presentation.http.routers.auth import router as auth_router
    from src.presentation.http.routers.repairs import router as repairs_router
    from src.presentation.http.routers.documents import router as documents_router
    from src.presentation.http.routers.asset_photos import router as asset_photos_router
    from src.presentation.http.routers.reports import router as reports_router
    from src.presentation.http.routers.admin import router as admin_router
    from src.presentation.http.routers.inventory_import import router as inventory_import_router
    from src.presentation.http.routers.asset_types import router as asset_types_router
    from src.presentation.http.routers.maintenance_events import router as maintenance_events_router
    from src.presentation.http.routers.placements import router as placements_router
    from src.presentation.http.routers.employees import router as employees_router
    from src.presentation.http.routers.placement_assignments import router as placement_assignments_router
    from src.presentation.http.routers.asset_documents import router as asset_documents_router

    app.include_router(assets_router, prefix="/api")
    app.include_router(assets_export_router)
    app.include_router(assets_restore_router)
    app.include_router(users_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(repairs_router, prefix="/api")
    app.include_router(documents_router, prefix="/api")
    app.include_router(asset_photos_router, prefix="/api")
    app.include_router(reports_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(inventory_import_router, prefix="/api")
    app.include_router(asset_types_router, prefix="/api")
    app.include_router(maintenance_events_router, prefix="/api")
    app.include_router(placements_router, prefix="/api")
    app.include_router(employees_router, prefix="/api")
    app.include_router(placement_assignments_router, prefix="/api")
    app.include_router(asset_documents_router, prefix="/api")


@app.on_event("startup")
def startup_event():
    init_db()
    get_or_create_admin()
    try:
        db = SessionLocal()
        seed_asset_types(db)
        db.close()
    except Exception as e:
        logger.warning(f"Could not seed asset types: {e}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_trailing_slash(request: Request, call_next):
    import logging
    logger = logging.getLogger(__name__)
    
    # Обрабатываем preflight OPTIONS запросы
    if request.method == "OPTIONS":
        response = JSONResponse(status_code=200, content={"detail": "OK"})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response
    
# Добавляем trailing slash, если его нет (кроме корня и статических путей)
    # Исключаем API пути из редиректа, чтобы избежать проблем с CORS
    # Также исключаем /docs, /openapi.json, /redoc — у них redirect_slashes=False ломает маршруты
    if not request.url.path.endswith("/") and request.url.path != "/" and "." not in request.url.path.split("/")[-1] and not request.url.path.startswith("/api") and request.url.path not in ("/docs", "/openapi.json", "/redoc"):
        from fastapi.responses import RedirectResponse
        redirect_url = request.url.path + "/"
        if request.url.query:
            redirect_url += "?" + request.url.query
        response = RedirectResponse(url=redirect_url, status_code=308)
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response
    
    # Редирект /docs/ → /docs (и /redoc/ → /redoc), т.к. redirect_slashes=False
    if request.url.path in ("/docs/", "/redoc/"):
        from fastapi.responses import RedirectResponse
        redirect_url = request.url.path.rstrip("/")
        if request.url.query:
            redirect_url += "?" + request.url.query
        response = RedirectResponse(url=redirect_url, status_code=307)
        return response
    
    logger.info(f"[Request] {request.method} {request.url.path}")
    headers_dict = dict(request.headers)
    logger.info(f"[Request] Headers: {headers_dict}")
    content_type = headers_dict.get('content-type', '')
    logger.info(f"[Request] Content-Type: {content_type}")
    if 'authorization' not in headers_dict:
        logger.error("[Request] ❌ NO AUTHORIZATION HEADER - This is the problem!")
    else:
        logger.info(f"[Request] ✅ Authorization header present: {headers_dict['authorization'][:50]}...")
    response = await call_next(request)
    return response


register_routers()