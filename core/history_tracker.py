# core/history_tracker.py - ОТСЛЕЖИВАНИЕ ИЗМЕНЕНИЙ ПРОКСИ И ИСТОЧНИКОВ
import json
import os
from datetime import datetime

class HistoryTracker:
    """Отслеживание истории изменений прокси и источников"""
    
    def __init__(self):
        self.history_file = 'data/history.json'
        self.history = self.load()
    
    def load(self):
        """Загрузка истории"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return {'events': [], 'source_stats': {}}
        return {'events': [], 'source_stats': {}}
    
    def save(self):
        """Сохранение истории"""
        os.makedirs('data', exist_ok=True)
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_event(self, event_type: str, proxy: str, details: dict = None):
        """Добавление события"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'proxy': proxy,
            'details': details or {}
        }
        self.history['events'].append(event)
        
        # Ограничиваем размер (последние 5000 событий)
        if len(self.history['events']) > 5000:
            self.history['events'] = self.history['events'][-5000:]
        
        self.save()
    
    def add_source_event(self, source_name: str, event_type: str, count: int = 0):
        """Добавление события источника"""
        if source_name not in self.history['source_stats']:
            self.history['source_stats'][source_name] = {
                'first_seen': datetime.now().isoformat(),
                'last_seen': None,
                'total_found': 0,
                'events': []
            }
        
        stats = self.history['source_stats'][source_name]
        stats['last_seen'] = datetime.now().isoformat()
        if event_type == 'found':
            stats['total_found'] += count
        
        stats['events'].append({
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'count': count
        })
        
        # Ограничиваем историю источника
        if len(stats['events']) > 100:
            stats['events'] = stats['events'][-100:]
        
        self.save()
    
    def get_source_report(self) -> list:
        """Получение отчёта по источникам"""
        report = []
        for name, stats in self.history['source_stats'].items():
            report.append({
                'источник': name,
                'первое_появление': stats.get('first_seen', '')[:19],
                'последнее_появление': stats.get('last_seen', '')[:19],
                'всего_найдено': stats.get('total_found', 0),
                'активен': (datetime.now() - datetime.fromisoformat(stats.get('last_seen', '2000-01-01'))).days < 1
            })
        return sorted(report, key=lambda x: x['всего_найдено'], reverse=True)
