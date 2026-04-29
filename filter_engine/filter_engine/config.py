"""
Configuration for Filter Engine
"""

class FilterConfig:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # REPLACE WITH YOUR ACTUAL TOKEN
    TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"     # REPLACE WITH YOUR ACTUAL CHAT ID
    
    # Filter thresholds
    HIGH_CONFIDENCE_THRESHOLD = 65
    MEDIUM_CONFIDENCE_THRESHOLD = 50
    
    # Output settings
    TOP_MATCHES_TO_SHOW = 20
    
    # Blueprint weights (based on historical trends)
    BLUEPRINT_WEIGHTS = {
        'BP1': 95,   # Elite Home Banker
        'BP2': 85,   # Primary Favorite
        'BP3': 80,   # Moderate Favorite Safety
        'BP4': 65,   # Goal Engine
        'BP5': 60,   # Defensive Trap
        'BP6': 40,   # Strong Draw
        'BP7': 55    # High-Scoring Signals
    }
    
    # Competition trust weights (matches with 0 are auto-rejected)
    COMPETITION_WEIGHTS = {
        'Champions League': 90,
        'Eredivisie': 85,
        'Copa Libertadores': 85,
        'Copa Sudamericana': 80,
        'J1 League': 80,
        'Serie A': 85,
        'LaLiga': 85,
        'Super League': 60,
        'Premier League': 65,
        'U20': 0,
        'Women': 0,
        'W': 0,
        'Reserve League': 0,
        'I-League': 0,
        'Copa do Brasil Women': 0,
        'Brasileiro U20': 0,
        'U19': 0
    }
