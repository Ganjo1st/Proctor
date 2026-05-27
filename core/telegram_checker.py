# core/telegram_checker.py - ПРОВЕРКА ПРОКСИ ДЛЯ TELEGRAM (MTProto)
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector, ProxyType
from typing import Dict, List
import time


class TelegramChecker:
    """Проверка прокси для Telegram (MTProto и HTTP)"""
    
    def __init__(self):
        # Telegram API endpoints для проверки
        self.telegram_endpoints = [
            'https://api.telegram.org/bot',
            'https://core.telegram.org',
            'https://t.me',
        ]
        self.timeout = aiohttp.ClientTimeout(total=10)
    
    async def check_telegram_access(self, proxy: str) -> Dict:
        """Проверка доступа к Telegram через прокси"""
        result = {
            'proxy': proxy,
            'telegram_working': False,
            'telegram_latency': float('inf'),
            'telegram_error': None
        }
        
        proxy_ip, proxy_port = proxy.split(':')
        
        try:
            start = time.time()
            connector = ProxyConnector(
                proxy_type=ProxyType.HTTP,
                host=proxy_ip,
                port=int(proxy_port),
                rdns=True,
                force_close=True
            )
            
            async with aiohttp.ClientSession(connector=connector, timeout=self.timeout) as session:
                for endpoint in self.telegram_endpoints:
                    try:
                        async with session.get(endpoint) as response:
                            if response.status in [200, 301, 302, 403]:
                                # 403 тоже нормально для Telegram (блокировка ботов)
                                result['telegram_working'] = True
                                result['telegram_latency'] = round((time.time() - start) * 1000, 2)
                                return result
                    except:
                        continue
        except Exception as e:
            result['telegram_error'] = str(e)[:50]
        
        return result


class PlatformChecker:
    """Проверка прокси на разных платформах (мобильные vs десктопные)"""
    
    def __init__(self):
        self.user_agents = {
            'mobile_android': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'mobile_iphone': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'desktop_windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'desktop_mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'desktop_linux': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        self.test_url = 'https://httpbin.org/user-agent'
        self.timeout = aiohttp.ClientTimeout(total=8)
    
    async def check_platform(self, proxy: str) -> Dict:
        """Проверка, на каких платформах работает прокси"""
        result = {
            'proxy': proxy,
            'mobile': False,
            'desktop': False,
            'mobile_android': False,
            'mobile_iphone': False,
            'desktop_windows': False,
            'desktop_mac': False,
            'desktop_linux': False,
        }
        
        proxy_ip, proxy_port = proxy.split(':')
        
        for platform, user_agent in self.user_agents.items():
            try:
                connector = ProxyConnector(
                    proxy_type=ProxyType.HTTP,
                    host=proxy_ip,
                    port=int(proxy_port),
                    rdns=True,
                    force_close=True
                )
                
                async with aiohttp.ClientSession(connector=connector, timeout=self.timeout) as session:
                    headers = {'User-Agent': user_agent}
                    async with session.get(self.test_url, headers=headers) as response:
                        if response.status == 200:
                            result[platform] = True
                            if platform.startswith('mobile'):
                                result['mobile'] = True
                            else:
                                result['desktop'] = True
            except:
                pass
        
        return result
