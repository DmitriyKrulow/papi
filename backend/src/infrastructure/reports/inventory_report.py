# src/infrastructure/reports/inventory_report.py
from typing import Dict, List
from datetime import datetime

import pandas as pd

from .base import BaseReportGenerator


class InventoryReportGenerator(BaseReportGenerator):
    """Генератор отчета по инвентаризации"""

    def __init__(self):
        super().__init__()
        self.title = "Отчет по инвентаризации"
        self.date = datetime.now().strftime('%d.%m.%Y')

    def generate(
        self,
        inventory_check_id: int,
        assets: List[Dict],
        results: List[Dict],
        **kwargs
    ) -> bytes:
        """Генерация отчета по инвентаризации"""
        
        df = pd.DataFrame(assets)
        results_df = pd.DataFrame(results) if results else pd.DataFrame()
        
        if df.empty:
            df = pd.DataFrame(columns=[
                'ID', 'Инвентарный номер', 'Название', 'Стоимость', 'Ответственный',
                'Местоположение', 'Фактическое местоположение', 'Состояние', 'Примечания'
            ])
        
        self._add_summary_sheet(df, inventory_check_id)
        self._add_assets_sheet(df)
        
        if not results_df.empty:
            self._add_discrepancies_sheet(df, results_df)
        
        return self.save_bytes()

    def _add_summary_sheet(self, df: pd.DataFrame, check_id: int) -> None:
        """Добавление листа сводки"""
        sheet = self.workbook.create_sheet("Сводка")
        
        sheet.merge_cells('A1:D1')
        title_cell = sheet['A1']
        title_cell.value = self.title
        title_cell.font = self._get_title_font()
        title_cell.alignment = self._get_center_alignment()
        
        sheet['A3'] = f"ID инвентаризации: {check_id}"
        sheet['A4'] = f"Дата генерации: {self.date}"
        sheet['A5'] = f"Всего активов: {len(df)}"
        
        if not df.empty:
            total_value = df['purchase_price'].sum() if 'purchase_price' in df.columns else 0
            sheet['A6'] = f"Общая стоимость: {self._format_currency(total_value)}"
        
        sheet.column_dimensions['A'].width = 35
        sheet.column_dimensions['B'].width = 20

    def _add_assets_sheet(self, df: pd.DataFrame) -> None:
        """Добавление листа с активами"""
        sheet = self.workbook.create_sheet("Активы")
        
        sheet.merge_cells('A1:D1')
        title_cell = sheet['A1']
        title_cell.value = "Список активов"
        title_cell.font = self._get_title_font()
        title_cell.alignment = self._get_center_alignment()
        
        headers = [
            'ID', 'Инвентарный номер', 'Название', 'Модель', 'Стоимость',
            'Ответственный', 'Местоположение', 'Статус'
        ]
        
        for col_idx, header in enumerate(headers, 1):
            cell = sheet.cell(row=3, column=col_idx, value=header)
            cell.font = self._get_header_font()
            cell.fill = self._get_header_fill()
            cell.border = self._get_border()
        
        for row_idx, (_, row) in enumerate(df.iterrows(), 4):
            sheet.cell(row=row_idx, column=1, value=row.get('id', ''))
            sheet.cell(row=row_idx, column=2, value=row.get('inventory_number', ''))
            sheet.cell(row=row_idx, column=3, value=row.get('name', ''))
            sheet.cell(row=row_idx, column=4, value=row.get('model', ''))
            sheet.cell(row=row_idx, column=5, value=self._format_currency(row.get('purchase_price', 0)))
            sheet.cell(row=row_idx, column=6, value=row.get('responsible_person', ''))
            sheet.cell(row=row_idx, column=7, value=row.get('location_address', ''))
            sheet.cell(row=row_idx, column=8, value=row.get('status', ''))
        
        if not df.empty:
            total_row = 4 + len(df)
            sheet.cell(row=total_row, column=1, value="Итого:")
            sheet.cell(row=total_row, column=5, value=self._format_currency(df['purchase_price'].sum() if 'purchase_price' in df.columns else 0))
            
            for col in range(1, 9):
                cell = sheet.cell(row=total_row, column=col)
                cell.font = self._get_header_font()
                cell.fill = self._get_header_fill()
                cell.border = self._get_border()
        
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            sheet.column_dimensions[col].width = 18

    def _add_discrepancies_sheet(self, df: pd.DataFrame, results_df: pd.DataFrame) -> None:
        """Добавление листа с расхождениями"""
        sheet = self.workbook.create_sheet("Расхождения")
        
        sheet.merge_cells('A1:C1')
        title_cell = sheet['A1']
        title_cell.value = "Выявленные расхождения"
        title_cell.font = self._get_title_font()
        title_cell.alignment = self._get_center_alignment()
        
        if not results_df.empty:
            headers = [
                'ID актива', 'Инвентарный номер', 'Ожидаемое местоположение',
                'Фактическое местоположение', 'Состояние', 'Примечания'
            ]
            
            for col_idx, header in enumerate(headers, 1):
                cell = sheet.cell(row=3, column=col_idx, value=header)
                cell.font = self._get_header_font()
                cell.fill = self._get_header_fill()
                cell.border = self._get_border()
            
            for row_idx, (_, row) in enumerate(results_df.iterrows(), 4):
                for col_idx, value in enumerate(row, 1):
                    cell = sheet.cell(row=row_idx, column=col_idx, value=value)
                    cell.border = self._get_border()
                    if 'стоимость' in str(value).lower():
                        cell.font = self._get_header_font()
                        cell.fill = self._get_discrepancy_fill()
            
            discrepancy_count = len(results_df)
            sheet.cell(row=4 + discrepancy_count, column=1, value=f"Всего расхождений: {discrepancy_count}")
        
        sheet.column_dimensions['A'].width = 15
        sheet.column_dimensions['B'].width = 20
        sheet.column_dimensions['C'].width = 30
        sheet.column_dimensions['D'].width = 30
        sheet.column_dimensions['E'].width = 20
        sheet.column_dimensions['F'].width = 30

    def _get_title_font(self):
        from openpyxl.styles import Font
        return Font(size=16, bold=True)

    def _get_header_font(self):
        from openpyxl.styles import Font
        return Font(bold=True)

    def _get_header_fill(self):
        from openpyxl.styles import PatternFill
        return PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')

    def _get_discrepancy_fill(self):
        from openpyxl.styles import PatternFill
        return PatternFill(start_color='FFC000', end_color='FFC000', fill_type='solid')

    def _get_center_alignment(self):
        from openpyxl.styles import Alignment
        return Alignment(horizontal='center')

    def _get_right_alignment(self):
        from openpyxl.styles import Alignment
        return Alignment(horizontal='right')

    def _get_border(self):
        from openpyxl.styles import Border, Side
        thin = Side(border_style='thin', color='000000')
        return Border(left=thin, right=thin, top=thin, bottom=thin)
