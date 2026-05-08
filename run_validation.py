"""
RUN VALIDATION - Automatically fetches results from Flashscore
No manual CSV creation needed!
"""

import os
import sys
import asyncio
import pandas as pd
from datetime import datetime
from results_validator import ResultsValidator
from auto_fetch_results import fetch_match_results

def send_telegram(message):
    """Send message to Telegram"""
    import requests
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=30)
        return r.json().get('ok', False)
    except:
        return False

def main():
    print("\n" + "="*60)
    print("⚽ AUTOMATIC MATCH VALIDATION")
    print("Fetching results from Flashscore...")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load predictions
    if not os.path.exists("predictions.json"):
        print("❌ No predictions.json found - run main.py first")
        return 1
    
    with open("predictions.json", 'r') as f:
        predictions = json.load(f)
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    # Try to auto-fetch from Flashscore
    print("\n📡 Connecting to Flashscore...")
    
    # Run async fetch
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    actual_results = loop.run_until_complete(fetch_match_results(predictions))
    loop.close()
    
    if actual_results.empty:
        print("\n⚠️ Could not fetch results from Flashscore")
        print("   Possible reasons:")
        print("   1. Matches haven't finished yet")
        print("   2. Flashscore website structure changed")
        print("   3. Network connectivity issues")
        print("\n💡 Fallback: You can still create actual_results.csv manually")
        send_telegram("⚠️ VALIDATION: Could not auto-fetch results from Flashscore. Please check matches manually.")
        return 0
    
    # Save results
    actual_results.to_csv("actual_results.csv", index=False)
    print(f"\n✅ Auto-fetched {len(actual_results)} results from Flashscore")
    
    # Validate using your existing validator
    validator = ResultsValidator()
    validated = validator.validate_predictions(predictions, actual_results)
    
    # Calculate accuracy
    total = len([v for v in validated if v['actual_result'] != 'NO_RESULT_FOUND'])
    correct = sum(1 for v in validated if v['is_correct'])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"\n📊 VALIDATION RESULTS:")
    print(f"   Total matches: {total}")
    print(f"   Correct: {correct}")
    print(f"   Wrong: {total - correct}")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    # Generate report
    report = validator.generate_performance_report(validated)
    validator.update_history(validated)
    
    # Send to Telegram
    summary = f"""⚽ PERFORMANCE REPORT
📅 {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 VALIDATION RESULTS
   Total Predictions: {total}
   Correct: {correct}
   Wrong: {total - correct}
   Accuracy: {accuracy:.1f}%

✅ Results automatically fetched from Flashscore
"""
    send_telegram(summary)
    
    print("\n✅ Validation complete! Report sent to Telegram")
    return 0

if __name__ == "__main__":
    sys.exit(main())
