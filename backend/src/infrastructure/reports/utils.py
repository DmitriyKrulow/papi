# src/infrastructure/reports/utils.py
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from openpyxl import load_workbook


def format_currency(value: float, decimals: int = 2) -> str:
    """Форматирование валюты с разделителями"""
    if value is None or (isinstance(value, float) and value != value):  # NaN check
        return '0.00'
    return f"{value:,.{decimals}f}".replace(',', ' ')


def format_date(value: Any) -> str:
    """Форматирование даты"""
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.strftime('%d.%m.%Y')
    return str(value)


def load_report_template(template_path: str) -> Any:
    """Загрузка шаблона отчета"""
    if not Path(template_path).exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return load_workbook(template_path)


def get_month_name(russian: bool = True) -> List[str]:
    """Названия месяцев"""
    if russian:
        return [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
    return [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]


def get_quarter_names(russian: bool = True) -> List[str]:
    """Названия кварталов"""
    if russian:
        return ['I квартал', 'II квартал', 'III квартал', 'IV квартал']
    return ['Q1', 'Q2', 'Q3', 'Q4']


def filter_by_date_range(data: List[Dict], start_date: str, end_date: str) -> List[Dict]:
    """Фильтрация данных по диапазону дат"""
    filtered = []
    for item in data:
        item_date = item.get('date') or item.get('created_at')
        if item_date:
            if start_date <= item_date <= end_date:
                filtered.append(item)
    return filtered


def calculate_depreciation(
    purchase_price: float,
    residual_value: float,
    useful_life_months: int
) -> Dict[str, float]:
    """Расчет амортизации"""
    if useful_life_months <= 0:
        return {
            'monthly': 0,
            'annual': 0,
            'total': 0,
            'remaining': purchase_price - residual_value
        }
    
    depreciable_amount = purchase_price - residual_value
    monthly = depreciable_amount / useful_life_months
    annual = monthly * 12
    total = monthly * min(useful_life_months, 12)  # За текущий год
    
    return {
        'monthly': monthly,
        'annual': annual,
        'total': total,
        'remaining': depreciable_amount - total
    }


def pivot_data(data: List[Dict], index: str, columns: str, values: List[str]) -> Any:
    """Создание сводной таблицы"""
    import pandas as pd
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    if df.empty:
        return df
    
    try:
        pivot = df.pivot_table(
            index=index,
            columns=columns,
            values=values,
            aggfunc='sum',
            fill_value=0,
            margins=True,
            margins_name='Итого'
        )
        return pivot
    except Exception:
        return df
