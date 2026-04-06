#!/usr/bin/env python3
# find_sources.py - ПОИСК НОВЫХ ИСТОЧНИКОВ ПРОКСИ С РОТАЦИЕЙ ПРОКСИ
import asyncio
import aiohttp
import re
import json
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from colorama import init, Fore, Style

# Добавляем core в путь
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import ProxyDatabase
from core.proxy_rotator import ProxyRotator

init(autoreset=True)

SOURCES_FILE = 'data/sources.json'

# Список доверенных доменов
TRUSTED_DOMAINS = [
    'raw.githubusercontent.com',
    'github.com',
    'gitlab.com',
    'bitbucket.org',
    'pastebin.com',
    'textbin.net',
    'ghostbin.com',
    'controlc.com',
]

# Расширенные поисковые запросы
SEARCH_QUERIES = [
    'intitle:"index of" "proxy" txt',
    'intitle:"index of" "socks" txt',
    'intitle:"index of" "http" txt',
    '"free proxy list" filetype:txt',
    '"free proxy list" filetype:csv',
    '"proxies" filetype:txt',
    '"socks5" filetype:txt',
    'free proxy list site:github.com',
    'proxies list site:github.com',
    'socks5 proxy list site:github.com',
    'free proxy list site:pastebin.com',
    'proxy list site:controlc.com',
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


def is_valid_source_url(url: str) -> bool:
    """Проверка, является ли URL источником прокси"""
    url_lower = url.lower()
    
    # Исключаем поисковые системы и мусор
    exclude_patterns = [
        'google.com/search', 'bing.com/search', 'duckduckgo.com',
        'yandex.ru/search', 'yahoo.com/search',
        '?', '&', '#', 'javascript:', 'mailto:',
        'login', 'signup', 'register', 'account',
        'facebook.com', 'twitter.com', 'instagram.com',
    ]
    for pattern in exclude_patterns:
        if pattern in url_lower:
            return False
    
    # Проверяем расширения файлов
    file_extensions = ['.txt', '.csv', '.json', '.xml', '.lst']
    for ext in file_extensions:
        if url_lower.endswith(ext):
            return True
    
    # Проверяем наличие ключевых слов в URL
    keywords = ['proxy', 'proxies', 'proxylist', 'proxy-list', 'socks', 'http', 'https', 'free-proxy']
    for keyword in keywords:
        if keyword in url_lower:
            return True
    
    # Проверяем доверенные домены
    parsed = urlparse(url)
    for domain in TRUSTED_DOMAINS:
        if domain in parsed.netloc:
            return True
    
    return False


async def fetch_url(session, url, headers):
    """Загрузка URL"""
    try:
        async with session.get(url, headers=headers, timeout=15, ssl=False) as response:
            if response.status == 200:
                return await response.text()
    except:
        pass
    return None


async def extract_links_from_github(session, url, headers):
    """Специальная обработка GitHub для поиска файлов"""
    links = set()
    
    if 'github.com' in url and '/blob/' not in url:
        api_url = url.replace('github.com', 'api.github.com/repos')
        if not api_url.endswith('/contents'):
            api_url += '/contents'
        
        try:
            async with session.get(api_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    for item in data:
                        if item.get('type') == 'file':
                            name = item.get('name', '').lower()
                            if any(ext in name for ext in ['proxy', 'socks', 'http', '.txt', '.csv', '.json']):
                                links.add((item.get('download_url'), 'text'))
        except:
            pass
    
    return links


async def extract_links_from_page(session, html, base_url, headers):
    """Извлечение ссылок из HTML страницы"""
    links = set()
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем прямые ссылки на файлы
        for a in soup.find_all('a', href=True):
            href = a['href']
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            full_url = urljoin(base_url, href)
            
            if is_valid_source_url(full_url):
                source_type = 'text'
                if full_url.endswith('.html') or full_url.endswith('.htm') or 'html' in full_url:
                    source_type = 'html'
                elif 'api' in full_url.lower():
                    source_type = 'api'
                links.add((full_url, source_type))
            
            elif 'github.com' in full_url and 'blob' in full_url:
                raw_url = full_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                if is_valid_source_url(raw_url):
                    links.add((raw_url, 'text'))
        
        # Ищем pre и code блоки с IP:PORT
        for pre in soup.find_all(['pre', 'code', 'textarea']):
            text = pre.get_text()
            if re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}\b', text):
                if is_valid_source_url(base_url):
                    links.add((base_url, 'html'))
                break
                
    except Exception as e:
        pass
    
    return links


async def search_for_sources(db):
    """Поиск новых источников в поисковиках с ротацией прокси"""
    print(f"\n{Fore.YELLOW}🔍 ПОИСК НОВЫХ ИСТОЧНИКОВ...{Style.RESET_ALL}")
    
    ua = UserAgent()
    existing_sources = load_sources()
    existing_urls = {s['url'] for s in existing_sources}
    new_sources = []
    seen_urls = set()
    rotator = ProxyRotator(db)
    
    async with aiohttp.ClientSession() as session:
        for query in SEARCH_QUERIES:
            print(f"\n  🔎 Поиск: {query}")
            
            for engine in SEARCH_ENGINES:
                url = engine.format(query.replace(' ', '+'))
                headers = {'User-Agent': ua.random}
                
                html = await fetch_url(session, url, headers)
                if html:
                    links = await extract_links_from_page(session, html, engine.split('?')[0], headers)
                    
                    for link, source_type in links:
                        if link not in existing_urls and link not in seen_urls:
                            seen_urls.add(link)
                            new_sources.append({
                                'url': link,
                                'type': source_type,
                                'added': datetime.now().isoformat(),
                                'status': 'pending',
                                'source_query': query,
                                'source_engine': engine.split('//')[1].split('/')[0]
                            })
                            print(f"    ✅ Найден: {link[:80]}...")
                    
                    for link, source_type in links:
                        if 'github.com' in link and link not in existing_urls:
                            github_links = await extract_links_from_github(session, link, headers)
                            for gh_link, gh_type in github_links:
                                if gh_link not in existing_urls and gh_link not in seen_urls:
                                    seen_urls.add(gh_link)
                                    new_sources.append({
                                        'url': gh_link,
                                        'type': gh_type,
                                        'added': datetime.now().isoformat(),
                                        'status': 'pending',
                                        'source_query': query,
                                        'source_engine': 'github'
                                    })
                                    print(f"    ✅ GitHub найден: {gh_link[:80]}...")
                
                await asyncio.sleep(2)
    
    return new_sources


async def verify_source(url: str, source_type: str, db) -> bool:
    """Проверка работоспособности источника с ротацией прокси"""
    rotator = ProxyRotator(db)
    headers = {'User-Agent': UserAgent().random}
    
    html, used_proxy = await rotator.fetch_with_proxy_rotation(url, headers)
    
    if html:
        pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}\b'
        if re.search(pattern, html):
            return True
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, html)
        if len(ips) > 5:
            return True
    return False


async def main():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}      PROCTOR SMART - ПОИСК НОВЫХ ИСТОЧНИКОВ         {Fore.CYAN}║
║{Fore.WHITE}      Автоматическое добавление новых прокси-сайтов   {Fore.CYAN}║
║{Fore.GREEN}      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    # Загружаем базу данных
    db = ProxyDatabase()
    
    # Загружаем существующие источники
    existing = load_sources()
    print(f"📊 Существующих источников: {len(existing)}")
    
    # Ищем новые
    new_sources = await search_for_sources(db)
    
    if not new_sources:
        print(f"\n{Fore.YELLOW}ℹ️ Новых источников не найдено{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.GREEN}✅ Найдено {len(new_sources)} потенциальных источников{Style.RESET_ALL}")
    
    # Проверяем каждый
    print(f"\n{Fore.YELLOW}🔍 ПРОВЕРКА ИСТОЧНИКОВ...{Style.RESET_ALL}")
    verified_sources = []
    
    for src in new_sources:
        print(f"  Проверяю {src['url'][:60]}...", end=' ', flush=True)
        if await verify_source(src['url'], src['type'], db):
            src['status'] = 'active'
            verified_sources.append(src)
            print(f"✅ РАБОТАЕТ")
        else:
            src['status'] = 'failed'
            print(f"❌ НЕ РАБОТАЕТ")
        
        await asyncio.sleep(0.5)
    
    # Добавляем проверенные источники
    if verified_sources:
        all_sources = existing + verified_sources
        save_sources(all_sources)
        
        print(f"\n{Fore.GREEN}✅ ДОБАВЛЕНО {len(verified_sources)} НОВЫХ ИСТОЧНИКОВ:{Style.RESET_ALL}")
        for src in verified_sources:
            print(f"  📌 {src['url']}")
            print(f"     Тип: {src['type']}, найден на: {src.get('source_engine', 'неизвестно')}")
    else:
        print(f"\n{Fore.YELLOW}⚠️ Не найдено рабочих источников{Style.RESET_ALL}")


if __name__ == "__main__":
    asyncio.run(main())
