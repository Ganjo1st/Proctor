#!/usr/bin/env python3
# rapid_report_md.py - ГЕНЕРАЦИЯ ПРОСТОГО ТЕКСТОВОГО ОТЧЁТА В MARKDOWN
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
        'CN': '🇨🇳 Китай', 'SG': '🇸🇬 Сингапур', 'IN': '🇮🇳 Индия',
        'BR': '🇧🇷 Бразилия', 'KR': '🇰🇷 Корея', 'HK': '🇭🇰 Гонконг',
        'VN': '🇻🇳 Вьетнам', 'ID': '🇮🇩 Индонезия', 'PH': '🇵🇭 Филиппины',
        'EC': '🇪🇨 Эквадор', 'CO': '🇨🇴 Колумбия', 'DO': '🇩🇴 Доминикана',
        'BG': '🇧🇬 Болгария', 'CZ': '🇨🇿 Чехия', 'PL': '🇵🇱 Польша',
        'UA': '🇺🇦 Украина', 'KZ': '🇰🇿 Казахстан', 'BY': '🇧🇾 Беларусь'
    }
    return countries.get(code, code)


def generate_report():
    """Генерирует текстовый отчёт в формате Markdown"""
    db = ProxyDatabase()
    stats = db.get_stats()
    
    # Собираем данные для статистики по странам
    countries = Counter()
    ru_only_proxies = []
    us_only_proxies = []
    global_proxies = []
    
    for proxy, data in db.db.get('proxies', {}).items():
        if not data.get('working'):
            continue
        
        ru, us = db._determine_region_flags(data)
        country_code = data.get('country_code', '')
        
        if country_code:
            countries[country_code] += 1
        
        if ru and us:
            global_proxies.append(proxy)
        elif ru:
            ru_only_proxies.append(proxy)
        elif us:
            us_only_proxies.append(proxy)
        else:
            if country_code:
                countries[country_code] += 1
    
    # Формируем отчёт
    report = f"""# 📊 Proctor SMART - Ежеминутный отчёт

**Последнее обновление:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

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
    
    # Сортируем страны по количеству
    if countries:
        for country_code, count in sorted(countries.items(), key=lambda x: -x[1]):
            country_name = get_country_name(country_code)
            report += f"| {country_name} | {count} |\n"
    else:
        report += "| Нет данных | 0 |\n"
    
    report += f"""
---

## 📋 Список рабочих прокси

### 🌍 Глобальные (РФ + США) — {len(global_proxies)} шт.
"""
    
    if global_proxies:
        for proxy in global_proxies[:20]:  # Показываем первые 20
            report += f"- `{proxy}`\n"
        if len(global_proxies) > 20:
            report += f"\n*... и ещё {len(global_proxies) - 20} прокси*\n"
    else:
        report += "*Нет глобальных прокси*\n"
    
    report += f"""
### 🇷🇺 Российские (только РФ) — {len(ru_only_proxies)} шт.
"""
    
    if ru_only_proxies:
        for proxy in ru_only_proxies[:20]:
            report += f"- `{proxy}`\n"
        if len(ru_only_proxies) > 20:
            report += f"\n*... и ещё {len(ru_only_proxies) - 20} прокси*\n"
    else:
        report += "*Нет российских прокси*\n"
    
    report += f"""
### 🇺🇸 Американские (только США) — {len(us_only_proxies)} шт.
"""
    
    if us_only_proxies:
        for proxy in us_only_proxies[:20]:
            report += f"- `{proxy}`\n"
        if len(us_only_proxies) > 20:
            report += f"\n*... и ещё {len(us_only_proxies) - 20} прокси*\n"
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
