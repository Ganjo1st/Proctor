# core/notifier.py - ОТПРАВКА УВЕДОМЛЕНИЙ В TELEGRAM
import requests
import os
from datetime import datetime

class TelegramNotifier:
    """Отправка уведомлений в Telegram"""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
    
    def is_configured(self) -> bool:
        """Проверка, настроен ли бот"""
        return bool(self.token and self.chat_id)
    
    def send(self, message: str) -> bool:
        """Отправка сообщения"""
        if not self.is_configured():
            print("⚠️ Telegram не настроен (нет токена или chat_id)")
            return False
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка отправки в Telegram: {e}")
            return False
    
    def send_stats(self, stats: dict, new_count: int = 0) -> bool:
        """Отправка статистики"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"""
<b>🔄 PROCTOR SMART - ОБНОВЛЕНИЕ БАЗЫ ПРОКСИ</b>
⏰ <b>Время:</b> {now}

<b>📊 СТАТИСТИКА:</b>
├─ 📦 Всего в базе: {stats['total_in_db']}
├─ ✅ Рабочих: <b>{stats['working_now']}</b>
├─ 🇷🇺 Российских: {stats['russian']}
├─ 🇺🇸 Американских: {stats['american']}
└─ 🌍 Глобальных: {stats['global']}

<b>📈 ДИНАМИКА:</b>
└─ 🆕 Новых добавлено: <b>{new_count}</b>

<b>🔗 ССЫЛКИ НА ПРОКСИ:</b>
<a href="https://raw.githubusercontent.com/Ganjo1st/Proctor/main/data/proxies_all.txt">📦 Все прокси</a> | 
<a href="https://raw.githubusercontent.com/Ganjo1st/Proctor/main/data/proxies_russia.txt">🇷🇺 Россия</a> | 
<a href="https://raw.githubusercontent.com/Ganjo1st/Proctor/main/data/proxies_usa.txt">🇺🇸 США</a>

<i>Автоматическое обновление каждые 8 минут</i>
"""
        return self.send(message)
    
    def send_alert(self, message: str) -> bool:
        """Отправка срочного уведомления"""
        alert = f"""
<b>🚨 PROCTOR ALERT</b>
{message}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send(alert)
