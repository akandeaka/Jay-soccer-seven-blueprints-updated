"""
Main Orchestrator - Runs the complete blueprint system
"""
# Add this at the beginning of the run() method
import os

# Delete old cache at the start of every run
if os.path.exists("predictions.json"):
    os.remove("predictions.json")
    print("🗑️ Deleted old predictions.json cache")
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


class SoccerBlueprintSystem:
    """Main system orchestrator"""
    
    def __init__(self):
        self.parser = Soccer24Parser()
        self.blueprint_engine = BlueprintEngine()
        self.ai_analyzer = AIAnalyzer()
        self.accumulator_builder = AccumulatorBuilder()
        self.telegram = TelegramSender(
            Config.TELEGRAM_BOT_TOKEN,
            Config.TELEGRAM_CHAT_ID
        )
    
    def run(self):
        """Run the complete system pipeline"""
        
        print("\n" + "="*60)
        print("⚽ JAY SOCCER BLUEPRINTS - 8 BLUEPRINT SYSTEM")
        print("="*60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check for input file
        if not os.path.exists(Config.INPUT_FILE):
            print(f"\n❌ {Config.INPUT_FILE} not found!")
            return False
        
        # Read and parse input
        with open(Config.INPUT_FILE, 'r') as f:
            input_text = f.read()
        
        matches = self.parser.parse_match_text(input_text)
        df = self.parser.create_dataframe(matches)
        
        if df.empty:
            print("\n❌ No valid matches found in input_matches.txt")
            return False
        
        print(f"\n✅ Loaded {len(df)} matches")
        
        # Apply blueprints
        bp_matches = self.blueprint_engine.filter_matches(df)
        
        if not bp_matches:
            print("❌ No matches passed any blueprint")
            return False
        
        print(f"\n✅ {len(bp_matches)} matches passed blueprints:")
        stats = self.blueprint_engine.get_stats()
        for bp, count in stats.items():
            if count > 0:
                print(f"   {bp}: {count} matches")
        
        # AI Analysis
        ai_analyzed = self.ai_analyzer.analyze_batch(bp_matches)
        
        # Build accumulators
        accumulators = self.accumulator_builder.build_accumulators(ai_analyzed)
        
        # Send to Telegram
        success = self.telegram.send_predictions(ai_analyzed, accumulators)
        
        # Save results
        with open("predictions.json", "w") as f:
            json.dump(ai_analyzed, f, indent=2)
        
        print("\n✅ Done!")
        return success


def main():
    system = SoccerBlueprintSystem()
    success = system.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
