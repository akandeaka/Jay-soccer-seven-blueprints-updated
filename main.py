"""
Main Orchestrator - Runs the complete system with API data
"""

import os
import sys
import json
from datetime import datetime

from config import Config
from data_parser import Soccer24Parser
from blueprint_engine import BlueprintEngine
from ai_analyzer import AIAnalyzer
from accumulator_builder import AccumulatorBuilder
from telegram_sender import TelegramSender
from results_validator import ResultsValidator
from api_fetcher import APIDataManager


class SoccerBlueprintSystem:
    """Main system orchestrator"""
    
    def __init__(self):
        self.config = Config()
        self.parser = Soccer24Parser()
        self.blueprint_engine = BlueprintEngine()
        self.ai_analyzer = AIAnalyzer()
        self.accumulator_builder = AccumulatorBuilder()
        self.telegram = TelegramSender(
            self.config.TELEGRAM_BOT_TOKEN,
            self.config.TELEGRAM_CHAT_ID
        )
        self.validator = ResultsValidator()
        self.api_manager = APIDataManager()
    
    def run(self, input_text: str = None):
        """
        Run the complete system pipeline
        Automatically uses API if available, otherwise falls back to manual input
        """
        print("\n" + "="*60)
        print("⚽ SOCCER BLUEPRINT SYSTEM WITH AI ANALYSIS")
        print("="*60)
        print(f"📅 Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # STEP 1: Get match data (API first, then manual fallback)
        print("\n" + "─"*40)
        print("📥 STEP 1: GETTING MATCH DATA")
        print("─"*40)
        
        df = pd.DataFrame()
        
        # Try API first
        if Config.USE_API:
            print("🔄 Fetching data from API...")
            df = self.api_manager.get_todays_matches()
        
        # Fallback to manual input if API fails or no data
        if df.empty and input_text:
            print("🔄 Falling back to manual input...")
            matches = self.parser.parse_match_text(input_text)
            df = self.parser.create_dataframe(matches)
        elif df.empty and os.path.exists(Config.INPUT_FILE):
            print("🔄 Falling back to input_matches.txt...")
            with open(Config.INPUT_FILE, 'r') as f:
                input_text = f.read()
            matches = self.parser.parse_match_text(input_text)
            df = self.parser.create_dataframe(matches)
        
        if df.empty:
            print("❌ No data available. Please check API keys or provide input_matches.txt")
            print("\n💡 To fix:")
            print("   1. Add ODDS_API_KEY to GitHub Secrets")
            print("   2. OR create input_matches.txt manually")
            return False
        
        print(f"✅ Loaded {len(df)} matches for analysis")
        
        # STEP 2: Apply Blueprint Filter
        print("\n" + "─"*40)
        print("🔵 STEP 2: BLUEPRINT FILTER (8 BLUEPRINTS)")
        print("─"*40)
        
        bp_matches = self.blueprint_engine.filter_matches(df)
        print(f"✅ {len(bp_matches)} matches passed blueprint criteria")
        
        # Print blueprint statistics
        stats = self.blueprint_engine.get_stats()
        for bp, count in stats.items():
            if count > 0:
                print(f"   {bp}: {count} matches")
        
        if len(bp_matches) == 0:
            print("❌ No matches passed blueprint filter")
            return False
        
        # STEP 3: AI Analysis
        print("\n" + "─"*40)
        print("🤖 STEP 3: AI ANALYSIS")
        print("─"*40)
        
        # For BP7 matches, fetch BTTS records from stats API
        for match in bp_matches:
            if match.get('blueprint') == 'BP7':
                home_team = match.get('match', '').split(' vs ')[0]
                league = match.get('league', '')
                btts_record = self.api_manager.stats_fetcher.get_btts_record_for_match(
                    home_team, '', league
                )
                if btts_record:
                    match['btts_record'] = btts_record
        
        ai_analyzed = self.ai_analyzer.analyze_batch(bp_matches)
        print(f"✅ {len(ai_analyzed)} matches passed AI validation (≥60% confidence)")
        
        if len(ai_analyzed) == 0:
            print("❌ No matches passed AI analysis")
            return False
        
        # Display top AI picks
        print("\n🎯 TOP AI PICKS:")
        for i, match in enumerate(ai_analyzed[:5], 1):
            match_name = match.get('match', 'Unknown')[:40]
            play = match.get('play', 'Unknown')
            confidence = match.get('ai_confidence', 0)
            print(f"   {i}. {match_name} - {play} ({confidence:.0f}%)")
        
        # STEP 4: Build Accumulators
        print("\n" + "─"*40)
        print("🎰 STEP 4: BUILDING ACCUMULATORS")
        print("─"*40)
        
        accumulators = self.accumulator_builder.build_accumulators(ai_analyzed)
        
        for acc_name, acc_data in accumulators.items():
            if 'error' not in acc_data and acc_data:
                matches_count = len(acc_data.get('matches', []))
                odds = acc_data.get('total_odds', 0)
                print(f"   {acc_name}: {matches_count} matches @ {odds} odds")
        
        # STEP 5: Send to Telegram
        print("\n" + "─"*40)
        print("📱 STEP 5: SENDING TO TELEGRAM")
        print("─"*40)
        
        try:
            success = self.telegram.send_predictions(ai_analyzed, accumulators)
            if success:
                print("✅ Predictions sent to Telegram")
            else:
                print("⚠️ Failed to send to Telegram (continuing)")
        except Exception as e:
            print(f"⚠️ Telegram error: {e}")
        
        # STEP 6: Save results
        print("\n" + "─"*40)
        print("💾 STEP 6: SAVING RESULTS")
        print("─"*40)
        
        try:
            with open("predictions.json", "w") as f:
                json.dump(ai_analyzed, f, indent=2)
            print("✅ Predictions saved to predictions.json")
        except Exception as e:
            print(f"❌ Error saving predictions: {e}")
        
        # Summary
        print("\n" + "="*60)
        print("✅ SYSTEM EXECUTION COMPLETE")
        print("="*60)
        print(f"📊 Summary:")
        print(f"   Total input matches: {len(df)}")
        print(f"   Blueprint passed: {len(bp_matches)}")
        print(f"   AI validated: {len(ai_analyzed)}")
        
        valid_accs = [a for a in accumulators.values() if a and 'error' not in a]
        print(f"   Accumulators built: {len(valid_accs)}")
        print(f"\n📁 Output files:")
        print(f"   - predictions.json")
        print("\n✨ Done!")
        
        return True


def main():
    """Main entry point"""
    
    # Check if input provided via command line (manual mode)
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        try:
            with open(input_file, 'r') as f:
                input_text = f.read()
        except Exception as e:
            print(f"❌ Error reading {input_file}: {e}")
            sys.exit(1)
    else:
        input_text = None
    
    system = SoccerBlueprintSystem()
    success = system.run(input_text)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
