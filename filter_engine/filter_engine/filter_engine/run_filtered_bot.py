#!/usr/bin/env python3
"""
Main entry point for Filtered Blueprint Bot
This script wraps around your existing blueprint system without modifying it.

HOW TO INTEGRATE WITH YOUR EXISTING SYSTEM:
=============================================
Option A: If your system outputs to a file
    - Set OUTPUT_FILE_PATH to your blueprint output file path
    - Set TOTAL_QUALIFIED_FILE if you extract counts from a separate file

Option B: If your system is a Python module
    - Uncomment the import and function call in _run_blueprint_system()

Option C: If your system sends to Telegram
    - Implement the webhook listener or read from your database
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Tuple, Optional

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import filter engine
from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('filter_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ================================================================
# CONFIGURATION - ADJUST THESE BASED ON YOUR SETUP
# ================================================================

class IntegrationConfig:
    """Configuration for integrating with your existing system"""
    
    # OPTION A: File-based integration
    # If your blueprint system writes output to a file
    BLUEPRINT_OUTPUT_FILE = "blueprint_output.txt"  # Path to your blueprint output file
    TOTAL_QUALIFIED_FILE = None  # Optional: separate file for total qualified count
    
    # OPTION B: Module-based integration
    # If your blueprint system is a Python module you can import
    BLUEPRINT_MODULE_PATH = None  # e.g., "your_package.blueprint_scanner"
    BLUEPRINT_FUNCTION_NAME = "run_blueprint_scan"  # Function that returns (text, total)
    
    # OPTION C: API/Webhook integration
    # If your blueprint system sends data via API
    API_ENDPOINT = None  # e.g., "http://localhost:5000/webhook"
    API_KEY = None
    
    # Fallback: Use mock data for testing (set to False in production)
    USE_MOCK_DATA = False  # Change to False when integrating with real system


# ================================================================
# BLUEPRINT WRAPPER - CONNECTS TO YOUR EXISTING SYSTEM
# ================================================================

class BlueprintWrapper:
    """
    Wrapper around your existing blueprint system.
    This connects to your current code WITHOUT modifying it.
    """
    
    def __init__(self):
        self.last_blueprint_output = None
        self.last_total_qualified = 0
    
    def _run_blueprint_system_via_file(self) -> Tuple[Optional[str], int]:
        """Read blueprint output from file"""
        try:
            if not os.path.exists(IntegrationConfig.BLUEPRINT_OUTPUT_FILE):
                logger.warning(f"Blueprint output file not found: {IntegrationConfig.BLUEPRINT_OUTPUT_FILE}")
                return None, 0
            
            with open(IntegrationConfig.BLUEPRINT_OUTPUT_FILE, 'r', encoding='utf-8') as f:
                blueprint_text = f.read()
            
            # Try to extract total qualified from the text
            import re
            total_match = re.search(r'Total qualifying matches:\s*(\d+)', blueprint_text)
            total_qualified = int(total_match.group(1)) if total_match else 0
            
            logger.info(f"Loaded blueprint from file: {len(blueprint_text)} characters, {total_qualified} matches")
            return blueprint_text, total_qualified
            
        except Exception as e:
            logger.error(f"Error reading blueprint file: {e}")
            return None, 0
    
    def _run_blueprint_system_via_module(self) -> Tuple[Optional[str], int]:
        """Import and call your existing blueprint module"""
        try:
            # Dynamically import your module
            module_path = IntegrationConfig.BLUEPRINT_MODULE_PATH
            function_name = IntegrationConfig.BLUEPRINT_FUNCTION_NAME
            
            if not module_path:
                return None, 0
            
            # Split module path (e.g., "my_package.blueprint_scanner")
            parts = module_path.split('.')
            module_name = '.'.join(parts[:-1]) if len(parts) > 1 else parts[0]
            class_or_func_name = parts[-1] if len(parts) > 1 else None
            
            # Import the module
            imported_module = __import__(module_name, fromlist=[class_or_func_name] if class_or_func_name else ['*'])
            
            # Get the function or class
            if class_or_func_name:
                blueprint_func = getattr(imported_module, function_name, None)
                if blueprint_func:
                    result = blueprint_func()
                    
                    # Handle different return types
                    if isinstance(result, tuple) and len(result) == 2:
                        blueprint_text, total_qualified = result
                    elif isinstance(result, str):
                        blueprint_text = result
                        total_qualified = self._extract_total_qualified(blueprint_text)
                    else:
                        blueprint_text = str(result)
                        total_qualified = 0
                    
                    return blueprint_text, total_qualified
            
            return None, 0
            
        except ImportError as e:
            logger.warning(f"Could not import blueprint module: {e}")
            return None, 0
        except Exception as e:
            logger.error(f"Error running blueprint module: {e}")
            return None, 0
    
    def _run_blueprint_system_via_api(self) -> Tuple[Optional[str], int]:
        """Fetch blueprint output from API/webhook"""
        try:
            import requests
            
            if not IntegrationConfig.API_ENDPOINT:
                return None, 0
            
            headers = {}
            if IntegrationConfig.API_KEY:
                headers['Authorization'] = f"Bearer {IntegrationConfig.API_KEY}"
            
            response = requests.get(
                IntegrationConfig.API_ENDPOINT,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                blueprint_text = data.get('blueprint_text', '')
                total_qualified = data.get('total_qualified', 0)
                return blueprint_text, total_qualified
            else:
                logger.warning(f"API returned status {response.status_code}")
                return None, 0
                
        except ImportError:
            logger.warning("requests module not installed. Install with: pip install requests")
            return None, 0
        except Exception as e:
            logger.error(f"Error calling API: {e}")
            return None, 0
    
    def _get_mock_data(self) -> Tuple[str, int]:
        """Return mock data for testing"""
        mock_text = """
📊 Summary:
   🟢 Blueprint 1: 5 matches
   🟢 Blueprint 2: 1 matches
   🟡 Blueprint 3: 3 matches
   🟡 Blueprint 4: 11 matches
   🟡 Blueprint 5: 19 matches
   🔴 Blueprint 6: 105 matches
   🔴 Blueprint 7: 61 matches

🔍 Total qualifying matches: 205
📊 Total scanned: 251
"""
        return mock_text, 205
    
    def _extract_total_qualified(self, blueprint_text: str) -> int:
        """Extract total qualified matches from blueprint text"""
        import re
        patterns = [
            r'Total qualifying matches:\s*(\d+)',
            r'🔍 Total qualifying matches:\s*(\d+)',
            r'Qualifying matches:\s*(\d+)',
            r'Total matches:\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, blueprint_text)
            if match:
                return int(match.group(1))
        
        return 0
    
    def run_existing_blueprint_system(self) -> Tuple[Optional[str], int]:
        """
        Run your existing blueprint system and return:
        1. The raw blueprint output text
        2. The total number of qualifying matches
        
        This method tries multiple integration methods in order.
        """
        
        # Use mock data for testing if enabled
        if IntegrationConfig.USE_MOCK_DATA:
            logger.info("Using mock data (USE_MOCK_DATA = True)")
            return self._get_mock_data()
        
        # Try file-based integration first
        if IntegrationConfig.BLUEPRINT_OUTPUT_FILE:
            logger.info(f"Attempting to read blueprint from file: {IntegrationConfig.BLUEPRINT_OUTPUT_FILE}")
            text, total = self._run_blueprint_system_via_file()
            if text:
                return text, total
        
        # Try module-based integration
        if IntegrationConfig.BLUEPRINT_MODULE_PATH:
            logger.info(f"Attempting to import blueprint module: {IntegrationConfig.BLUEPRINT_MODULE_PATH}")
            text, total = self._run_blueprint_system_via_module()
            if text:
                return text, total
        
        # Try API/webhook integration
        if IntegrationConfig.API_ENDPOINT:
            logger.info(f"Attempting to fetch from API: {IntegrationConfig.API_ENDPOINT}")
            text, total = self._run_blueprint_system_via_api()
            if text:
                return text, total
        
        # If all methods fail, log error and return None
        logger.error("""
        ╔════════════════════════════════════════════════════════════════╗
        ║  No blueprint integration method configured!                  ║
        ║                                                                ║
        ║  Please configure one of the following in IntegrationConfig:  ║
        ║  1. BLUEPRINT_OUTPUT_FILE - Path to your blueprint output file║
        ║  2. BLUEPRINT_MODULE_PATH - Import path to your blueprint code║
        ║  3. API_ENDPOINT - API endpoint that returns blueprint data   ║
        ║                                                                ║
        ║  Or set USE_MOCK_DATA = True for testing                      ║
        ╚════════════════════════════════════════════════════════════════╝
        """)
        
        return None, 0
    
    def capture_telegram_output(self) -> Tuple[Optional[str], int]:
        """
        If your system sends to Telegram, capture the webhook output.
        Implement this based on your webhook setup.
        """
        # Example: Read from a webhook receiver file
        webhook_file = "webhook_payload.json"
        if os.path.exists(webhook_file):
            try:
                with open(webhook_file, 'r') as f:
                    data = json.load(f)
                    blueprint_text = data.get('message', '')
                    total_qualified = self._extract_total_qualified(blueprint_text)
                    return blueprint_text, total_qualified
            except Exception as e:
                logger.error(f"Error reading webhook file: {e}")
        
        return None, 0
    
    def save_state(self, blueprint_text: str, total_qualified: int, results_df):
        """Save current state for debugging and recovery"""
        try:
            # Convert DataFrame to serializable format
            filtered_results = []
            if results_df is not None and not results_df.empty:
                filtered_results = results_df.head(50).to_dict('records')
            
            state = {
                'timestamp': datetime.now().isoformat(),
                'total_qualified': total_qualified,
                'blueprint_text_length': len(blueprint_text) if blueprint_text else 0,
                'blueprint_text_preview': blueprint_text[:500] if blueprint_text else '',
                'filtered_results': filtered_results,
                'config': {
                    'USE_MOCK_DATA': IntegrationConfig.USE_MOCK_DATA,
                    'BLUEPRINT_OUTPUT_FILE': IntegrationConfig.BLUEPRINT_OUTPUT_FILE,
                    'BLUEPRINT_MODULE_PATH': IntegrationConfig.BLUEPRINT_MODULE_PATH,
                    'API_ENDPOINT': IntegrationConfig.API_ENDPOINT
                }
            }
            
            with open('filter_bot_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info("State saved to filter_bot_state.json")
        except Exception as e:
            logger.warning(f"Could not save state: {e}")


# ================================================================
# MAIN EXECUTION
# ================================================================

def main():
    """Main execution function"""
    logger.info("="*60)
    logger.info("FILTERED BLUEPRINT BOT STARTING")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    # Initialize wrapper (connects to your existing system)
    wrapper = BlueprintWrapper()
    
    # Initialize filter engine
    filter_engine = BlueprintFilterEngine()
    
    # Initialize Telegram integrator
    telegram = TelegramIntegrator()
    
    try:
        # Step 1: Run your existing blueprint system
        logger.info("Step 1: Running existing blueprint system...")
        blueprint_text, total_qualified = wrapper.run_existing_blueprint_system()
        
        if not blueprint_text:
            logger.error("No blueprint output received from existing system")
            logger.info("Attempting to send error notification to Telegram...")
            telegram.send_to_telegram("⚠️ Filter Engine Error: No blueprint output received from Stage 1")
            return
        
        logger.info(f"✅ Received {total_qualified} qualifying matches from Stage 1")
        
        # Step 2: Parse the blueprint output
        logger.info("Step 2: Parsing blueprint data...")
        matches = filter_engine.parse_blueprint_text(blueprint_text)
        
        if not matches:
            logger.warning("No matches parsed from blueprint text. Check the format.")
            logger.info("Blueprint text preview:")
            logger.info(blueprint_text[:500])
            return
        
        logger.info(f"✅ Parsed {len(matches)} matches")
        
        # Step 3: Apply filters and calculate confidence scores
        logger.info("Step 3: Applying filters and calculating confidence...")
        results_df = filter_engine.process_matches(matches)
        
        if results_df.empty:
            logger.warning("No matches passed the filter engine")
            telegram.send_to_telegram("⚠️ Filter Engine Warning: No matches passed the filter thresholds")
            return
        
        # Step 4: Calculate pass rates
        passed = len(results_df[results_df['Confidence'] >= FilterConfig.MEDIUM_CONFIDENCE_THRESHOLD])
        high_conf = len(results_df[results_df['Confidence'] >= FilterConfig.HIGH_CONFIDENCE_THRESHOLD])
        rejected = total_qualified - passed if total_qualified > 0 else len(matches) - passed
        
        logger.info(f"✅ High confidence ({FilterConfig.HIGH_CONFIDENCE_THRESHOLD}%+): {high_conf} matches")
        logger.info(f"✅ Medium confidence ({FilterConfig.MEDIUM_CONFIDENCE_THRESHOLD}-{FilterConfig.HIGH_CONFIDENCE_THRESHOLD-1}%): {passed - high_conf} matches")
        logger.info(f"❌ Rejected: {rejected} matches")
        
        # Step 5: Save state for debugging
        wrapper.save_state(blueprint_text, total_qualified, results_df)
        
        # Step 6: Send filtered results to Telegram
        logger.info("Step 4: Sending filtered results to Telegram...")
        success = telegram.process_and_send(results_df, blueprint_text, total_qualified, send=True)
        
        if success:
            logger.info("✅ Filtered results sent to Telegram successfully")
        else:
            logger.warning("⚠️ Failed to send to Telegram (check credentials in config.py)")
        
        # Step 7: Save results to CSV for backup
        results_df.to_csv('filtered_results_backup.csv', index=False)
        logger.info("📁 Results saved to filtered_results_backup.csv")
        
        # Step 8: Save top 20 for quick reference
        top_20 = results_df.head(20)
        top_20.to_csv('top_20_picks.csv', index=False)
        logger.info("📁 Top 20 picks saved to top_20_picks.csv")
        
    except Exception as e:
        logger.error(f"❌ Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        
        # Send error notification to Telegram if possible
        try:
            error_msg = f"⚠️ Filter Engine Error: {str(e)[:200]}"
            telegram.send_to_telegram(error_msg)
        except:
            pass
        
        sys.exit(1)
    
    logger.info("="*60)
    logger.info("FILTERED BLUEPRINT BOT FINISHED SUCCESSFULLY")
    logger.info("="*60)


# For running as a cron job or scheduled task
def run_as_cron():
    """Function to be called by cron/scheduler"""
    main()


# For running as a webhook listener
def webhook_listener(event=None, context=None):
    """For cloud functions (AWS Lambda, Google Cloud Functions)"""
    main()
    return {"statusCode": 200, "body": "Success"}


if __name__ == "__main__":
    main()
