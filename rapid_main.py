# rapid_main.py - фрагмент
def run(self):
    # ... сбор и проверка ...
    
    # Сохраняем в базу
    for result, (proxy, source) in zip(results, to_check):
        if result['working']:
            result['source'] = source
            self.db.add_proxy(result['proxy'], result, source)
            self.source_stats.update(source, 1)
            new_working += 1
    
    # ⚡ НЕМЕДЛЕННЫЙ ЭКСПОРТ В ТЕКСТОВЫЕ ФАЙЛЫ
    self.db.export_to_txt()  # ← ВАЖНО!
    
    stats = self.db.get_stats()
    print(f"\n{Fore.GREEN}✅ ГОТОВО!{Style.RESET_ALL}")
    print(f"  ✨ Добавлено новых рабочих: {new_working}")
    print(f"  📊 Всего рабочих: {stats['working_now']}")
