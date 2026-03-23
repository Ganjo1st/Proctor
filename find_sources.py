#!/usr/bin/env python3
# find_sources.py - ДИАГНОСТИКА И ПОИСК НОВЫХ ИСТОЧНИКОВ

import sys
import os
import requests
from datetime import datetime
from colorama import init, Fore, Style

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.smart_scraper import SmartScraper
from core.source_stats import SourceStats

init(autoreset=True)

def main():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR SMART - ДИАГНОСТИКА ИСТОЧНИКОВ         {Fore.CYAN}║
║{Fore.WHITE}         Проверка актуальности всех источников          {Fore.CYAN}║
║{Fore.GREEN}         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    scraper = SmartScraper()
    
    print(f"\n{Fore.CYAN}🔍 ПРОВЕРКА АКТУАЛЬНОСТИ ИСТОЧНИКОВ:{Style.RESET_ALL}")
    print("─" * 60)
    
    for name, source in scraper.sources.items():
        print(f"\n{Fore.YELLOW}📡 {name}:{Style.RESET_ALL}")
        print(f"   URL: {source['url'][:70]}...")
        
        try:
            response = requests.get(source['url'], timeout=10)
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                text = response.text[:500]
                # Проверяем наличие прокси
                import re
                ip_port_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}\b'
                found = re.findall(ip_port_pattern, text)
                print(f"   Прокси в ответе: {len(found)}")
                
                # Первые 3 прокси для примера
                if found:
                    print(f"   Примеры: {', '.join(found[:3])}")
            else:
                print(f"   {Fore.RED}❌ ИСТОЧНИК НЕДОСТУПЕН{Style.RESET_ALL}")
        except Exception as e:
            print(f"   {Fore.RED}❌ ОШИБКА: {e}{Style.RESET_ALL}")
    
    print("\n" + "─" * 60)
    print(f"\n{Fore.GREEN}✅ Диагностика завершена{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
