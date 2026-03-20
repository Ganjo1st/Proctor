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
        self.BATCH_SIZE = 500  # Проверяем по 500 за раз!
    
    def run(self):
        """Основной цикл"""
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR RAPID - МАКСИМАЛЬНАЯ СКОРОСТЬ           {Fore.CYAN}║
║{Fore.WHITE}         Сбор и проверка 500 прокси за 5 секунд          {Fore.CYAN}║
║{Fore.GREEN}         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)
        
        # ШАГ 1: БЫСТРЫЙ СБОР
        raw_proxies = self.scraper.get_all()
        
        if not raw_proxies:
            print(f"{Fore.RED}❌ Нет прокси для проверки{Style.RESET_ALL}")
            return
        
        # ШАГ 2: БЕРЁМ ТОЛЬКО НОВЫЕ
        existing = set(self.db.db['proxies'].keys())
        new_proxies = [p for p in raw_proxies if p not in existing]
        
        print(f"📊 Новых прокси: {len(new_proxies)} из {len(raw_proxies)}")
        
        if not new_proxies:
            print(f"{Fore.YELLOW}⚠️ Нет новых прокси{Style.RESET_ALL}")
            stats = self.db.get_stats()
            print(f"\n📊 ТЕКУЩАЯ СТАТИСТИКА:")
            print(f"  Всего в базе: {stats['total_in_db']}")
            print(f"  Рабочих: {stats['working_now']}")
            return
        
        # ШАГ 3: БЕРЁМ ПЕРВЫЕ 500
        to_check = new_proxies[:self.BATCH_SIZE]
        
        # ШАГ 4: ПАРАЛЛЕЛЬНАЯ ПРОВЕРКА
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self.checker.check_all(to_check))
        loop.close()
        
        # ШАГ 5: СОХРАНЯЕМ РАБОЧИЕ
        working_count = 0
        for result in results:
            if result['working']:
                self.db.add_proxy(result['proxy'], result)
                working_count += 1
        
        # ШАГ 6: ЭКСПОРТ
        stats = self.db.export_to_txt()
        
        print(f"{Fore.GREEN}✅ ГОТОВО!{Style.RESET_ALL}")
        print(f"  ✨ Новых рабочих: {working_count}")
        print(f"  📊 Всего в базе: {stats['all']}")
        
        if stats['all'] > 0:
            print(f"\n{Fore.GREEN}🔥 ПРИМЕРЫ РАБОЧИХ ПРОКСИ:{Style.RESET_ALL}")
            for i, proxy in enumerate(stats['fast'][:5]):
                print(f"  {i+1}. {proxy}")

if __name__ == "__main__":
    collector = RapidCollector()
    collector.run()
