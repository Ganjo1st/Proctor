#!/usr/bin/env python3
# rapid_clean.py - ПОЛНАЯ ПРОВЕРКА БАЗЫ ПРОКСИ

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
    """Полная проверка базы прокси и удаление нерабочих"""
    
    def __init__(self):
        self.db = ProxyDatabase()
        self.checker = RapidChecker()
        self.MAX_AGE_MINUTES = 30  # Проверяем прокси старше 30 минут
    
    def run(self):
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR SMART - ПРОВЕРКА БАЗЫ                  {Fore.CYAN}║
║{Fore.WHITE}         Полная верификация всех сохранённых прокси     {Fore.CYAN}║
║{Fore.GREEN}         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)
        
        all_proxies = list(self.db.db['proxies'].keys())
        
        if not all_proxies:
            print(f"{Fore.YELLOW}⚠️ Нет прокси для проверки{Style.RESET_ALL}")
            return
        
        print(f"📊 В базе: {len(all_proxies)} прокси")
        
        # Определяем, какие прокси нужно проверить
        now = datetime.now()
        need_check = []
        
        for proxy, data in self.db.db['proxies'].items():
            last_seen = datetime.fromisoformat(data['last_seen'])
            age = now - last_seen
            
            if age > timedelta(minutes=self.MAX_AGE_MINUTES):
                need_check.append(proxy)
        
        if not need_check:
            print(f"  ✅ Все прокси проверены менее {self.MAX_AGE_MINUTES} мин назад")
            self._show_stats()
            return
        
        print(f"🔍 Проверяем {len(need_check)} прокси (старше {self.MAX_AGE_MINUTES} мин)...")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self.checker.check_all(need_check))
        loop.close()
        
        # Обновляем статус и удаляем нерабочие
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
        
        print(f"\n{Fore.GREEN}✅ ПРОВЕРКА ЗАВЕРШЕНА{Style.RESET_ALL}")
        print(f"  🟢 Живых: {alive}")
        print(f"  🔴 Мёртвых удалено: {dead}")
        
        self._show_stats()
    
    def _show_stats(self):
        """Показать статистику по регионам"""
        stats = self.db.export_to_txt()
        print(f"\n{Fore.CYAN}📊 СТАТИСТИКА ПО РЕГИОНАМ:{Style.RESET_ALL}")
        print(f"  🇷🇺 Российских: {stats['ru']}")
        print(f"  🇺🇸 Американских: {stats['us']}")
        print(f"  🌍 Глобальных: {stats['global']}")
        print(f"  📦 Всего рабочих: {stats['all']}")

if __name__ == "__main__":
    cleaner = RapidCleaner()
    cleaner.run()
