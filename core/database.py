# core/database.py - УПРАВЛЕНИЕ БАЗОЙ ПРОКСИ
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

class ProxyDatabase:
    """Управление базой прокси с автоочисткой"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        self.db_file = os.path.join(data_dir, 'proxy_db.json')
        
        os.makedirs(data_dir, exist_ok=True)
        self.db = self.load_db()
    
    def load_db(self) -> Dict:
        """Загрузка базы"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except:
                return {'proxies': {}, 'stats': {'total_seen': 0}}
        return {'proxies': {}, 'stats': {'total_seen': 0}}
    
    def save_db(self):
        """Сохранение базы"""
        with open(self.db_file, 'w') as f:
            json.dump(self.db, f, indent=2)
    
    def add_proxy(self, proxy: str, proxy_data: Dict):
        """Добавление прокси"""
        now = datetime.now().isoformat()
        
        if proxy in self.db['proxies']:
            # Обновляем
            self.db['proxies'][proxy]['last_seen'] = now
            self.db['proxies'][proxy]['working'] = proxy_data.get('working', False)
            self.db['proxies'][proxy]['latency'] = proxy_data.get('latency', 9999)
        else:
            # Добавляем
            self.db['proxies'][proxy] = {
                'first_seen': now,
                'last_seen': now,
                'working': proxy_data.get('working', False),
                'latency': proxy_data.get('latency', 9999)
            }
            self.db['stats']['total_seen'] += 1
        
        self.db['stats']['last_update'] = now
        self.save_db()
    
    def export_to_txt(self) -> Dict[str, List[str]]:
        """Экспорт в текстовые файлы"""
        working = [p for p, d in self.db['proxies'].items() if d['working']]
        
        # Сортируем по скорости
        working.sort(key=lambda p: self.db['proxies'][p].get('latency', 9999))
        
        # Сохраняем
        with open(os.path.join(self.data_dir, 'proxies_all.txt'), 'w') as f:
            f.write('\n'.join(working))
        
        with open(os.path.join(self.data_dir, 'proxies_fast.txt'), 'w') as f:
            f.write('\n'.join(working[:20]))
        
        return {
            'all': len(working),
            'fast': working[:20]
        }
    
    def get_stats(self) -> Dict:
        """Статистика"""
        total = len(self.db['proxies'])
        working = sum(1 for p in self.db['proxies'].values() if p['working'])
        
        return {
            'total_in_db': total,
            'working_now': working,
            'last_update': self.db['stats'].get('last_update'),
            'total_seen': self.db['stats'].get('total_seen', 0)
        }
