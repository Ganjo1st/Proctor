# core/excel_report.py - СОЗДАНИЕ EXCEL-ОТЧЁТА
import pandas as pd
from datetime import datetime

class ExcelReport:
    """Создание подробного отчёта в формате Excel"""
    
    def __init__(self, db, data_dir='data'):
        self.db = db
        self.data_dir = data_dir
    
    def create_report(self, filename='proxy_report.xlsx'):
        """Создание Excel-отчёта"""
        print("📊 Создаю Excel-отчёт...")
        
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
                'Доступность США': '✅ Да' if info.get('us_access') else '❌ Нет',
                'Источник': info.get('source', 'неизвестен')
            })
        
        df = pd.DataFrame(data)
        
        # Создаём Excel файл
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Все прокси', index=False)
            df[df['Рабочий'] == '✅ Да'].to_excel(writer, sheet_name='Рабочие', index=False)
            df[df['Рабочий'] == '❌ Нет'].to_excel(writer, sheet_name='Нерабочие', index=False)
            df[df['Доступность РФ'] == '✅ Да'].to_excel(writer, sheet_name='Российские', index=False)
            df[df['Доступность США'] == '✅ Да'].to_excel(writer, sheet_name='Американские', index=False)
            
            # Лист "Глобальные"
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
        
        print(f"✅ Отчёт сохранён: {filename}")
        return filename
    
    def _get_region(self, info):
        ru = info.get('ru_access', False)
        us = info.get('us_access', False)
        if ru and us:
            return '🌍 Глобальный'
        elif ru:
            return '🇷🇺 Россия'
        elif us:
            return '🇺🇸 США'
        return '❓ Неизвестно'
    
    def _format_date(self, date_str):
        if not date_str:
            return '-'
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return date_str[:19] if len(date_str) > 19 else date_str
