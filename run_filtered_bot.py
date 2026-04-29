#!/usr/bin/env python3
"""
Main entry point for Filtered Blueprint Bot - NOW WITH TELEGRAM SENDING
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig


def create_sample_blueprint_data():
    """Create sample blueprint data for testing"""
    return """
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

🟢 1. BP1: THE ELITE HOME BANKER
   🏟️ Entebbe UPPC vs Calvary
   🏆 Premier League
   📊 Odds: 1.28 | 4.2 | 12.2
   🎯 Play: Straight Home Win
   ⚠️ Risk: Ultra-Low

🟢 2. BP1: THE ELITE HOME BANKER
   🏟️ Monastir vs AS Gabes
   🏆 Ligue Professionnelle 1
   📊 Odds: 1.27 | 4.35 | 11.9
   🎯 Play: Straight Home Win
   ⚠️ Risk: Ultra-Low

🟢 3. BP1: THE ELITE HOME BANKER
   🏟️ Neftchi Fargona vs Kokand 1912
   🏆 Super League
   📊 Odds: 1.24 | 5.48 | 12.1
   🎯 Play: Straight Home Win
   ⚠️ Risk: Ultra-Low

🟡 4. BP7: THE HIGH-SCORING SIGNALS (A)
   🏟️ Tromso vs Brann
   🏆 Eliteserien
   📊 Odds: 1.95 | 3.5 | 3.8
   🎯 Play: GG / Over 2.5 Goals
   ⚠️ Risk: Moderate-High

🟡 5. BP4: THE GOAL ENGINE
   🏟️ FC Astana vs Tobol
   🏆 Kazakhstan Cup
   📊 Odds: 1.8 | 3.32 | 4.13
   🎯 Play: Over 1.5 Goals
   ⚠️ Risk: Moderate

🔴 6. BP6: THE STRONG DRAW
   🏟️ Atl. Madrid vs Arsenal
   🏆 Champions League - Play Offs
   📊 Odds: 2.9 | 3.25 | 2.5
   🎯 Play: Full Time Draw (X) Potential
   ⚠️ Risk: High (Strategic)
"""


def get_blueprint_name(bp: str) -> str:
    """Return full blueprint name"""
    names = {
        'BP1': 'THE ELITE HOME BANKER',
        'BP2': 'THE PRIMARY FAVORITE',
        'BP3': 'THE MODERATE FAVORITE SAFETY',
        'BP4': 'THE GOAL ENGINE',
        'BP5': 'THE DEFENSIVE TRAP',
        'BP6': 'THE STRONG DRAW',
        'BP7': 'THE HIGH-SCORING SIGNALS'
    }
    return names.get(bp, bp)


def main():
    """Main execution function"""
    print("="*60)
    print("FILTERED BLUEPRINT BOT")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Initialize components
    filter_engine = BlueprintFilterEngine()
    telegram = TelegramIntegrator(
        bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
        chat_id=FilterConfig.TELEGRAM_CHAT_ID
    )
    
    # Get blueprint data (replace this with your actual blueprint system)
    blueprint_text = create_sample_blueprint_data()
    total_qualified = 205
    
    print(f"\n📊 Received {total_qualified} qualifying matches from Stage 1")
    
    # Parse and process matches
    print("\n🔄 Parsing blueprint data...")
    matches = filter_engine.parse_blueprint_text(blueprint_text)
    print(f"✅ Parsed {len(matches)} matches")
    
    print("\n🔄 Applying filters and calculating confidence...")
    results_df = filter_engine.process_matches(matches)
    
    # Calculate statistics
    high_conf = len(results_df[results_df['Confidence'] >= FilterConfig.HIGH_CONFIDENCE_THRESHOLD])
    medium_conf = len(results_df[(results_df['Confidence'] >= FilterConfig.MEDIUM_CONFIDENCE_THRESHOLD) & 
                                  (results_df['Confidence'] < FilterConfig.HIGH_CONFIDENCE_THRESHOLD)])
    
    print(f"\n📊 RESULTS:")
    print(f"   🔥 High confidence ({FilterConfig.HIGH_CONFIDENCE_THRESHOLD}%+): {high_conf} matches")
    print(f"   ⚠️ Medium confidence: {medium_conf} matches")
    
    # Display top results
    print("\n" + "="*60)
    print("🏆 TOP PICKS")
    print("="*60)
    
    for idx, row in results_df.head(10).iterrows():
        print(f"\n{row['Tier']} {row['Blueprint']}: {get_blueprint_name(row['Blueprint'])}")
        print(f"   🏟️ {row['Match']}")
        print(f"   🏆 {row['League']}")
        print(f"   📊 Odds: {row['Home Odds']} | {row['Draw Odds']} | {row['Away Odds']}")
        print(f"   🎯 Play: {row['Play']}")
        print(f"   📈 Confidence: {row['Confidence']:.0f}%")
    
    # Send to Telegram - CHANGE THIS TO True TO ACTUALLY SEND
    print("\n" + "="*60)
    print("SENDING TO TELEGRAM...")
    print("="*60)
    
    # 🔴 CHANGE THIS LINE: set send=True to actually send to Telegram
    SEND_TO_TELEGRAM = True  # <-- CHANGE FROM False TO True
    
    success = telegram.process_and_send(
        results_df, 
        blueprint_text, 
        total_qualified, 
        send=SEND_TO_TELEGRAM  # Now set to True
    )
    
    if success:
        print("\n✅ Filtered results sent to Telegram successfully!")
    else:
        print("\n⚠️ Failed to send to Telegram. Check your bot token and chat ID.")
    
    # Save results to CSV
    results_df.to_csv('filtered_results_backup.csv', index=False)
    results_df.head(20).to_csv('top_20_picks.csv', index=False)
    print("\n📁 Results saved to filtered_results_backup.csv and top_20_picks.csv")
    
    print("\n" + "="*60)
    print("BOT EXECUTION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
