    def add_proxy(self, proxy: str, proxy_data: Dict, source: str = None):
        """Добавление прокси с гео-данными"""
        now = datetime.now().isoformat()
        
        if proxy in self.db['proxies']:
            self.db['proxies'][proxy].update({
                'last_seen': now,
                'working': proxy_data.get('working', False),
                'latency': proxy_data.get('latency', 9999),
                'ru_access': proxy_data.get('ru_access', False),
                'us_access': proxy_data.get('us_access', False),
                'source': source or self.db['proxies'][proxy].get('source', 'неизвестен'),
                'country': proxy_data.get('country'),
                'country_code': proxy_data.get('country_code'),
                'region': proxy_data.get('region')
            })
        else:
            self.db['proxies'][proxy] = {
                'first_seen': now,
                'last_seen': now,
                'working': proxy_data.get('working', False),
                'latency': proxy_data.get('latency', 9999),
                'ru_access': proxy_data.get('ru_access', False),
                'us_access': proxy_data.get('us_access', False),
                'source': source or 'неизвестен',
                'country': proxy_data.get('country'),
                'country_code': proxy_data.get('country_code'),
                'region': proxy_data.get('region')
            }
            self.db['stats']['total_seen'] += 1
