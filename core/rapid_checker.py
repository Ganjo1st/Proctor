# core/rapid_checker.py - ПРОВЕРКА ПРОКСИ С ГЕО-ОПРЕДЕЛЕНИЕМ, TELEGRAM И ПЛАТФОРМАМИ
import aiohttp
import asyncio
from aiohttp_socks import ProxyConnector, ProxyType
from typing import List, Dict
import time
from colorama import Fore, Style
from core.telegram_checker import TelegramChecker, PlatformChecker


class RapidChecker:
    """Проверка прокси с точным гео-определением, доступом к Telegram и определением платформ"""

    def __init__(self):
        self.test_urls = ['http://httpbin.org/ip']
        self.timeout = aiohttp.ClientTimeout(total=8)
        self.max_concurrent = 200

        # Сайты для проверки доступности
        self.ru_sites = ['https://yandex.ru', 'https://vk.com', 'https://mail.ru']
        self.us_sites = ['https://www.google.com', 'https://www.github.com', 'https://www.microsoft.com']
        
        # Инициализация проверщиков
        self.telegram_checker = TelegramChecker()
        self.platform_checker = PlatformChecker()

    async def check_one(self, proxy: str) -> Dict:
        """Проверка с определением страны, региона, Telegram и платформ"""
        result = {
            'proxy': proxy,
            'working': False,
            'latency': 9999,
            'country': None,
            'country_code': None,
            'region': 'unknown',
            'checked_at': time.time(),
            'ru_access': False,
            'us_access': False,
            'telegram_access': False,
            'telegram_latency': None,
            'mobile_supported': False,
            'desktop_supported': False,
            'platforms': []
        }

        if ':' not in proxy:
            return result

        ip, port = proxy.split(':')
        if not port.isdigit():
            return result

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
                # Базовая проверка
                try:
                    async with session.get(self.test_urls[0]) as resp:
                        if resp.status != 200:
                            return result
                        result['working'] = True
                        result['latency'] = round((time.time() - start) * 1000, 2)
                except:
                    return result

                # Определение страны
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
                        async with session.get(site, timeout=3) as resp:
                            if resp.status == 200:
                                result['ru_access'] = True
                                break
                    except:
                        continue

                # Проверка доступа к американским сайтам
                for site in self.us_sites:
                    try:
                        async with session.get(site, timeout=3) as resp:
                            if resp.status == 200:
                                result['us_access'] = True
                                break
                    except:
                        continue

                # Определение региона
                if result['ru_access'] and result['us_access']:
                    result['region'] = 'global'
                elif result['ru_access']:
                    result['region'] = 'ru'
                elif result['us_access']:
                    result['region'] = 'us'
                elif result['country_code'] == 'RU':
                    result['region'] = 'ru'
                    result['ru_access'] = True
                elif result['country_code'] == 'US':
                    result['region'] = 'us'
                    result['us_access'] = True

        except Exception:
            pass

        # Дополнительные проверки (если прокси рабочий)
        if result['working']:
            # Проверка Telegram
            tg_result = await self.telegram_checker.check_telegram_access(proxy)
            result['telegram_access'] = tg_result['telegram_working']
            result['telegram_latency'] = tg_result['telegram_latency'] if tg_result['telegram_working'] else None

            # Проверка платформ
            platform_result = await self.platform_checker.check_platform(proxy)
            result['mobile_supported'] = platform_result['mobile']
            result['desktop_supported'] = platform_result['desktop']
            result['platforms'] = [p for p, v in platform_result.items() if v and p != 'proxy' and p not in ['mobile', 'desktop']]

        return result

    async def check_all(self, proxy_list: List[str]) -> List[Dict]:
        """Массовая параллельная проверка с ограничением"""
        if not proxy_list:
            return []

        print(f"\n⚡ ПРОВЕРКА {len(proxy_list)} ПРОКСИ С ГЕО-ОПРЕДЕЛЕНИЕМ...")
        start = time.time()

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def check_with_semaphore(proxy):
            async with semaphore:
                return await self.check_one(proxy)

        tasks = [check_with_semaphore(proxy) for proxy in proxy_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for r in results:
            if isinstance(r, Exception):
                continue
            valid_results.append(r)

        elapsed = time.time() - start
        working = [r for r in valid_results if r.get('working')]
        tg_working = [r for r in working if r.get('telegram_access')]
        mobile_working = [r for r in working if r.get('mobile_supported')]
        desktop_working = [r for r in working if r.get('desktop_supported')]
        ru = len([r for r in working if r.get('ru_access')])
        us = len([r for r in working if r.get('us_access')])

        print(f"✅ ЗА {elapsed:.1f} СЕК: {len(working)}/{len(proxy_list)} рабочих")
        print(f"   🇷🇺 РФ доступ: {ru} | 🇺🇸 США доступ: {us}")
        print(f"   📱 Telegram доступ: {len(tg_working)} | Мобильные: {mobile_working} | Десктопные: {desktop_working}")

        return valid_results
