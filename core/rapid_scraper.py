# core/rapid_scraper.py - БЫСТРЫЙ СБОР СВЕЖИХ ПРОКСИ
import requests
import re
from fake_useragent import UserAgent
from typing import List, Set

class RapidScraper:
    """Максимально быстрый сбор прокси"""
    
    def __init__(self):
        self.session = requests.Session()
        ua = UserAgent()
        self.session.headers.update({'User-Agent': ua.random})
        
        # ТОЛЬКО САМЫЕ БЫСТРЫЕ ИСТОЧНИКИ
        self.sources = [
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
            'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
            'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt',
            'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt',
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&country=RU',
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&country=US',
        ]
    
    def fetch(self, url: str) -> Set[str]:
        """Быстрый сбор из одного источника"""
        proxies = set()
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code != 200:
                return proxies
            
            text = response.text
            ip_port_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}\b'
            found = re.findall(ip_port_pattern, text)
            proxies.update(found)
            
        except:
            pass
        
        return proxies
    
    def get_all(self) -> List[str]:
        """Быстрый сбор всех прокси"""
        print("\n⚡ БЫСТРЫЙ СБОР ПРОКСИ...")
        
        all_proxies = set()
        
        for source in self.sources:
            proxies = self.fetch(source)
            all_proxies.update(proxies)
            print(f"  {source.split('/')[-1][:30]}: +{len(proxies)}")
        
        print(f"\n📊 ИТОГО: {len(all_proxies)} прокси\n")
        return list(all_proxies)
