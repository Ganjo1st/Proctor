#!/usr/bin/env python3
# rapid_main.py - СУПЕР-БЫСТРЫЙ СБОР И ПРОВЕРКА

import sys
import os
import asyncio
from datetime import datetime
from colorama import init, Fore, Style

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.rapid_scraper import RapidScraper
from core.rapid_checker import RapidChecker
from core.database import ProxyDatabase

init(autoreset=True)

class RapidCollector:
    """Максимально быстрый сбор и проверка прокси"""
    
    def __init__(self):
        self.db = ProxyDatabase()
        self.scraper = RapidScraper()
        self.checker = RapidChecker()
        self.BATCH_SIZE = 500
    
    def run(self):
        """Основной цикл"""
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR RAPID - МАКСИМАЛЬНАЯ СКОРОСТЬ           {Fore.CYAN}║
║{Fore.WHITE}         Сбор и проверка 500 прокси за 5 секунд          {Fore.CYAN}║
║{Fore.GREEN}         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)
        
        raw_proxies = self.scraper.get_all()
        
        if not raw_proxies:
            print(f"{Fore.RED}❌ Нет прокси для проверки{Style.RESET_ALL}")
            return
        
        existing = set(self.db.db['proxies'].keys())
        new_proxies = [p for p in raw_proxies if p not in existing]
        
        print(f"📊 Новых прокси: {len(new_proxies)} из {len(raw_proxies)}")
        
        if not new_proxies:
            print(f"{Fore.YELLOW}⚠️ Нет новых прокси{Style.RESET_ALL}")
            stats = self.db.get_stats()
            print(f"\n📊 ТЕКУЩАЯ СТАТИСТИКА:")
            print(f"  🇷🇺 Российских: {stats['russian']}")
            print(f"  🇺🇸 Американских: {stats['american']}")
            print(f"  🌍 Глобальных: {stats['global']}")
            print(f"  📦 Всего рабочих: {stats['working_now']}")
            return
        
        to_check = new_proxies[:self.BATCH_SIZE]
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self.checker.check_all(to_check))
        loop.close()
        
        working_count = 0
        ru_count = 0
        us_count = 0
        global_count = 0
        
        for result in results:
            if result['working']:
                working_count += 1
                self.db.add_proxy(result['proxy'], result)
                if result['ru_access']:
                    ru_count += 1
                if result['us_access']:
                    us_count += 1
                if result['ru_access'] and result['us_access']:
                    global_count += 1
        
        stats = self.db.export_to_txt()
        
        print(f"{Fore.GREEN}✅ ГОТОВО!{Style.RESET_ALL}")
        print(f"  ✨ Новых рабочих: {working_count}")
        print(f"  🇷🇺 Российских: {ru_count}")
        print(f"  🇺🇸 Американских: {us_count}")
        print(f"  🌍 Глобальных: {global_count}")
        print(f"  📊 Всего в базе: {stats['all']}")
        
        if stats['all'] > 0:
            print(f"\n{Fore.GREEN}📁 ФАЙЛЫ С ПРОКСИ:{Style.RESET_ALL}")
            print(f"  🇷🇺 Россия: https://raw.githubusercontent.com/Ganjo1st/Proctor/main/data/proxies_russia.txt")
            print(f"  🇺🇸 США: https://raw.githubusercontent.com/Ganjo1st/Proctor/main/data/proxies_usa.txt")
            print(f"  🌍 Глобальные: https://raw.githubusercontent.com/Ganjo1st/Proctor/main/data/proxies_global.txt")
            print(f"  📦 Все: https://raw.githubusercontent.com/Ganjo1st/Proctor/main/data/proxies_all.txt")

if __name__ == "__main__":
    collector = RapidCollector()
    collector.run()
