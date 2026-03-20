# core/rapid_checker.py - СУПЕР-БЫСТРАЯ ПАРАЛЛЕЛЬНАЯ ПРОВЕРКА С РЕГИОНАМИ
import aiohttp
import asyncio
from aiohttp_socks import ProxyConnector, ProxyType
from typing import List, Dict
import time

class RapidChecker:
    """Максимально быстрая параллельная проверка прокси с определением региона"""
    
    def __init__(self):
        # Российские сайты
        self.ru_sites = [
            'https://yandex.ru',
            'https://vk.com',
        ]
        
        # Американские/западные сайты
        self.us_sites = [
            'https://www.google.com',
            'https://www.github.com',
        ]
        
        # 1.5 секунды на прокси - жёсткий таймаут!
        self.timeout = aiohttp.ClientTimeout(total=1.5)
        self.max_concurrent = 500
    
    async def check_one(self, proxy: str) -> Dict:
        """Мгновенная проверка одного прокси с определением региона"""
        result = {
            'proxy': proxy,
            'working': False,
            'latency': 9999,
            'ru_access': False,
            'us_access': False,
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
                    async with session.get('http://httpbin.org/ip') as resp:
                        if resp.status == 200:
                            result['working'] = True
                            result['latency'] = round((time.time() - start) * 1000, 2)
                        else:
                            return result
                except:
                    return result
                
                # Проверка РФ
                for site in self.ru_sites:
                    try:
                        async with session.get(site, timeout=1) as resp:
                            if resp.status == 200:
                                result['ru_access'] = True
                                break
                    except:
                        continue
                
                # Проверка США
                for site in self.us_sites:
                    try:
                        async with session.get(site, timeout=1) as resp:
                            if resp.status == 200:
                                result['us_access'] = True
                                break
                    except:
                        continue
                        
        except:
            pass
        
        return result
    
    async def check_all(self, proxy_list: List[str]) -> List[Dict]:
        """Массовая параллельная проверка"""
        if not proxy_list:
            return []
        
        print(f"\n⚡ ПАРАЛЛЕЛЬНАЯ ПРОВЕРКА {len(proxy_list)} ПРОКСИ...")
        print(f"   (500 одновременно, таймаут 1.5 сек)")
        
        start = time.time()
        
        tasks = [self.check_one(proxy) for proxy in proxy_list]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        working = [r for r in results if r['working']]
        ru = [r for r in working if r['ru_access']]
        us = [r for r in working if r['us_access']]
        
        print(f"✅ ЗА {elapsed:.1f} СЕК: {len(working)}/500 рабочих")
        print(f"   🇷🇺 РФ: {len(ru)} | 🇺🇸 США: {len(us)} | 🌍 Глобальных: {len([r for r in working if r['ru_access'] and r['us_access']])}")
        print(f"   Скорость: {len(proxy_list)/elapsed:.0f} прокси/сек\n")
        
        return results
