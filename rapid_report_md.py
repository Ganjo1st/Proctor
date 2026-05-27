#!/usr/bin/env python3
# rapid_report_md.py - ПРОСТОЙ ТЕКСТОВЫЙ ОТЧЁТ В MARKDOWN
import os
import sys
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import ProxyDatabase


def get_country_name(code):
    countries = {
        'RU': '🇷🇺 Россия', 'US': '🇺🇸 США', 'GB': '🇬🇧 Великобритания',
        'DE': '🇩🇪 Германия', 'FR': '🇫🇷 Франция', 'NL': '🇳🇱 Нидерланды',
        'CA': '🇨🇦 Канада', 'AU': '🇦🇺 Австралия', 'JP': '🇯🇵 Япония',
        'SG': '🇸🇬 Сингапур', 'IN': '🇮🇳 Индия', 'BR': '🇧🇷 Бразилия',
        'KR': '🇰🇷 Корея', 'HK': '🇭🇰 Гонконг', 'VN': '🇻🇳 Вьетнам',
        'ID': '🇮🇩 Индонезия', 'PH': '🇵🇭 Филиппины', 'EC': '🇪🇨 Эквадор',
        'CO': '🇨🇴 Колумбия', 'DO': '🇩🇴 Доминикана', 'KZ': '🇰🇿 Казахстан',
        'UZ': '🇺🇿 Узбекистан', 'TH': '🇹🇭 Таиланд', 'FI': '🇫🇮 Финляндия',
        'SE': '🇸🇪 Швеция', 'CN': '🇨🇳 Китай', 'HK': '🇭🇰 Гонконг',
    }
    return countries.get(code, code)


def generate_report():
    db = ProxyDatabase()
    stats = db.get_stats()
    
    # Собираем данные для разделения
    ru_only = []
    us_only = []
    global_proxies = []
    telegram_proxies = []
    mobile_proxies = []
    desktop_proxies = []
    other_countries = Counter()
    
    for proxy, data in db.db.get('proxies', {}).items():
        if not data.get('working'):
            continue
        
        ru, us = db._determine_region_flags(data)
        
        # Telegram доступ
        if data.get('telegram_access'):
            telegram_proxies.append(proxy)
        
        # Поддержка платформ
        if data.get('mobile_supported'):
            mobile_proxies.append(proxy)
        if data.get('desktop_supported'):
            desktop_proxies.append(proxy)
        
        # Региональная классификация
        if ru and us:
            global_proxies.append(proxy)
        elif ru:
            ru_only.append(proxy)
        elif us:
            us_only.append(proxy)
        else:
            country = data.get('country_code', '')
            if country:
                other_countries[country] += 1
    
    # Формируем отчёт
    report = f"""# 📊 Proctor SMART - Автоматический отчёт

**Обновлено:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📈 Общая статистика

| Показатель | Значение |
|------------|----------|
| 📦 Всего прокси в базе | {stats['total_in_db']} |
| ✅ Рабочих прокси | {stats['working_now']} |
| ❌ Нерабочих прокси | {stats['total_in_db'] - stats['working_now']} |
| 🔄 Всего проверено за всё время | {stats['total_seen']} |

---

## 🌍 Географическое распределение

| Регион | Количество | Описание |
|--------|------------|----------|
| 🌍 Глобальные (РФ+США) | {len(global_proxies)} | Работают и в РФ, и в США |
| 🇷🇺 Российские (только РФ) | {len(ru_only)} | Работают только в РФ |
| 🇺🇸 Американские (только США) | {len(us_only)} | Работают только в США |

---

## 📱 Специализированные прокси

| Тип | Количество | Описание |
|-----|------------|----------|
| 📨 Telegram прокси | {len(telegram_proxies)} | Работают с Telegram (MTProto/HTTP) |
| 📱 Мобильные прокси | {len(mobile_proxies)} | Поддерживают мобильные User-Agent |
| 💻 Десктопные прокси | {len(desktop_proxies)} | Поддерживают десктопные User-Agent |

"""

    if other_countries:
        report += "## 🗺️ Распределение по странам (остальные)\n\n"
        report += "| Страна | Количество |\n|--------|------------|\n"
        for country_code, count in sorted(other_countries.items(), key=lambda x: -x[1]):
            report += f"| {get_country_name(country_code)} | {count} |\n"
        report += "\n"
    
    report += f"""
---

## 📋 Список рабочих прокси

### 🌍 Глобальные (РФ + США) — {len(global_proxies)} шт.
"""
    
    if global_proxies:
        for proxy in global_proxies[:15]:
            report += f"- `{proxy}`\n"
        if len(global_proxies) > 15:
            report += f"\n*... и ещё {len(global_proxies) - 15}*\n"
    else:
        report += "*Нет глобальных прокси*\n"
    
    report += f"""
### 🇷🇺 Российские (только РФ) — {len(ru_only)} шт.
"""
    
    if ru_only:
        for proxy in ru_only[:15]:
            report += f"- `{proxy}`\n"
        if len(ru_only) > 15:
            report += f"\n*... и ещё {len(ru_only) - 15}*\n"
    else:
        report += "*Нет российских прокси*\n"
    
    report += f"""
### 🇺🇸 Американские (только США) — {len(us_only)} шт.
"""
    
    if us_only:
        for proxy in us_only[:15]:
            report += f"- `{proxy}`\n"
        if len(us_only) > 15:
            report += f"\n*... и ещё {len(us_only) - 15}*\n"
    else:
        report += "*Нет американских прокси*\n"

    report += f"""
### 📨 Telegram прокси — {len(telegram_proxies)} шт.
"""
    
    if telegram_proxies:
        for proxy in telegram_proxies[:15]:
            report += f"- `{proxy}`\n"
        if len(telegram_proxies) > 15:
            report += f"\n*... и ещё {len(telegram_proxies) - 15}*\n"
    else:
        report += "*Нет Telegram прокси*\n"
    
    report += f"""
### 📱 Мобильные прокси — {len(mobile_proxies)} шт.
"""
    
    if mobile_proxies:
        for proxy in mobile_proxies[:15]:
            report += f"- `{proxy}`\n"
        if len(mobile_proxies) > 15:
            report += f"\n*... и ещё {len(mobile_proxies) - 15}*\n"
    else:
        report += "*Нет мобильных прокси*\n"
    
    report += f"""
### 💻 Десктопные прокси — {len(desktop_proxies)} шт.
"""
    
    if desktop_proxies:
        for proxy in desktop_proxies[:15]:
            report += f"- `{proxy}`\n"
        if len(desktop_proxies) > 15:
            report += f"\n*... и ещё {len(desktop_proxies) - 15}*\n"
    else:
        report += "*Нет десктопных прокси*\n"

    report += f"""

---

## 📁 Источники прокси

| Источник | Количество | Статус |
|----------|------------|--------|
"""
    
    # Собираем статистику по источникам
    sources = Counter()
    for proxy, data in db.db.get('proxies', {}).items():
        if data.get('working'):
            source = data.get('source', 'неизвестен')
            sources[source] += 1
    
    for source, count in sorted(sources.items(), key=lambda x: -x[1]):
        status = "✅ Активен" if count > 0 else "⏸ Ожидает"
        report += f"| {source} | {count} | {status} |\n"
    
    report += f"""

---

*Отчёт сгенерирован автоматически. Обновляется каждые 2 минуты.*
"""
    
    os.makedirs('reports', exist_ok=True)
    with open('reports/proxy_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ Отчёт сохранён: reports/proxy_report.md")
    return report


if __name__ == "__main__":
    generate_report()
