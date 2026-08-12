# src/main.py
import re
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.infrastructure.db.init_db import init_db, get_or_create_admin
from src.infrastructure.db.session import SessionLocal
from src.infrastructure.db.models.asset_type_config import seed_asset_types
from src.core.services.notification_scheduler import NotificationScheduler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем необходимые папки
import os
os.makedirs("uploads/documents", exist_ok=True)
os.makedirs("uploads/reports", exist_ok=True)
os.makedirs("uploads/inventory", exist_ok=True)
os.makedirs("uploads/asset_photos", exist_ok=True)

app = FastAPI(title="PAPI Backend", redirect_slashes=True)


# ---------------------------------------------------------------------------
# Сопоставление маршрутов для корректной обработки trailing slash.
#
# Роуты объявлены НЕОДНОРОДНО: часть с trailing slash (напр. POST /),
# часть без (напр. POST /{department_id}/rooms). При этом фронтенд шлёт пути
# без завершающего слэша. Чтобы не полагаться на 307-редиректы FastAPI
# (которые при кросс-ориджин переходе теряют Authorization header и могут
# зацикливаться), middleware добавляет trailing slash к scope-пути ТОЛЬКО
# когда маршрут реально объявлен с trailing slash. Иначе роут без слэша
# совпадает напрямую и редиректа не происходит.
# ---------------------------------------------------------------------------

# Кэш матчеров маршрутов: список (regex, methods). Строится один раз.
_route_matcher_cache = None


def _build_route_matcher(app):
    routes = []
    for r in app.router.routes:
        if type(r).__name__ == "_IncludedRouter":
            prefix = getattr(r.include_context, "prefix", "") or ""
            for rr in r.original_router.routes:
                pr = getattr(rr, "path_regex", None)
                if pr is None:
                    continue
                pat = pr.pattern
                if pat.startswith("^"):
                    pat = pat[1:]
                if pat.endswith("$"):
                    pat = pat[:-1]
                rx = re.compile("^" + re.escape(prefix) + pat + "$")
                routes.append((rx, getattr(rr, "methods", None)))
        else:
            pr = getattr(r, "path_regex", None)
            if pr is not None:
                routes.append((pr, getattr(r, "methods", None)))
    return routes


def _get_route_matcher(app):
    global _route_matcher_cache
    if _route_matcher_cache is None:
        _route_matcher_cache = _build_route_matcher(app)
    return _route_matcher_cache


def _route_matches(matcher, path, method):
    for rx, methods in matcher:
        if rx.fullmatch(path) and (not methods or method in methods):
            return True
    return False


@app.middleware("http")
async def add_trailing_slash_if_missing(request: Request, call_next):
    """Добавляет trailing slash к POST/PUT/PATCH/DELETE запросам, если его нет —
    но ТОЛЬКО когда маршрут реально объявлен с trailing slash.

    Раньше слэш добавлялся принудительно ко всем запросам, из-за чего роуты,
    объявленные БЕЗ trailing slash (например POST /{department_id}/rooms),
    попадали в бесконечную 307-редирект-петлю (redirect_slashes=True),
    а при кросс-ориджин редиректе ещё и терялся Authorization header.
    """
    path = request.url.path
    method = request.method
    if method in ("POST", "PUT", "PATCH", "DELETE") and not path.endswith("/") and path != "/":
        matcher = _get_route_matcher(request.app)
        candidate = path + "/"
        # Есть ли маршрут, объявленный С trailing slash
        matches_with_slash = _route_matches(matcher, candidate, method)
        # Есть ли маршрут, объявленный БЕЗ trailing slash
        matches_without_slash = _route_matches(matcher, path, method)

        # Переписываем путь только если слэш действительно нужен,
        # иначе оставляем без слэша, чтобы роут без слэша совпал напрямую.
        if matches_with_slash and not matches_without_slash:
            scope = request.scope
            scope["path"] = candidate
            if scope.get("raw_path"):
                scope["raw_path"] = candidate.encode("utf-8")
    response = await call_next(request)
    return response


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
    from src.presentation.http.routers.inventory_checks import router as inventory_checks_router
    from src.presentation.http.routers.marking import router as marking_router
    from src.presentation.http.routers.password_reset import public_router as password_reset_public_router
    from src.presentation.http.routers.password_reset import admin_router as password_reset_admin_router
    from src.presentation.http.routers.notifications import router as notifications_router
    from src.presentation.http.routers.notification_settings import router as notification_settings_router
    from src.presentation.http.routers.audit import router as audit_router

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
    app.include_router(inventory_checks_router, prefix="/api")
    app.include_router(marking_router, prefix="/api")
    app.include_router(password_reset_public_router, prefix="/api")
    app.include_router(password_reset_admin_router, prefix="/api")
    app.include_router(notifications_router, prefix="/api")
    app.include_router(notification_settings_router, prefix="/api")
    app.include_router(audit_router)


def seed_notification_templates(db):
    """Создать шаблоны уведомлений по умолчанию"""
    from src.infrastructure.db.models.notification_template import NotificationTemplate
    
    templates = [
        {
            "key": "inventory_started",
            "name": "Инвентаризация начата",
            "title_template": "📋 Начата инвентаризация: {check_name}",
            "message_template": "Начата инвентаризация «{check_name}». Пожалуйста, проверьте наличие вашего имущества.\n\nНайдено: {found}\nОтсутствует: {missing}",
            "type": "inventory",
        },
        {
            "key": "inventory_completed",
            "name": "Инвентаризация завершена",
            "title_template": "✅ Инвентаризация завершена: {check_name}",
            "message_template": "Инвентаризация «{check_name}» завершена.\n\nИтого активов: {total}\nНайдено: {found}\nОтсутствует: {missing}",
            "type": "inventory",
        },
        {
            "key": "repair_created",
            "name": "Заявка на ремонт создана",
            "title_template": "🔧 Новая заявка на ремонт: {repair_id}",
            "message_template": "Создана заявка на ремонт актива «{asset_name}».\n\nЗаявка #{repair_id}\nСтатус: {status}",
            "type": "repair",
        },
        {
            "key": "manual",
            "name": "Ручное уведомление",
            "title_template": "📢 Уведомление",
            "message_template": "{message}",
            "type": "general",
        },
    ]
    
    for tpl in templates:
        existing = db.query(NotificationTemplate).filter(
            NotificationTemplate.key == tpl["key"]
        ).first()
        if not existing:
            db.add(NotificationTemplate(**tpl))
    
    db.commit()


def seed_notification_settings(db):
    """Создать настройки уведомлений по умолчанию"""
    from src.infrastructure.db.models.notification_settings import NotificationSettings
    
    if not db.query(NotificationSettings).first():
        db.add(NotificationSettings())
        db.commit()


@app.on_event("startup")
def startup_event():
    """Запуск при старте приложения."""
    global notification_scheduler
    
    init_db()
    get_or_create_admin()
    try:
        db = SessionLocal()
        seed_asset_types(db)
        seed_notification_templates(db)
        seed_notification_settings(db)
        db.close()
    except Exception as e:
        logger.warning(f"Could not seed data: {e}")
    
    # Запуск планировщика уведомлений
    notification_scheduler = NotificationScheduler(interval_seconds=3600)  # 1 час
    notification_scheduler.start()
    
    # Запускаем генерацию уведомлений при старте
    try:
        results = notification_scheduler.run_once()
        total = sum(results.values())
        if total > 0:
            logger.info(f"Startup notification generation: {total} notifications created")
    except Exception as e:
        logger.error(f"Failed to generate notifications at startup: {e}")
    
    logger.info("Application started with notification scheduler")


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