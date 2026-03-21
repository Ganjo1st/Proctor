#!/usr/bin/env python3
# rapid_clean.py - АГРЕССИВНАЯ ОЧИСТКА МЁРТВЫХ ПРОКСИ (каждые 8 минут)

import sys
import os
import asyncio
from datetime import datetime, timedelta
from colorama import init, Fore, Style

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import ProxyDatabase
from core.rapid_checker import RapidChecker

init(autoreset=True)

class RapidCleaner:
    """Агрессивная очистка – удаляем прокси, не работающие в последние 15 минут"""
    
    def __init__(self):
        self.db = ProxyDatabase()
        self.checker = RapidChecker()
        self.MAX_AGE_MINUTES = 15  # Удаляем прокси старше 15 минут без проверки
    
    def run(self):
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR SMART - АГРЕССИВНАЯ ОЧИСТКА            {Fore.CYAN}║
║{Fore.WHITE}         Удаляем прокси, не работающие > 15 минут       {Fore.CYAN}║
║{Fore.GREEN}         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)
        
        all_proxies = list(self.db.db['proxies'].keys())
        
        if not all_proxies:
            print(f"{Fore.YELLOW}⚠️ Нет прокси для проверки{Style.RESET_ALL}")
            return
        
        print(f"📊 В базе: {len(all_proxies)} прокси")
        
        # Проверяем только те, которые не проверялись последние 15 минут
        now = datetime.now()
        need_check = []
        
        for proxy, data in self.db.db['proxies'].items():
            last_seen = datetime.fromisoformat(data['last_seen'])
            age = now - last_seen
            
            if age > timedelta(minutes=self.MAX_AGE_MINUTES):
                need_check.append(proxy)
        
        if need_check:
            print(f"🔍 Проверяем {len(need_check)} устаревших прокси...")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.checker.check_all(need_check))
            loop.close()
            
            # Удаляем неработающие
            removed = 0
            for result in results:
                if not result['working']:
                    if result['proxy'] in self.db.db['proxies']:
                        del self.db.db['proxies'][result['proxy']]
                        removed += 1
                else:
                    # Обновляем время последней проверки
                    self.db.add_proxy(result['proxy'], result)
            
            self.db.save_db()
            print(f"  🗑️ Удалено нерабочих: {removed}")
        else:
            print(f"  ✅ Все прокси свежие (проверены менее {self.MAX_AGE_MINUTES} мин назад)")
        
        stats = self.db.export_to_txt()
        print(f"\n{Fore.GREEN}✅ ОЧИСТКА ЗАВЕРШЕНА{Style.RESET_ALL}")
        print(f"  📦 Осталось в базе: {stats['all']}")

if __name__ == "__main__":
    cleaner = RapidCleaner()
    cleaner.run()
