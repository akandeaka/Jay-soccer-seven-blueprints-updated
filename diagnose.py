#!/usr/bin/env python3
"""
Diagnostic script - Check where data is coming from
"""

import os
import sys
from datetime import datetime

print("="*60)
print("🔍 DATA SOURCE DIAGNOSTIC")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# Check production_config.py
print("\n📋 1. Checking production_config.py:")
try:
    from production_config import ProductionConfig
    print(f"   BLUEPRINT_OUTPUT_FILE: {ProductionConfig.BLUEPRINT_OUTPUT_FILE}")
    print(f"   BLUEPRINT_CSV_FILE: {ProductionConfig.BLUEPRINT_CSV_FILE}")
    print(f"   USE_MOCK_DATA: {getattr(ProductionConfig, 'USE_MOCK_DATA', 'Not set')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check config.py
print("\n📋 2. Checking filter_engine/config.py:")
try:
    from filter_engine.config import FilterConfig
    print(f"   TELEGRAM_BOT_TOKEN: {'SET' if FilterConfig.TELEGRAM_BOT_TOKEN else 'MISSING'}")
    print(f"   TELEGRAM_CHAT_ID: {'SET' if FilterConfig.TELEGRAM_CHAT_ID else 'MISSING'}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check for files
print("\n📁 3. Checking for data files:")
files_to_check = [
    'blueprint_output.txt',
    'matches_today.csv',
    'raw_blueprint_output.txt',
    'filtered_results.csv',
    'top_20_picks.csv'
]

for filename in files_to_check:
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        modified = datetime.fromtimestamp(os.path.getmtime(filename))
        print(f"   ✅ {filename} - {size} bytes (modified: {modified.strftime('%Y-%m-%d %H:%M')})")
    else:
        print(f"   ❌ {filename} - NOT FOUND")

# Check for hardcoded data in run_production.py
print("\n📋 4. Checking run_production.py for hardcoded data:")
try:
    with open('run_production.py', 'r') as f:
        content = f.read()
        if 'create_sample_blueprint_data' in content:
            print("   ⚠️ WARNING: run_production.py contains hardcoded sample data!")
            print("      This function will override your real data.")
        if 'USE_MOCK_DATA' in content:
            print("   ⚠️ WARNING: USE_MOCK_DATA found - using fake data!")
        else:
            print("   ✅ No hardcoded sample data found")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check blueprint_reader.py
print("\n📋 5. Checking blueprint_reader.py configuration:")
try:
    from blueprint_reader import BlueprintReader
    reader = BlueprintReader(ProductionConfig())
    print("   ✅ BlueprintReader imported successfully")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("✅ Diagnostic complete")
print("="*60)
