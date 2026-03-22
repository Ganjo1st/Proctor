#!/usr/bin/env python3
# find_sources.py - ПОИСК НОВЫХ ИСТОЧНИКОВ ПРОКСИ С АНАЛИТИКОЙ

import sys
import os
import json
from datetime import datetime
from colorama import init, Fore, Style

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.source_finder import SourceFinder
from core.source_stats import SourceStats
from core.history_tracker import HistoryTracker

init(autoreset=True)

def main():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR SMART - ПОИСК ИСТОЧНИКОВ               {Fore.CYAN}║
║{Fore.WHITE}         Автоматический поиск + аналитика эффективности {Fore.CYAN}║
║{Fore.GREEN}         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    finder = SourceFinder()
    source_stats = SourceStats()
    tracker = HistoryTracker()
    
    # Статистика текущих источников
    current_stats = source_stats.get_stats()
    print(f"\n{Fore.CYAN}📊 СТАТИСТИКА ИЗВЕСТНЫХ ИСТОЧНИКОВ:{Style.RESET_ALL}")
    print(f"  📦 Всего источников: {current_stats['total_sources']}")
    print(f"  🟢 Активных: {current_stats['active_sources']}")
    print(f"  🔴 Отключено: {current_stats['total_sources'] - current_stats['active_sources']}")
    
    # Поиск новых источников
    new_sources = finder.find_new_sources()
    
    if new_sources:
        print(f"\n{Fore.GREEN}✨ НАЙДЕНЫ НОВЫЕ ИСТОЧНИКИ:{Style.RESET_ALL}")
        for src in new_sources[:10]:
            print(f"  🔗 {src['url'][:70]}")
            print(f"     📊 {src['proxies']} прокси, пример: {src['sample'][:2] if src['sample'] else 'нет'}")
            
            # Сохраняем в историю
            tracker.add_source_event(src['url'], 'found', src['proxies'])
            source_stats.update(src['url'], src['proxies'])
    else:
        print(f"\n{Fore.YELLOW}⚠️ Новых источников не найдено{Style.RESET_ALL}")
    
    # Показываем неактивные источники
    inactive = [name for name, s in source_stats.stats.items() if not s.get('enabled', True)]
    if inactive:
        print(f"\n{Fore.RED}🔴 НЕАКТИВНЫЕ ИСТОЧНИКИ (автоотключены):{Style.RESET_ALL}")
        for name in inactive[:10]:
            s = source_stats.stats[name]
            print(f"  📍 {name[:60]}... (успех: {s['success_rate']:.1f}/проверку)")
    
    # Сохраняем статистику
    source_stats.save()
    
    print(f"\n{Fore.GREEN}✅ Поиск завершён{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
