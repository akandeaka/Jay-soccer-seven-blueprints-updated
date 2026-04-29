#!/usr/bin/env python3
"""
Main entry point for Filtered Blueprint Bot
This script wraps around your existing blueprint system without modifying it.
"""

import sys
import os
import json
import logging
from datetime import datetime

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


class BlueprintWrapper:
    """
    Wrapper around your existing blueprint system.
    Replace the methods below with calls to your actual existing code.
    """
    
    def __init__(self):
        self.last_blueprint_output = None
        self.last_total_qualified = 0
    
    def run_existing_blueprint_system(self) -> tuple:
        """
        CALL YOUR EXISTING BLUEPRINT SYSTEM HERE
        This function should execute your current blueprint scanning code
        and return:
        1. The raw blueprint output text
        2. The total number of qualifying matches
        """
        
        # ================================================================
        # OPTION 1: If your existing system outputs to a file
        # ================================================================
        # with open('blueprint_output.txt', 'r') as f:
        #     blueprint_text = f.read()
        # total_qualified = 205  # Extract this from your system
        # return blueprint_text, total_qualified
        
        # ================================================================
        # OPTION 2: If your existing system is a function you can import
        # ================================================================
        # from your_existing_module import run_blueprint_scan
        # blueprint_text, total_qualified = run_blueprint_scan()
        # return blueprint_text, total_qualified
        
        # ================================================================
        # OPTION 3: If your existing system outputs to Telegram/Webhook
        # ================================================================
        # blueprint_text, total_qualified = self.capture_telegram_output()
        # return blueprint_text, total_qualified
        
        # ================================================================
        # PLACEHOLDER - REPLACE WITH YOUR ACTUAL SYSTEM CALL
        # ================================================================
        logger.warning("Using placeholder blueprint data. Replace with your actual system!")
        
        # Example placeholder (REMOVE THIS and use your actual system)
        blueprint_text = """
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
        total_qualified = 205
        
        return blueprint_text, total_qualified
    
    def capture_telegram_output(self) -> tuple:
        """
        If your system sends to Telegram, capture the webhook/webhook output
        """
        # Implement webhook listener or read from database
        pass
    
    def save_state(self, blueprint_text: str, total_qualified: int, results_df):
        """Save current state for debugging"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'total_qualified': total_qualified,
            'blueprint_text': blueprint_text[:1000],  # Save first 1000 chars
            'filtered_results': results_df.to_dict('records') if results_df is not None else []
        }
        
        with open('filter_bot_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info("State saved to filter_bot_state.json")


def main():
    """Main execution function"""
    logger.info("="*60)
    logger.info("FILTERED BLUEPRINT BOT STARTING")
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
            return
        
        logger.info(f"✅ Received {total_qualified} qualifying matches from Stage 1")
        
        # Step 2: Parse the blueprint output
        logger.info("Step 2: Parsing blueprint data...")
        matches = filter_engine.parse_blueprint_text(blueprint_text)
        logger.info(f"✅ Parsed {len(matches)} matches")
        
        # Step 3: Apply filters and calculate confidence scores
        logger.info("Step 3: Applying filters and calculating confidence...")
        results_df = filter_engine.process_matches(matches)
        
        # Step 4: Calculate pass rates
        passed = len(results_df[results_df['Confidence'] >= FilterConfig.MEDIUM_CONFIDENCE_THRESHOLD])
        high_conf = len(results_df[results_df['Confidence'] >= FilterConfig.HIGH_CONFIDENCE_THRESHOLD])
        
        logger.info(f"✅ High confidence (65%+): {high_conf} matches")
        logger.info(f"✅ Medium confidence (50-64%): {passed - high_conf} matches")
        logger.info(f"❌ Rejected: {total_qualified - passed} matches")
        
        # Step 5: Save state for debugging
        wrapper.save_state(blueprint_text, total_qualified, results_df)
        
        # Step 6: Send filtered results to Telegram
        logger.info("Step 4: Sending filtered results to Telegram...")
        success = telegram.process_and_send(results_df, blueprint_text, total_qualified, send=True)
        
        if success:
            logger.info("✅ Filtered results sent to Telegram successfully")
        else:
            logger.warning("⚠️ Failed to send to Telegram (check credentials)")
        
        # Step 7: Save results to CSV for backup
        results_df.to_csv('filtered_results_backup.csv', index=False)
        logger.info("📁 Results saved to filtered_results_backup.csv")
        
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
    logger.info("FILTERED BLUEPRINT BOT FINISHED")
    logger.info("="*60)


# For running as a cron job or scheduled task
def run_as_cron():
    """Function to be called by cron/scheduler"""
    main()


# For running as a webhook listener
def webhook_listener(event, context):
    """For cloud functions (AWS Lambda, Google Cloud Functions)"""
    main()
    return {"statusCode": 200, "body": "Success"}


if __name__ == "__main__":
    main()
