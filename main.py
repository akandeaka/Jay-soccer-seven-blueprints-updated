"""
Main Orchestrator - MANUAL MODE ONLY
Reads ONLY from input_matches.txt
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


class SoccerBlueprintSystem:
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
        print("\n" + "="*60)
        print("⚽ SOCCER BLUEPRINT SYSTEM")
        print("📋 READING FROM input_matches.txt ONLY")
        print("="*60)
        
        # Check input file
        if not os.path.exists(Config.INPUT_FILE):
            print(f"\n❌ {Config.INPUT_FILE} not found!")
            return False
        
        # Read and parse
        with open(Config.INPUT_FILE, 'r') as f:
            input_text = f.read()
        
        matches = self.parser.parse_match_text(input_text)
        df = self.parser.create_dataframe(matches)
        
        if df.empty:
            print("❌ No valid matches found in input_matches.txt")
            return False
        
        print(f"\n✅ Loaded {len(df)} matches from input_matches.txt")
        
        # Apply blueprints
        bp_matches = self.blueprint_engine.filter_matches(df)
        
        if not bp_matches:
            print("❌ No matches passed blueprint filter")
            return False
        
        # AI Analysis
        ai_analyzed = self.ai_analyzer.analyze_batch(bp_matches)
        
        # Build accumulators
        accumulators = self.accumulator_builder.build_accumulators(ai_analyzed)
        
        # Send to Telegram
        self.telegram.send_predictions(ai_analyzed, accumulators)
        
        print("\n✅ Done!")
        return True


def main():
    system = SoccerBlueprintSystem()
    success = system.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
