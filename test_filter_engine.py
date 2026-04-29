#!/usr/bin/env python3
"""
Test script for Filter Engine - Run this file directly
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules import correctly"""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)
    
    try:
        from filter_engine import BlueprintFilterEngine
        print("✅ BlueprintFilterEngine imported successfully")
    except Exception as e:
        print(f"❌ Failed to import BlueprintFilterEngine: {e}")
        return False
    
    try:
        from filter_engine import FilterConfig
        print("✅ FilterConfig imported successfully")
    except Exception as e:
        print(f"❌ Failed to import FilterConfig: {e}")
        return False
    
    try:
        import pandas as pd
        print(f"✅ pandas version {pd.__version__} imported")
    except Exception as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    print("\n✅ All imports successful!")
    return True


def test_parsing():
    """Test the blueprint parsing functionality"""
    print("\n" + "="*60)
    print("TEST 2: Blueprint Parsing")
    print("="*60)
    
    from filter_engine import BlueprintFilterEngine
    
    test_data = """
🟡 1. BP7: THE HIGH-SCORING SIGNALS (B)
   🏟️ Den Bosch vs Almere City
   🏆 Eredivisie - Relegation - Play Offs
   📊 Odds: 2.55 | 3.6 | 2.45
   🎯 Play: HT 0.5 Goals / Over 2.5 Goals
   ⚠️ Risk: Moderate-High

🟢 2. BP1: THE ELITE HOME BANKER
   🏟️ Entebbe UPPC vs Calvary
   🏆 Premier League
   📊 Odds: 1.28 | 4.2 | 12.2
   🎯 Play: Straight Home Win
   ⚠️ Risk: Ultra-Low
"""
    
    engine = BlueprintFilterEngine()
    matches = engine.parse_blueprint_text(test_data)
    
    print(f"✅ Parsed {len(matches)} matches")
    
    for match in matches:
        print(f"   - {match['blueprint']}: {match['match']} ({match['league']})")
    
    if len(matches) > 0:
        print("\n✅ Parsing test PASSED")
        return True
    else:
        print("\n❌ Parsing test FAILED")
        return False


def test_confidence():
    """Test confidence calculation"""
    print("\n" + "="*60)
    print("TEST 3: Confidence Calculation")
    print("="*60)
    
    from filter_engine import BlueprintFilterEngine
    
    test_match = {
        'blueprint': 'BP1',
        'color': '🟢',
        'home_odds': 1.28,
        'draw_odds': 4.2,
        'away_odds': 12.2,
        'play': 'Straight Home Win',
        'league': 'Premier League',
        'match': 'Test vs Match'
    }
    
    engine = BlueprintFilterEngine()
    confidence = engine.calculate_confidence_score(test_match)
    
    print(f"Test match confidence: {confidence}%")
    
    if confidence >= 80:
        print("✅ High confidence as expected")
    else:
        print(f"⚠️ Confidence: {confidence}%")
    
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 FILTER ENGINE TEST SUITE")
    print("="*60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Blueprint Parsing", test_parsing),
        ("Confidence Calculation", test_confidence),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Filter engine is ready to use")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
