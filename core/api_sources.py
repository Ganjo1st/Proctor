# core/api_sources.py - API-источники для получения прокси
import httpx
import asyncio
from typing import List
from bs4 import BeautifulSoup

class APISourceFetcher:
    """Сбор прокси из API-источников"""
    
    def __init__(self):
        self.sources = [
            {
                'name': 'proxyscrape',
                'url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all',
                'type': 'text'
            },
            {
                'name': 'freeproxylist',
                'url': 'https://free-proxy-list.net/',
                'type': 'html'
            },
            {
                'name': 'pubproxy',
                'url': 'https://pubproxy.com/api/proxy?limit=30&format=txt&http=true&https=true',
                'type': 'text'
            },
            {
                'name': 'proxyscan',
                'url': 'https://www.proxyscan.io/download?type=http',
                'type': 'text'
            }
        ]
    
    async def fetch_text(self, url: str) -> List[str]:
        """Загрузка текстового списка"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    proxies = [p.strip() for p in response.text.split('\n') if p.strip() and ':' in p]
                    return proxies
        except Exception as e:
            print(f"  ❌ Ошибка {url}: {e}")
        return []
    
    async def fetch_html(self, url: str) -> List[str]:
        """Парсинг HTML страницы"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Ищем текст в textarea или таблице
                    textarea = soup.find('textarea')
                    if textarea:
                        proxies = [p.strip() for p in textarea.text.split('\n') if p.strip() and ':' in p]
                        return proxies
        except Exception as e:
            print(f"  ❌ Ошибка {url}: {e}")
        return []
    
    async def get_all(self) -> List[str]:
        """Сбор прокси из всех API-источников"""
        print("\n🌐 СБОР ИЗ API-ИСТОЧНИКОВ:")
        all_proxies = set()
        
        for source in self.sources:
            print(f"  🔍 {source['name']}...", end=' ')
            if source['type'] == 'text':
                proxies = await self.fetch_text(source['url'])
            else:
                proxies = await self.fetch_html(source['url'])
            
            all_proxies.update(proxies)
            print(f"✅ {len(proxies)}")
        
        print(f"📊 ИТОГО из API: {len(all_proxies)} прокси\n")
        return list(all_proxies)
