#!/usr/bin/env python3
"""
Production Runner for Soccer Blueprints Filter Engine
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Import required modules
from telegram_integration import TelegramIntegrator

# Try to import filter engine components
try:
    from blueprint_scanner import BlueprintScanner
    from filter_engine import FilterEngine
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("   Make sure blueprint_scanner.py and filter_engine.py exist")
    sys.exit(1)


def load_environment_config():
    """Load configuration from environment variables"""
    config = {
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
        'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID'),
        'DEBUG_MODE': os.getenv('DEBUG_MODE', 'False').lower() == 'true',
        'SEND_TO_TELEGRAM': os.getenv('SEND_TO_TELEGRAM', 'True').lower() == 'true'
    }
    
    # Validate required config
    if config['SEND_TO_TELEGRAM']:
        if not config['TELEGRAM_BOT_TOKEN'] or not config['TELEGRAM_CHAT_ID']:
            print("⚠️ Warning: Telegram credentials missing. Messages will not be sent.")
            config['SEND_TO_TELEGRAM'] = False
    
    return config


def load_match_data(filepath: str = "match_data.csv") -> pd.DataFrame:
    """Load match data from CSV file"""
    try:
        if not os.path.exists(filepath):
            print(f"❌ Match data file not found: {filepath}")
            return None
        
        df = pd.read_csv(filepath)
        print(f"✅ Loaded {len(df)} matches from {filepath}")
        return df
    
    except Exception as e:
        print(f"❌ Error loading match data: {e}")
        return None


def run_production_pipeline(match_data: pd.DataFrame, config: dict):
    """Run the complete production pipeline"""
    print("\n" + "="*60)
    print("🏆 JAY SOCCER BLUEPRINTS - PRODUCTION PIPELINE")
    print("="*60)
    print(f"📅 Run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 Debug mode: {config['DEBUG_MODE']}")
    print(f"📤 Send to Telegram: {config['SEND_TO_TELEGRAM']}")
    
    # Stage 1: Blueprint Scanner
    print("\n" + "─"*40)
    print("📊 STAGE 1: BLUEPRINT SCANNER")
    print("─"*40)
    
    scanner = BlueprintScanner()
    blueprint_results = scanner.scan_matches(match_data)
    
    if blueprint_results.empty:
        print("❌ No matches passed the blueprint scanner")
        return False
    
    total_qualified = len(blueprint_results)
    print(f"✅ {total_qualified} matches passed blueprint scan")
    
    # Stage 2: Filter Engine
    print("\n" + "─"*40)
    print("⚙️ STAGE 2: FILTER ENGINE")
    print("─"*40)
    
    filter_engine = FilterEngine()
    final_results = filter_engine.apply_filters(blueprint_results)
    
    if final_results.empty:
        print("❌ No matches passed the filter engine")
        return False
    
    print(f"✅ {len(final_results)} matches passed all filters")
    
    # Display summary statistics
    print("\n" + "─"*40)
    print("📈 RESULTS SUMMARY")
    print("─"*40)
    
    high_conf = len(final_results[final_results['Confidence'] >= 65])
    medium_conf = len(final_results[(final_results['Confidence'] >= 50) & (final_results['Confidence'] < 65)])
    
    print(f"🔥 High confidence (65%+): {high_conf} matches")
    print(f"⚠️ Medium confidence (50-64%): {medium_conf} matches")
    print(f"📊 Average confidence: {final_results['Confidence'].mean():.1f}%")
    
    # Display top 5 picks
    print("\n" + "─"*40)
    print("🎯 TOP 5 PICKS")
    print("─"*40)
    
    top_picks = final_results.nlargest(5, 'Confidence')
    for idx, row in top_picks.iterrows():
        print(f"\n{idx+1}. {row['Match']}")
        print(f"   League: {row['League']}")
        print(f"   Play: {row['Play']}")
        print(f"   Confidence: {row['Confidence']:.0f}%")
    
    # Stage 3: Telegram Integration
    if config['SEND_TO_TELEGRAM']:
        print("\n" + "─"*40)
        print("📱 STAGE 3: TELEGRAM INTEGRATION")
        print("─"*40)
        
        telegram = TelegramIntegrator(
            bot_token=config['TELEGRAM_BOT_TOKEN'],
            chat_id=config['TELEGRAM_CHAT_ID']
        )
        
        # Get original text for context (if available)
        original_text = "Soccer Blueprints Filter Results"
        
        # Send results to Telegram
        success = telegram.process_and_send(
            results_df=final_results,
            original_text=original_text,
            total_qualified=total_qualified,
            send=True
        )
        
        if success:
            print("✅ Results sent to Telegram successfully")
        else:
            print("❌ Failed to send results to Telegram")
    
    # Save results to CSV
    output_file = f"filtered_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    final_results.to_csv(output_file, index=False)
    print(f"\n💾 Results saved to: {output_file}")
    
    print("\n" + "="*60)
    print("✅ PRODUCTION PIPELINE COMPLETED SUCCESSFULLY")
    print("="*60)
    
    return True


def main():
    """Main execution function"""
    print("🚀 Starting Soccer Blueprints Production Pipeline...")
    
    # Load configuration
    config = load_environment_config()
    
    # Load match data
    match_data = load_match_data("match_data.csv")
    
    if match_data is None:
        print("❌ Cannot proceed without match data")
        sys.exit(1)
    
    # Run production pipeline
    success = run_production_pipeline(match_data, config)
    
    if success:
        print("\n✨ Pipeline completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Pipeline failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
