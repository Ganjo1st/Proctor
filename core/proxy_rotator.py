# core/proxy_rotator.py - УМНЫЙ ПЕРЕБОР ПРОКСИ ДЛЯ ТРУДНОДОСТУПНЫХ САЙТОВ
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector, ProxyType
from typing import Optional, List, Dict, Tuple
import time


class ProxyRotator:
    """Перебор прокси для доступа к труднодоступным источникам"""
    
    def __init__(self, db, max_attempts: int = 10):
        self.db = db
        self.max_attempts = max_attempts
        self.bad_proxies = set()
        self.timeout = aiohttp.ClientTimeout(total=15)
    
    async def get_working_proxies(self) -> List[str]:
        """Получить список рабочих прокси из базы"""
        working = []
        for proxy, data in self.db.db.get('proxies', {}).items():
            if data.get('working'):
                # Приоритет глобальным прокси
                ru = data.get('ru_access', False)
                us = data.get('us_access', False)
                score = 2 if (ru and us) else 1
                latency = data.get('latency', 9999)
                working.append((score, proxy, latency))
        
        # Сортируем по приоритету (глобальные первые) и скорости
        working.sort(key=lambda x: (-x[0], x[2]))
        return [p[1] for p in working[:20]]  # Берём топ-20
    
    async def fetch_with_proxy_rotation(self, url: str, headers: dict) -> Tuple[Optional[str], Optional[str]]:
        """Пытается получить URL через разные прокси, перебирая их"""
        proxies = await self.get_working_proxies()
        
        # Если нет рабочих прокси, пробуем без прокси
        if not proxies:
            print(f"  ⚠️ Нет рабочих прокси, пробую напрямую...")
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(url, headers=headers, ssl=False) as response:
                        if response.status == 200:
                            return await response.text(), None
            except Exception as e:
                pass
            return None, None
        
        # Перебираем прокси
        for i, proxy in enumerate(proxies[:self.max_attempts]):
            if proxy in self.bad_proxies:
                continue
            
            proxy_ip, proxy_port = proxy.split(':')
            print(f"    🔄 Попытка {i+1}/{min(len(proxies), self.max_attempts)} через {proxy}...", end=' ', flush=True)
            
            try:
                connector = ProxyConnector(
                    proxy_type=ProxyType.HTTP,
                    host=proxy_ip,
                    port=int(proxy_port),
                    rdns=True,
                    force_close=True
                )
                
                async with aiohttp.ClientSession(connector=connector, timeout=self.timeout) as session:
                    async with session.get(url, headers=headers, ssl=False) as response:
                        if response.status == 200:
                            text = await response.text()
                            print(f"✅ УСПЕХ!")
                            return text, proxy
                        else:
                            print(f"❌ {response.status}")
                            self.bad_proxies.add(proxy)
            except Exception as e:
                print(f"⚠️ {str(e)[:20]}")
                self.bad_proxies.add(proxy)
        
        print(f"    ❌ Все прокси не сработали")
        return None, None
    
    def reset_bad_proxies(self):
        """Сбросить список плохих прокси (для новой сессии)"""
        self.bad_proxies.clear()
