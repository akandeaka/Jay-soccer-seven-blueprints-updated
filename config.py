"""
# In config.py - already configured
FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', '')
Configuration for Soccer Blueprint System
"""

import os


class Config:
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # API Keys
    ODDS_API_KEY = os.getenv('ODDS_API_KEY', '')
    FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', '')
    
    # File Paths (for manual fallback only)
    INPUT_FILE = "input_matches.txt"
    RESULTS_FILE = "results.csv"
    REPORT_FILE = "performance_report.md"
    
    # API Settings
    USE_API = True  # Set to False to use manual copy/paste instead
    SPORT = 'soccer'  # Options: 'soccer_epl', 'soccer_spain_la_liga', etc.
    REGIONS = 'uk'  # 'uk', 'us', 'eu', 'au'
    MARKETS = 'h2h,btts,totals'  # Get home/draw/away + BTTS + Over/Under
    
    # Accumulator Targets
    ACCUMULATOR_TARGETS = {
        '2_odds': {'min_matches': 2, 'max_matches': 3, 'target_odds': 2.0},
        '4_odds': {'min_matches': 4, 'max_matches': 4, 'target_odds': 4.0},
        '7_odds': {'min_matches': 5, 'max_matches': 5, 'target_odds': 7.0},
        '10_odds': {'min_matches': 5, 'max_matches': 6, 'target_odds': 10.0}
    }
    
    # Confidence Thresholds
    HIGH_CONFIDENCE = 75
    MEDIUM_CONFIDENCE = 60
    LOW_CONFIDENCE = 50
    
    # AI Analysis Settings
    AI_TREND_DAYS = 7
    MIN_RECENT_FORM = 5
