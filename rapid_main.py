#!/usr/bin/env python3
# rapid_main.py - УМНЫЙ СБОР ПРОКСИ С ГЕО-ОПРЕДЕЛЕНИЕМ
import asyncio
import sys
import os
from datetime import datetime
from colorama import init, Fore, Style

# Добавляем core в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.smart_scraper import SmartScraper
from core.rapid_checker import RapidChecker
from core.database import ProxyDatabase

init(autoreset=True)


def print_banner():
    """Красивый баннер"""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║{Fore.YELLOW}      PROCTOR SMART - УМНЫЙ СБОР (с гео-данными)        {Fore.CYAN}║
║{Fore.WHITE}      Сохраняем географию каждого прокси                {Fore.CYAN}║
║{Fore.GREEN}      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    {Fore.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)


def get_working_proxies_from_db() -> list:
    """Получает список рабочих прокси из базы для использования в сборщике"""
    db = ProxyDatabase()
    working = []
    for proxy, data in db.db.get('proxies', {}).items():
        if data.get('working'):
            working.append(proxy)
    return working


async def main():
    print_banner()
    
    # Получаем рабочие прокси из базы для обхода блокировок
    working_proxies = get_working_proxies_from_db()
    print(f"📡 Загружено {len(working_proxies)} рабочих прокси для обхода блокировок")
    
    # Инициализация с передачей рабочих прокси
    scraper = SmartScraper(working_proxies=working_proxies)
    checker = RapidChecker()
    db = ProxyDatabase()
    
    # Фаза 1: Сбор прокси
    print(f"\n{Fore.YELLOW}🧠 УМНЫЙ СБОР ПРОКСИ (с источниками){Style.RESET_ALL}")
    print("─" * 60)
    
    # Сбор из всех источников
    all_proxies = await scraper.get_all_proxies()
    
    if not all_proxies:
        print(f"{Fore.RED}❌ Не удалось собрать прокси{Style.RESET_ALL}")
        return
    
    # Фаза 2: Проверка (проверяем 3000 прокси для большего охвата)
    print(f"\n{Fore.YELLOW}⚡ ПРОВЕРКА 3000 ПРОКСИ С ГЕО-ОПРЕДЕЛЕНИЕМ...{Style.RESET_ALL}")
    
    start_time = datetime.now()
    proxies_to_check = all_proxies[:3000]
    results = await checker.check_all(proxies_to_check)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Фильтруем рабочие
    working_proxies_new = [r for r in results if r.get('working')]
    ru_count = len([r for r in working_proxies_new if r.get('ru_access')])
    us_count = len([r for r in working_proxies_new if r.get('us_access')])
    
    print(f"{Fore.GREEN}✅ ЗА {elapsed:.1f} СЕК: {len(working_proxies_new)}/{len(proxies_to_check)} рабочих{Style.RESET_ALL}")
    print(f"   🇷🇺 РФ доступ: {ru_count} | 🇺🇸 США доступ: {us_count}")
    
    # Фаза 3: Добавление в базу
    new_count = 0
    for proxy_data in working_proxies_new:
        proxy = proxy_data['proxy']
        # Добавляем в базу
        db.add_proxy(proxy, proxy_data, source=proxy_data.get('source', 'rapid_check'))
        new_count += 1
    
    # Фаза 4: Экспорт в текстовые файлы
    print()
    db.export_to_txt()
    
    # Финальная статистика
    stats = db.get_stats()
    print(f"\n{Fore.GREEN}✅ ГОТОВО!{Style.RESET_ALL}")
    print(f"  ✨ Добавлено новых рабочих: {new_count}")
    print(f"  📊 Всего рабочих: {stats['working_now']}")
    print(f"\n{Fore.CYAN}📊 СТАТИСТИКА ПО РЕГИОНАМ:{Style.RESET_ALL}")
    print(f"  🇷🇺 Российских: {stats['russian']}")
    print(f"  🇺🇸 Американских: {stats['american']}")
    print(f"  🌍 Глобальных: {stats['global']}")


if __name__ == "__main__":
    asyncio.run(main())
