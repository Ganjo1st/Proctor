# core/smart_scraper.py - УМНЫЙ СБОР ПРОКСИ С ПОДДЕРЖКОЙ ПРОКСИ ДЛЯ ЗАПРОСОВ
import re
import asyncio
import httpx
import random
from bs4 import BeautifulSoup
from typing import List, Set, Optional
from fake_useragent import UserAgent
from colorama import Fore, Style

ua = UserAgent()


class SmartScraper:
    """Умный сборщик прокси с фильтрацией и поддержкой прокси для запросов"""

    def __init__(self, working_proxies: Optional[List[str]] = None):
        self.ua = UserAgent()
        self.working_proxies = working_proxies or []
        self.proxy_index = 0

    def _get_next_proxy(self) -> Optional[str]:
        """Получить следующий рабочий прокси для обхода блокировок (round-robin)"""
        if not self.working_proxies:
            return None
        proxy = self.working_proxies[self.proxy_index % len(self.working_proxies)]
        self.proxy_index += 1
        return proxy

    def is_valid_proxy_format(self, proxy: str) -> bool:
        """Проверка формата прокси перед добавлением в очередь"""
        if not proxy or ':' not in proxy:
            return False
        
        parts = proxy.split(':')
        if len(parts) != 2:
            return False
        
        ip, port = parts
        
        # Проверка IP-адреса
        ip_parts = ip.split('.')
        if len(ip_parts) != 4:
            return False
        
        for part in ip_parts:
            if not part.isdigit() or not (0 <= int(part) <= 255):
                return False
        
        # Проверка порта
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            return False
        
        return True

    async def fetch_from_url(self, url: str, source_type: str = 'text', use_proxy: bool = False) -> Set[str]:
        """Сбор прокси из одного источника с возможностью использования прокси"""
        proxies = set()
        proxy_url = None
        
        if use_proxy:
            proxy = self._get_next_proxy()
            if proxy:
                proxy_url = f"http://{proxy}"
                print(f"  🔍 {url.split('/')[-1][:20]} (через прокси {proxy})...", end=' ', flush=True)
            else:
                print(f"  🔍 {url.split('/')[-1][:20]} (нет прокси)...", end=' ', flush=True)
        else:
            print(f"  🔍 {url.split('/')[-1][:20]}...", end=' ', flush=True)
        
        try:
            headers = {'User-Agent': self.ua.random}
            
            # Используем прокси, если указано
            async with httpx.AsyncClient(timeout=30, follow_redirects=True, proxy=proxy_url) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code != 200:
                    print(f"❌ {response.status_code}")
                    return proxies
                
                text = response.text
                
                if source_type == 'html':
                    soup = BeautifulSoup(text, 'html.parser')
                    textarea = soup.find('textarea')
                    if textarea:
                        text = textarea.text
                
                # Ищем все IP:PORT
                pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}\b'
                found = re.findall(pattern, text)
                
                # Фильтруем по формату
                for p in found:
                    if self.is_valid_proxy_format(p):
                        proxies.add(p)
                
                # Если это просто список IP (построчно)
                if not found:
                    lines = text.strip().split('\n')
                    for line in lines[:200]:
                        line = line.strip()
                        if re.match(r'^\d+\.\d+\.\d+\.\d+$', line):
                            for port in ['3128', '8080', '1080']:
                                proxy = f"{line}:{port}"
                                if self.is_valid_proxy_format(proxy):
                                    proxies.add(proxy)
                        elif ':' in line:
                            if self.is_valid_proxy_format(line):
                                proxies.add(line)
                
                print(f"✅ {len(proxies)}")
                return proxies
                
        except Exception as e:
            print(f"⚠️ {str(e)[:20]}")
            return proxies

    async def get_all_proxies(self) -> List[str]:
        """Сбор прокси из всех источников"""
        all_proxies = set()
        
        # Российские источники (часто блокируют, используем прокси)
        ru_sources = [
            ('https://spys.one/en/free-proxy-list/', 'html', True),      # требует прокси
            ('https://openproxy.space/list/ru', 'text', True),            # может требовать прокси
            ('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt', 'text', False),
        ]
        
        # Американские/международные источники
        int_sources = [
            ('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt', 'text', False),
            ('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt', 'text', False),
            ('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt', 'text', False),
            ('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt', 'text', False),
            ('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt', 'text', False),
        ]
        
        # API-источники (проблемные, используем прокси)
        api_sources = [
            ('https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all', 'text', True),
            ('https://www.proxy-list.download/api/v1/get?type=http', 'text', True),
            ('https://www.proxy-list.download/api/v1/get?type=https', 'text', True),
        ]
        
        print("\n🌐 СБОР ИЗ ИСТОЧНИКОВ:")
        
        # Сбор из российских источников
        print("\n  🇷🇺 Российские источники:")
        for url, source_type, use_proxy in ru_sources:
            proxies = await self.fetch_from_url(url, source_type, use_proxy)
            all_proxies.update(proxies)
            await asyncio.sleep(0.5)
        
        # Сбор из международных источников
        print("\n  🌍 Международные источники:")
        for url, source_type, use_proxy in int_sources:
            proxies = await self.fetch_from_url(url, source_type, use_proxy)
            all_proxies.update(proxies)
            await asyncio.sleep(0.5)
        
        # Сбор из API
        print("\n  🌐 API-источники:")
        for url, source_type, use_proxy in api_sources:
            proxies = await self.fetch_from_url(url, source_type, use_proxy)
            all_proxies.update(proxies)
            await asyncio.sleep(0.5)
        
        # Преобразуем в список и перемешиваем
        proxy_list = list(all_proxies)
        random.shuffle(proxy_list)
        
        # Статистика
        print(f"\n{Fore.CYAN}────────────────────────────────────────────────────────────{Style.RESET_ALL}")
        print(f"{Fore.GREEN}📊 ИТОГО собрано: {len(proxy_list)} прокси{Style.RESET_ALL}")
        
        # Подсчёт российских IP (для статистики)
        ru_count = 0
        for proxy in proxy_list[:100]:
            ip = proxy.split(':')[0]
            if ip.startswith('5.') or ip.startswith('95.') or ip.startswith('85.') or ip.startswith('176.'):
                ru_count += 1
        
        print(f"   🇷🇺 Российских источников: 3")
        print(f"   🇷🇺 Найдено российских прокси: ~{ru_count * 10}")
        
        return proxy_list


# Для обратной совместимости
async def get_all_proxies():
    scraper = SmartScraper()
    return await scraper.get_all_proxies()
