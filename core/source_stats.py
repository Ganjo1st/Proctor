# core/source_stats.py - СТАТИСТИКА И АВТООТКЛЮЧЕНИЕ ИСТОЧНИКОВ
import json
import os
from datetime import datetime

class SourceStats:
    """Отслеживание эффективности источников"""
    
    def __init__(self, stats_file='data/source_stats.json'):
        self.stats_file = stats_file
        self.stats = self.load()
    
    def load(self):
        """Загрузка статистики"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save(self):
        """Сохранение статистики"""
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def update(self, source_name: str, found_count: int):
        """Обновление статистики источника"""
        now = datetime.now().isoformat()
        
        if source_name not in self.stats:
            self.stats[source_name] = {
                'first_seen': now,
                'last_seen': now,
                'checks': 0,
                'total_found': 0,
                'success_rate': 0,
                'enabled': True
            }
        
        stats = self.stats[source_name]
        stats['last_seen'] = now
        stats['checks'] += 1
        stats['total_found'] = stats.get('total_found', 0) + found_count
        
        # Обновляем процент успеха
        if stats['checks'] > 0:
            stats['success_rate'] = stats['total_found'] / stats['checks']
        
        # Автоотключение: если за 5 проверок не нашли >1 прокси
        if stats['checks'] >= 5 and stats['success_rate'] < 1.0:
            if stats['enabled']:
                print(f"  ⚠️ Источник {source_name} ОТКЛЮЧЁН (мало прокси: {stats['success_rate']:.1f}/проверку)")
                stats['enabled'] = False
        
        self.save()
    
    def get_active_sources(self) -> list:
        """Получение списка активных источников"""
        return [name for name, s in self.stats.items() if s.get('enabled', True)]
    
    def get_stats(self) -> dict:
        """Получение всей статистики"""
        return {
            'total_sources': len(self.stats),
            'active_sources': len(self.get_active_sources()),
            'sources': self.stats
        }
