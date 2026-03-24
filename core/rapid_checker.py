# core/rapid_checker.py - УСИЛЕННОЕ ГЕО-ОПРЕДЕЛЕНИЕ
import aiohttp
import asyncio
from aiohttp_socks import ProxyConnector, ProxyType
from typing import List, Dict
import time
from colorama import Fore, Style

class RapidChecker:
    """Проверка прокси с точным гео-определением"""
    
    def __init__(self):
        self.test_urls = ['http://httpbin.org/ip']
        self.timeout = aiohttp.ClientTimeout(total=3)
        self.max_concurrent = 500
        
        # Сайты для проверки доступности
        self.ru_sites = ['https://yandex.ru', 'https://vk.com', 'https://mail.ru']
        self.us_sites = ['https://www.google.com', 'https://www.github.com', 'https://www.microsoft.com']
    
    async def check_one(self, proxy: str) -> Dict:
        """Проверка с определением страны и региона"""
        result = {
            'proxy': proxy,
            'working': False,
            'latency': 9999,
            'country': None,
            'country_code': None,
            'region': 'unknown',
            'checked_at': time.time(),
            'ru_access': False,
            'us_access': False
        }
        
        ip, port = proxy.split(':')
        
        try:
            start = time.time()
            connector = ProxyConnector(
                proxy_type=ProxyType.HTTP,
                host=ip,
                port=int(port),
                rdns=True,
                force_close=True
            )
            
            async with aiohttp.ClientSession(connector=connector, timeout=self.timeout) as session:
                # Базовая проверка работоспособности
                try:
                    async with session.get(self.test_urls[0]) as resp:
                        if resp.status != 200:
                            return result
                        result['working'] = True
                        result['latency'] = round((time.time() - start) * 1000, 2)
                except:
                    return result
                
                # Определение страны через IP-API
                try:
                    async with session.get(f'http://ip-api.com/json/{ip}', timeout=2) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('status') == 'success':
                                result['country'] = data.get('country')
                                result['country_code'] = data.get('countryCode')
                except:
                    pass
                
                # Проверка доступа к российским сайтам
                for site in self.ru_sites:
                    try:
                        async with session.get(site, timeout=2) as resp:
                            if resp.status == 200:
                                result['ru_access'] = True
                                break
                    except:
                        continue
                
                # Проверка доступа к американским сайтам
                for site in self.us_sites:
                    try:
                        async with session.get(site, timeout=2) as resp:
                            if resp.status == 200:
                                result['us_access'] = True
                                break
                    except:
                        continue
                
                # Определяем регион
                if result['ru_access'] and result['us_access']:
                    result['region'] = 'global'
                elif result['ru_access']:
                    result['region'] = 'ru'
                elif result['us_access']:
                    result['region'] = 'us'
                elif result['country_code'] == 'RU':
                    result['region'] = 'ru'
                elif result['country_code'] == 'US':
                    result['region'] = 'us'
                elif result['country_code'] in ['GB', 'DE', 'FR', 'IT', 'ES']:
                    result['region'] = 'eu'
                        
        except Exception as e:
            pass
        
        return result
    
    async def check_all(self, proxy_list: List[str]) -> List[Dict]:
        """Массовая параллельная проверка"""
        if not proxy_list:
            return []
        
        print(f"\n⚡ ПРОВЕРКА {len(proxy_list)} ПРОКСИ С ГЕО-ОПРЕДЕЛЕНИЕМ...")
        start = time.time()
        
        tasks = [self.check_one(proxy) for proxy in proxy_list]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        working = [r for r in results if r['working']]
        
        # Статистика по регионам
        ru = sum(1 for r in working if r['ru_access'])
        us = sum(1 for r in working if r['us_access'])
        
        print(f"✅ ЗА {elapsed:.1f} СЕК: {len(working)}/{len(proxy_list)} рабочих")
        print(f"   🇷🇺 РФ доступ: {ru} | 🇺🇸 США доступ: {us}\n")
        
        return results
