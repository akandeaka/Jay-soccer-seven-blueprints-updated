"""
Configuration for Filter Engine
"""

class FilterConfig:
    TELEGRAM_BOT_TOKEN = "8634288532:AAEGeI0DaqNIklrx8jWrLnW7dzhc41_wrS4"
    TELEGRAM_CHAT_ID = "401821398"
    HIGH_CONFIDENCE_THRESHOLD = 65
    MEDIUM_CONFIDENCE_THRESHOLD = 50
    TOP_MATCHES_TO_SHOW = 20
    
    BLUEPRINT_WEIGHTS = {
        'BP1': 95, 'BP2': 85, 'BP3': 80,
        'BP4': 65, 'BP5': 60, 'BP6': 40, 'BP7': 55
    }
    
    COMPETITION_WEIGHTS = {
        'U20': 0, 'Women': 0, 'Reserve League': 0
    }