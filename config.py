# config.py
import os

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # SMTP Email Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 465))
    SMTP_USER = os.getenv('SMTP_USER', 'aisec2025.notifications@gmail.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'Qwerasd@()34$')
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', 'your_email@gmail.com')
