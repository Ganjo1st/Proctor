# core/rapid_checker.py - СУПЕР-БЫСТРАЯ ПАРАЛЛЕЛЬНАЯ ПРОВЕРКА
import aiohttp
import asyncio
from aiohttp_socks import ProxyConnector, ProxyType
from typing import List, Dict
import time

class RapidChecker:
    """Максимально быстрая параллельная проверка прокси"""
    
    def __init__(self):
        # Только самые быстрые сайты
        self.test_urls = [
            'http://httpbin.org/ip',
            'https://cloudflare.com/cdn-cgi/trace',
        ]
        
        # 1.5 секунды на прокси - жёсткий таймаут!
        self.timeout = aiohttp.ClientTimeout(total=1.5)
        self.max_concurrent = 500  # 500 прокси одновременно!
    
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
                # Пробуем первый URL
                try:
                    async with session.get(self.test_urls[0]) as resp:
                        if resp.status == 200:
                            result['working'] = True
                            result['latency'] = round((time.time() - start) * 1000, 2)
                            return result
                except:
                    pass
                
                # Пробуем второй URL
                try:
                    async with session.get(self.test_urls[1]) as resp:
                        if resp.status == 200:
                            result['working'] = True
                            result['latency'] = round((time.time() - start) * 1000, 2)
                except:
                    pass
                        
        except:
            pass
        
        return result
    
    async def check_all(self, proxy_list: List[str]) -> List[Dict]:
        """МАССИВНАЯ ПАРАЛЛЕЛЬНАЯ ПРОВЕРКА - ВСЕ СРАЗУ"""
        if not proxy_list:
            return []
        
        print(f"\n⚡ ПАРАЛЛЕЛЬНАЯ ПРОВЕРКА {len(proxy_list)} ПРОКСИ...")
        print(f"   (500 одновременно, таймаут 1.5 сек)")
        
        start = time.time()
        
        # СОЗДАЁМ ВСЕ ЗАДАЧИ ПАРАЛЛЕЛЬНО
        tasks = [self.check_one(proxy) for proxy in proxy_list]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        working = [r for r in results if r['working']]
        
        print(f"✅ ЗА {elapsed:.1f} СЕК: {len(working)}/{len(proxy_list)} рабочих")
        print(f"   Скорость: {len(proxy_list)/elapsed:.0f} прокси/сек\n")
        
        return results
