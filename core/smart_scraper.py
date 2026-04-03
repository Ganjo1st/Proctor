# core/smart_scraper.py - УМНЫЙ СБОР ПРОКСИ С ИСПОЛЬЗОВАНИЕМ ГЛОБАЛЬНЫХ ПРОКСИ
import re
import asyncio
import httpx
import random
import json
import os
from bs4 import BeautifulSoup
from typing import List, Set, Optional
from fake_useragent import UserAgent
from colorama import Fore, Style
from core.health_checker import HealthChecker

ua = UserAgent()


class SmartScraper:
    """Умный сборщик прокси с использованием глобальных прокси для обхода"""

    def __init__(self, db=None):
        self.ua = UserAgent()
        self.db = db
        self.sources_file = os.path.join('data', 'sources.json')
        self.current_proxy = None
        self.bad_proxies = set()
        self.health_checker = HealthChecker(db) if db else None

    async def get_best_global_proxy(self) -> Optional[str]:
        """Получить лучший глобальный прокси из базы"""
        if not self.health_checker:
            return None
        
        proxy = await self.health_checker.get_best_proxy()
        if proxy and proxy not in self.bad_proxies:
            return proxy
        return None

    def mark_proxy_bad(self, proxy: str):
        """Отметить прокси как плохой для текущей сессии"""
        self.bad_proxies.add(proxy)

    def is_valid_proxy_format(self, proxy: str) -> bool:
        """Проверка формата прокси"""
        if not proxy or ':' not in proxy:
            return False
        
        parts = proxy.split(':')
        if len(parts) != 2:
            return False
        
        ip, port = parts
        
        ip_parts = ip.split('.')
        if len(ip_parts) != 4:
            return False
        
        for part in ip_parts:
            if not part.isdigit() or not (0 <= int(part) <= 255):
                return False
        
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            return False
        
        return True

    def load_dynamic_sources(self) -> List[tuple]:
        """Загрузка динамических источников из sources.json"""
        sources = []
        if os.path.exists(self.sources_file):
            try:
                with open(self.sources_file, 'r') as f:
                    data = json.load(f)
                    for s in data:
                        if s.get('status') == 'active':
                            sources.append((s['url'], s.get('type', 'text'), True))
            except:
                pass
        return sources

    async def fetch_from_url(self, url: str, source_type: str = 'text', use_proxy: bool = False) -> Set[str]:
        """Сбор прокси из одного источника с возможностью использования прокси"""
        proxies = set()
        proxy_url = None
        proxy_used = None
        
        if use_proxy:
            # Берём лучший глобальный прокси из базы
            proxy_used = await self.get_best_global_proxy()
            if proxy_used:
                proxy_url = f"http://{proxy_used}"
                print(f"  🔍 {url.split('/')[-1][:20]} (через прокси {proxy_used})...", end=' ', flush=True)
            else:
                print(f"  🔍 {url.split('/')[-1][:20]} (нет прокси)...", end=' ', flush=True)
        else:
            print(f"  🔍 {url.split('/')[-1][:20]}...", end=' ', flush=True)
        
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                'Connection': 'keep-alive',
            }
            
            async with httpx.AsyncClient(timeout=30, follow_redirects=True, proxy=proxy_url, verify=False) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code != 200:
                    if proxy_used:
                        self.mark_proxy_bad(proxy_used)
                    print(f"❌ {response.status_code}")
                    return proxies
                
                text = response.text
                
                if source_type == 'html':
                    soup = BeautifulSoup(text, 'html.parser')
                    textarea = soup.find('textarea')
                    if textarea:
                        text = textarea.text
                    else:
                        pre = soup.find('pre')
                        if pre:
                            text = pre.text
                    # Для табличных сайтов
                    table = soup.find('table')
                    if table:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                ip_cell = cells[0].text.strip()
                                port_cell = cells[1].text.strip()
                                if ip_cell and port_cell:
                                    proxy = f"{ip_cell}:{port_cell}"
                                    if self.is_valid_proxy_format(proxy):
                                        proxies.add(proxy)
                
                pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}\b'
                found = re.findall(pattern, text)
                
                for p in found:
                    if self.is_valid_proxy_format(p):
                        proxies.add(p)
                
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
            if proxy_used:
                self.mark_proxy_bad(proxy_used)
            print(f"⚠️ {str(e)[:20]}")
            return proxies

    async def get_all_proxies(self) -> List[str]:
        """Сбор прокси из всех источников"""
        all_proxies = set()
        
        # ОСНОВНЫЕ НАДЁЖНЫЕ ИСТОЧНИКИ
        reliable_sources = [
            ('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt', 'text', False),
            ('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt', 'text', False),
            ('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt', 'text', False),
            ('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt', 'text', False),
            ('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt', 'text', False),
            ('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt', 'text', False),
        ]
        
        # FALLBACK ИСТОЧНИКИ
        fallback_sources = [
            ('https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt', 'text', False),
            ('https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt', 'text', False),
            ('https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt', 'text', False),
        ]
        
        # РОССИЙСКИЕ СПЕЦИАЛИЗИРОВАННЫЕ ИСТОЧНИКИ
        ru_specialized_sources = [
            ('https://raw.githubusercontent.com/lkxshaw1334/fresh-proxy-list/main/proxies_RU.txt', 'text', False),
            ('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt', 'text', False),
            ('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt', 'text', False),
            ('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt', 'text', False),
            ('https://api.proxyscrape.com/v2/?request=getproxies&country=RU', 'text', False),
            ('https://raw.githubusercontent.com/kort0881/telegram-proxy-collector/main/proxy_ru.txt', 'text', False),
            ('https://proxymania.su/free-proxy', 'html', False),
            ('https://free-proxy-list.net/ru/', 'html', False),
            ('https://redscrape.com/free-proxy-list', 'text', False),
            ('https://flamingoproxies.com/free-proxies', 'text', False),
            ('https://free-proxy-list.net/', 'text', False),
            ('https://htmlweb.ru/analiz/proxy_list.php', 'html', False),
            ('https://hidemium.io/free-proxy/', 'text', False),
        ]
        
        # РОССИЙСКИЕ ИСТОЧНИКИ (требуют прокси)
        ru_sources = [
            ('https://2ip.ru/proxy/', 'html', True),
            ('https://spys.one/en/free-proxy-list/', 'html', True),
        ]
        
        print("\n🌐 СБОР ИЗ ИСТОЧНИКОВ:")
        
        # Сбор из основных источников
        print("\n  📡 Основные источники:")
        for url, source_type, use_proxy in reliable_sources:
            proxies = await self.fetch_from_url(url, source_type, use_proxy)
            all_proxies.update(proxies)
            await asyncio.sleep(0.3)
        
        # Сбор из российских специализированных источников
        print("\n  🇷🇺 Российские специализированные источники:")
        for url, source_type, use_proxy in ru_specialized_sources:
            proxies = await self.fetch_from_url(url, source_type, use_proxy)
            all_proxies.update(proxies)
            await asyncio.sleep(0.3)
        
        # Сбор из российских источников (с прокси)
        print("\n  🇷🇺 Российские источники (с прокси):")
        for url, source_type, use_proxy in ru_sources:
            proxies = await self.fetch_from_url(url, source_type, use_proxy)
            all_proxies.update(proxies)
            await asyncio.sleep(0.5)
        
        # Если собрали мало, подключаем fallback
        if len(all_proxies) < 1000:
            print("\n  🔄 Fallback источники:")
            for url, source_type, use_proxy in fallback_sources:
                proxies = await self.fetch_from_url(url, source_type, use_proxy)
                all_proxies.update(proxies)
                await asyncio.sleep(0.3)
        
        # Загружаем динамические источники из sources.json
        dynamic_sources = self.load_dynamic_sources()
        if dynamic_sources:
            print("\n  🔍 Динамические источники:")
            for url, source_type, use_proxy in dynamic_sources:
                proxies = await self.fetch_from_url(url, source_type, use_proxy)
                all_proxies.update(proxies)
                await asyncio.sleep(0.5)
        
        proxy_list = list(all_proxies)
        random.shuffle(proxy_list)
        
        print(f"\n{Fore.CYAN}────────────────────────────────────────────────────────────{Style.RESET_ALL}")
        print(f"{Fore.GREEN}📊 ИТОГО собрано: {len(proxy_list)} прокси{Style.RESET_ALL}")
        
        # Подсчёт российских IP
        ru_count = 0
        ru_ranges = ['5.', '31.', '37.', '46.', '62.', '77.', '78.', '79.', '80.', '81.', '82.', '83.', '84.', '85.', '86.', '87.', '88.', '89.', '90.', '91.', '92.', '93.', '94.', '95.', '109.', '128.', '129.', '130.', '131.', '132.', '133.', '134.', '135.', '136.', '137.', '138.', '139.', '140.', '141.', '142.', '143.', '144.', '145.', '146.', '147.', '148.', '149.', '150.', '151.', '152.', '153.', '154.', '155.', '156.', '157.', '158.', '159.', '160.', '161.', '162.', '163.', '164.', '165.', '166.', '167.', '168.', '169.', '170.', '171.', '172.', '173.', '174.', '175.', '176.', '178.', '185.', '188.', '193.', '194.', '195.', '212.', '213.', '217.']
        
        for proxy in proxy_list[:100]:
            ip = proxy.split(':')[0]
            for prefix in ru_ranges:
                if ip.startswith(prefix):
                    ru_count += 1
                    break
        
        print(f"   🇷🇺 Найдено российских прокси: ~{ru_count * 10}")
        
        return proxy_list
