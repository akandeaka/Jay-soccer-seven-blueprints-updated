"""
Configuration for Filter Engine
"""

import os

class FilterConfig:
    # Telegram Bot Configuration
    # ⚠️ For security, consider using environment variables instead of hardcoding:
    # TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    # TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
    
    TELEGRAM_BOT_TOKEN = "8634288532:AAEGeI0DaqNIklrx8jWrLnW7dzhc41_wrS4"
    TELEGRAM_CHAT_ID = "401821398"
    
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
        # Top European competitions
        'Champions League': 90,
        'Europa League': 85,
        'Conference League': 80,
        
        # Top 5 European Leagues
        'Premier League': 90,
        'LaLiga': 85,
        'Serie A': 85,
        'Bundesliga': 85,
        'Ligue 1': 80,
        
        # Second divisions
        'Championship': 75,
        'Serie B': 70,
        '2. Bundesliga': 70,
        'LaLiga 2': 70,
        
        # South American competitions
        'Copa Libertadores': 85,
        'Copa Sudamericana': 80,
        'Serie A Brazil': 75,
        'Primera Division Argentina': 70,
        
        # Asian top leagues
        'J1 League': 80,
        'K League 1': 75,
        'Saudi Pro League': 70,
        'Super League': 60,
        
        # European others
        'Eredivisie': 75,
        'Primeira Liga': 75,
        'Belgian Pro League': 70,
        'Scottish Premiership': 70,
        'Turkish Super Lig': 65,
        'Russian Premier League': 65,
        
        # Lower trust
        'Elite One': 50,
        'Botola Pro': 55,
        'Ligue Professionnelle 1': 55,
        'Kazakhstan Cup': 50,
        'Thai League 1': 55,
        'I Liqa': 45,
        'Liga 3': 40,
        '3. MSFL': 40,
        'Carioca 2': 35,
        'Cearense 2': 35,
        'Copa Norte': 35,
        'Copa Centro-Oeste': 35,
        
        # Auto-reject categories (weight = 0)
        'U20': 0,
        'U19': 0,
        'U18': 0,
        'U17': 0,
        'Women': 0,
        'W': 0,
        'Womens': 0,
        'Reserve League': 0,
        'Reserves': 0,
        'I-League': 0,
        'Copa do Brasil Women': 0,
        'Brasileiro U20': 0,
        'Brasileiro U20 B': 0,
        'Paulista A2': 30,  # Lower tier Brazilian
        'Campeonato Brasileiro U20': 0,
        'WE League Cup Women': 0,
        'SWPL 1 Women': 0,
        'Copa do Brasil Women': 0,
    }


class IntegrationConfig:
    """
    Configuration for integrating with your existing blueprint system.
    Configure ONE of the options below based on your setup.
    """
    
    # ================================================================
    # OPTION A: File-based integration (Recommended for simplicity)
    # ================================================================
    # Set this to the file path where your blueprint system writes output
    BLUEPRINT_OUTPUT_FILE = "blueprint_output.txt"
    
    # Optional: If your system writes total qualified to a separate file
    TOTAL_QUALIFIED_FILE = None
    
    
    # ================================================================
    # OPTION B: Module-based integration (If your system is Python code)
    # ================================================================
    # Example: "my_package.blueprint_scanner"
    BLUEPRINT_MODULE_PATH = None
    
    # The function name that returns (blueprint_text, total_qualified)
    BLUEPRINT_FUNCTION_NAME = "run_blueprint_scan"
    
    
    # ================================================================
    # OPTION C: API/Webhook integration (If your system exposes an API)
    # ================================================================
    API_ENDPOINT = None
    API_KEY = None
    API_METHOD = "GET"  # GET or POST
    
    
    # ================================================================
    # OPTION D: Database integration (If your system writes to a database)
    # ================================================================
    DATABASE_CONFIG = {
        'host': None,
        'port': None,
        'database': None,
        'table': None,
        'user': None,
        'password': None
    }
    
    
    # ================================================================
    # TESTING MODE
    # ================================================================
    # Set to True to use mock data for testing (no real integration)
    USE_MOCK_DATA = False
    
    
    # ================================================================
    # ADVANCED SETTINGS
    # ================================================================
    # Timeout for API calls (seconds)
    API_TIMEOUT = 30
    
    # Maximum retries for failed API calls
    MAX_RETRIES = 3
    
    # Delay between retries (seconds)
    RETRY_DELAY = 5
    
    # Log level for integration (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL = "INFO"
    
    # Whether to save raw blueprint output to file
    SAVE_RAW_OUTPUT = True
    
    # Path to save raw output
    RAW_OUTPUT_FILE = "raw_blueprint_output.txt"
    
    
    # ================================================================
    # HELPER METHOD: Validate configuration
    # ================================================================
    @classmethod
    def is_configured(cls) -> bool:
        """Check if at least one integration method is configured"""
        return (
            cls.USE_MOCK_DATA or
            cls.BLUEPRINT_OUTPUT_FILE is not None or
            cls.BLUEPRINT_MODULE_PATH is not None or
            cls.API_ENDPOINT is not None or
            cls._is_database_configured()
        )
    
    @classmethod
    def _is_database_configured(cls) -> bool:
        """Check if database is configured"""
        return all([
            cls.DATABASE_CONFIG.get('host'),
            cls.DATABASE_CONFIG.get('database'),
            cls.DATABASE_CONFIG.get('table')
        ])
    
    @classmethod
    def get_active_method(cls) -> str:
        """Return the active integration method"""
        if cls.USE_MOCK_DATA:
            return "MOCK_DATA"
        if cls.BLUEPRINT_OUTPUT_FILE:
            return "FILE"
        if cls.BLUEPRINT_MODULE_PATH:
            return "MODULE"
        if cls.API_ENDPOINT:
            return "API"
        if cls._is_database_configured():
            return "DATABASE"
        return "NONE"


# ================================================================
# ENVIRONMENT VARIABLE SUPPORT (For security)
# ================================================================

def load_from_env():
    """Load configuration from environment variables (overrides hardcoded values)"""
    
    # Telegram credentials from environment
    if os.environ.get('TELEGRAM_BOT_TOKEN'):
        FilterConfig.TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
        print("✓ Loaded TELEGRAM_BOT_TOKEN from environment")
    
    if os.environ.get('TELEGRAM_CHAT_ID'):
        FilterConfig.TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
        print("✓ Loaded TELEGRAM_CHAT_ID from environment")
    
    # Integration config from environment
    if os.environ.get('BLUEPRINT_OUTPUT_FILE'):
        IntegrationConfig.BLUEPRINT_OUTPUT_FILE = os.environ.get('BLUEPRINT_OUTPUT_FILE')
    
    if os.environ.get('BLUEPRINT_MODULE_PATH'):
        IntegrationConfig.BLUEPRINT_MODULE_PATH = os.environ.get('BLUEPRINT_MODULE_PATH')
    
    if os.environ.get('API_ENDPOINT'):
        IntegrationConfig.API_ENDPOINT = os.environ.get('API_ENDPOINT')
    
    if os.environ.get('API_KEY'):
        IntegrationConfig.API_KEY = os.environ.get('API_KEY')
    
    if os.environ.get('USE_MOCK_DATA', '').lower() == 'true':
        IntegrationConfig.USE_MOCK_DATA = True


# Auto-load from environment when module is imported
load_from_env()


# ================================================================
# CONFIGURATION VALIDATION
# ================================================================

def validate_config():
    """Validate the configuration and print warnings for issues"""
    
    print("\n" + "="*60)
    print("CONFIGURATION VALIDATION")
    print("="*60)
    
    # Check Telegram credentials
    if FilterConfig.TELEGRAM_BOT_TOKEN and FilterConfig.TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        print("✅ Telegram Bot Token: Configured")
    else:
        print("⚠️ Telegram Bot Token: Missing or using placeholder")
    
    if FilterConfig.TELEGRAM_CHAT_ID and FilterConfig.TELEGRAM_CHAT_ID != "YOUR_CHAT_ID_HERE":
        print("✅ Telegram Chat ID: Configured")
    else:
        print("⚠️ Telegram Chat ID: Missing or using placeholder")
    
    # Check integration method
    print(f"\n📡 Integration Method: {IntegrationConfig.get_active_method()}")
    
    if IntegrationConfig.get_active_method() == "MOCK_DATA":
        print("⚠️ Using MOCK DATA - Not connected to real blueprint system")
        print("   Set USE_MOCK_DATA = False when ready for production")
    
    elif IntegrationConfig.get_active_method() == "FILE":
        print(f"   File path: {IntegrationConfig.BLUEPRINT_OUTPUT_FILE}")
        import os
        if os.path.exists(IntegrationConfig.BLUEPRINT_OUTPUT_FILE):
            print("   ✅ File exists")
        else:
            print("   ⚠️ File does not exist yet (will be created when blueprint runs)")
    
    elif IntegrationConfig.get_active_method() == "MODULE":
        print(f"   Module path: {IntegrationConfig.BLUEPRINT_MODULE_PATH}")
        print(f"   Function name: {IntegrationConfig.BLUEPRINT_FUNCTION_NAME}")
    
    elif IntegrationConfig.get_active_method() == "API":
        print(f"   API Endpoint: {IntegrationConfig.API_ENDPOINT}")
    
    elif IntegrationConfig.get_active_method() == "NONE":
        print("❌ NO INTEGRATION METHOD CONFIGURED!")
        print("   Please configure one of the methods in IntegrationConfig")
    
    print("="*60 + "\n")


# Run validation when config is loaded (optional)
if __name__ == "__main__":
    validate_config()
