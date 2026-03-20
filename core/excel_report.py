# core/excel_report.py - СОЗДАНИЕ EXCEL-ОТЧЁТА
import json
import os
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

class ExcelReport:
    """Создание подробного отчёта в формате Excel"""
    
    def __init__(self, db, data_dir='data'):
        self.db = db
        self.data_dir = data_dir
    
    def create_report(self, filename='proxy_report.xlsx'):
        """Создание Excel-отчёта"""
        
        # Собираем данные
        data = []
        for proxy, info in self.db.db['proxies'].items():
            data.append({
                'Прокси': proxy,
                'Рабочий': '✅ Да' if info.get('working') else '❌ Нет',
                'Регион': self._get_region(info),
                'Задержка (мс)': info.get('latency', 9999) if info.get('working') else '-',
                'Дата добавления': self._format_date(info.get('first_seen')),
                'Последняя проверка': self._format_date(info.get('last_seen')),
                'Доступность РФ': '✅ Да' if info.get('ru_access') else '❌ Нет',
                'Доступность США': '✅ Да' if info.get('us_access') else '❌ Нет'
            })
        
        df = pd.DataFrame(data)
        
        # Создаём Excel файл
        writer = pd.ExcelWriter(filename, engine='openpyxl')
        
        # Лист "Все прокси"
        df.to_excel(writer, sheet_name='Все прокси', index=False)
        
        # Лист "Рабочие прокси"
        df[df['Рабочий'] == '✅ Да'].to_excel(writer, sheet_name='Рабочие', index=False)
        
        # Лист "Нерабочие прокси"
        df[df['Рабочий'] == '❌ Нет'].to_excel(writer, sheet_name='Нерабочие', index=False)
        
        # Лист "Российские прокси"
        df[df['Доступность РФ'] == '✅ Да'].to_excel(writer, sheet_name='Российские', index=False)
        
        # Лист "Американские прокси"
        df[df['Доступность США'] == '✅ Да'].to_excel(writer, sheet_name='Американские', index=False)
        
        # Лист "Глобальные прокси"
        df[(df['Доступность РФ'] == '✅ Да') & (df['Доступность США'] == '✅ Да')].to_excel(writer, sheet_name='Глобальные', index=False)
        
        # Лист "Статистика"
        stats = self.db.get_stats()
        stats_df = pd.DataFrame({
            'Показатель': [
                'Всего прокси в базе',
                'Рабочих прокси',
                'Российских',
                'Американских',
                'Глобальных',
                'Всего проверено за всё время',
                'Последнее обновление'
            ],
            'Значение': [
                stats['total_in_db'],
                stats['working_now'],
                stats['russian'],
                stats['american'],
                stats['global'],
                stats['total_seen'],
                stats['last_update'][:19] if stats['last_update'] else '-'
            ]
        })
        stats_df.to_excel(writer, sheet_name='Статистика', index=False)
        
        # Форматирование
        workbook = writer.book
        
        # Стили
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='4CAF50', end_color='4CAF50', fill_type='solid')
        center_alignment = Alignment(horizontal='center', vertical='center')
        
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            
            # Заголовки
            for cell in sheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
            
            # Автоширина колонок
            for column in sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                sheet.column_dimensions[column_letter].width = adjusted_width
        
        writer.close()
        print(f"📊 Отчёт сохранён: {filename}")
        return filename
    
    def _get_region(self, info):
        """Определение региона по доступности"""
        ru = info.get('ru_access', False)
        us = info.get('us_access', False)
        
        if ru and us:
            return '🌍 Глобальный'
        elif ru:
            return '🇷🇺 Россия'
        elif us:
            return '🇺🇸 США'
        else:
            return '❓ Неизвестно'
    
    def _format_date(self, date_str):
        """Форматирование даты"""
        if not date_str:
            return '-'
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return date_str[:19] if len(date_str) > 19 else date_str
