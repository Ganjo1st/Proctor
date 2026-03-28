# core/notifier.py - TELEGRAM УВЕДОМЛЕНИЯ
import asyncio
import aiohttp
import os
from typing import Optional


class TelegramNotifier:
    """Отправка уведомлений в Telegram"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Инициализация нотификатора.
        Токен и chat_id можно передать или взять из переменных окружения.
        """
        self.bot_token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.environ.get('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
    
    async def send_message(self, message: str) -> bool:
        """Отправка сообщения в Telegram"""
        if not self.enabled:
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def send_proxy_stats(self, stats: dict):
        """Отправка статистики по прокси"""
        if not self.enabled:
            return
        
        message = (
            f"📊 <b>Proctor Stats</b>\n"
            f"├─ Всего в базе: {stats.get('total_in_db', 0)}\n"
            f"├─ Рабочих: {stats.get('working_now', 0)}\n"
            f"├─ 🇷🇺 Российских: {stats.get('russian', 0)}\n"
            f"├─ 🇺🇸 Американских: {stats.get('american', 0)}\n"
            f"└─ 🌍 Глобальных: {stats.get('global', 0)}"
        )
        await self.send_message(message)
    
    async def send_new_proxies(self, new_count: int, ru_count: int = 0, us_count: int = 0):
        """Отправка уведомления о новых прокси"""
        if not self.enabled:
            return
        
        message = f"✅ Найдено {new_count} новых прокси!"
        if ru_count > 0:
            message += f"\n🇷🇺 Российских: {ru_count}"
        if us_count > 0:
            message += f"\n🇺🇸 Американских: {us_count}"
        
        await self.send_message(message)
