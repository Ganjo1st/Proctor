# core/health_checker.py - ФОНОВАЯ ПРОВЕРКА РАБОТОСПОСОБНОСТИ ВСЕХ ПРОКСИ
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector, ProxyType
from typing import List, Dict
from datetime import datetime
import time


class HealthChecker:
    """Проверка здоровья всех прокси в базе"""
    
    def __init__(self, db, max_concurrent: int = 100):
        self.db = db
        self.max_concurrent = max_concurrent
        self.test_url = 'http://httpbin.org/ip'
        self.timeout = aiohttp.ClientTimeout(total=5)
    
    async def check_single_proxy(self, proxy: str) -> tuple:
        """Проверка одного прокси на работоспособность"""
        proxy_ip, proxy_port = proxy.split(':')
        try:
            connector = ProxyConnector(
                proxy_type=ProxyType.HTTP,
                host=proxy_ip,
                port=int(proxy_port),
                rdns=True,
                force_close=True
            )
            async with aiohttp.ClientSession(connector=connector, timeout=self.timeout) as session:
                start = time.time()
                async with session.get(self.test_url) as response:
                    if response.status == 200:
                        latency = (time.time() - start) * 1000
                        return proxy, True, latency
        except:
            pass
        return proxy, False, float('inf')
    
    async def check_all_proxies(self) -> Dict[str, Dict]:
        """Проверка всех прокси в базе"""
        proxies_dict = self.db.db.get('proxies', {})
        working_proxies = {p: d for p, d in proxies_dict.items() if d.get('working')}
        
        if not working_proxies:
            print("  ⚠️ Нет прокси для проверки")
            return {}
        
        print(f"  🔍 Проверяю {len(working_proxies)} прокси на работоспособность...")
        
        # Создаём семафор для ограничения конкурентности
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def check_with_semaphore(proxy):
            async with semaphore:
                return await self.check_single_proxy(proxy)
        
        tasks = [check_with_semaphore(proxy) for proxy in working_proxies.keys()]
        results = await asyncio.gather(*tasks)
        
        # Обновляем статусы в базе
        updated = {'alive': 0, 'dead': 0}
        for proxy, is_alive, latency in results:
            if proxy in self.db.db['proxies']:
                old_status = self.db.db['proxies'][proxy]['working']
                self.db.db['proxies'][proxy]['working'] = is_alive
                self.db.db['proxies'][proxy]['last_check'] = datetime.now().isoformat()
                if is_alive:
                    self.db.db['proxies'][proxy]['latency'] = round(latency, 2)
                    updated['alive'] += 1
                else:
                    updated['dead'] += 1
        
        self.db.save_db()
        print(f"  ✅ Живых: {updated['alive']}, Мёртвых: {updated['dead']}")
        
        return updated
    
    async def get_global_proxies(self) -> List[str]:
        """Получить список глобальных прокси (работают и в РФ, и в США)"""
        global_proxies = []
        for proxy, data in self.db.db.get('proxies', {}).items():
            if data.get('working'):
                ru = data.get('ru_access', False)
                us = data.get('us_access', False)
                if ru and us:
                    global_proxies.append(proxy)
        return global_proxies
    
    async def get_best_proxy(self) -> str:
        """Получить самый быстрый глобальный прокси для обхода блокировок"""
        global_proxies = await self.get_global_proxies()
        if not global_proxies:
            return None
        
        # Сортируем по задержке
        global_proxies.sort(key=lambda p: self.db.db['proxies'][p].get('latency', 9999))
        return global_proxies[0] if global_proxies else None
