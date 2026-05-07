"""
Configuration for Soccer Blueprint System
"""

import os


class Config:
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # File Paths
    INPUT_FILE = "input_matches.txt"
    
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
