# core/smart_scraper.py - УМНЫЙ СБОР С АВТООТКЛЮЧЕНИЕМ ИСТОЧНИКОВ
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
    """Умный сбор прокси с оценкой эффективности источников"""
    
    def __init__(self):
        self.session = requests.Session()
        ua = UserAgent()
        self.session.headers.update({'User-Agent': ua.random})
        
        # Источники с их эффективностью
        self.sources = {
            'proxymania': {
                'url': 'https://proxymania.su/free-proxy',
                'type': 'html',
                'success_rate': 0,
                'checks': 0,
                'enabled': True,
                'last_success': None
            },
            'thespeedx_http': {
                'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                'type': 'text',
                'success_rate': 0,
                'checks': 0,
                'enabled': True,
                'last_success': None
            },
            'thespeedx_socks4': {
                'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
                'type': 'text',
                'success_rate': 0,
                'checks': 0,
                'enabled': True,
                'last_success': None
            },
            'thespeedx_socks5': {
                'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
                'type': 'text',
                'success_rate': 0,
                'checks': 0,
                'enabled': True,
                'last_success': None
            },
            'jetkai_http': {
                'url': 'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
                'type': 'text',
                'success_rate': 0,
                'checks': 0,
                'enabled': True,
                'last_success': None
            },
            'ru_scrape': {
                'url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&country=RU',
                'type': 'text',
                'success_rate': 0,
                'checks': 0,
                'enabled': True,
                'last_success': None
            },
            'us_scrape': {
                'url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&country=US',
                'type': 'text',
                'success_rate': 0,
                'checks': 0,
                'enabled': True,
                'last_success': None
            }
        }
        
        # Файл для сохранения статистики источников
        self.stats_file = 'data/source_stats.json'
        self.load_stats()
    
    def load_stats(self):
        """Загрузка статистики источников"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    saved = json.load(f)
                    for name, stats in saved.items():
                        if name in self.sources:
                            self.sources[name]['success_rate'] = stats.get('success_rate', 0)
                            self.sources[name]['checks'] = stats.get('checks', 0)
                            self.sources[name]['enabled'] = stats.get('enabled', True)
            except:
                pass
    
    def save_stats(self):
        """Сохранение статистики источников"""
        os.makedirs('data', exist_ok=True)
        to_save = {}
        for name, data in self.sources.items():
            to_save[name] = {
                'success_rate': data['success_rate'],
                'checks': data['checks'],
                'enabled': data['enabled'],
                'last_success': data['last_success']
            }
        with open(self.stats_file, 'w') as f:
            json.dump(to_save, f, indent=2)
    
    def update_source_stats(self, source_name: str, found_count: int):
        """Обновление статистики источника"""
        source = self.sources[source_name]
        source['checks'] += 1
        
        # Обновляем успешность
        old_rate = source['success_rate']
        new_rate = (old_rate * (source['checks'] - 1) + found_count) / source['checks']
        source['success_rate'] = new_rate
        
        if found_count > 0:
            source['last_success'] = datetime.now().isoformat()
        
        # Отключаем источник, если за 5 проверок не дал >1 прокси
        if source['checks'] >= 5 and source['success_rate'] < 1.0:
            if source['enabled']:
                print(f"  ⚠️ Источник {source_name} отключён (мало прокси: {source['success_rate']:.1f}/проверку)")
                source['enabled'] = False
        
        self.save_stats()
    
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
        api_sources = [
            ('proxyscrape', 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all'),
            ('pubproxy', 'https://pubproxy.com/api/proxy?limit=30&format=txt&http=true&https=true'),
            ('proxyscan', 'https://www.proxyscan.io/download?type=http'),
        ]
        
        all_proxies = []
        print("\n  🌐 API-источники:")
        
        for name, url in api_sources:
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
            if not source['enabled']:
                print(f"  ⏭️ {name} - ОТКЛЮЧЁН")
                continue
            
            print(f"  🔍 {name}...", end=' ')
            
            if source['type'] == 'html':
                proxies = self.fetch_from_html(source['url'])
            else:
                proxies = self.fetch_from_text(source['url'])
            
            self.update_source_stats(name, len(proxies))
            
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
        print(f"📊 ИТОГО собрано: {len(all_proxies)} прокси")
        print(f"   Активных источников: {sum(1 for s in self.sources.values() if s['enabled'])}/{len(self.sources)}")
        print(f"   API-источников: 3\n")
        
        return all_proxies
