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
        
        # 1. Данные о прокси
        data = []
        for proxy, info in self.db.db['proxies'].items():
            data.append({
                'Прокси': proxy,
                'Рабочий': '✅ Да' if info.get('working') else '❌ Нет',
                'Регион': self._get_region(info),
                'Страна': info.get('country_code', 'unknown'),
                'Задержка (мс)': info.get('latency', 9999) if info.get('working') else '-',
                'Дата добавления': self._format_date(info.get('first_seen')),
                'Последняя проверка': self._format_date(info.get('last_seen')),
                'Источник': info.get('source', 'неизвестен')
            })
        
        df = pd.DataFrame(data)
        
        # 2. Статистика по источникам
        source_stats = self._get_source_stats()
        df_sources = pd.DataFrame(source_stats)
        
        # 3. История изменений
        history = self._get_history()
        df_history = pd.DataFrame(history)
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Основные листы
            df.to_excel(writer, sheet_name='Все прокси', index=False)
            df[df['Рабочий'] == '✅ Да'].to_excel(writer, sheet_name='Рабочие', index=False)
            df[df['Рабочий'] == '❌ Нет'].to_excel(writer, sheet_name='Нерабочие', index=False)
            df[df['Регион'] == '🇷🇺 Россия'].to_excel(writer, sheet_name='Российские', index=False)
            df[df['Регион'] == '🇺🇸 США'].to_excel(writer, sheet_name='Американские', index=False)
            df[df['Регион'] == '🌍 Глобальный'].to_excel(writer, sheet_name='Глобальные', index=False)
            
            # Лист со статистикой источников
            df_sources.to_excel(writer, sheet_name='Источники', index=False)
            
            # Лист с историей изменений
            if not df_history.empty:
                df_history.to_excel(writer, sheet_name='История', index=False)
            
            # Лист со сводной статистикой
            stats = self.db.get_stats()
            stats_df = pd.DataFrame({
                'Показатель': [
                    'Всего прокси в базе',
                    'Рабочих прокси',
                    'Российских',
                    'Американских',
                    'Глобальных',
                    'Активных источников',
                    'Всего найдено источников',
                    'Всего проверено за всё время',
                    'Последнее обновление'
                ],
                'Значение': [
                    stats['total_in_db'],
                    stats['working_now'],
                    stats['russian'],
                    stats['american'],
                    stats['global'],
                    len([s for s in source_stats if s.get('активен')]),
                    len(source_stats),
                    stats['total_seen'],
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
                    'последнее_появление': None
                }
            sources[source]['всего_найдено'] += 1
            if info.get('working'):
                sources[source]['рабочих_сейчас'] += 1
            sources[source]['последнее_появление'] = info.get('last_seen')
        
        # Добавляем информацию из source_stats.json
        source_stats_file = os.path.join(self.data_dir, 'source_stats.json')
        if os.path.exists(source_stats_file):
            try:
                import json
                with open(source_stats_file, 'r') as f:
                    saved = json.load(f)
                    for name, stats in saved.items():
                        if name in sources:
                            sources[name]['checks'] = stats.get('checks', 0)
                            sources[name]['success_rate'] = stats.get('success_rate', 0)
                        else:
                            sources[name] = {
                                'источник': name,
                                'активен': stats.get('enabled', True),
                                'всего_найдено': 0,
                                'рабочих_сейчас': 0,
                                'checks': stats.get('checks', 0),
                                'success_rate': stats.get('success_rate', 0),
                                'последнее_появление': stats.get('last_success')
                            }
            except:
                pass
        
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
            events = history.get('events', [])[-500:]  # Последние 500 событий
            
            # Форматируем для отображения
            formatted = []
            for e in events:
                formatted.append({
                    'Время': e.get('timestamp', '')[:19],
                    'Тип': e.get('type', ''),
                    'Прокси': e.get('proxy', ''),
                    'Детали': str(e.get('details', {}))[:100]
                })
            return formatted
        except:
            return []
    
    def _get_region(self, info):
        ru = info.get('ru_access', False)
        us = info.get('us_access', False)
        country = info.get('country_code', '')
        
        if ru and us:
            return '🌍 Глобальный'
        elif ru or country == 'RU':
            return '🇷🇺 Россия'
        elif us or country == 'US':
            return '🇺🇸 США'
        elif country in ['GB', 'DE', 'FR', 'IT', 'ES']:
            return '🇪🇺 Европа'
        return '❓ Неизвестно'
    
    def _format_date(self, date_str):
        if not date_str: return '-'
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return date_str[:19] if len(date_str) > 19 else date_str
