import os
import re
import logging
from typing import Optional, Tuple, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)


class InventoryExcelParser:
    """
    Универсальный парсер бухгалтерских Excel-файлов для импорта активов.
    
    Поддерживает два основных формата:
    1. Формат "счёт" (69 колонок):
       - name_col=3, inv_col=10, cost_col=50, qty_col=26
       - Инв. номера: С21010573299, 0416361243420160000000026
    
    2. Формат "опись" (82 колонки):
       - name_col=3, inv_col=21, cost_col=77, qty_col=70
       - Инв. номера: Э99936792, С21010573299
    
    3. Формат "расписка" (23 колонки): без таблиц с данными — игнорируется.
    """
    
    # Ключевые слова для поиска заголовков колонок
    HEADERS = {
        'name': ['наименование объекта нефинансового актива', 'наименование объекта'],
        'inventory': ['инвентарн', 'номер (код) объекта учета', 'инвентарный номер'],
        'cost': ['балансовая стоимость', 'остаточная стоимость', 'балансовая'],
        'qty': ['количество', 'кол-во'],
        'unit': ['единица измерения', 'ед. изм'],
    }
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df: Optional[pd.DataFrame] = None
        self.col_map: Dict[str, int] = {}  # name -> column index
        self.file_type: str = "unknown"  # "account", "inventory", "receipt"
        self.data_start_row: int = 0
    
    def load(self) -> bool:
        """Загружает Excel-файл и определяет его тип."""
        try:
            self.df = pd.read_excel(self.file_path)
            logger.info(f"[Parser] Loaded: {len(self.df)} rows, {len(self.df.columns)} cols")
            return True
        except Exception as e:
            logger.error(f"[Parser] Failed to load file: {e}")
            return False
    
    def detect_type(self) -> str:
        """
        Определяет тип файла по структуре и содержимому.
        Возвращает: 'account', 'inventory', 'receipt', или 'unknown'
        """
        if self.df is None or len(self.df) == 0:
            return "unknown"
        
        num_cols = len(self.df.columns)
        
        # Расписки — мало колонок, нет таблиц
        if num_cols < 30:
            self.file_type = "receipt"
            return "receipt"
        
        # Ищем заголовки колонок в первых 100 строках
        self._find_headers()
        
        # Если нашли хотя бы 2 из 4 ключевых колонок — это таблица с данными
        found_cols = sum(1 for k in ['name', 'inventory', 'cost'] if k in self.col_map)
        
        if found_cols >= 2:
            # Определяем детальный тип по индексам колонок
            if 'inventory' in self.col_map and self.col_map['inventory'] <= 15:
                self.file_type = "account"  # короткий формат (69 колонок)
            else:
                self.file_type = "inventory"  # полный формат (82 колонки)
            return self.file_type
        
        # Не нашли заголовков — проверяем, есть ли строки с инвентарными номерами
        # Инвентарные номера начинаются с Э или С
        data_rows = self._find_data_rows()
        if data_rows:
            self.file_type = "inventory"
            return "inventory"
        
        return "unknown"
    
    def _find_headers(self):
        """Ищет заголовочные строки и определяет индексы ключевых колонок."""
        self.col_map = {}
        
        for row_idx in range(min(100, len(self.df))):
            row = self.df.iloc[row_idx]
            
            for col_idx, col_name in enumerate(self.df.columns):
                val = row.iloc[col_idx]
                if pd.notna(val):
                    text = str(val).lower().strip()
                    
                    # Ищем заголовки по ключевым словам
                    for field, keywords in self.HEADERS.items():
                        if field in self.col_map:
                            continue  # Уже нашли эту колонку
                        for kw in keywords:
                            if kw in text:
                                self.col_map[field] = col_idx
                                logger.info(f"[Parser] Found '{field}' at col {col_idx} (row {row_idx}, value: '{val}')")
                                break
    
    def _find_data_rows(self) -> list:
        """Ищет строки с инвентарными номерами (начинаются с Э или С + цифры)."""
        data_rows = []
        
        for idx in range(len(self.df)):
            row = self.df.iloc[idx]
            
            for col_idx in range(len(self.df.columns)):
                val = row.iloc[col_idx]
                if pd.notna(val):
                    text = str(val).strip()
                    # Инвентарные номера: Э + цифры, или С + цифры, или длинные числа
                    if (text.startswith('Э') and re.match(r'Э\d{5,}', text)) or \
                       (text.startswith('С') and re.match(r'С\d{8,}', text)) or \
                       (re.match(r'^\d{20,}$', text)):
                        data_rows.append((idx, text))
                        break
        
        return data_rows
    
    def _find_data_start_row(self) -> int:
        """
        Определяет строку, с которой начинаются реальные данные.
        Ищет первую строку с инвентарным номером и осмысленным наименованием.
        """
        for idx in range(len(self.df)):
            row = self.df.iloc[idx]
            
            # Получаем значение из колонки наименования
            name_val = ""
            if 'name' in self.col_map:
                name_val = str(row.iloc[self.col_map['name']]).strip() if pd.notna(row.iloc[self.col_map['name']]) else ""
            
            # Получаем значение из колонки инвентарного номера
            inv_val = ""
            if 'inventory' in self.col_map:
                inv_val = str(row.iloc[self.col_map['inventory']]).strip() if pd.notna(row.iloc[self.col_map['inventory']]) else ""
            
            # Пропускаем заголовки и служебные строки
            if not name_val or not inv_val:
                continue
            
            # Пропускаем строки-заголовки
            skip_keywords = ['наименование объекта', 'код строки', 'n/п', '№', 'единица измерения', 
                           'количество', 'балансовая стоимость', 'остаточная стоимость']
            if any(kw in name_val.lower() for kw in skip_keywords):
                continue
            
            # Проверяем, что name — не просто число
            try:
                float(name_val)
                continue
            except ValueError:
                pass
            
            # Это строка с данными!
            return idx
        
        return 0
    
    def parse(self) -> list:
        """
        Парсит файл и возвращает список словарей с данными активов.
        
        Returns:
            List[Dict] — список активов:
            [
                {
                    'inventory_number': str,
                    'name': str,
                    'model': str or None,
                    'purchase_price': float or None,
                    'quantity': int or None,
                },
                ...
            ]
        """
        if self.df is None:
            return []
        
        # Определяем тип файла
        file_type = self.detect_type()
        logger.info(f"[Parser] File type: {file_type}")
        
        if file_type in ("receipt", "unknown"):
            logger.info(f"[Parser] No data table found in file")
            return []
        
        # Определяем стартовую строку данных
        self.data_start_row = self._find_data_start_row()
        logger.info(f"[Parser] Data starts at row index: {self.data_start_row}")
        
        # Определяем колонки (fallback на фиксированные индексы)
        row_num_col = self.col_map.get('name', 0)
        name_col = self.col_map.get('name', 3)
        inventory_col = self.col_map.get('inventory', 21 if len(self.df.columns) > 80 else 10)
        cost_col = self.col_map.get('cost', 77 if len(self.df.columns) > 80 else 50)
        qty_col = self.col_map.get('qty', 70 if len(self.df.columns) > 80 else 26)
        
        logger.info(f"[Parser] Column mapping: name={name_col}, inventory={inventory_col}, cost={cost_col}, qty={qty_col}")
        
        # Парсим строки
        assets = []
        seen_inv = set()
        
        for idx in range(self.data_start_row, len(self.df)):
            row = self.df.iloc[idx]
            
            # Извлекаем значения
            name = self._get_cell_str(row, name_col)
            inventory_number = self._get_cell_str(row, inventory_col)
            cost = self._get_cell_str(row, cost_col)
            qty = self._get_cell_val(row, qty_col)
            
            # Обрезаем пробелы и кириллическую "Р"
            if inventory_number:
                inventory_number = inventory_number.strip()
                if inventory_number.startswith('Р'):
                    inventory_number = inventory_number[1:].strip()
            
            # Пропускаем пустые строки
            if not inventory_number or not name:
                continue
            
            # Пропускаем служебные строки
            skip_keywords = ['n/п', 'n п', '№', 'наименование', 'код', 'единица', 
                           'количество', 'балансовая', 'остаточная', 'инвентарный', 'всего']
            if any(kw in name.lower() for kw in skip_keywords):
                continue
            if inventory_number.lower() in ['код строки', 'всего']:
                continue
            
            # Пропускаем строки, где name — просто число
            try:
                float(name)
                continue
            except ValueError:
                pass
            
            # Пропускаем дубликаты
            if inventory_number in seen_inv:
                logger.debug(f"[Parser] Skipping duplicate: {inventory_number}")
                continue
            seen_inv.add(inventory_number)
            
            # Парсим стоимость
            purchase_price = self._parse_price(cost)
            
            # Извлекаем модель из наименования (если есть технические характеристики)
            model = self._extract_model(name)
            
            asset = {
                'inventory_number': inventory_number,
                'name': name,
                'model': model,
                'purchase_price': purchase_price,
                'quantity': int(qty) if qty and pd.notna(qty) else None,
            }
            
            assets.append(asset)
        
        logger.info(f"[Parser] Parsed {len(assets)} assets from file")
        return assets
    
    def _get_cell_str(self, row: pd.Series, col_idx: int) -> str:
        """Безопасно получает строковое значение ячейки."""
        val = row.iloc[col_idx] if col_idx < len(row) else None
        if pd.notna(val):
            return str(val).strip()
        return ""
    
    def _get_cell_val(self, row: pd.Series, col_idx: int):
        """Безопасно получает значение ячейки."""
        val = row.iloc[col_idx] if col_idx < len(row) else None
        return val
    
    def _parse_price(self, cost_str: str) -> Optional[float]:
        """Парсит стоимость из строки (формат: 256,18 или 256.18)."""
        if not cost_str or cost_str.lower() == 'nan' or not cost_str.strip():
            return None
        
        try:
            cost_clean = cost_str.replace(' ', '').replace(',', '.')
            if cost_clean.replace('.', '').replace('-', '').strip():
                return float(cost_clean)
        except ValueError:
            pass
        
        return None
    
    def _extract_model(self, name: str) -> Optional[str]:
        """
        Извлекает модель из наименования.
        Например:
          "Штамп 60*50 2970,00" -> "Штамп 60*50"
          "Печать диаметр 28 мм 256,18" -> "Печать диаметр 28 мм"
        """
        # Убираем цену в конце (число с запятой/точкой)
        # Пример: "Штамп 60*50 2970,00" -> "Штамп 60*50"
        # Пример: "Печать диаметр 28 мм 256,18" -> "Печать диаметр 28 мм"
        parts = re.split(r'\s+\d+[,.]\d+\s*$', name)
        if len(parts) > 1:
            return parts[0].strip()
        
        return None


# Фабрика для создания парсера из файла
def create_inventory_parser(file_path: str) -> InventoryExcelParser:
    """Создаёт и настраивает парсер для файла."""
    parser = InventoryExcelParser(file_path)
    parser.load()
    return parser
