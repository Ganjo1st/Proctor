# core/excel_report.py - СОЗДАНИЕ EXCEL-ОТЧЁТА ИЗ БАЗЫ
import pandas as pd
from datetime import datetime
import os

class ExcelReport:
    """Создание подробного отчёта в формате Excel"""
    
    def __init__(self, db, data_dir='data'):
        self.db = db          # экземпляр ProxyDatabase
        self.data_dir = data_dir
    
    def _determine_region(self, info):
        """Определение региона с учётом всех данных"""
        ru = info.get('ru_access', False)
        us = info.get('us_access', False)
        country_code = info.get('country_code', '')
        region = info.get('region', '')
        
        # Дополнительная логика
        if not ru and country_code == 'RU':
            ru = True
        if not ru and region == 'ru':
            ru = True
        if not us and country_code == 'US':
            us = True
        if not us and region == 'us':
            us = True
        
        if ru and us:
            return '🌍 Глобальный'
        elif ru:
            return '🇷🇺 Россия'
        elif us:
            return '🇺🇸 США'
        elif country_code:
            return f'❓ {country_code}'
        return '❓ Неизвестно'
    
    def create_report(self, filename='proxy_report.xlsx'):
        """Создание Excel-отчёта из базы данных"""
        print("📊 Создаю Excel-отчёт...")
        
        # Обеспечиваем существование папки reports
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        # Собираем данные из базы
        data = []
        proxies_dict = self.db.db.get('proxies', {})  # Доступ к внутреннему словарю
        
        for proxy, info in proxies_dict.items():
            # Определяем регион
            region = self._determine_region(info)
            
            data.append({
                'Прокси': proxy,
                'Рабочий': '✅ Да' if info.get('working') else '❌ Нет',
                'Регион': region,
                'Страна': info.get('country_code', ''),
                'Задержка (мс)': info.get('latency', 9999) if info.get('working') else '-',
                'Дата добавления': self._format_date(info.get('first_seen')),
                'Последняя проверка': self._format_date(info.get('last_seen')),
                'Источник': info.get('source', 'неизвестен')
            })
        
        if not data:
            print("⚠️ Нет данных для отчёта")
            return None
        
        df = pd.DataFrame(data)
        
        # Сортируем по работоспособности и задержке
        df_sorted = df.sort_values(['Рабочий', 'Задержка (мс)'], ascending=[False, True])
        
        # Создаём Excel файл
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df_sorted.to_excel(writer, sheet_name='Все прокси', index=False)
            df[df['Рабочий'] == '✅ Да'].to_excel(writer, sheet_name='Рабочие', index=False)
            df[df['Рабочий'] == '❌ Нет'].to_excel(writer, sheet_name='Нерабочие', index=False)
            df[df['Регион'] == '🇷🇺 Россия'].to_excel(writer, sheet_name='Российские', index=False)
            df[df['Регион'] == '🇺🇸 США'].to_excel(writer, sheet_name='Американские', index=False)
            df[df['Регион'] == '🌍 Глобальный'].to_excel(writer, sheet_name='Глобальные', index=False)
            
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
    
    def _format_date(self, date_str):
        if not date_str:
            return '-'
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return date_str[:19] if len(date_str) > 19 else date_str
