#!/usr/bin/env python3
"""
Production Runner for Soccer Blueprints Filter Engine
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from filter_engine directory
from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig


def load_match_data(filepath: str = "matches_today.csv") -> pd.DataFrame:
    """Load match data from CSV file"""
    try:
        # Try multiple possible locations
        possible_paths = [
            filepath,
            f"input/{filepath}",
            f".github/workflows/{filepath}",
            filepath.replace("matches_today.csv", "input/matches_today.csv")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Loading data from: {path}")
                df = pd.read_csv(path)
                print(f"   Loaded {len(df)} matches")
                return df
        
        print(f"❌ Match data file not found in any location")
        print(f"   Searched in: {possible_paths}")
        return None
    
    except Exception as e:
        print(f"❌ Error loading match data: {e}")
        return None


def parse_matches_from_text(text: str) -> pd.DataFrame:
    """Parse matches from blueprint text format"""
    engine = BlueprintFilterEngine()
    matches = engine.parse_blueprint_text(text)
    
    if matches:
        df = engine.process_matches(matches)
        print(f"✅ Parsed {len(df)} matches from blueprint text")
        return df
    
    return pd.DataFrame()


def run_production_pipeline(match_data: pd.DataFrame = None, blueprint_text: str = None):
    """Run the complete production pipeline"""
    print("\n" + "="*60)
    print("🏆 JAY SOCCER BLUEPRINTS - PRODUCTION PIPELINE")
    print("="*60)
    print(f"📅 Run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize filter engine
    engine = BlueprintFilterEngine()
    results_df = pd.DataFrame()
    
    # Process matches from either CSV or text
    if match_data is not None and not match_data.empty:
        print("\n📊 Processing matches from CSV...")
        # Convert CSV data to blueprint format
        matches = []
        for _, row in match_data.iterrows():
            # Classify each match using the blueprint rules
            classification = engine.classify_blueprint(
                home_odds=float(row.get('Home Odds', 0)),
                draw_odds=float(row.get('Draw Odds', 0)),
                away_odds=float(row.get('Away Odds', 0))
            )
            
            if classification:
                matches.append({
                    'blueprint': classification['bp'],
                    'color': classification['color'],
                    'match': f"{row.get('Home', 'Home')} vs {row.get('Away', 'Away')}",
                    'league': row.get('League', 'Unknown'),
                    'home_odds': float(row.get('Home Odds', 0)),
                    'draw_odds': float(row.get('Draw Odds', 0)),
                    'away_odds': float(row.get('Away Odds', 0)),
                    'play': classification['play'],
                    'risk': classification['risk']
                })
        
        if matches:
            results_df = engine.process_matches(matches)
            print(f"✅ {len(results_df)} matches classified")
    
    elif blueprint_text:
        print("\n📊 Processing matches from blueprint text...")
        results_df = parse_matches_from_text(blueprint_text)
    
    else:
        print("❌ No data source provided (either match_data or blueprint_text)")
        return False
    
    if results_df.empty:
        print("❌ No matches passed the blueprint filter")
        return False
    
    # Display results summary
    print("\n" + "─"*40)
    print("📈 RESULTS SUMMARY")
    print("─"*40)
    
    # Count by tier
    tier_counts = results_df['Tier'].value_counts()
    for tier, count in tier_counts.items():
        print(f"{tier}: {count} matches")
    
    print(f"\n📊 Average confidence: {results_df['Confidence'].mean():.1f}%")
    
    # Display top 10 picks
    print("\n" + "─"*40)
    print("🎯 TOP 10 PICKS")
    print("─"*40)
    
    for idx, row in results_df.head(10).iterrows():
        print(f"\n{idx+1}. {row['Blueprint']}: {row['Match']}")
        print(f"   League: {row['League']}")
        print(f"   Play: {row['Play']}")
        print(f"   Confidence: {row['Confidence']:.0f}% | Risk: {row['Risk']}")
    
    # Send to Telegram
    config = FilterConfig()
    
    if config.ENABLE_TELEGRAM:
        print("\n" + "─"*40)
        print("📱 SENDING TO TELEGRAM")
        print("─"*40)
        
        telegram = TelegramIntegrator(
            bot_token=config.TELEGRAM_BOT_TOKEN,
            chat_id=config.TELEGRAM_CHAT_ID
        )
        
        # Build message content
        message = build_telegram_message(results_df)
        success = telegram.send_telegram_message(message)
        
        if success:
            print("✅ Results sent to Telegram successfully")
        else:
            print("❌ Failed to send results to Telegram")
    
    # Save results
    output_file = f"filtered_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n💾 Results saved to: {output_file}")
    
    print("\n" + "="*60)
    print("✅ PRODUCTION PIPELINE COMPLETED SUCCESSFULLY")
    print("="*60)
    
    return True


def build_telegram_message(results_df: pd.DataFrame) -> str:
    """Build formatted Telegram message from results"""
    message = f"""
⚽ JAY SOCCER BLUEPRINTS - FILTER RESULTS
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 FILTER ENGINE RESULTS
   🔥 GOLD (85%+): {len(results_df[results_df['Tier'] == '🔥 GOLD'])} matches
   ✅ SILVER (70-84%): {len(results_df[results_df['Tier'] == '✅ SILVER'])} matches
   ⚠️ BRONZE (<70%): {len(results_df[results_df['Tier'] == '⚠️ BRONZE'])} matches

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 TOP 10 PICKS BY CONFIDENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for idx, row in results_df.head(10).iterrows():
        message += f"""
{idx+1}. {row['Blueprint']}: {row['Match']}
   🏆 {row['League']}
   🎯 {row['Play']}
   📈 Confidence: {row['Confidence']:.0f}% | Risk: {row['Risk']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    message += """
⚠️ Always bet responsibly!
📊 Data provided for informational purposes only.
"""
    
    return message


def main():
    """Main execution function"""
    print("🚀 Starting Soccer Blueprints Production Pipeline...")
    
    # Try to load match data from CSV
    match_data = load_match_data("matches_today.csv")
    
    # If no CSV found, check for blueprint text file
    blueprint_text = None
    if match_data is None:
        text_paths = ["blueprint_data.txt", "input/blueprint_data.txt"]
        for path in text_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    blueprint_text = f.read()
                print(f"✅ Loaded blueprint text from: {path}")
                break
    
    # Run pipeline
    success = run_production_pipeline(
        match_data=match_data,
        blueprint_text=blueprint_text
    )
    
    if success:
        print("\n✨ Pipeline completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Pipeline failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
