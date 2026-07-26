# backend/src/infrastructure/services/repair_print_service.py
import os
from datetime import datetime
from typing import Dict, Any

# Путь для сохранения печатных форм
PRINT_DIR = "uploads/prints"
os.makedirs(PRINT_DIR, exist_ok=True)


class RepairPrintService:
    """Сервис для печати заявок на ремонт"""

    @staticmethod
    def generate_repair_print(repair_data: Dict[str, Any], template_data: Dict[str, Any]) -> str:
        """
        Генерирует PDF для печати заявки.
        Временная реализация - создает простой текстовый файл.
        Для полноценной PDF используйте reportlab.
        """
        filename = f"repair_request_{repair_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(PRINT_DIR, filename)

        # Создаем простой текстовый файл для печати
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("           ЗАЯВКА НА РЕМОНТ\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Номер заявки: № {repair_data.get('id', '—')}\n")
            f.write(f"Дата создания: {repair_data.get('created_at', '—')}\n")
            f.write(f"Статус: {repair_data.get('status', '—')}\n")
            f.write(f"Приоритет: {repair_data.get('priority', '—')}\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("ИНФОРМАЦИЯ ОБ АКТИВЕ\n")
            f.write("-" * 60 + "\n")
            f.write(f"Наименование: {repair_data.get('asset_name', '—')}\n")
            f.write(f"Инвентарный номер: {repair_data.get('inventory_number', '—')}\n")
            f.write(f"Ответственный: {repair_data.get('responsible_person', '—')}\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("ОПИСАНИЕ РАБОТ\n")
            f.write("-" * 60 + "\n")
            f.write(f"{repair_data.get('description', '—')}\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ\n")
            f.write("-" * 60 + "\n")
            f.write(f"Желаемая дата выполнения: {repair_data.get('desired_completion_date', '—')}\n")
            f.write(f"Ориентировочная стоимость: {repair_data.get('estimated_cost', 0)} ₽\n")
            f.write(f"Исполнитель: {repair_data.get('assigned_to_name', 'Не назначен')}\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("ПОДПИСИ\n")
            f.write("-" * 60 + "\n")
            f.write("\n_________________________\n")
            f.write("(подпись ответственного лица)\n")
            f.write("\n_________________________\n")
            f.write("(подпись исполнителя)\n")

        return filepath

    @staticmethod
    def generate_repair_pdf(repair_data: Dict[str, Any]) -> str:
        """
        Генерирует PDF для печати заявки используя reportlab.
        Требуется установка: pip install reportlab
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm

            filename = f"repair_request_{repair_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(PRINT_DIR, filename)

            doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)

            styles = getSampleStyleSheet()
            title_style = styles['Title']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']

            story = []

            # Заголовок
            story.append(Paragraph("ЗАЯВКА НА РЕМОНТ", title_style))
            story.append(Spacer(1, 0.5*cm))

            # Информация о заявке
            info_data = [
                ["Номер заявки:", f"№ {repair_data.get('id', '—')}"],
                ["Дата создания:", repair_data.get('created_at', '—')[:10] if repair_data.get('created_at') else '—'],
                ["Статус:", repair_data.get('status', '—')],
                ["Приоритет:", repair_data.get('priority', '—')],
            ]

            info_table = Table(info_data, colWidths=[5*cm, 10*cm])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 1*cm))

            # Информация об активе
            story.append(Paragraph("ИНФОРМАЦИЯ ОБ АКТИВЕ", heading_style))
            story.append(Spacer(1, 0.3*cm))

            asset_data = [
                ["Наименование:", repair_data.get('asset_name', '—')],
                ["Инвентарный номер:", repair_data.get('inventory_number', '—')],
                ["Ответственный:", repair_data.get('responsible_person', '—')],
            ]

            asset_table = Table(asset_data, colWidths=[5*cm, 10*cm])
            asset_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ]))
            story.append(asset_table)
            story.append(Spacer(1, 1*cm))

            # Описание работ
            story.append(Paragraph("ОПИСАНИЕ РАБОТ", heading_style))
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(repair_data.get('description', '—'), normal_style))
            story.append(Spacer(1, 1*cm))

            # Дополнительная информация
            story.append(Paragraph("ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ", heading_style))
            story.append(Spacer(1, 0.3*cm))

            extra_data = [
                ["Желаемая дата выполнения:", repair_data.get('desired_completion_date', '—')],
                ["Ориентировочная стоимость:", f"{repair_data.get('estimated_cost', 0)} ₽"],
                ["Исполнитель:", repair_data.get('assigned_to_name', 'Не назначен')],
            ]

            extra_table = Table(extra_data, colWidths=[5*cm, 10*cm])
            extra_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ]))
            story.append(extra_table)

            # Подписи
            story.append(Spacer(1, 2*cm))
            story.append(Paragraph("_________________________", normal_style))
            story.append(Paragraph("Подпись ответственного лица", normal_style))

            doc.build(story)
            return filepath

        except ImportError:
            # Если reportlab не установлен, используем текстовый файл
            return RepairPrintService.generate_repair_print(repair_data, {})
        except Exception as e:
            # В случае ошибки используем текстовый файл
            print(f"PDF generation error: {e}")
            return RepairPrintService.generate_repair_print(repair_data, {})