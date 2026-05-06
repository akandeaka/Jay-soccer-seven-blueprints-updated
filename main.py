"""
Main Orchestrator - Runs the complete system
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
    
    def run(self, input_text: str = None):
        """
        Run the complete system pipeline
        
        Args:
            input_text: Raw copied text from Soccer24
                       If None, reads from input_matches.txt
        """
        print("\n" + "="*60)
        print("⚽ SOCCER BLUEPRINT SYSTEM WITH AI ANALYSIS")
        print("="*60)
        print(f"📅 Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # STEP 1: Parse input data
        print("\n" + "─"*40)
        print("📥 STEP 1: PARSING INPUT DATA")
        print("─"*40)
        
        if input_text is None:
            if os.path.exists(Config.INPUT_FILE):
                with open(Config.INPUT_FILE, 'r') as f:
                    input_text = f.read()
                print(f"✅ Loaded input from {Config.INPUT_FILE}")
            else:
                print(f"❌ No input file found. Please provide Soccer24 data.")
                print(f"   Create {Config.INPUT_FILE} with copied data")
                return False
        
        matches = self.parser.parse_match_text(input_text)
        df = self.parser.create_dataframe(matches)
        print(f"✅ Parsed {len(matches)} matches")
        
        if df.empty:
            print("❌ No matches parsed")
            return False
        
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
        
        ai_analyzed = self.ai_analyzer.analyze_batch(bp_matches)
        print(f"✅ {len(ai_analyzed)} matches passed AI validation (≥60% confidence)")
        
        if len(ai_analyzed) == 0:
            print("❌ No matches passed AI analysis")
            return False
        
        # Display top AI picks
        print("\n🎯 TOP AI PICKS:")
        for i, match in enumerate(ai_analyzed[:5], 1):
            print(f"   {i}. {match['match'][:40]} - {match['play']} ({match['ai_confidence']:.0f}%)")
        
        # STEP 4: Build Accumulators
        print("\n" + "─"*40)
        print("🎰 STEP 4: BUILDING ACCUMULATORS")
        print("─"*40)
        
        accumulators = self.accumulator_builder.build_accumulators(ai_analyzed)
        
        for acc_name, acc_data in accumulators.items():
            if 'error' not in acc_data:
                print(f"   {acc_name}: {len(acc_data['matches'])} matches @ {acc_data['total_odds']} odds")
        
        # STEP 5: Send to Telegram
        print("\n" + "─"*40)
        print("📱 STEP 5: SENDING TO TELEGRAM")
        print("─"*40)
        
        success = self.telegram.send_predictions(ai_analyzed, accumulators)
        
        if success:
            print("✅ Predictions sent to Telegram")
        else:
            print("⚠️ Failed to send to Telegram (continuing)")
        
        # STEP 6: Validate Results (if actual results available)
        print("\n" + "─"*40)
        print("✅ STEP 6: VALIDATING RESULTS")
        print("─"*40)
        
        actual_results = self.validator.load_actual_results("actual_results.csv")
        
        if not actual_results.empty:
            validated = self.validator.validate_batch(ai_analyzed, actual_results)
            report = self.validator.generate_report(validated)
            print(f"✅ Validation complete. Accuracy: {sum(1 for v in validated if v['is_correct'])/len(validated)*100:.1f}%")
            
            # Send report to Telegram
            self.telegram.send_message(f"📊 *Daily Performance Report*\n\n{report[:500]}...")
        else:
            print("⚠️ No actual results available for validation")
            print("   Create actual_results.csv with columns: match,home_score,away_score,result")
        
        # STEP 7: Save results
        print("\n" + "─"*40)
        print("💾 STEP 7: SAVING RESULTS")
        print("─"*40)
        
        # Save predictions
        with open("predictions.json", "w") as f:
            json.dump(ai_analyzed, f, indent=2)
        print("✅ Predictions saved to predictions.json")
        
        # Summary
        print("\n" + "="*60)
        print("✅ SYSTEM EXECUTION COMPLETE")
        print("="*60)
        print(f"📊 Summary:")
        print(f"   Total input matches: {len(matches)}")
        print(f"   Blueprint passed: {len(bp_matches)}")
        print(f"   AI validated: {len(ai_analyzed)}")
        print(f"   Accumulators built: {len([a for a in accumulators.values() if 'error' not in a])}")
        print(f"\n📁 Output files:")
        print(f"   - predictions.json")
        print(f"   - performance_report.md")
        print(f"   - input_matches.txt (source)")
        print("\n✨ Done!")
        
        return True


def main():
    """Main entry point"""
    
    # Check if input provided via command line
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        with open(input_file, 'r') as f:
            input_text = f.read()
    else:
        input_text = None
    
    system = SoccerBlueprintSystem()
    success = system.run(input_text)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
