# core/rapid_checker.py - БЫСТРАЯ ПРОВЕРКА ТОЛЬКО ДЛЯ НОВЫХ ПРОКСИ
import aiohttp
import asyncio
from aiohttp_socks import ProxyConnector, ProxyType
from typing import List, Dict
import time

class RapidChecker:
    """Быстрая проверка прокси (только для новых из непроверенных источников)"""
    
    def __init__(self):
        self.test_urls = ['http://httpbin.org/ip']
        self.timeout = aiohttp.ClientTimeout(total=2)
        self.max_concurrent = 500
    
    async def check_one(self, proxy: str) -> Dict:
        """Мгновенная проверка одного прокси"""
        result = {
            'proxy': proxy,
            'working': False,
            'latency': 9999,
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
                async with session.get(self.test_urls[0]) as resp:
                    if resp.status == 200:
                        result['working'] = True
                        result['latency'] = round((time.time() - start) * 1000, 2)
        except:
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
        
        print(f"✅ ЗА {elapsed:.1f} СЕК: {len(working)}/{len(proxy_list)} рабочих")
        return results
