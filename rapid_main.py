#!/usr/bin/env python3
# rapid_main.py - БЫСТРЫЙ СБОР С ПРИОРИТЕТОМ ПРОВЕРЕННЫХ ПРОКСИ

import sys
import os
import asyncio
from datetime import datetime
from colorama import init, Fore, Style

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.smart_scraper import SmartScraper
from core.rapid_checker import RapidChecker
from core.database import ProxyDatabase

init(autoreset=True)

class RapidCollector:
    """Умный сбор и проверка прокси"""
    
    def __init__(self):
        self.db = ProxyDatabase()
        self.scraper = SmartScraper()
        self.checker = RapidChecker()
        self.BATCH_SIZE = 500
    
    def run(self):
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}      PROCTOR SMART - УМНЫЙ СБОР ПРОКСИ                 {Fore.CYAN}║
║{Fore.WHITE}      Приоритет: проверенные, быстрые, рабочие         {Fore.CYAN}║
║{Fore.GREEN}      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)
        
        # ШАГ 1: УМНЫЙ СБОР
        raw_proxies = self.scraper.get_all_proxies()
        
        if not raw_proxies:
            print(f"{Fore.RED}❌ Нет прокси для проверки{Style.RESET_ALL}")
            return
        
        # ШАГ 2: БЕРЁМ ТОЛЬКО НОВЫЕ (не в базе)
        existing = set(self.db.db['proxies'].keys())
        new_proxies = [p for p in raw_proxies if p not in existing]
        
        print(f"📊 Новых прокси: {len(new_proxies)} из {len(raw_proxies)}")
        
        if not new_proxies:
            print(f"{Fore.YELLOW}⚠️ Нет новых прокси{Style.RESET_ALL}")
            self.show_stats()
            return
        
        # ШАГ 3: ПРОВЕРКА ТОЛЬКО НОВЫХ (если они из непроверенных источников)
        to_check = new_proxies[:self.BATCH_SIZE]
        
        # Проверка только если есть непроверенные
        if any('proxymania' not in p for p in to_check):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.checker.check_all(to_check))
            loop.close()
        else:
            # Прокси с proxymania уже проверены, добавляем сразу
            results = [{'proxy': p, 'working': True, 'latency': 0} for p in to_check]
        
        # ШАГ 4: СОХРАНЯЕМ РАБОЧИЕ
        added = 0
        for result in results:
            if result['working']:
                # Для proxymania ставим задержку 0 (не проверяем)
                if 'proxymania' in result['proxy']:
                    result['latency'] = 50  # Условная хорошая скорость
                self.db.add_proxy(result['proxy'], result)
                added += 1
        
        # ШАГ 5: ЭКСПОРТ
        stats = self.db.export_to_txt()
        
        print(f"\n{Fore.GREEN}✅ ГОТОВО!{Style.RESET_ALL}")
        print(f"  ✨ Добавлено: {added}")
        print(f"  📊 Всего рабочих: {stats['all']}")
        self.show_stats()
        
        # Показываем примеры
        if stats['all'] > 0:
            print(f"\n{Fore.GREEN}🔥 ПРИМЕРЫ РАБОЧИХ ПРОКСИ:{Style.RESET_ALL}")
            with open('data/proxies_all.txt', 'r') as f:
                proxies = f.read().splitlines()[:5]
                for p in proxies:
                    print(f"  {p}")
    
    def show_stats(self):
        """Показать текущую статистику"""
        stats = self.db.get_stats()
        print(f"\n{Fore.CYAN}📊 СТАТИСТИКА БАЗЫ:{Style.RESET_ALL}")
        print(f"  Всего в базе: {stats['total_in_db']}")
        print(f"  Рабочих: {stats['working_now']}")
        print(f"  🇷🇺 РФ: {stats['russian']} | 🇺🇸 США: {stats['american']} | 🌍 Глобальных: {stats['global']}")

if __name__ == "__main__":
    collector = RapidCollector()
    collector.run()
