# backend/scripts/test_rfid_inventory_user.py
"""
Проверка, что RFID-сканер проставляет last_inventory_by_id
и confirmed_by от авторизованного пользователя.

Запуск внутри контейнера:
    docker exec papi-backend python /app/scripts/test_rfid_inventory_user.py
"""
import os
import sys

sys.path.insert(0, "/app")

from datetime import datetime, date, timedelta

from src.infrastructure.db.init_db import SessionLocal
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.department import Room
from src.infrastructure.db.models.inventory_check import InventoryCheck
from src.infrastructure.db.models.inventory_check_item import InventoryCheckItem
from src.infrastructure.db.models.rfid_api_key import RfidApiKey
from src.infrastructure.db.models.user import User
from src.presentation.http.routers.rfid import (
    finish_inventory_check,
    scan_rfid_for_inventory,
    skip_all_pending,
    sync_scan_results,
)


def make_token(username: str) -> str:
    from jose import jwt

    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY не задан")
    return jwt.encode(
        {"sub": username, "exp": datetime.utcnow() + timedelta(hours=1)},
        secret,
        algorithm="HS256",
    )


class FakeRequest:
    """Минимальная заглушка fastapi.Request для get_optional_user"""

    def __init__(self, token: str | None):
        self.headers = {}
        if token:
            self.headers["authorization"] = f"Bearer {token}"

    async def json(self):
        return {}


class FakeScanner(dict):
    """Заглушка зависимости get_rfid_scanner"""


async def resolve_user(db, token: str | None) -> User | None:
    """Эмуляция зависимости get_optional_user через реальный декодер"""
    from src.presentation.http.dependencies.rfid_auth import get_optional_user

    return await get_optional_user(FakeRequest(token), db)


async def run():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.role == "admin").first()
        if not user:
            print("FAIL: нет ни одного администратора в БД")
            return 1

        api_key = db.query(RfidApiKey).filter(RfidApiKey.is_active == True).first()
        if not api_key:
            print("FAIL: нет активного RFID-ключа")
            return 1

        room = db.query(Room).filter(Room.is_active == True).first()
        assets = (
            db.query(Asset)
            .filter(Asset.is_active == True)
            .limit(2)
            .all()
        )
        if not assets:
            print("FAIL: нет активов")
            return 1

        # Присваиваем RFID-метки для тестирования scan
        for a in assets:
            if not a.rfid_tag:
                a.rfid_tag = f"TEST_{a.id}"
                db.add(a)
        db.commit()

        token = make_token(user.username)
        scanner = FakeScanner(id=api_key.id, name=api_key.name)

        # Готовим тестовую инвентаризацию
        inv = InventoryCheck(
            name="Тест: проверка проставления проверяющего",
            check_date=date.today(),
            check_type="by_room",
            scope_id=room.id if room else None,
            scope_name=room.name if room else "test",
            status="in_progress",
            created_at=datetime.now(),
            started_at=datetime.now(),
            created_by=user.id,
            responsible_id=user.id,
            total_checked=len(assets),
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        for a in assets:
            db.add(
                InventoryCheckItem(
                    inventory_check_id=inv.id,
                    asset_id=a.id,
                    result="pending",
                )
            )
            a.last_inventory_by_id = None
            a.last_inventory_confirmed = False
            a.last_inventory_date = None
            a.last_inventory_source = None
        db.commit()

        print(f"Инвентаризация #{inv.id}, пользователь {user.id} ({user.username})")
        print(f"Активы: {[a.inventory_number for a in assets]}")

        # 1. Сканирование первого актива с токеном
        await scan_rfid_for_inventory(
            inventory_id=inv.id,
            request=FakeRequest(token),
            rfid_tag=assets[0].rfid_tag,
            result="found",
            scanner=scanner,
            current_user=await resolve_user(db, token),
            db=db,
        )
        db.refresh(assets[0])
        print(
            f"  после scan: by_id={assets[0].last_inventory_by_id}, "
            f"confirmed={assets[0].last_inventory_confirmed}"
        )

        # 2. Sync второго актива с токеном
        class SyncReq(FakeRequest):
            async def json(self):
                return {
                    "results": [
                        {"rfid_tag": assets[1].rfid_tag, "result": "missing"}
                    ]
                }

        await sync_scan_results(
            inventory_id=inv.id,
            request=SyncReq(token),
            scanner=scanner,
            current_user=await resolve_user(db, token),
            db=db,
        )
        db.refresh(assets[1])
        print(
            f"  после sync: by_id={assets[1].last_inventory_by_id}, "
            f"confirmed={assets[1].last_inventory_confirmed}"
        )

        # 3. Завершение инвентаризации
        res = await finish_inventory_check(
            inventory_id=inv.id,
            skip_pending=True,
            scanner=scanner,
            current_user=await resolve_user(db, token),
            db=db,
        )
        print(f"  finish: {res.get('message')}")

        ok = True
        for a in assets:
            db.refresh(a)
            if a.last_inventory_by_id != user.id:
                ok = False
            print(
                f"  ИТОГ {a.inventory_number}: by_id={a.last_inventory_by_id}, "
                f"confirmed={a.last_inventory_confirmed}, date={a.last_inventory_date}"
            )

        # Проверка confirmed_by в элементах
        items = (
            db.query(InventoryCheckItem)
            .filter(InventoryCheckItem.inventory_check_id == inv.id)
            .all()
        )
        for it in items:
            if it.confirmed_by != user.id:
                ok = False
            print(f"  item asset={it.asset_id}: confirmed_by={it.confirmed_by}")

        # Без токена — пользователь не должен проставляться
        anon = await resolve_user(db, None)
        print(f"  get_optional_user без токена -> {anon}")
        if anon is not None:
            ok = False

        # Неверный токен — тоже None
        bad = await resolve_user(db, "не_токен")
        print(f"  get_optional_user с битым токеном -> {bad}")
        if bad is not None:
            ok = False

        # Откат тестовых данных
        db.query(InventoryCheckItem).filter(
            InventoryCheckItem.inventory_check_id == inv.id
        ).delete()
        db.query(InventoryCheck).filter(InventoryCheck.id == inv.id).delete()
        for a in assets:
            a.last_inventory_by_id = None
            a.last_inventory_confirmed = False
            a.last_inventory_date = None
            a.last_inventory_source = None
        db.commit()

        print("RESULT:", "OK" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio

    sys.exit(asyncio.run(run()))
