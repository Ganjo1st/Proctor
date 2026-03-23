#!/usr/bin/env python3
# rapid_main.py - СБОР С СОХРАНЕНИЕМ ИСТОЧНИКА И ГЕО

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
from core.source_stats import SourceStats

init(autoreset=True)

class RapidCollector:
    """Умный сбор с сохранением источника и гео-данных"""
    
    def __init__(self):
        self.db = ProxyDatabase()
        self.scraper = SmartScraper()
        self.checker = RapidChecker()
        self.notifier = TelegramNotifier()
        self.source_stats = SourceStats()
        self.BATCH_SIZE = 300
    
    def run(self):
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}      PROCTOR SMART - УМНЫЙ СБОР (с гео-данными)        {Fore.CYAN}║
║{Fore.WHITE}      Сохраняем источник и географию каждого прокси     {Fore.CYAN}║
║{Fore.GREEN}      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)
        
        # Получаем статистику ДО
        old_stats = self.db.get_stats()
        
        # ШАГ 1: СБОР С ИСТОЧНИКАМИ
        raw_proxies_with_sources = self.scraper.get_all_proxies_with_sources()
        
        if not raw_proxies_with_sources:
            print(f"{Fore.RED}❌ Нет прокси для проверки{Style.RESET_ALL}")
            return
        
        # ШАГ 2: БЕРЁМ ТОЛЬКО НОВЫЕ
        existing = set(self.db.db['proxies'].keys())
        new_proxies = [(p, src) for p, src in raw_proxies_with_sources if p not in existing]
        
        print(f"📊 Новых прокси: {len(new_proxies)} из {len(raw_proxies_with_sources)}")
        
        new_working = 0
        if new_proxies:
            to_check = new_proxies[:self.BATCH_SIZE]
            
            # Проверка с гео-данными
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.checker.check_all([p for p, _ in to_check]))
            loop.close()
            
            # Сохраняем с источником и гео
            for result, (proxy, source) in zip(results, to_check):
                if result['working']:
                    # Добавляем источник и гео-данные
                    result['source'] = source
                    self.db.add_proxy(result['proxy'], result, source)
                    self.source_stats.update(source, 1)
                    new_working += 1
        
        # ШАГ 3: ЭКСПОРТ
        stats = self.db.export_to_txt()
        new_stats = self.db.get_stats()
        
        print(f"\n{Fore.GREEN}✅ ГОТОВО!{Style.RESET_ALL}")
        print(f"  ✨ Добавлено новых рабочих: {new_working}")
        print(f"  📊 Всего рабочих: {stats['all']}")
        print(f"\n{Fore.CYAN}📊 СТАТИСТИКА ПО РЕГИОНАМ:{Style.RESET_ALL}")
        print(f"  🇷🇺 Российских: {stats['ru']}")
        print(f"  🇺🇸 Американских: {stats['us']}")
        print(f"  🌍 Глобальных: {stats['global']}")
        
        # Отправка уведомления, если есть новые рабочие
        if new_working > 0:
            if self.notifier.send_stats(new_stats, new_working):
                print(f"  🤖 Уведомление отправлено в Telegram")
            else:
                print(f"  ⚠️ Не удалось отправить уведомление (бот не настроен)")
        
        # Показываем примеры с гео
        if stats['all'] > 0:
            print(f"\n{Fore.GREEN}🔥 ПРИМЕРЫ РАБОЧИХ ПРОКСИ С ГЕО:{Style.RESET_ALL}")
            with open('data/proxies_all.txt', 'r') as f:
                proxies = f.read().splitlines()[:5]
                for p in proxies:
                    # Находим гео для прокси
                    for proxy, info in self.db.db['proxies'].items():
                        if proxy == p:
                            country = info.get('country', 'unknown')
                            region = info.get('region', 'unknown')
                            print(f"  {p} [{country}] ({region})")
                            break

if __name__ == "__main__":
    collector = RapidCollector()
    collector.run()
