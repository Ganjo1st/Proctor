#!/usr/bin/env python3
# rapid_report.py - ГЕНЕРАЦИЯ ОТЧЁТА (поддерживает оба формата)
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rapid_report_md import generate_report as generate_md_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--single', action='store_true', help='Создать отчёт')
    parser.add_argument('--format', choices=['md', 'xlsx'], default='md', help='Формат отчёта')
    args = parser.parse_args()
    
    if args.format == 'md':
        generate_md_report()
    else:
        # Если нужен Excel, используем старый
        from core.database import ProxyDatabase
        from core.excel_report import ExcelReport
        
        db = ProxyDatabase()
        report = ExcelReport(db)
        report.create_report('reports/proxy_report.xlsx')
        print("✅ Отчёт сохранён: reports/proxy_report.xlsx")


if __name__ == "__main__":
    main()
