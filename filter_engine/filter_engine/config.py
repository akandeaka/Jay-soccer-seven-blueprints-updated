"""
Configuration for Filter Engine
"""

class FilterConfig:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = "8634288532:AAEGeI0DaqNIklrx8jWrLnW7dzhc41_wrS4"
    TELEGRAM_CHAT_ID = "401821398"
    
    # Filter thresholds
    HIGH_CONFIDENCE_THRESHOLD = 65
    MEDIUM_CONFIDENCE_THRESHOLD = 50
    
    # Output settings
    TOP_MATCHES_TO_SHOW = 20
    
    # Blueprint weights
    BLUEPRINT_WEIGHTS = {
        'BP1': 95,
        'BP2': 85,
        'BP3': 80,
        'BP4': 65,
        'BP5': 60,
        'BP6': 40,
        'BP7': 55
    }
    
    # Competition trust weights
    COMPETITION_WEIGHTS = {
        'Champions League': 90,
        'Eredivisie': 85,
        'Copa Libertadores': 85,
        'Copa Sudamericana': 80,
        'J1 League': 80,
        'Serie A': 85,
        'LaLiga': 85,
        'Premier League': 90,
        'U20': 0,
        'Women': 0,
        'W': 0,
        'Reserve League': 0,
        'I-League': 0,
        'Copa do Brasil Women': 0,
        'Brasileiro U20': 0,
        'U19': 0
    }


class IntegrationConfig:
    """Configuration for integrating with your blueprint system"""
    
    # File-based integration (recommended for testing)
    BLUEPRINT_OUTPUT_FILE = "blueprint_output.txt"
    
    # Module-based integration
    BLUEPRINT_MODULE_PATH = None
    BLUEPRINT_FUNCTION_NAME = "run_blueprint_scan"
    
    # API integration
    API_ENDPOINT = None
    API_KEY = None
    
    # Testing mode
    USE_MOCK_DATA = True  # Set to False when ready for production
