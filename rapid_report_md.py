#!/usr/bin/env python3
# rapid_report_md.py - ПРОСТОЙ ТЕКСТОВЫЙ ОТЧЁТ В MARKDOWN
import os
import sys
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import ProxyDatabase


def get_country_name(code):
    """Преобразует код страны в название"""
    countries = {
        'RU': '🇷🇺 Россия', 'US': '🇺🇸 США', 'GB': '🇬🇧 Великобритания',
        'DE': '🇩🇪 Германия', 'FR': '🇫🇷 Франция', 'NL': '🇳🇱 Нидерланды',
        'CA': '🇨🇦 Канада', 'AU': '🇦🇺 Австралия', 'JP': '🇯🇵 Япония',
        'SG': '🇸🇬 Сингапур', 'IN': '🇮🇳 Индия', 'BR': '🇧🇷 Бразилия',
        'KR': '🇰🇷 Корея', 'HK': '🇭🇰 Гонконг', 'VN': '🇻🇳 Вьетнам',
        'ID': '🇮🇩 Индонезия', 'PH': '🇵🇭 Филиппины', 'EC': '🇪🇨 Эквадор',
        'CO': '🇨🇴 Колумбия', 'DO': '🇩🇴 Доминикана'
    }
    return countries.get(code, code)


def generate_report():
    """Генерирует текстовый отчёт в формате Markdown"""
    db = ProxyDatabase()
    stats = db.get_stats()
    
    # Собираем статистику по странам
    countries = Counter()
    ru_only = []
    us_only = []
    global_proxies = []
    
    for proxy, data in db.db.get('proxies', {}).items():
        if not data.get('working'):
            continue
        
        ru, us = db._determine_region_flags(data)
        
        if ru and us:
            global_proxies.append(proxy)
        elif ru:
            ru_only.append(proxy)
        elif us:
            us_only.append(proxy)
        else:
            country = data.get('country_code', '')
            if country:
                countries[country] += 1
    
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

| Регион | Количество |
|--------|------------|
| 🌍 Глобальные (РФ + США) | {stats['global']} |
| 🇷🇺 Российские (только РФ) | {stats['russian']} |
| 🇺🇸 Американские (только США) | {stats['american']} |

---

## 🗺️ Распределение по странам (остальные)

"""
    
    if countries:
        for country_code, count in sorted(countries.items(), key=lambda x: -x[1]):
            report += f"| {get_country_name(country_code)} | {count} |\n"
    else:
        report += "| Нет данных | 0 |\n"
    
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
    
    # Сохраняем отчёт
    os.makedirs('reports', exist_ok=True)
    with open('reports/proxy_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ Отчёт сохранён: reports/proxy_report.md")
    return report


if __name__ == "__main__":
    generate_report()
