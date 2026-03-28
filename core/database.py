# core/database.py - УПРАВЛЕНИЕ БАЗОЙ ПРОКСИ С РАСПРЕДЕЛЕНИЕМ ПО РЕГИОНАМ
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

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
        """Добавление прокси с гео-данными"""
        now = datetime.now().isoformat()
        
        ru_access = proxy_data.get('ru_access', False)
        us_access = proxy_data.get('us_access', False)
        country_code = proxy_data.get('country_code', '')
        region = proxy_data.get('region', '')
        
        # Дополнительная логика
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
        
        if ru_access:
            print(f"  🇷🇺 Добавлен российский прокси: {proxy} (страна: {country_code}, регион: {region})")
    
    def export_to_txt(self) -> Dict[str, List[str]]:
        """Экспорт в текстовые файлы по регионам"""
        all_proxies = []
        ru_proxies = []
        us_proxies = []
        global_proxies = []
        
        for proxy, data in self.db['proxies'].items():
            if not data['working']:
                continue
            
            all_proxies.append(proxy)
            
            ru, us = self._determine_region_flags(data)
            
            if ru and us:
                global_proxies.append(proxy)
                ru_proxies.append(proxy)
                us_proxies.append(proxy)
            elif ru:
                ru_proxies.append(proxy)
            elif us:
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
        
        print(f"  📁 Экспортировано: РФ={len(ru_proxies)}, США={len(us_proxies)}, Глобальных={len(global_proxies)}")
        
        return {
            'all': len(all_proxies),
            'ru': len(ru_proxies),
            'us': len(us_proxies),
            'global': len(global_proxies)
        }
    
    def get_stats(self) -> Dict:
        """Статистика с ЕДИНОЙ логикой определения региона"""
        total = len(self.db['proxies'])
        working = 0
        ru = 0
        us = 0
        global_ = 0
        
        for proxy, data in self.db['proxies'].items():
            if not data['working']:
                continue
            
            working += 1
            ru_flag, us_flag = self._determine_region_flags(data)
            
            if ru_flag and us_flag:
                global_ += 1
            elif ru_flag:
                ru += 1
            elif us_flag:
                us += 1
        
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
