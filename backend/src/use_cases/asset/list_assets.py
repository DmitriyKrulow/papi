# src/use_cases/asset/list_assets.py
"""
Use case: получение списка активов с фильтрацией и пагинацией.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session, Query

from src.infrastructure.db.models.asset import Asset

logger = logging.getLogger(__name__)


class ListAssets:
    """Use case: получение списка активов."""

    def __call__(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        asset_type: Optional[str] = None,
        department: Optional[str] = None,
        location: Optional[str] = None,
        employee: Optional[str] = None,
        include_hidden: bool = False,
        sort_by: Optional[str] = None,
        sort_dir: Optional[str] = None,
        # Empty field filters
        empty_department: bool = False,
        empty_location: bool = False,
        empty_responsible: bool = False,
        empty_serial_number: bool = False,
        empty_model: bool = False,
        empty_purchase_date: bool = False,
        empty_warranty_expiry: bool = False,
    ) -> dict:
        """
        Получает список активов с фильтрацией и пагинацией.

        Args:
            db: Сессия SQLAlchemy
            skip: Количество пропускаемых записей
            limit: Максимальное количество записей
            search: Поиск по названию/инвентарному номеру
            status: Фильтр по статусу
            asset_type: Фильтр по типу актива
            department: Фильтр по отделу
            location: Фильтр по местоположению
            employee: Фильтр по сотруднику
            include_hidden: Включать скрытые активы
            sort_by: Поле для сортировки
            sort_dir: Направление сортировки (asc/desc)
            empty_department: Только активы без отдела
            empty_location: Только активы без местоположения
            empty_responsible: Только активы без ответственного
            empty_serial_number: Только активы без серийного номера
            empty_model: Только активы без модели
            empty_purchase_date: Только активы без даты покупки
            empty_warranty_expiry: Только активы без гарантии

        Returns:
            dict: {items: [...], total: int, skip: int, limit: int}
        """
        query: Query = db.query(Asset)

        # Фильтр видимости
        if not include_hidden:
            query = query.filter(Asset.is_active == True)

        # Поиск
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                Asset.name.ilike(search_pattern) |
                Asset.inventory_number.ilike(search_pattern) |
                Asset.serial_number.ilike(search_pattern)
            )

        # Статус
        if status:
            query = query.filter(Asset.status == status)

        # Тип актива
        if asset_type:
            query = query.filter(Asset.asset_type == asset_type)

        # Отдел
        if department:
            query = query.filter(Asset.department_name.ilike(f"%{department}%"))

        # Местоположение
        if location:
            query = query.filter(Asset.location_address.ilike(f"%{location}%"))

        # Сотрудник
        if employee:
            query = query.filter(Asset.employee_name.ilike(f"%{employee}%"))

        # Фильтры по пустым полям
        if empty_department:
            query = query.filter(
                (Asset.department_code == None) | (Asset.department_code == "")
            )
        if empty_location:
            query = query.filter(
                (Asset.location_address == None) | (Asset.location_address == "")
            )
        if empty_responsible:
            query = query.filter(
                (Asset.responsible_person == None) | (Asset.responsible_person == "")
            )
        if empty_serial_number:
            query = query.filter(
                (Asset.serial_number == None) | (Asset.serial_number == "")
            )
        if empty_model:
            query = query.filter(
                (Asset.model == None) | (Asset.model == "")
            )
        if empty_purchase_date:
            query = query.filter(Asset.purchase_date == None)
        if empty_warranty_expiry:
            query = query.filter(Asset.warranty_expiry == None)

        # Сортировка
        if sort_by and hasattr(Asset, sort_by):
            column = getattr(Asset, sort_by)
            if sort_dir == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

        # Подсчёт общего количества
        total = query.count()

        # Пагинация
        items = query.offset(skip).limit(limit).all()

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }


list_assets = ListAssets()
