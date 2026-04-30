"""
Production Configuration for Filter Engine
"""

import os

class ProductionConfig:
    # ================================================================
    # HOW YOUR BLUEPRINT SYSTEM OUTPUTS DATA - CHOOSE ONE:
    # ================================================================
    
    # OPTION 1: File-based (recommended - easiest)
    # Your blueprint system writes output to this file
    BLUEPRINT_OUTPUT_FILE = "blueprint_output.txt"
    
    # OPTION 2: CSV file (if your system outputs CSV)
    BLUEPRINT_CSV_FILE = "matches_today.csv"
    
    # OPTION 3: API endpoint (if your system has an API)
    BLUEPRINT_API_URL = None  # e.g., "http://localhost:8000/blueprint"
    BLUEPRINT_API_KEY = None
    
    # OPTION 4: Database (if your system writes to database)
    DATABASE_URL = None
    
    # ================================================================
    # SCHEDULE SETTINGS
    # ================================================================
    
    # When to run the filter (24-hour format)
    RUN_HOUR = 5  # 5 AM
    RUN_MINUTE = 30  # 30 minutes
    
    # Timezone (default UTC)
    TIMEZONE = "UTC"
    
    # ================================================================
    # OUTPUT SETTINGS
    # ================================================================
    
    # Save filtered results to CSV
    SAVE_FILTERED_CSV = True
    
    # Save raw blueprint output for debugging
    SAVE_RAW_OUTPUT = True
    
    # ================================================================
    # TELEGRAM SETTINGS (from config.py)
    # ================================================================
    
    @property
    def TELEGRAM_BOT_TOKEN(self):
        return os.environ.get('TELEGRAM_BOT_TOKEN', '')
    
    @property
    def TELEGRAM_CHAT_ID(self):
        return os.environ.get('TELEGRAM_CHAT_ID', '')


# Load from environment
config = ProductionConfig()
