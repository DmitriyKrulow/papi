from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from . import Base


class AssetTypeConfig(Base):
    """Конфигурация типа актива с полями и настройками"""
    __tablename__ = "asset_type_configs"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    icon = Column(String(20), nullable=False, default="📦")
    category = Column(String(50), nullable=False, default="general")
    description = Column(Text, nullable=True)

    assets = relationship("Asset", back_populates="asset_type_config")

    default_depreciation_years = Column(Integer, nullable=False, default=5)
    default_maintenance_type = Column(String(100), nullable=True)
    maintenance_interval_months = Column(Integer, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    def __repr__(self) -> str:
        return f"<AssetTypeConfig(code='{self.code}', name='{self.name}')>"


def seed_asset_types(db):
    """Создаёт предустановленные типы активов, если они ещё не существуют"""
    default_types = [
        {
            "code": "furniture",
            "name": "Мебель",
            "icon": "🪑",
            "category": "office",
            "description": "Офисная и производственная мебель",
            "default_depreciation_years": 7,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 12,
        },
        {
            "code": "fire_extinguisher",
            "name": "Огнетушители",
            "icon": "🧯",
            "category": "safety",
            "description": "Огнетушители и средства пожаротушения",
            "default_depreciation_years": 3,
            "default_maintenance_type": "refilling",
            "maintenance_interval_months": 12,
        },
        {
            "code": "crypto_token",
            "name": "Криптотокены",
            "icon": "🔑",
            "category": "digital",
            "description": "USB-носители, карты и ключи доступа для пользователей",
            "default_depreciation_years": 3,
            "default_maintenance_type": "software_update",
            "maintenance_interval_months": 6,
        },
        {
            "code": "printer",
            "name": "Принтеры",
            "icon": "🖨️",
            "category": "equipment",
            "description": "Принтеры, МФУ и копировальная техника",
            "default_depreciation_years": 5,
            "default_maintenance_type": "toner_replacement",
            "maintenance_interval_months": 6,
        },
        {
            "code": "computer",
            "name": "Компьютеры",
            "icon": "💻",
            "category": "equipment",
            "description": "Компьютеры, ноутбуки и периферия (без серверного оборудования)",
            "default_depreciation_years": 5,
            "default_maintenance_type": "cleaning",
            "maintenance_interval_months": 6,
        },
        {
            "code": "consumables",
            "name": "Расходники",
            "icon": "📦",
            "category": "supplies",
            "description": "Расходные материалы и канцелярия",
            "default_depreciation_years": 1,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 0,
        },
        {
            "code": "ventilation",
            "name": "Системы вентиляции и кондиционирования",
            "icon": "❄️",
            "category": "engineering",
            "description": "Вентиляционные системы, кондиционеры, сплит-системы, климатическое оборудование",
            "default_depreciation_years": 10,
            "default_maintenance_type": "cleaning",
            "maintenance_interval_months": 6,
        },
        {
            "code": "electrical",
            "name": "Электрооборудование",
            "icon": "⚡",
            "category": "engineering",
            "description": "Электрощиты, трансформаторы, генераторы, системы электроснабжения, розетки и выключатели",
            "default_depreciation_years": 10,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 12,
        },
        {
            "code": "it_network",
            "name": "Сетевое и серверное оборудование",
            "icon": "🖧",
            "category": "it",
            "description": "Серверы, коммутаторы, маршрутизаторы, фаерволы, точки доступа WiFi, СКС",
            "default_depreciation_years": 5,
            "default_maintenance_type": "cleaning",
            "maintenance_interval_months": 6,
        },
        {
            "code": "power_supply",
            "name": "Источники питания",
            "icon": "🔋",
            "category": "engineering",
            "description": "ИБП, генераторы, ДГУ, стабилизаторы напряжения, аккумуляторы",
            "default_depreciation_years": 7,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 12,
        },
        {
            "code": "security",
            "name": "Системы безопасности",
            "icon": "🛡️",
            "category": "security",
            "description": "Камеры видеонаблюдения, СКУД, домофоны, системы пожарной сигнализации, датчики дыма",
            "default_depreciation_years": 7,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 6,
        },
        {
            "code": "plumbing",
            "name": "Сантехника и водоснабжение",
            "icon": "🚿",
            "category": "engineering",
            "description": "Краны, смесители, унитазы, раковины, водонагреватели, трубы, системы водоотведения",
            "default_depreciation_years": 10,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 12,
        },
        {
            "code": "doors_windows",
            "name": "Окна и двери",
            "icon": "🚪",
            "category": "building",
            "description": "Оконные блоки, дверные блоки, замки, доводчики, домофонные панели",
            "default_depreciation_years": 10,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 24,
        },
        {
            "code": "tools",
            "name": "Инструмент",
            "icon": "🔧",
            "category": "general",
            "description": "Ручной и электроинструмент, измерительные приборы, слесарный инструмент",
            "default_depreciation_years": 5,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 12,
        },
        {
            "code": "appliances",
            "name": "Электроприборы",
            "icon": "🔌",
            "category": "general",
            "description": "Бытовая и специальная электроника, чайники, обогреватели, увлажнители, вентиляторы",
            "default_depreciation_years": 5,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 12,
        },
        {
            "code": "multifunction",
            "name": "МФУ и копировальная техника",
            "icon": "🖥️",
            "category": "it",
            "description": "Многофункциональные устройства, копировальные аппараты, сканеры, факсы",
            "default_depreciation_years": 5,
            "default_maintenance_type": "toner_replacement",
            "maintenance_interval_months": 6,
        },
        {
            "code": "furniture_server",
            "name": "Серверные стойки и шкафы",
            "icon": "🗄️",
            "category": "it",
            "description": "Серверные стойки, кроссовые шкафы, шкафы управления, напольные и навесные шкафы",
            "default_depreciation_years": 15,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 12,
        },
        {
            "code": "furniture_storage",
            "name": "Стеллажи и архивная мебель",
            "icon": "📚",
            "category": "general",
            "description": "Складские стеллажи, архивные шкафы, металлические шкафы для одежды и вещей",
            "default_depreciation_years": 10,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 24,
        },
        {
            "code": "parking",
            "name": "Инфраструктура парковки",
            "icon": "🅿️",
            "category": "building",
            "description": "Шлагбаумы, паркоматы, разметка, знаки, освещение парковки, погрузочные платформы",
            "default_depreciation_years": 10,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 12,
        },
        {
            "code": "communication",
            "name": "Связь и телефония",
            "icon": "📞",
            "category": "it",
            "description": "IP-телефоны, АТС, радиостанции, рации, системы оповещения и громкой связи",
            "default_depreciation_years": 7,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 12,
        },
        {
            "code": "ppe",
            "name": "СИЗ и спецодежда",
            "icon": "🦺",
            "category": "safety",
            "description": "Средства индивидуальной защиты, спецодежда, защитные каски, перчатки, очки",
            "default_depreciation_years": 1,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 0,
        },
        {
            "code": "other",
            "name": "Прочее",
            "icon": "📋",
            "category": "general",
            "description": "Оборудование и активы, не вошедшие в другие категории",
            "default_depreciation_years": 5,
            "default_maintenance_type": "inspection",
            "maintenance_interval_months": 12,
        },
    ]

    for type_data in default_types:
        existing = db.query(AssetTypeConfig).filter_by(code=type_data["code"]).first()
        if existing:
            for key, value in type_data.items():
                setattr(existing, key, value)
        else:
            db.add(AssetTypeConfig(**type_data))
    db.commit()

