# core/database.py - УПРАВЛЕНИЕ БАЗОЙ ПРОКСИ С РАСПРЕДЕЛЕНИЕМ ПО РЕГИОНАМ
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

class ProxyDatabase:
    """Управление базой прокси с региональным распределением"""
    
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
    
    def add_proxy(self, proxy: str, proxy_data: Dict, source: str = None):
        """Добавление прокси с гео-данными"""
        now = datetime.now().isoformat()
        
        if proxy in self.db['proxies']:
            self.db['proxies'][proxy].update({
                'last_seen': now,
                'working': proxy_data.get('working', False),
                'latency': proxy_data.get('latency', 9999),
                'ru_access': proxy_data.get('ru_access', False),
                'us_access': proxy_data.get('us_access', False),
                'source': source or self.db['proxies'][proxy].get('source', 'неизвестен'),
                'country': proxy_data.get('country'),
                'country_code': proxy_data.get('country_code'),
                'region': proxy_data.get('region')
            })
        else:
            self.db['proxies'][proxy] = {
                'first_seen': now,
                'last_seen': now,
                'working': proxy_data.get('working', False),
                'latency': proxy_data.get('latency', 9999),
                'ru_access': proxy_data.get('ru_access', False),
                'us_access': proxy_data.get('us_access', False),
                'source': source or 'неизвестен',
                'country': proxy_data.get('country'),
                'country_code': proxy_data.get('country_code'),
                'region': proxy_data.get('region')
            }
            self.db['stats']['total_seen'] += 1
        
        self.db['stats']['last_update'] = now
        self.save_db()
    
    def export_to_txt(self) -> Dict[str, List[str]]:
        """Экспорт в текстовые файлы по регионам"""
        all_proxies = []
        ru_proxies = []
        us_proxies = []
        global_proxies = []
        
        for proxy, data in self.db['proxies'].items():
            if data['working']:
                all_proxies.append(proxy)
                
                if data.get('ru_access') and data.get('us_access'):
                    global_proxies.append(proxy)
                elif data.get('ru_access'):
                    ru_proxies.append(proxy)
                elif data.get('us_access'):
                    us_proxies.append(proxy)
        
        # Сортируем по скорости
        all_proxies.sort(key=lambda p: self.db['proxies'][p].get('latency', 9999))
        ru_proxies.sort(key=lambda p: self.db['proxies'][p].get('latency', 9999))
        us_proxies.sort(key=lambda p: self.db['proxies'][p].get('latency', 9999))
        global_proxies.sort(key=lambda p: self.db['proxies'][p].get('latency', 9999))
        
        # Сохраняем
        with open(os.path.join(self.data_dir, 'proxies_all.txt'), 'w') as f:
            f.write('\n'.join(all_proxies))
        
        with open(os.path.join(self.data_dir, 'proxies_russia.txt'), 'w') as f:
            f.write('\n'.join(ru_proxies))
        
        with open(os.path.join(self.data_dir, 'proxies_usa.txt'), 'w') as f:
            f.write('\n'.join(us_proxies))
        
        with open(os.path.join(self.data_dir, 'proxies_global.txt'), 'w') as f:
            f.write('\n'.join(global_proxies))
        
        with open(os.path.join(self.data_dir, 'proxies_fast.txt'), 'w') as f:
            f.write('\n'.join(all_proxies[:20]))
        
        return {
            'all': len(all_proxies),
            'ru': len(ru_proxies),
            'us': len(us_proxies),
            'global': len(global_proxies)
        }
    
    def get_stats(self) -> Dict:
        """Статистика"""
        total = len(self.db['proxies'])
        working = sum(1 for p in self.db['proxies'].values() if p['working'])
        ru = sum(1 for p in self.db['proxies'].values() if p['working'] and p.get('ru_access'))
        us = sum(1 for p in self.db['proxies'].values() if p['working'] and p.get('us_access'))
        global_ = sum(1 for p in self.db['proxies'].values() if p['working'] and p.get('ru_access') and p.get('us_access'))
        
        return {
            'total_in_db': total,
            'working_now': working,
            'russian': ru,
            'american': us,
            'global': global_,
            'last_update': self.db['stats'].get('last_update'),
            'total_seen': self.db['stats'].get('total_seen', 0)
        }
    
    def get_proxy_history(self, proxy: str) -> Dict:
        """История конкретного прокси"""
        return self.db['proxies'].get(proxy, {})
