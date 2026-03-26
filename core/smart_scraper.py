# core/smart_scraper.py - УМНЫЙ СБОР БЕЗ АВТООТКЛЮЧЕНИЯ
import requests
import re
import json
import os
from fake_useragent import UserAgent
from typing import List, Set, Dict, Tuple
from bs4 import BeautifulSoup
from datetime import datetime
import httpx
import asyncio

class SmartScraper:
    """Умный сбор прокси из всех источников"""
    
    def __init__(self):
        self.session = requests.Session()
        ua = UserAgent()
        self.session.headers.update({'User-Agent': ua.random})
        
        # ВСЕ источники (без автоотключения)
        self.sources = {
            'proxymania': {
                'url': 'https://proxymania.su/free-proxy',
                'type': 'html'
            },
            'thespeedx_http': {
                'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                'type': 'text'
            },
            'thespeedx_socks4': {
                'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
                'type': 'text'
            },
            'thespeedx_socks5': {
                'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
                'type': 'text'
            },
            'jetkai_http': {
                'url': 'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
                'type': 'text'
            },
            'ru_scrape': {
                'url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&country=RU',
                'type': 'text'
            },
            'us_scrape': {
                'url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&country=US',
                'type': 'text'
            }
        }
        
        # API-источники
        self.api_sources = [
            ('proxyscrape_api', 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all'),
            ('pubproxy', 'https://pubproxy.com/api/proxy?limit=30&format=txt&http=true&https=true'),
            ('proxyscan', 'https://www.proxyscan.io/download?type=http'),
        ]
    
    def fetch_from_html(self, url: str) -> Set[str]:
        """Парсинг HTML страницы (для proxymania)"""
        proxies = set()
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return proxies
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            if not table:
                return proxies
            
            rows = table.find_all('tr')[1:]  # Пропускаем заголовок
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    proxy_text = cols[0].get_text(strip=True)
                    if ':' in proxy_text:
                        proxies.add(proxy_text)
            
        except Exception:
            pass
        
        return proxies
    
    def fetch_from_text(self, url: str) -> Set[str]:
        """Сбор из текстового источника"""
        proxies = set()
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code != 200:
                return proxies
            
            text = response.text
            ip_port_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}\b'
            found = re.findall(ip_port_pattern, text)
            proxies.update(found)
            
        except Exception:
            pass
        
        return proxies
    
    async def fetch_from_api_async(self, url: str, source_name: str) -> List[str]:
        """Асинхронная загрузка из API-источников"""
        proxies = []
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    if 'text/plain' in response.headers.get('content-type', ''):
                        proxies = [p.strip() for p in response.text.split('\n') if p.strip() and ':' in p]
                    else:
                        try:
                            data = response.json()
                            if 'proxies' in data:
                                proxies = [f"{p['ip']}:{p['port']}" for p in data['proxies']]
                        except:
                            pass
        except Exception:
            pass
        
        return proxies
    
    async def get_api_proxies(self) -> List[Tuple[str, str]]:
        """Сбор прокси из API-источников"""
        all_proxies = []
        print("\n  🌐 API-источники:")
        
        for name, url in self.api_sources:
            print(f"    🔍 {name}...", end=' ')
            proxies = await self.fetch_from_api_async(url, name)
            for proxy in proxies:
                all_proxies.append((proxy, f"api_{name}"))
            print(f"✅ {len(proxies)}")
        
        return all_proxies
    
    def get_all_proxies(self) -> List[str]:
        """Сбор всех прокси (только адреса)"""
        proxies_with_sources = self.get_all_proxies_with_sources()
        return [p for p, _ in proxies_with_sources]
    
    def get_all_proxies_with_sources(self) -> List[Tuple[str, str]]:
        """Сбор прокси с указанием источника"""
        print("\n🧠 УМНЫЙ СБОР ПРОКСИ (с источниками)")
        print("─" * 60)
        
        all_proxies = []
        
        # 1. Основные источники
        for name, source in self.sources.items():
            print(f"  🔍 {name}...", end=' ')
            
            if source['type'] == 'html':
                proxies = self.fetch_from_html(source['url'])
            else:
                proxies = self.fetch_from_text(source['url'])
            
            for proxy in proxies:
                all_proxies.append((proxy, name))
            
            status = f"✅ {len(proxies)}" if proxies else "❌ 0"
            print(status)
        
        # 2. API-источники (асинхронные)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        api_proxies = loop.run_until_complete(self.get_api_proxies())
        loop.close()
        
        all_proxies.extend(api_proxies)
        
        print("─" * 60)
        print(f"📊 ИТОГО собрано: {len(all_proxies)} прокси\n")
        
        return all_proxies
