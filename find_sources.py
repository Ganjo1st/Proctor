#!/usr/bin/env python3
# find_sources.py - ПОИСК НОВЫХ ИСТОЧНИКОВ ПРОКСИ
import asyncio
import aiohttp
import re
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from colorama import init, Fore, Style

init(autoreset=True)

SOURCES_FILE = 'data/sources.json'
SEARCH_QUERIES = [
    'free proxy list',
    'public proxy servers',
    'socks5 proxy list',
    'http proxy list',
    'бесплатные прокси список',
    'прокси сервера список',
    'proxy list txt',
    'proxies list',
    'fresh proxy list',
]

SEARCH_ENGINES = [
    'https://www.google.com/search?q={}',
    'https://www.bing.com/search?q={}',
    'https://duckduckgo.com/html/?q={}',
]


def load_sources():
    """Загрузка существующих источников"""
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_sources(sources):
    """Сохранение источников"""
    os.makedirs('data', exist_ok=True)
    with open(SOURCES_FILE, 'w') as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)


def is_proxy_source_url(url: str) -> bool:
    """Проверка, является ли URL источником прокси"""
    proxy_patterns = [
        r'proxy', r'proxies', r'free-proxy', r'proxylist',
        r'socks', r'http.*proxy', r'proxy-list'
    ]
    url_lower = url.lower()
    return any(re.search(p, url_lower) for p in proxy_patterns)


async def fetch_url(session, url, headers):
    """Загрузка URL"""
    try:
        async with session.get(url, headers=headers, timeout=10, ssl=False) as response:
            if response.status == 200:
                return await response.text()
    except:
        pass
    return None


async def extract_links_from_page(html, base_url):
    """Извлечение ссылок из HTML"""
    links = set()
    try:
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/'):
                href = base_url.rstrip('/') + href
            elif href.startswith('http'):
                pass
            else:
                continue
            
            if is_proxy_source_url(href):
                # Определяем тип источника
                source_type = 'text'
                if 'html' in href or '/page/' in href:
                    source_type = 'html'
                elif 'api' in href:
                    source_type = 'api'
                
                links.add((href, source_type))
    except:
        pass
    return links


async def search_for_sources():
    """Поиск новых источников в поисковиках"""
    print(f"\n{Fore.YELLOW}🔍 ПОИСК НОВЫХ ИСТОЧНИКОВ...{Style.RESET_ALL}")
    
    ua = UserAgent()
    existing_sources = load_sources()
    existing_urls = {s['url'] for s in existing_sources}
    new_sources = []
    
    async with aiohttp.ClientSession() as session:
        for query in SEARCH_QUERIES:
            print(f"\n  🔎 Поиск: {query}")
            
            for engine in SEARCH_ENGINES:
                url = engine.format(query.replace(' ', '+'))
                headers = {'User-Agent': ua.random}
                
                html = await fetch_url(session, url, headers)
                if html:
                    links = await extract_links_from_page(html, engine.split('?')[0])
                    
                    for link, source_type in links:
                        if link not in existing_urls:
                            new_sources.append({
                                'url': link,
                                'type': source_type,
                                'added': datetime.now().isoformat(),
                                'status': 'pending',
                                'source_query': query
                            })
                            existing_urls.add(link)
                            print(f"    ✅ Найден: {link[:60]}...")
                
                await asyncio.sleep(2)  # Вежливость к поисковикам
    
    return new_sources


async def verify_source(url: str, source_type: str) -> bool:
    """Проверка работоспособности источника"""
    try:
        headers = {'User-Agent': UserAgent().random}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    # Проверяем наличие прокси
                    pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}\b'
                    if re.search(pattern, text):
                        return True
    except:
        pass
    return False


async def main():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}      PROCTOR SMART - ПОИСК НОВЫХ ИСТОЧНИКОВ         {Fore.CYAN}║
║{Fore.WHITE}      Автоматическое добавление новых прокси-сайтов   {Fore.CYAN}║
║{Fore.GREEN}      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    # Загружаем существующие источники
    existing = load_sources()
    print(f"📊 Существующих источников: {len(existing)}")
    
    # Ищем новые
    new_sources = await search_for_sources()
    
    if not new_sources:
        print(f"\n{Fore.YELLOW}ℹ️ Новых источников не найдено{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.GREEN}✅ Найдено {len(new_sources)} потенциальных источников{Style.RESET_ALL}")
    
    # Проверяем каждый
    print(f"\n{Fore.YELLOW}🔍 ПРОВЕРКА ИСТОЧНИКОВ...{Style.RESET_ALL}")
    verified_sources = []
    
    for src in new_sources:
        print(f"  Проверяю {src['url'][:50]}...", end=' ')
        if await verify_source(src['url'], src['type']):
            src['status'] = 'active'
            verified_sources.append(src)
            print(f"✅ РАБОТАЕТ")
        else:
            src['status'] = 'failed'
            print(f"❌ НЕ РАБОТАЕТ")
        
        await asyncio.sleep(1)
    
    # Добавляем проверенные источники
    if verified_sources:
        all_sources = existing + verified_sources
        save_sources(all_sources)
        
        print(f"\n{Fore.GREEN}✅ ДОБАВЛЕНО {len(verified_sources)} НОВЫХ ИСТОЧНИКОВ:{Style.RESET_ALL}")
        for src in verified_sources:
            print(f"  📌 {src['url']}")
            print(f"     Тип: {src['type']}, найден по запросу: {src['source_query']}")
    else:
        print(f"\n{Fore.YELLOW}⚠️ Не найдено рабочих источников{Style.RESET_ALL}")


if __name__ == "__main__":
    asyncio.run(main())
