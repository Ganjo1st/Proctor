#!/usr/bin/env python3
# rapid_report.py - ЕДИНЫЙ ОТЧЁТ (перезаписывается)

import sys
import os
import argparse
from datetime import datetime
from colorama import init, Fore, Style

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import ProxyDatabase
from core.excel_report import ExcelReport

init(autoreset=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--single', action='store_true', help='Создать единый отчёт (перезапись)')
    args = parser.parse_args()
    
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR SMART - ЕДИНЫЙ ОТЧЁТ                   {Fore.CYAN}║
║{Fore.WHITE}         Обновление каждые 2 минуты                     {Fore.CYAN}║
║{Fore.GREEN}         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    db = ProxyDatabase()
    stats = db.get_stats()
    
    print(f"📊 Текущая статистика:")
    print(f"  📦 Всего в базе: {stats['total_in_db']}")
    print(f"  ✅ Рабочих: {stats['working_now']}")
    print(f"  🇷🇺 Российских: {stats['russian']}")
    print(f"  🇺🇸 Американских: {stats['american']}")
    print(f"  🌍 Глобальных: {stats['global']}")
    
    if stats['working_now'] == 0:
        print(f"\n{Fore.YELLOW}⚠️ Нет рабочих прокси для отчёта{Style.RESET_ALL}")
        return
    
    # Создаём папку для отчётов
    os.makedirs('reports', exist_ok=True)
    
    # Единый отчёт (перезаписывается)
    report = ExcelReport(db)
    filename = "reports/proxy_report.xlsx"
    
    report.create_report(filename)
    
    print(f"\n{Fore.GREEN}✅ Отчёт обновлён: {filename}{Style.RESET_ALL}")
    print(f"   Прямая ссылка: https://github.com/Ganjo1st/Proctor/blob/main/{filename}")

if __name__ == "__main__":
    main()
