# core/database.py - УПРАВЛЕНИЕ БАЗОЙ ПРОКСИ С РАСПРЕДЕЛЕНИЕМ ПО РЕГИОНАМ
import json
import os
from datetime import datetime
from typing import List, Dict

class ProxyDatabase:
    """Управление базой прокси с региональным распределением"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        self.db_file = os.path.join(data_dir, 'proxy_db.json')
        
        os.makedirs(data_dir, exist_ok=True)
        self.db = self.load_db()
    
    def load_db(self) -> Dict:
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except:
                return {'proxies': {}, 'stats': {'total_seen': 0}}
        return {'proxies': {}, 'stats': {'total_seen': 0}}
    
    def save_db(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.db, f, indent=2)
    
    def _determine_region_flags(self, data: Dict) -> tuple:
        """Единая логика определения региона"""
        ru = data.get('ru_access', False)
        us = data.get('us_access', False)
        country_code = data.get('country_code', '')
        region = data.get('region', '')
        
        if not ru and country_code == 'RU':
            ru = True
        if not ru and region == 'ru':
            ru = True
        if not us and country_code == 'US':
            us = True
        if not us and region == 'us':
            us = True
        
        return ru, us
    
    def add_proxy(self, proxy: str, proxy_data: Dict, source: str = None):
        """Добавление прокси"""
        now = datetime.now().isoformat()
        
        ru_access = proxy_data.get('ru_access', False)
        us_access = proxy_data.get('us_access', False)
        country_code = proxy_data.get('country_code', '')
        region = proxy_data.get('region', '')
        
        if not ru_access and country_code == 'RU':
            ru_access = True
        if not ru_access and region == 'ru':
            ru_access = True
        if not us_access and country_code == 'US':
            us_access = True
        if not us_access and region == 'us':
            us_access = True
        
        if proxy in self.db['proxies']:
            self.db['proxies'][proxy].update({
                'last_seen': now,
                'working': proxy_data.get('working', False),
                'latency': proxy_data.get('latency', 9999),
                'ru_access': ru_access,
                'us_access': us_access,
                'source': source or self.db['proxies'][proxy].get('source', 'неизвестен'),
                'country': proxy_data.get('country'),
                'country_code': country_code,
                'region': region
            })
        else:
            self.db['proxies'][proxy] = {
                'first_seen': now,
                'last_seen': now,
                'working': proxy_data.get('working', False),
                'latency': proxy_data.get('latency', 9999),
                'ru_access': ru_access,
                'us_access': us_access,
                'source': source or 'неизвестен',
                'country': proxy_data.get('country'),
                'country_code': country_code,
                'region': region
            }
            self.db['stats']['total_seen'] += 1
        
        self.db['stats']['last_update'] = now
        self.save_db()
    
    def export_to_txt(self) -> Dict[str, List[str]]:
        """Экспорт в текстовые файлы"""
        all_proxies = []
        ru_only_proxies = []
        us_only_proxies = []
        global_proxies = []
        
        for proxy, data in self.db['proxies'].items():
            if not data['working']:
                continue
            
            all_proxies.append(proxy)
            ru, us = self._determine_region_flags(data)
            
            if ru and us:
                global_proxies.append(proxy)
            elif ru:
                ru_only_proxies.append(proxy)
            elif us:
                us_only_proxies.append(proxy)
        
        all_proxies.sort(key=lambda p: self.db['proxies'][p].get('latency', 9999))
        
        with open(os.path.join(self.data_dir, 'proxies_all.txt'), 'w') as f:
            f.write('\n'.join(all_proxies))
        
        with open(os.path.join(self.data_dir, 'proxies_russia.txt'), 'w') as f:
            f.write('\n'.join(ru_only_proxies))
        
        with open(os.path.join(self.data_dir, 'proxies_usa.txt'), 'w') as f:
            f.write('\n'.join(us_only_proxies))
        
        with open(os.path.join(self.data_dir, 'proxies_global.txt'), 'w') as f:
            f.write('\n'.join(global_proxies))
        
        with open(os.path.join(self.data_dir, 'proxies_fast.txt'), 'w') as f:
            f.write('\n'.join(all_proxies[:20]))
        
        print(f"  📁 Экспортировано: РФ (только)={len(ru_only_proxies)}, США (только)={len(us_only_proxies)}, Глобальных={len(global_proxies)}")
        
        return {
            'all': len(all_proxies),
            'ru_only': len(ru_only_proxies),
            'us_only': len(us_only_proxies),
            'global': len(global_proxies)
        }
    
    def get_stats(self) -> Dict:
        """Статистика"""
        total = len(self.db['proxies'])
        working = 0
        ru_only = 0
        us_only = 0
        global_ = 0
        
        for proxy, data in self.db['proxies'].items():
            if not data['working']:
                continue
            
            working += 1
            ru_flag, us_flag = self._determine_region_flags(data)
            
            if ru_flag and us_flag:
                global_ += 1
            elif ru_flag:
                ru_only += 1
            elif us_flag:
                us_only += 1
        
        return {
            'total_in_db': total,
            'working_now': working,
            'russian': ru_only,
            'american': us_only,
            'global': global_,
            'last_update': self.db['stats'].get('last_update'),
            'total_seen': self.db['stats'].get('total_seen', 0)
        }
