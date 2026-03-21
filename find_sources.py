#!/usr/bin/env python3
# find_sources.py - ПОИСК НОВЫХ ИСТОЧНИКОВ ПРОКСИ

import sys
import os
import json
from datetime import datetime
from colorama import init, Fore, Style

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.source_finder import SourceFinder
from core.history_tracker import HistoryTracker

init(autoreset=True)

def main():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR SMART - ПОИСК ИСТОЧНИКОВ               {Fore.CYAN}║
║{Fore.WHITE}         Автоматический поиск новых прокси-источников   {Fore.CYAN}║
║{Fore.GREEN}         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    finder = SourceFinder()
    tracker = HistoryTracker()
    
    # Поиск новых источников
    new_sources = finder.find_new_sources()
    
    if new_sources:
        print(f"\n{Fore.GREEN}✨ НАЙДЕНЫ НОВЫЕ ИСТОЧНИКИ:{Style.RESET_ALL}")
        for src in new_sources[:10]:
            print(f"  🔗 {src['url'][:70]}")
            print(f"     📊 {src['proxies']} прокси, пример: {src['sample'][:2] if src['sample'] else 'нет'}")
            
            # Сохраняем в историю
            tracker.add_source_event(src['url'], 'found', src['proxies'])
    else:
        print(f"\n{Fore.YELLOW}⚠️ Новых источников не найдено{Style.RESET_ALL}")
    
    # Показываем статистику известных источников
    source_report = tracker.get_source_report()
    if source_report:
        print(f"\n{Fore.CYAN}📊 СТАТИСТИКА ИЗВЕСТНЫХ ИСТОЧНИКОВ:{Style.RESET_ALL}")
        active = [s for s in source_report if s['активен']]
        inactive = [s for s in source_report if not s['активен']]
        print(f"  🟢 Активных: {len(active)}")
        print(f"  🔴 Неактивных: {len(inactive)}")
        print(f"  📦 Всего найдено источников: {len(source_report)}")

if __name__ == "__main__":
    main()
