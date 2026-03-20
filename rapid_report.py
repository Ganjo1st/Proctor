#!/usr/bin/env python3
# rapid_report.py - СОЗДАНИЕ EXCEL-ОТЧЁТА ПО ПРОКСИ

import sys
import os
from datetime import datetime
from colorama import init, Fore, Style

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import ProxyDatabase
from core.excel_report import ExcelReport

init(autoreset=True)

def main():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}         PROCTOR RAPID - ГЕНЕРАЦИЯ ОТЧЁТА              {Fore.CYAN}║
║{Fore.WHITE}         Подробный Excel-отчёт с фильтрами             {Fore.CYAN}║
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
    
    # Создаём отчёт
    report = ExcelReport(db)
    filename = f"reports/proxy_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    # Создаём папку для отчётов
    os.makedirs('reports', exist_ok=True)
    
    report.create_report(filename)
    
    print(f"\n{Fore.GREEN}✅ Отчёт создан: {filename}{Style.RESET_ALL}")
    print(f"   Открыть: https://github.com/Ganjo1st/Proctor/blob/main/{filename}")

if __name__ == "__main__":
    main()
