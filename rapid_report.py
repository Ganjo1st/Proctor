#!/usr/bin/env python3
# rapid_report.py - ПОЛНЫЙ ОТЧЁТ С АНАЛИТИКОЙ И ПОИСКОМ ИСТОЧНИКОВ

import sys
import os
from datetime import datetime
from colorama import init, Fore, Style

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import ProxyDatabase
from core.excel_report import ExcelReport
from core.source_finder import SourceFinder
from core.history_tracker import HistoryTracker

init(autoreset=True)

def main():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR SMART - ПОЛНЫЙ АНАЛИЗ                  {Fore.CYAN}║
║{Fore.WHITE}         Отчёт + поиск новых источников                 {Fore.CYAN}║
║{Fore.GREEN}         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    # 1. Поиск новых источников
    finder = SourceFinder()
    new_sources = finder.find_new_sources()
    
    if new_sources:
        print(f"\n{Fore.GREEN}✨ НАЙДЕНЫ НОВЫЕ ИСТОЧНИКИ:{Style.RESET_ALL}")
        for src in new_sources:
            print(f"  🔗 {src['url'][:70]}")
            print(f"     📊 {src['proxies']} прокси, пример: {src['sample'][:2]}")
    
    # 2. Получение статистики по источникам
    tracker = HistoryTracker()
    source_report = tracker.get_source_report()
    
    if source_report:
        print(f"\n{Fore.CYAN}📊 СТАТИСТИКА ИСТОЧНИКОВ:{Style.RESET_ALL}")
        for src in source_report[:10]:
            status = "🟢 активен" if src['активен'] else "🔴 неактивен"
            print(f"  {src['источник'][:40]}: {src['всего_найдено']} прокси ({status})")
    
    # 3. Создание Excel-отчёта
    db = ProxyDatabase()
    stats = db.get_stats()
    
    if stats['working_now'] == 0:
        print(f"\n{Fore.YELLOW}⚠️ Нет рабочих прокси для отчёта{Style.RESET_ALL}")
        return
    
    os.makedirs('reports', exist_ok=True)
    
    report = ExcelReport(db)
    filename = f"reports/proxy_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    report.create_report(filename)
    
    print(f"\n{Fore.GREEN}✅ ОТЧЁТ ГОТОВ!{Style.RESET_ALL}")
    print(f"   📁 Файл: {filename}")
    print(f"   🔗 Ссылка: https://github.com/Ganjo1st/Proctor/blob/main/{filename}")

if __name__ == "__main__":
    main()
