#!/usr/bin/env python3
# rapid_clean.py - АГРЕССИВНАЯ ОЧИСТКА МЁРТВЫХ ПРОКСИ

import sys
import os
import asyncio
from datetime import datetime
from colorama import init, Fore, Style

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import ProxyDatabase
from core.rapid_checker import RapidChecker

init(autoreset=True)

class RapidCleaner:
    """Агрессивная очистка мёртвых прокси"""
    
    def __init__(self):
        self.db = ProxyDatabase()
        self.checker = RapidChecker()
    
    def run(self):
        """Проверка всех прокси и удаление мёртвых"""
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR RAPID - АГРЕССИВНАЯ ОЧИСТКА            {Fore.CYAN}║
║{Fore.WHITE}         Удаление прокси, не работающих сейчас          {Fore.CYAN}║
║{Fore.GREEN}         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)
        
        # Получаем все прокси
        all_proxies = list(self.db.db['proxies'].keys())
        
        if not all_proxies:
            print(f"{Fore.YELLOW}⚠️ Нет прокси для проверки{Style.RESET_ALL}")
            return
        
        print(f"📊 В базе: {len(all_proxies)} прокси")
        
        # ПАРАЛЛЕЛЬНАЯ ПРОВЕРКА ВСЕХ
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self.checker.check_all(all_proxies))
        loop.close()
        
        # Обновляем статус и удаляем мёртвые
        alive = 0
        dead = 0
        
        for result in results:
            if result['working']:
                alive += 1
                self.db.add_proxy(result['proxy'], result)
            else:
                dead += 1
                if result['proxy'] in self.db.db['proxies']:
                    del self.db.db['proxies'][result['proxy']]
        
        self.db.save_db()
        stats = self.db.export_to_txt()
        
        print(f"\n{Fore.GREEN}✅ ОЧИСТКА ЗАВЕРШЕНА{Style.RESET_ALL}")
        print(f"  🟢 Живых: {alive}")
        print(f"  🔴 Мёртвых удалено: {dead}")
        print(f"  📦 Осталось в базе: {stats['all']}")
        
        if stats['all'] > 0:
            print(f"\n{Fore.GREEN}🔥 БЫСТРЫЕ ПРОКСИ:{Style.RESET_ALL}")
            for i, proxy in enumerate(stats['fast'][:5]):
                print(f"  {i+1}. {proxy}")

if __name__ == "__main__":
    cleaner = RapidCleaner()
    cleaner.run()
