#!/usr/bin/env python3
"""
PRODUCTION: Filtered Blueprint Bot
Runs daily, reads real blueprint data, sends filtered results to Telegram
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig
from production_config import ProductionConfig
from blueprint_reader import BlueprintReader


def main():
    """Production execution function"""
    print("="*60)
    print("🚀 FILTERED BLUEPRINT BOT - PRODUCTION MODE")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    # Initialize components
    filter_engine = BlueprintFilterEngine()
    reader = BlueprintReader(ProductionConfig())
    
    # Initialize Telegram
    telegram = TelegramIntegrator(
        bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
        chat_id=FilterConfig.TELEGRAM_CHAT_ID
    )
    
    # Step 1: Read blueprint data from your system
    print("\n📥 STEP 1: Reading blueprint data...")
    blueprint_text, total_qualified = reader.get_blueprint_data()
    
    if not blueprint_text:
        print("❌ No blueprint data found!")
        print("\n💡 Make sure one of these is configured:")
        print("   1. BLUEPRINT_OUTPUT_FILE - text file with blueprint output")
        print("   2. BLUEPRINT_CSV_FILE - CSV file with match data")
        print("   3. BLUEPRINT_API_URL - API endpoint")
        
        # Send error notification to Telegram
        error_msg = "⚠️ Filter Engine Error: No blueprint data found. Please check configuration."
        telegram.send_telegram_message(error_msg)
        return
    
    print(f"✅ Found {total_qualified} qualifying matches")
    
    # Save raw output for debugging (optional)
    if ProductionConfig.SAVE_RAW_OUTPUT:
        with open('raw_blueprint_output.txt', 'w', encoding='utf-8') as f:
            f.write(blueprint_text)
        print("📁 Saved raw blueprint output to raw_blueprint_output.txt")
    
    # Step 2: Parse and filter
    print("\n🔄 STEP 2: Parsing and filtering matches...")
    matches = filter_engine.parse_blueprint_text(blueprint_text)
    print(f"✅ Parsed {len(matches)} matches")
    
    results_df = filter_engine.process_matches(matches)
    
    # Step 3: Calculate statistics
    high_conf = len(results_df[results_df['Confidence'] >= FilterConfig.HIGH_CONFIDENCE_THRESHOLD])
    medium_conf = len(results_df[(results_df['Confidence'] >= FilterConfig.MEDIUM_CONFIDENCE_THRESHOLD) & 
                                  (results_df['Confidence'] < FilterConfig.HIGH_CONFIDENCE_THRESHOLD)])
    
    print(f"\n📊 FILTER RESULTS:")
    print(f"   🔥 High confidence ({FilterConfig.HIGH_CONFIDENCE_THRESHOLD}%+): {high_conf} matches")
    print(f"   ⚠️ Medium confidence: {medium_conf} matches")
    print(f"   ❌ Rejected: {total_qualified - (high_conf + medium_conf)} matches")
    
    # Step 4: Save filtered results
    if ProductionConfig.SAVE_FILTERED_CSV:
        results_df.to_csv('filtered_results.csv', index=False)
        results_df.head(20).to_csv('top_20_picks.csv', index=False)
        print("📁 Saved filtered results to CSV files")
        #!/usr/bin/env python3
"""
PRODUCTION: Filtered Blueprint Bot with Accumulators
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig
from production_config import ProductionConfig
from blueprint_reader import BlueprintReader
from accumulator_builder import AccumulatorBuilder


def main():
    """Production execution function"""
    print("="*60)
    print("🚀 FILTERED BLUEPRINT BOT - PRODUCTION MODE")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    # Initialize components
    filter_engine = BlueprintFilterEngine()
    reader = BlueprintReader(ProductionConfig())
    accumulator_builder = AccumulatorBuilder()
    
    # Initialize Telegram
    telegram = TelegramIntegrator(
        bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
        chat_id=FilterConfig.TELEGRAM_CHAT_ID
    )
    
    # Step 1: Read blueprint data from your system
    print("\n📥 STEP 1: Reading blueprint data...")
    blueprint_text, total_qualified = reader.get_blueprint_data()
    
    if not blueprint_text:
        print("❌ No blueprint data found!")
        error_msg = "⚠️ Filter Engine Error: No blueprint data found."
        telegram.send_telegram_message(error_msg)
        return
    
    print(f"✅ Found {total_qualified} qualifying matches")
    
    # Step 2: Parse and filter
    print("\n🔄 STEP 2: Parsing and filtering matches...")
    matches = filter_engine.parse_blueprint_text(blueprint_text)
    print(f"✅ Parsed {len(matches)} matches")
    
    results_df = filter_engine.process_matches(matches)
    
    # Get top 20 matches (or all if less than 20)
    top_matches = results_df.head(20).to_dict('records')
    
    # Step 3: Build accumulators
    print("\n🔨 STEP 3: Building accumulators...")
    accumulators = accumulator_builder.build_all_accumulators(top_matches)
    
    # Step 4: Calculate statistics
    high_conf = len(results_df[results_df['Confidence'] >= FilterConfig.HIGH_CONFIDENCE_THRESHOLD])
    medium_conf = len(results_df[(results_df['Confidence'] >= FilterConfig.MEDIUM_CONFIDENCE_THRESHOLD) & 
                                  (results_df['Confidence'] < FilterConfig.HIGH_CONFIDENCE_THRESHOLD)])
    
    print(f"\n📊 FILTER RESULTS:")
    print(f"   🔥 High confidence (65%+): {high_conf} matches")
    print(f"   ⚠️ Medium confidence: {medium_conf} matches")
    
    # Step 5: Build full Telegram message
    print("\n📤 STEP 4: Building Telegram message...")
    
    # Get the main filtered results message
    filtered_message = telegram.build_telegram_message(results_df, blueprint_text, total_qualified)
    
    # Get accumulator message
    accumulator_message = accumulator_builder.format_accumulator_message(accumulators, len(top_matches))
    
    # Combine messages
    final_message = filtered_message + "\n" + accumulator_message
    
    # Step 6: Send to Telegram
    print("\n📤 STEP 5: Sending to Telegram...")
    success = telegram.send_telegram_message(final_message)
    
    if success:
        print("✅ Results sent to Telegram successfully!")
    else:
        print("❌ Failed to send to Telegram")
    
    # Save results
    results_df.to_csv('filtered_results.csv', index=False)
    results_df.head(20).to_csv('top_20_picks.csv', index=False)
    
    # Save accumulator details
    import json
    accumulator_data = {}
    for key, matches_list in accumulators.items():
        accumulator_data[key] = [
            {
                'match': m.get('Match'),
                'play': m.get('Play'),
                'odds': accumulator_builder.calculate_match_odds(m)
            }
            for m in matches_list
        ]
    
    with open('accumulators.json', 'w') as f:
        json.dump(accumulator_data, f, indent=2)
    
    print("\n📁 Files saved:")
    print("   - filtered_results.csv")
    print("   - top_20_picks.csv")
    print("   - accumulators.json")
    
    print("\n" + "="*60)
    print("✅ PRODUCTION BOT EXECUTION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
    
    # Step 5: Send to Telegram
    print("\n📤 STEP 3: Sending to Telegram...")
    success = telegram.process_and_send(
        results_df, 
        blueprint_text, 
        total_qualified, 
        send=True  # Actually send to Telegram
    )
    
    if success:
        print("✅ Results sent to Telegram successfully!")
    else:
        print("❌ Failed to send to Telegram")
    
    print("\n" + "="*60)
    print("✅ PRODUCTION BOT EXECUTION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
