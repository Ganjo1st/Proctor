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
from core.notifier import TelegramNotifier

init(autoreset=True)

class RapidCollector:
    """Умный сбор и проверка прокси с уведомлениями"""
    
    def __init__(self):
        self.db = ProxyDatabase()
        self.scraper = SmartScraper()
        self.checker = RapidChecker()
        self.notifier = TelegramNotifier()
        self.BATCH_SIZE = 500
    
    def run(self):
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}      PROCTOR SMART - УМНЫЙ СБОР ПРОКСИ                 {Fore.CYAN}║
║{Fore.WHITE}      Приоритет: проверенные, быстрые, рабочие         {Fore.CYAN}║
║{Fore.GREEN}      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)
        
        # Получаем статистику ДО обновления
        old_stats = self.db.get_stats()
        
        # ШАГ 1: УМНЫЙ СБОР
        raw_proxies = self.scraper.get_all_proxies()
        
        if not raw_proxies:
            print(f"{Fore.RED}❌ Нет прокси для проверки{Style.RESET_ALL}")
            return
        
        # ШАГ 2: БЕРЁМ ТОЛЬКО НОВЫЕ
        existing = set(self.db.db['proxies'].keys())
        new_proxies = [p for p in raw_proxies if p not in existing]
        
        print(f"📊 Новых прокси: {len(new_proxies)} из {len(raw_proxies)}")
        
        new_working = 0
        if new_proxies:
            to_check = new_proxies[:self.BATCH_SIZE]
            
            # Проверка
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.checker.check_all(to_check))
            loop.close()
            
            # Сохраняем рабочие
            for result in results:
                if result['working']:
                    self.db.add_proxy(result['proxy'], result)
                    new_working += 1
        
        # ШАГ 3: ЭКСПОРТ
        stats = self.db.export_to_txt()
        new_stats = self.db.get_stats()
        
        print(f"\n{Fore.GREEN}✅ ГОТОВО!{Style.RESET_ALL}")
        print(f"  ✨ Добавлено новых рабочих: {new_working}")
        print(f"  📊 Всего рабочих: {stats['all']}")
        
        # ШАГ 4: ОТПРАВКА УВЕДОМЛЕНИЯ В TELEGRAM
        if new_working > 0:
            if self.notifier.send_stats(new_stats, new_working):
                print(f"  🤖 Уведомление отправлено в Telegram")
            else:
                print(f"  ⚠️ Не удалось отправить уведомление (бот не настроен)")
        
        # Показываем примеры
        if stats['all'] > 0:
            print(f"\n{Fore.GREEN}🔥 ПРИМЕРЫ РАБОЧИХ ПРОКСИ:{Style.RESET_ALL}")
            with open('data/proxies_all.txt', 'r') as f:
                proxies = f.read().splitlines()[:5]
                for p in proxies:
                    print(f"  {p}")

if __name__ == "__main__":
    collector = RapidCollector()
    collector.run()
