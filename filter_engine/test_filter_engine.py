#!/usr/bin/env python3
"""
Test script for Filter Engine - Run this locally or in GitHub Actions
This does NOT send any messages to Telegram
"""

import sys
import os
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_blueprint_data():
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

🟡 1. BP7: THE HIGH-SCORING SIGNALS (B)
   🏟️ Den Bosch vs Almere City
   🏆 Eredivisie - Relegation - Play Offs
   📊 Odds: 2.55 | 3.6 | 2.45
   🎯 Play: HT 0.5 Goals / Over 2.5 Goals
   ⚠️ Risk: Moderate-High

🔴 2. BP6: THE STRONG DRAW
   🏟️ Atl. Madrid vs Arsenal
   🏆 Champions League - Play Offs
   📊 Odds: 2.9 | 3.25 | 2.5
   🎯 Play: Full Time Draw (X) Potential
   ⚠️ Risk: High (Strategic)

🟢 3. BP1: THE ELITE HOME BANKER
   🏟️ Entebbe UPPC vs Calvary
   🏆 Premier League
   📊 Odds: 1.28 | 4.2 | 12.2
   🎯 Play: Straight Home Win
   ⚠️ Risk: Ultra-Low
"""

def test_parsing():
    """Test the blueprint parsing functionality"""
    print("\n" + "="*60)
    print("TEST 1: Blueprint Parsing")
    print("="*60)
    
    from filter_engine import BlueprintFilterEngine
    
    engine = BlueprintFilterEngine()
    test_data = create_test_blueprint_data()
    
    matches = engine.parse_blueprint_text(test_data)
    
    print(f"✅ Parsed {len(matches)} matches")
    
    for i, match in enumerate(matches[:3], 1):
        print(f"   {i}. {match['blueprint']}: {match['match']} ({match['league']})")
    
    assert len(matches) > 0, "Failed to parse any matches"
    print("✅ Parsing test PASSED")
    return matches


def test_filtering(matches):
    """Test the filtering functionality"""
    print("\n" + "="*60)
    print("TEST 2: Filter Engine")
    print("="*60)
    
    from filter_engine import BlueprintFilterEngine
    
    engine = BlueprintFilterEngine()
    results_df = engine.process_matches(matches)
    
    print(f"✅ Processed {len(results_df)} results")
    print(f"\nConfidence Distribution:")
    
    gold = len(results_df[results_df['Confidence'] >= 80])
    silver = len(results_df[(results_df['Confidence'] >= 65) & (results_df['Confidence'] < 80)])
    bronze = len(results_df[(results_df['Confidence'] >= 50) & (results_df['Confidence'] < 65)])
    reject = len(results_df[results_df['Confidence'] < 50])
    
    print(f"   🔥 GOLD (80%+): {gold}")
    print(f"   ✅ SILVER (65-79%): {silver}")
    print(f"   ⚠️ BRONZE (50-64%): {bronze}")
    print(f"   ❌ REJECT (<50%): {reject}")
    
    # Show top 5
    print("\n📊 TOP 5 MATCHES:")
    for idx, row in results_df.head(5).iterrows():
        print(f"   {row['Tier']} | {row['Confidence']:.0f}% | {row['Blueprint']} | {row['Match'][:40]}...")
        print(f"        Play: {row['Play']}")
    
    assert len(results_df) > 0, "Filtering produced no results"
    print("\n✅ Filtering test PASSED")
    return results_df


def test_telegram_message_preview(results_df):
    """Test Telegram message generation (without sending)"""
    print("\n" + "="*60)
    print("TEST 3: Telegram Message Preview (No Send)")
    print("="*60)
    
    from filter_engine import TelegramIntegrator
    
    telegram = TelegramIntegrator()
    test_blueprint = create_test_blueprint_data()
    
    message = telegram.build_telegram_message(results_df, test_blueprint, 205)
    
    # Preview first 1000 characters
    print("\n📱 MESSAGE PREVIEW (first 1000 chars):")
    print("-"*40)
    print(message[:1000])
    print("-"*40)
    print(f"\n✅ Message length: {len(message)} characters")
    
    assert len(message) > 100, "Message too short"
    print("✅ Message generation test PASSED")
    return message


def test_config():
    """Test configuration loading"""
    print("\n" + "="*60)
    print("TEST 4: Configuration Validation")
    print("="*60)
    
    from filter_engine import FilterConfig
    
    print(f"✅ High confidence threshold: {FilterConfig.HIGH_CONFIDENCE_THRESHOLD}%")
    print(f"✅ Medium confidence threshold: {FilterConfig.MEDIUM_CONFIDENCE_THRESHOLD}%")
    print(f"✅ Top matches to show: {FilterConfig.TOP_MATCHES_TO_SHOW}")
    
    # Check if Telegram credentials are placeholders
    token = FilterConfig.TELEGRAM_BOT_TOKEN
    chat_id = FilterConfig.TELEGRAM_CHAT_ID
    
    if token and token != "YOUR_BOT_TOKEN_HERE":
        print(f"✅ Telegram Bot Token: Configured (length: {len(token)})")
    else:
        print("⚠️ Telegram Bot Token: Using placeholder (will not send)")
    
    if chat_id and chat_id != "YOUR_CHAT_ID_HERE":
        print(f"✅ Telegram Chat ID: Configured (length: {len(chat_id)})")
    else:
        print("⚠️ Telegram Chat ID: Using placeholder (will not send)")
    
    print("\n✅ Configuration test PASSED")


def test_export(results_df):
    """Test CSV export functionality"""
    print("\n" + "="*60)
    print("TEST 5: CSV Export")
    print("="*60)
    
    # Export to CSV
    results_df.to_csv('test_filtered_results.csv', index=False)
    results_df.head(20).to_csv('test_top_20.csv', index=False)
    
    # Check if files were created
    import os
    assert os.path.exists('test_filtered_results.csv'), "CSV export failed"
    assert os.path.exists('test_top_20.csv'), "Top 20 export failed"
    
    file_size = os.path.getsize('test_filtered_results.csv')
    print(f"✅ Exported to test_filtered_results.csv ({file_size} bytes)")
    print(f"✅ Exported to test_top_20.csv")
    
    print("\n✅ Export test PASSED")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 FILTER ENGINE TEST SUITE")
    print("="*60)
    print("\nRunning tests... (No Telegram messages will be sent)")
    
    try:
        # Run tests
        matches = test_parsing()
        results_df = test_filtering(matches)
        test_telegram_message_preview(results_df)
        test_config()
        test_export(results_df)
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\n✅ Filter engine is working correctly")
        print("✅ Ready to integrate with your blueprint system")
        print("\nNext steps:")
        print("1. Set USE_MOCK_DATA = False in config.py")
        print("2. Configure IntegrationConfig in config.py")
        print("3. Run: python run_filtered_bot.py")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
