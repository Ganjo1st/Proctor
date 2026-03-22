# core/rapid_checker.py - ПРОВЕРКА С ГЕОПОЗИЦИЕЙ И РЕГИОНАМИ
import aiohttp
import asyncio
from aiohttp_socks import ProxyConnector, ProxyType
from typing import List, Dict
import time

class RapidChecker:
    """Быстрая проверка прокси с определением региона"""
    
    def __init__(self):
        # Тестовые URL для проверки региона
        self.test_urls = [
            'http://httpbin.org/ip',
            'https://httpbin.org/ip'
        ]
        
        # Сайты для определения региона
        self.region_sites = {
            'ru': ['https://yandex.ru', 'https://vk.com'],
            'us': ['https://www.google.com', 'https://www.github.com'],
            'eu': ['https://www.bbc.com', 'https://www.spiegel.de']
        }
        
        self.timeout = aiohttp.ClientTimeout(total=2)
        self.max_concurrent = 500
    
    async def check_one(self, proxy: str) -> Dict:
        """Проверка одного прокси с определением региона"""
        result = {
            'proxy': proxy,
            'working': False,
            'latency': 9999,
            'region': 'unknown',
            'country_code': None,
            'checked_at': time.time()
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
            
            async with aiohttp.ClientSession(
                connector=connector, 
                timeout=self.timeout
            ) as session:
                # Базовая проверка
                try:
                    async with session.get(self.test_urls[0]) as resp:
                        if resp.status == 200:
                            result['working'] = True
                            result['latency'] = round((time.time() - start) * 1000, 2)
                        else:
                            return result
                except:
                    return result
                
                # Определяем регион по доступности сайтов
                for region, sites in self.region_sites.items():
                    for site in sites:
                        try:
                            async with session.get(site, timeout=1.5) as resp:
                                if resp.status == 200:
                                    result['region'] = region
                                    break
                        except:
                            continue
                    if result['region'] != 'unknown':
                        break
                
                # Попытка определить страну через IP-API
                try:
                    async with session.get('http://ip-api.com/json/', timeout=1.5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('status') == 'success':
                                result['country_code'] = data.get('countryCode')
                                # Приоритет: если IP-API дал страну, используем её
                                if data.get('countryCode') == 'RU':
                                    result['region'] = 'ru'
                                elif data.get('countryCode') == 'US':
                                    result['region'] = 'us'
                                elif data.get('countryCode') in ['GB', 'DE', 'FR', 'IT', 'ES']:
                                    result['region'] = 'eu'
                except:
                    pass
                        
        except Exception as e:
            pass
        
        return result
    
    async def check_all(self, proxy_list: List[str]) -> List[Dict]:
        """Массовая параллельная проверка"""
        if not proxy_list:
            return []
        
        print(f"\n⚡ ПАРАЛЛЕЛЬНАЯ ПРОВЕРКА {len(proxy_list)} ПРОКСИ...")
        start = time.time()
        
        tasks = [self.check_one(proxy) for proxy in proxy_list]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        working = [r for r in results if r['working']]
        
        # Считаем по регионам
        ru = len([r for r in working if r['region'] == 'ru'])
        us = len([r for r in working if r['region'] == 'us'])
        eu = len([r for r in working if r['region'] == 'eu'])
        
        print(f"✅ ЗА {elapsed:.1f} СЕК: {len(working)}/{len(proxy_list)} рабочих")
        print(f"   🇷🇺 РФ: {ru} | 🇺🇸 США: {us} | 🇪🇺 EU: {eu}")
        
        return results
