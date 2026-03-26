# rapid_clean.py - фрагмент
def run(self):
    # ... проверка и удаление ...
    
    self.db.save_db()
    # ⚡ НЕМЕДЛЕННЫЙ ЭКСПОРТ ПОСЛЕ ОЧИСТКИ
    self.db.export_to_txt()  # ← ВАЖНО!
    
    stats = self.db.export_to_txt()
    print(f"\n{Fore.GREEN}✅ ОЧИСТКА ЗАВЕРШЕНА{Style.RESET_ALL}")
    print(f"  🟢 Живых: {alive}")
    print(f"  🔴 Мёртвых удалено: {dead}")
    print(f"  📦 Осталось в базе: {stats['all']}")
