#!/usr/bin/env python3
# rapid_clean.py - АГРЕССИВНАЯ ОЧИСТКА МЁРТВЫХ ПРОКСИ

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
    """Агрессивная очистка – удаляем прокси старше 30 минут"""
    
    def __init__(self):
        self.db = ProxyDatabase()
        self.checker = RapidChecker()
    
    def run(self):
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR SMART - АГРЕССИВНАЯ ОЧИСТКА            {Fore.CYAN}║
║{Fore.WHITE}         Удаляем прокси старше 30 минут                 {Fore.CYAN}║
║{Fore.GREEN}         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)
        
        all_proxies = list(self.db.db['proxies'].keys())
        
        if not all_proxies:
            print(f"{Fore.YELLOW}⚠️ Нет прокси для проверки{Style.RESET_ALL}")
            return
        
        print(f"📊 В базе: {len(all_proxies)} прокси")
        
        # Удаляем прокси старше 30 минут
        now = datetime.now()
        to_remove = []
        
        for proxy, data in self.db.db['proxies'].items():
            last_seen = datetime.fromisoformat(data['last_seen'])
            age = now - last_seen
            
            if age > timedelta(minutes=30):
                to_remove.append(proxy)
        
        for proxy in to_remove:
            del self.db.db['proxies'][proxy]
        
        self.db.save_db()
        stats = self.db.export_to_txt()
        
        print(f"\n{Fore.GREEN}✅ ОЧИСТКА ЗАВЕРШЕНА{Style.RESET_ALL}")
        print(f"  🗑️ Удалено старых: {len(to_remove)}")
        print(f"  📦 Осталось в базе: {stats['all']}")

if __name__ == "__main__":
    cleaner = RapidCleaner()
    cleaner.run()
