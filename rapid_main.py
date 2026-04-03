#!/usr/bin/env python3
# rapid_main.py - УМНЫЙ СБОР ПРОКСИ С ГЕО-ОПРЕДЕЛЕНИЕМ И ФОНОВОЙ ПРОВЕРКОЙ
import asyncio
import sys
import os
from datetime import datetime
from colorama import init, Fore, Style

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.smart_scraper import SmartScraper
from core.rapid_checker import RapidChecker
from core.database import ProxyDatabase
from core.health_checker import HealthChecker

init(autoreset=True)


def print_banner():
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}      PROCTOR SMART - УМНЫЙ СБОР (с гео-данными)        {Fore.CYAN}║
║{Fore.WHITE}      Сохраняем географию каждого прокси                {Fore.CYAN}║
║{Fore.GREEN}      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)


async def main():
    print_banner()
    
    # ========== ИНИЦИАЛИЗАЦИЯ ==========
    db = ProxyDatabase()
    checker = RapidChecker()
    health_checker = HealthChecker(db)
    
    # ========== ФАЗА 0: ФОНОВАЯ ПРОВЕРКА ВСЕХ ПРОКСИ В БАЗЕ ==========
    print(f"\n{Fore.YELLOW}🩺 ФАЗА 0: Проверка здоровья всех прокси в базе...{Style.RESET_ALL}")
    health_results = await health_checker.check_all_proxies()
    
    stats = db.get_stats()
    print(f"  📊 После проверки: {stats['working_now']} рабочих прокси")
    
    # ========== ФАЗА 1: СБОР НОВЫХ ПРОКСИ ==========
    scraper = SmartScraper(db=db)
    
    print(f"\n{Fore.YELLOW}🧠 ФАЗА 1: Сбор новых прокси (с использованием глобальных прокси){Style.RESET_ALL}")
    print("─" * 60)
    
    all_proxies = await scraper.get_all_proxies()
    
    if not all_proxies:
        print(f"{Fore.RED}❌ Не удалось собрать прокси{Style.RESET_ALL}")
        return
    
    print(f"  📊 Собрано сырых прокси: {len(all_proxies)}")
    
    # ========== ФАЗА 2: ПРОВЕРКА НОВЫХ ПРОКСИ ==========
    # Берём первые 5000 для проверки (оптимально по времени)
    check_count = min(5000, len(all_proxies))
    print(f"\n{Fore.YELLOW}⚡ ФАЗА 2: Проверка {check_count} новых прокси...{Style.RESET_ALL}")
    
    start_time = datetime.now()
    proxies_to_check = all_proxies[:check_count]
    results = await checker.check_all(proxies_to_check)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    working_proxies_new = [r for r in results if r.get('working')]
    ru_count = len([r for r in working_proxies_new if r.get('ru_access')])
    us_count = len([r for r in working_proxies_new if r.get('us_access')])
    
    print(f"{Fore.GREEN}✅ ЗА {elapsed:.1f} СЕК: {len(working_proxies_new)}/{check_count} рабочих{Style.RESET_ALL}")
    print(f"   🇷🇺 РФ доступ: {ru_count} | 🇺🇸 США доступ: {us_count}")
    
    # ========== ФАЗА 3: ДОБАВЛЕНИЕ В БАЗУ ==========
    print(f"\n{Fore.YELLOW}💾 ФАЗА 3: Добавление новых прокси в базу...{Style.RESET_ALL}")
    new_count = 0
    for proxy_data in working_proxies_new:
        proxy = proxy_data['proxy']
        db.add_proxy(proxy, proxy_data, source=proxy_data.get('source', 'rapid_check'))
        new_count += 1
    
    # ========== ФАЗА 4: ЭКСПОРТ В ТЕКСТОВЫЕ ФАЙЛЫ ==========
    print(f"\n{Fore.YELLOW}📁 ФАЗА 4: Экспорт в текстовые файлы...{Style.RESET_ALL}")
    export_stats = db.export_to_txt()
    
    # ========== ФИНАЛЬНАЯ СТАТИСТИКА ==========
    stats = db.get_stats()
    global_proxies = await health_checker.get_global_proxies()
    best_global = await health_checker.get_best_proxy()
    
    print(f"\n{Fore.GREEN}✅ ГОТОВО!{Style.RESET_ALL}")
    print(f"  ✨ Добавлено новых рабочих: {new_count}")
    print(f"  📊 Всего рабочих: {stats['working_now']}")
    print(f"\n{Fore.CYAN}📊 СТАТИСТИКА ПО РЕГИОНАМ:{Style.RESET_ALL}")
    print(f"  🇷🇺 Российских (только РФ): {stats['russian']}")
    print(f"  🇺🇸 Американских (только США): {stats['american']}")
    print(f"  🌍 Глобальных (РФ+США): {stats['global']}")
    print(f"\n{Fore.CYAN}🌐 ГЛОБАЛЬНЫЕ ПРОКСИ ДЛЯ ОБХОДА:{Style.RESET_ALL}")
    print(f"  Доступно: {len(global_proxies)}")
    if best_global:
        print(f"  Лучший (самый быстрый): {best_global}")


if __name__ == "__main__":
    asyncio.run(main())
