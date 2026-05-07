"""
Main Orchestrator - Runs the complete system with API data
"""

import os
import sys
import json
import pandas as pd
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
    """Main system orchestrator - REAL DATA ONLY"""
    
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
        """Run the complete system pipeline - REAL MATCHES ONLY"""
        
        print("\n" + "="*60)
        print("⚽ SOCCER BLUEPRINT SYSTEM WITH AI ANALYSIS")
        print("🤖 REAL MATCHES ONLY - NO DEMO DATA")
        print("="*60)
        print(f"📅 Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # STEP 1: Get match data from API only
        print("\n" + "─"*40)
        print("📥 STEP 1: FETCHING REAL MATCH DATA")
        print("─"*40)
        
        df = self.api_manager.get_todays_matches()
        
        if df.empty:
            print("\n❌ NO REAL MATCHES AVAILABLE")
            print("   System will not generate predictions.")
            print("   Check your API key or try again later.")
            return False
        
        print(f"\n✅ Loaded {len(df)} REAL matches for analysis")
        
        # STEP 2: Apply Blueprint Filter
        print("\n" + "─"*40)
        print("🔵 STEP 2: BLUEPRINT FILTER (8 BLUEPRINTS)")
        print("─"*40)
        
        bp_matches = self.blueprint_engine.filter_matches(df)
        print(f"✅ {len(bp_matches)} matches passed blueprint criteria")
        
        if len(bp_matches) == 0:
            print("❌ No matches passed blueprint filter")
            return False
        
        stats = self.blueprint_engine.get_stats()
        for bp, count in stats.items():
            if count > 0:
                print(f"   {bp}: {count} matches")
        
        # STEP 3: AI Analysis
        print("\n" + "─"*40)
        print("🤖 STEP 3: AI ANALYSIS")
        print("─"*40)
        
        ai_analyzed = self.ai_analyzer.analyze_batch(bp_matches)
        print(f"✅ {len(ai_analyzed)} matches passed AI validation")
        
        if len(ai_analyzed) == 0:
            print("❌ No matches passed AI analysis")
            return False
        
        print("\n🎯 TOP AI PICKS:")
        for i, match in enumerate(ai_analyzed[:5], 1):
            match_name = match.get('match', 'Unknown')[:50]
            play = match.get('play', 'Unknown')
            confidence = match.get('ai_confidence', 0)
            print(f"   {i}. {match_name}")
            print(f"      🎯 {play} ({confidence:.0f}% confidence)")
        
        # STEP 4: Build Accumulators
        print("\n" + "─"*40)
        print("🎰 STEP 4: BUILDING ACCUMULATORS")
        print("─"*40)
        
        accumulators = self.accumulator_builder.build_accumulators(ai_analyzed)
        
        for acc_name, acc_data in accumulators.items():
            if acc_data and 'error' not in acc_data:
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
                print("⚠️ Failed to send to Telegram")
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
        
        print("\n" + "="*60)
        print("✅ SYSTEM EXECUTION COMPLETE")
        print("="*60)
        print(f"📊 Summary:")
        print(f"   Total REAL matches: {len(df)}")
        print(f"   Blueprint passed: {len(bp_matches)}")
        print(f"   AI validated: {len(ai_analyzed)}")
        print("\n✨ Done!")
        
        return True


def main():
    system = SoccerBlueprintSystem()
    success = system.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
