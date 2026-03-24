# core/rapid_checker.py - УСИЛЕННОЕ ГЕО-ОПРЕДЕЛЕНИЕ
import aiohttp
import asyncio
from aiohttp_socks import ProxyConnector, ProxyType
from typing import List, Dict
import time
from colorama import Fore, Style  # ← ДОЛЖНО БЫТЬ!

class RapidChecker:
    """Проверка прокси с точным гео-определением"""
    
    def __init__(self):
        self.test_urls = ['http://httpbin.org/ip']
        self.timeout = aiohttp.ClientTimeout(total=3)
        self.max_concurrent = 500
        
        # Множественные методы определения гео
        self.geo_methods = [
            self._check_by_country_api,
            self._check_by_site_access,
            self._check_by_ip_api
        ]
    
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
                
                # МНОГОКРАТНОЕ ГЕО-ОПРЕДЕЛЕНИЕ
                for method in self.geo_methods:
                    geo_result = await method(session, ip)
                    if geo_result:
                        result.update(geo_result)
                        if result['country_code']:
                            break
                
                # Определяем регион на основе страны
                result['region'] = self._country_to_region(result.get('country_code'))
                
                # Дополнительная проверка доступности РФ/США сайтов
                result['ru_access'] = await self._check_ru_access(session)
                result['us_access'] = await self._check_us_access(session)
                        
        except Exception as e:
            pass
        
        return result
    
    async def _check_by_country_api(self, session, ip: str) -> Dict:
        """Определение страны через country.is API"""
        try:
            async with session.get(f'http://country.is/{ip}', timeout=2) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        'country': data.get('country'),
                        'country_code': data.get('country_code')
                    }
        except:
            pass
        return None
    
    async def _check_by_ip_api(self, session, ip: str) -> Dict:
        """Определение через ip-api.com"""
        try:
            async with session.get(f'http://ip-api.com/json/{ip}', timeout=2) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('status') == 'success':
                        return {
                            'country': data.get('country'),
                            'country_code': data.get('countryCode')
                        }
        except:
            pass
        return None
    
    async def _check_by_site_access(self, session, ip: str) -> Dict:
        """Определение региона по доступности локальных сайтов"""
        # Пробуем определить по доступности российских сайтов
        try:
            async with session.get('https://yandex.ru', timeout=2) as resp:
                if resp.status == 200:
                    return {'country_code': 'RU', 'country': 'Russia'}
        except:
            pass
        
        try:
            async with session.get('https://www.google.com', timeout=2) as resp:
                if resp.status == 200:
                    return {'country_code': 'US', 'country': 'United States'}
        except:
            pass
        
        return None
    
    async def _check_ru_access(self, session) -> bool:
        """Проверка доступа к российским сайтам"""
        ru_sites = ['https://yandex.ru', 'https://vk.com', 'https://mail.ru']
        for site in ru_sites:
            try:
                async with session.get(site, timeout=2) as resp:
                    if resp.status == 200:
                        return True
            except:
                continue
        return False
    
    async def _check_us_access(self, session) -> bool:
        """Проверка доступа к американским сайтам"""
        us_sites = ['https://www.google.com', 'https://www.github.com', 'https://www.microsoft.com']
        for site in us_sites:
            try:
                async with session.get(site, timeout=2) as resp:
                    if resp.status == 200:
                        return True
            except:
                continue
        return False
    
    def _country_to_region(self, country_code: str) -> str:
        """Преобразование кода страны в регион"""
        if country_code == 'RU':
            return 'ru'
        elif country_code == 'US':
            return 'us'
        elif country_code in ['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'PL', 'UA']:
            return 'eu'
        elif country_code:
            return 'other'
        return 'unknown'
    
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
        
        # Статистика по странам
        countries = {}
        for r in working:
            cc = r.get('country_code', 'unknown')
            countries[cc] = countries.get(cc, 0) + 1
        
        print(f"✅ ЗА {elapsed:.1f} СЕК: {len(working)}/{len(proxy_list)} рабочих")
        print(f"   🌍 Страны: {', '.join([f'{k}:{v}' for k, v in list(countries.items())[:5]])}")
        
        return results
