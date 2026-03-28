#!/usr/bin/env python3
# rapid_report.py - ЕДИНЫЙ ОТЧЁТ ИЗ БАЗЫ PROXY_DB.JSON
import os
import sys
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import ProxyDatabase
from core.excel_report import ExcelReport


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--single', action='store_true', help='Создать один Excel-отчёт')
    args = parser.parse_args()

    print("\n" + "="*55)
    print("📊 PROCTOR SMART - ЕДИНЫЙ ОТЧЁТ")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*55)

    db = ProxyDatabase(data_dir='data')
    stats = db.get_stats()
    
    print("\n📊 Текущая статистика из базы:")
    print(f"  📦 Всего в базе: {stats['total_in_db']}")
    print(f"  ✅ Рабочих: {stats['working_now']}")
    print(f"  🇷🇺 Российских: {stats['russian']}")
    print(f"  🇺🇸 Американских: {stats['american']}")
    print(f"  🌍 Глобальных: {stats['global']}")

    report = ExcelReport(db, data_dir='data')
    filename = report.create_report('reports/proxy_report.xlsx')

    print(f"\n✅ Отчёт обновлён: {filename}")
    print(f"   Прямая ссылка: https://github.com/Ganjo1st/Proctor/blob/main/reports/proxy_report.xlsx")


if __name__ == "__main__":
    main()
