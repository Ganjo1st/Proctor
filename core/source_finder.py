# core/source_finder.py - УМНЫЙ ПОИСК НОВЫХ ИСТОЧНИКОВ ПРОКСИ
import requests
import re
import json
import os
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from typing import List, Dict, Set
from datetime import datetime

class SourceFinder:
    """Автоматический поиск новых источников прокси"""
    
    def __init__(self):
        self.session = requests.Session()
        ua = UserAgent()
        self.session.headers.update({'User-Agent': ua.random})
        
        # Базовые источники для поиска
        self.search_engines = [
            'https://github.com/search?q=free+proxy+list&type=repositories',
            'https://github.com/search?q=proxies+list&type=repositories',
            'https://github.com/search?q=socks5+list&type=repositories',
            'https://www.google.com/search?q=free+proxy+list+site:github.com',
        ]
        
        # Список уже известных источников
        self.known_sources = self.load_known_sources()
    
    def load_known_sources(self) -> Set[str]:
        """Загрузка известных источников"""
        known = set()
        sources_file = 'data/sources.json'
        if os.path.exists(sources_file):
            try:
                with open(sources_file, 'r') as f:
                    data = json.load(f)
                    known = set(data.get('known_sources', []))
            except:
                pass
        return known
    
    def save_known_sources(self):
        """Сохранение известных источников"""
        os.makedirs('data', exist_ok=True)
        with open('data/sources.json', 'w') as f:
            json.dump({
                'known_sources': list(self.known_sources),
                'last_update': datetime.now().isoformat()
            }, f, indent=2)
    
    def extract_github_urls(self, html: str) -> List[str]:
        """Извлечение ссылок на GitHub репозитории"""
        urls = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем ссылки на репозитории
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'github.com' in href and '/blob/' in href and any(ext in href for ext in ['.txt', '.lst', '.list']):
                # Преобразуем в raw-ссылку
                raw_url = href.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                if raw_url not in self.known_sources:
                    urls.append(raw_url)
            elif 'raw.githubusercontent.com' in href and any(ext in href for ext in ['.txt', '.lst', '.list']):
                if href not in self.known_sources:
                    urls.append(href)
        
        return urls
    
    def extract_web_urls(self, html: str) -> List[str]:
        """Извлечение ссылок на веб-страницы с прокси"""
        urls = []
        soup = BeautifulSoup(html, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(keyword in href.lower() for keyword in ['proxy', 'proxies', 'free-proxy', 'socks']):
                if href.startswith('http') and href not in self.known_sources:
                    urls.append(href)
        
        return urls
    
    def test_source(self, url: str) -> Dict:
        """Тестирование источника на наличие прокси"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'url': url, 'working': False, 'proxies': 0, 'error': 'HTTP ' + str(response.status_code)}
            
            text = response.text
            ip_port_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}\b'
            found = re.findall(ip_port_pattern, text)
            
            # Также ищем IP без порта
            if len(found) < 5:
                ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text)
                if len(ips) > 10:
                    found = [f"{ip}:8080" for ip in ips[:20]]
            
            return {
                'url': url,
                'working': len(found) > 0,
                'proxies': len(found),
                'sample': found[:5],
                'error': None
            }
        except Exception as e:
            return {'url': url, 'working': False, 'proxies': 0, 'error': str(e)[:50]}
    
    def find_new_sources(self) -> List[Dict]:
        """Поиск новых источников"""
        print("\n🔍 ПОИСК НОВЫХ ИСТОЧНИКОВ ПРОКСИ...")
        print("─" * 60)
        
        new_sources = []
        
        for search_url in self.search_engines:
            try:
                print(f"  🔎 Поиск в: {search_url[:60]}...")
                response = self.session.get(search_url, timeout=15)
                if response.status_code != 200:
                    continue
                
                # Извлекаем ссылки
                github_urls = self.extract_github_urls(response.text)
                web_urls = self.extract_web_urls(response.text)
                
                all_urls = github_urls + web_urls
                
                for url in all_urls:
                    if url in self.known_sources:
                        continue
                    
                    # Тестируем источник
                    print(f"     🧪 Тестирую: {url[:50]}...")
                    test_result = self.test_source(url)
                    
                    if test_result['working'] and test_result['proxies'] >= 5:
                        new_sources.append(test_result)
                        self.known_sources.add(url)
                        print(f"        ✅ НАЙДЕН! {test_result['proxies']} прокси")
                    else:
                        print(f"        ❌ Не подходит")
                
            except Exception as e:
                print(f"  ❌ Ошибка поиска: {e}")
        
        self.save_known_sources()
        
        print("─" * 60)
        print(f"📊 НАЙДЕНО НОВЫХ ИСТОЧНИКОВ: {len(new_sources)}")
        
        return new_sources
