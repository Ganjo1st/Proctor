# core/excel_report.py - СОЗДАНИЕ EXCEL-ОТЧЁТА ИЗ БАЗЫ
import pandas as pd
from datetime import datetime
import os

class ExcelReport:
    """Создание подробного отчёта в формате Excel"""
    
    def __init__(self, db, data_dir='data'):
        self.db = db
        self.data_dir = data_dir
    
    def _determine_region(self, info):
        """Определение региона для отображения"""
        ru = info.get('ru_access', False)
        us = info.get('us_access', False)
        country_code = info.get('country_code', '')
        region = info.get('region', '')
        
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
            return '🇷🇺 Россия (только)'
        elif us:
            return '🇺🇸 США (только)'
        elif country_code:
            return f'❓ {country_code}'
        return '❓ Неизвестно'
    
    def create_report(self, filename='reports/proxy_report.xlsx'):
        """Создание Excel-отчёта из базы данных"""
        print("📊 Создаю Excel-отчёт...")
        
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        data = []
        ru_only_data = []
        us_only_data = []
        global_data = []
        
        proxies_dict = self.db.db.get('proxies', {})
        
        for proxy, info in proxies_dict.items():
            ru, us = self.db._determine_region_flags(info)
            region = self._determine_region(info)
            
            row = {
                'Прокси': proxy,
                'Рабочий': '✅ Да' if info.get('working') else '❌ Нет',
                'Регион': region,
                'Страна': info.get('country_code', ''),
                'Задержка (мс)': info.get('latency', 9999) if info.get('working') else '-',
                'Дата добавления': self._format_date(info.get('first_seen')),
                'Последняя проверка': self._format_date(info.get('last_seen')),
                'Источник': info.get('source', 'неизвестен')
            }
            data.append(row)
            
            if info.get('working'):
                if ru and not us:
                    ru_only_data.append({'Прокси': proxy})
                elif us and not ru:
                    us_only_data.append({'Прокси': proxy})
                elif ru and us:
                    global_data.append({'Прокси': proxy})
        
        if not data:
            print("⚠️ Нет данных для отчёта")
            return None
        
        df = pd.DataFrame(data)
        df_sorted = df.sort_values(['Рабочий', 'Задержка (мс)'], ascending=[False, True])
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df_sorted.to_excel(writer, sheet_name='Все прокси', index=False)
            df[df['Рабочий'] == '✅ Да'].to_excel(writer, sheet_name='Рабочие', index=False)
            df[df['Рабочий'] == '❌ Нет'].to_excel(writer, sheet_name='Нерабочие', index=False)
            
            if ru_only_data:
                pd.DataFrame(ru_only_data).to_excel(writer, sheet_name='Российские (только)', index=False)
            else:
                pd.DataFrame({'Прокси': ['Нет прокси']}).to_excel(writer, sheet_name='Российские (только)', index=False)
            
            if us_only_data:
                pd.DataFrame(us_only_data).to_excel(writer, sheet_name='Американские (только)', index=False)
            else:
                pd.DataFrame({'Прокси': ['Нет прокси']}).to_excel(writer, sheet_name='Американские (только)', index=False)
            
            if global_data:
                pd.DataFrame(global_data).to_excel(writer, sheet_name='Глобальные', index=False)
            else:
                pd.DataFrame({'Прокси': ['Нет прокси']}).to_excel(writer, sheet_name='Глобальные', index=False)
            
            stats = self.db.get_stats()
            stats_df = pd.DataFrame({
                'Показатель': [
                    'Всего прокси в базе',
                    'Рабочих прокси',
                    'Российские (только РФ)',
                    'Американские (только США)',
                    'Глобальные (РФ+США)',
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
