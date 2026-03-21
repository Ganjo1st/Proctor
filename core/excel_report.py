# core/excel_report.py - РАСШИРЕННЫЙ ОТЧЁТ С АНАЛИТИКОЙ ИСТОЧНИКОВ
import pandas as pd
from datetime import datetime
import os

class ExcelReport:
    """Создание подробного отчёта с аналитикой источников"""
    
    def __init__(self, db, data_dir='data'):
        self.db = db
        self.data_dir = data_dir
    
    def create_report(self, filename='proxy_report.xlsx'):
        """Создание Excel-отчёта"""
        print("📊 Создаю Excel-отчёт...")
        
        # 1. Собираем данные о прокси
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
        
        # 2. Собираем статистику по источникам
        source_stats = self._get_source_stats()
        df_sources = pd.DataFrame(source_stats)
        
        # 3. История изменений (из файла history.json)
        history = self._get_history()
        df_history = pd.DataFrame(history)
        
        # Создаём Excel файл
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Все прокси', index=False)
            df[df['Рабочий'] == '✅ Да'].to_excel(writer, sheet_name='Рабочие', index=False)
            df[df['Рабочий'] == '❌ Нет'].to_excel(writer, sheet_name='Нерабочие', index=False)
            df[df['Доступность РФ'] == '✅ Да'].to_excel(writer, sheet_name='Российские', index=False)
            df[df['Доступность США'] == '✅ Да'].to_excel(writer, sheet_name='Американские', index=False)
            
            # ЛИСТ СТАТИСТИКИ ИСТОЧНИКОВ
            df_sources.to_excel(writer, sheet_name='Источники', index=False)
            
            # ЛИСТ ИСТОРИИ ИЗМЕНЕНИЙ
            if not df_history.empty:
                df_history.to_excel(writer, sheet_name='История изменений', index=False)
            
            # ЛИСТ СТАТИСТИКИ
            stats = self.db.get_stats()
            stats_df = pd.DataFrame({
                'Показатель': [
                    'Всего прокси в базе',
                    'Рабочих прокси',
                    'Российских',
                    'Американских',
                    'Глобальных',
                    'Всего проверено за всё время',
                    'Активных источников',
                    'Всего найдено источников',
                    'Последнее обновление'
                ],
                'Значение': [
                    stats['total_in_db'],
                    stats['working_now'],
                    stats['russian'],
                    stats['american'],
                    stats['global'],
                    stats['total_seen'],
                    len([s for s in source_stats if s.get('активен')]),
                    len(source_stats),
                    stats['last_update'][:19] if stats['last_update'] else '-'
                ]
            })
            stats_df.to_excel(writer, sheet_name='Статистика', index=False)
        
        print(f"✅ Отчёт сохранён: {filename}")
        return filename
    
    def _get_source_stats(self):
        """Сбор статистики по источникам"""
        sources = {}
        for proxy, info in self.db.db['proxies'].items():
            source = info.get('source', 'неизвестен')
            if source not in sources:
                sources[source] = {
                    'источник': source,
                    'активен': True,
                    'всего_найдено': 0,
                    'рабочих_сейчас': 0,
                    'последнее_появление': None,
                    'первое_появление': info.get('first_seen')
                }
            sources[source]['всего_найдено'] += 1
            if info.get('working'):
                sources[source]['рабочих_сейчас'] += 1
            sources[source]['последнее_появление'] = info.get('last_seen')
        
        # Сортируем по количеству
        return sorted(sources.values(), key=lambda x: x['всего_найдено'], reverse=True)
    
    def _get_history(self):
        """Загрузка истории изменений"""
        history_file = 'data/history.json'
        if not os.path.exists(history_file):
            return []
        
        try:
            import json
            with open(history_file, 'r') as f:
                history = json.load(f)
            return history.get('events', [])
        except:
            return []
    
    def _get_region(self, info):
        ru = info.get('ru_access', False)
        us = info.get('us_access', False)
        if ru and us: return '🌍 Глобальный'
        elif ru: return '🇷🇺 Россия'
        elif us: return '🇺🇸 США'
        return '❓ Неизвестно'
    
    def _format_date(self, date_str):
        if not date_str: return '-'
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return date_str[:19] if len(date_str) > 19 else date_str
