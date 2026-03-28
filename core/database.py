def export_to_txt(self) -> Dict[str, List[str]]:
    """Экспорт в текстовые файлы по регионам"""
    all_proxies = []
    ru_proxies = []
    us_proxies = []
    global_proxies = []
    
    for proxy, data in self.db['proxies'].items():
        if data['working']:
            all_proxies.append(proxy)
            
            if data.get('ru_access') and data.get('us_access'):
                global_proxies.append(proxy)
            elif data.get('ru_access'):
                ru_proxies.append(proxy)
            elif data.get('us_access'):
                us_proxies.append(proxy)
    
    # Сортируем по скорости
    all_proxies.sort(key=lambda p: self.db['proxies'][p].get('latency', 9999))
    ru_proxies.sort(key=lambda p: self.db['proxies'][p].get('latency', 9999))
    us_proxies.sort(key=lambda p: self.db['proxies'][p].get('latency', 9999))
    global_proxies.sort(key=lambda p: self.db['proxies'][p].get('latency', 9999))
    
    # Сохраняем
    with open(os.path.join(self.data_dir, 'proxies_all.txt'), 'w') as f:
        f.write('\n'.join(all_proxies))
    
    with open(os.path.join(self.data_dir, 'proxies_russia.txt'), 'w') as f:
        f.write('\n'.join(ru_proxies))
    
    with open(os.path.join(self.data_dir, 'proxies_usa.txt'), 'w') as f:
        f.write('\n'.join(us_proxies))
    
    with open(os.path.join(self.data_dir, 'proxies_global.txt'), 'w') as f:
        f.write('\n'.join(global_proxies))
    
    with open(os.path.join(self.data_dir, 'proxies_fast.txt'), 'w') as f:
        f.write('\n'.join(all_proxies[:20]))
    
    # Выводим для отладки
    print(f"  📁 Экспортировано: РФ={len(ru_proxies)}, США={len(us_proxies)}, Глобальных={len(global_proxies)}")
    
    return {
        'all': len(all_proxies),
        'ru': len(ru_proxies),
        'us': len(us_proxies),
        'global': len(global_proxies)
    }
