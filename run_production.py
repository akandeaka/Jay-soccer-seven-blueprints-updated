#!/usr/bin/env python3
"""
PRODUCTION SYSTEM - TOP 20 + ACCUMULATORS (2x, 5x, 7x, 10x)
"""

import sys
import os
import pandas as pd
import itertools
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filter_engine import BlueprintFilterEngine, TelegramIntegrator, FilterConfig

print("="*60)
print("📊 PRODUCTION SYSTEM")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# ============================================================
# READ CSV FILE
# ============================================================

CSV_FILE = "matches_today.csv"

if not os.path.exists(CSV_FILE):
    print(f"❌ ERROR: {CSV_FILE} not found!")
    sys.exit(1)

df = pd.read_csv(CSV_FILE)
print(f"📥 Read {len(df)} total rows")

# Filter valid odds
df = df[df['Odds Home'] != '-']
df = df[df['Odds Draw'] != '-']
df = df[df['Odds Away'] != '-']

df['Odds Home'] = pd.to_numeric(df['Odds Home'])
df['Odds Draw'] = pd.to_numeric(df['Odds Draw'])
df['Odds Away'] = pd.to_numeric(df['Odds Away'])
df = df.dropna()

print(f"✅ {len(df)} matches with valid odds")

if len(df) == 0:
    print("❌ No valid matches")
    sys.exit(1)

# ============================================================
# BUILD BLUEPRINT TEXT
# ============================================================

print("\n🔄 Building blueprint text...")

blueprint_lines = []

for idx, row in df.iterrows():
    h = float(row['Odds Home'])
    d = float(row['Odds Draw'])
    a = float(row['Odds Away'])
    
    # Determine blueprint using YOUR original rules
    if 1.20 <= h <= 1.29 and a >= 10.0:
        bp = "🟢 BP1"
        play = "Straight Home Win"
        risk = "Ultra-Low"
    elif 1.30 <= h <= 1.36 and a >= 9.0:
        bp = "🟢 BP2"
        play = "Home Win"
        risk = "Low"
    elif 1.30 <= h <= 1.36 and 7.0 <= a <= 8.99:
        bp = "🟡 BP3"
        play = "1X & Over 1.5 Goals"
        risk = "Low-Moderate"
    elif 1.72 <= h <= 1.80:
        bp = "🟡 BP4"
        play = "Over 1.5 Goals"
        risk = "Moderate"
    elif 1.90 <= h <= 2.02:
        bp = "🟡 BP5"
        play = "1X & Under 3.5 FT"
        risk = "Moderate (Value Pick)"
    elif 2.75 <= d <= 3.39:
        bp = "🔴 BP6"
        play = "Full Time Draw (X) Potential"
        risk = "High (Strategic)"
    elif 3.40 <= d <= 3.56:
        bp = "🟡 BP7"
        play = "GG / Over 2.5 Goals"
        risk = "Moderate-High"
    elif 3.60 <= d <= 3.75:
        bp = "🟡 BP7"
        play = "HT 0.5 Goals / Over 2.5 Goals"
        risk = "Moderate-High"
    else:
        continue  # Skip matches that don't qualify for any blueprint
    
    bp_names = {
        "🟢 BP1": "THE ELITE HOME BANKER",
        "🟢 BP2": "THE PRIMARY FAVORITE",
        "🟡 BP3": "THE MODERATE FAVORITE SAFETY",
        "🟡 BP4": "THE GOAL ENGINE",
        "🟡 BP5": "THE DEFENSIVE TRAP",
        "🔴 BP6": "THE STRONG DRAW",
        "🟡 BP7": "THE HIGH-SCORING SIGNALS"
    }
    
    blueprint_lines.append(f"{bp} {idx+1}. {bp_names.get(bp, 'MATCH')}")
    blueprint_lines.append(f"   🏟️ {row['Home Team']} vs {row['Away Team']}")
    blueprint_lines.append(f"   🏆 {row['Competition']}")
    blueprint_lines.append(f"   📊 Odds: {h} | {d} | {a}")
    blueprint_lines.append(f"   🎯 Play: {play}")
    blueprint_lines.append(f"   ⚠️ Risk: {risk}")
    blueprint_lines.append("")

blueprint_text = "\n".join(blueprint_lines)

# ============================================================
# APPLY FILTER ENGINE - GET TOP 20
# ============================================================

print("\n🔄 Applying filter engine...")

engine = BlueprintFilterEngine()
matches = engine.parse_blueprint_text(blueprint_text)
results_df = engine.process_matches(matches)

# Get top 20 matches
top_20 = results_df.head(20).to_dict('records')
print(f"✅ Top 20 matches selected from {len(matches)} total")

# ============================================================
# BUILD ACCUMULATORS (NO REPEATED TEAMS)
# ============================================================

print("\n🔨 Building accumulators...")

def get_teams_from_match(match):
    """Extract team names from match string"""
    match_str = match.get('Match', '')
    if ' vs ' in match_str:
        parts = match_str.split(' vs ')
        return {parts[0].strip(), parts[1].strip()}
    return set()

def build_accumulator(matches_list, target_odds, min_matches, max_matches):
    """Build accumulator with target odds without repeating teams"""
    best_combo = None
    best_odds = 0
    best_diff = float('inf')
    
    for num in range(min_matches, min(max_matches, len(matches_list)) + 1):
        for combo in itertools.combinations(matches_list, num):
            # Check for duplicate teams
            all_teams = set()
            duplicate = False
            for match in combo:
                teams = get_teams_from_match(match)
                if teams & all_teams:
                    duplicate = True
                    break
                all_teams.update(teams)
            
            if duplicate:
                continue
            
            # Calculate total odds
            total = 1.0
            for match in combo:
                total *= match.get('Home Odds', 1.5)
            
            diff = abs(total - target_odds)
            if diff < best_diff and total >= target_odds * 0.7:
                best_diff = diff
                best_combo = combo
                best_odds = total
    
    return best_combo, best_odds

# Try to build accumulators from top 20
accumulators = {}
used_matches_indices = set()

# 2x accumulator (2-3 matches)
remaining = [m for i, m in enumerate(top_20) if i not in used_matches_indices]
combo, odds = build_accumulator(remaining, 2.0, 2, 3)
if combo:
    accumulators['2x'] = {'matches': combo, 'odds': odds}
    for m in combo:
        for i, tm in enumerate(top_20):
            if tm.get('Match') == m.get('Match'):
                used_matches_indices.add(i)
                break

# 5x accumulator (3-5 matches)
remaining = [m for i, m in enumerate(top_20) if i not in used_matches_indices]
combo, odds = build_accumulator(remaining, 5.0, 3, 5)
if combo:
    accumulators['5x'] = {'matches': combo, 'odds': odds}
    for m in combo:
        for i, tm in enumerate(top_20):
            if tm.get('Match') == m.get('Match'):
                used_matches_indices.add(i)
                break

# 7x accumulator (4-6 matches)
remaining = [m for i, m in enumerate(top_20) if i not in used_matches_indices]
combo, odds = build_accumulator(remaining, 7.0, 4, 6)
if combo:
    accumulators['7x'] = {'matches': combo, 'odds': odds}
    for m in combo:
        for i, tm in enumerate(top_20):
            if tm.get('Match') == m.get('Match'):
                used_matches_indices.add(i)
                break

# 10x accumulator (5-6 matches)
remaining = [m for i, m in enumerate(top_20) if i not in used_matches_indices]
combo, odds = build_accumulator(remaining, 10.0, 5, 6)
if combo:
    accumulators['10x'] = {'matches': combo, 'odds': odds}

# ============================================================
# BUILD TELEGRAM MESSAGE
# ============================================================

print("\n📤 Building Telegram message...")

# Top 20 message
message = f"""
⚽ FILTER ENGINE RESULTS - {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Total matches scanned: {len(df)}
✅ Blueprint qualified: {len(matches)}
🏆 Top 20 picks shown below

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 TOP 20 PICKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

for idx, row in enumerate(top_20, 1):
    message += f"""
{idx}. {row['Tier']} {row['Blueprint']}
   🏟️ {row['Match']}
   🏆 {row['League']}
   📊 {row['Home Odds']} | {row['Draw Odds']} | {row['Away Odds']}
   🎯 {row['Play']}
   ⚠️ {row['Risk']}
   📈 Confidence: {row['Confidence']}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# Add accumulator section
message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 ACCUMULATOR RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

for acc_name, acc_data in accumulators.items():
    matches_list = acc_data['matches']
    total_odds = acc_data['odds']
    message += f"""
🎯 {acc_name} ACCUMULATOR ({len(matches_list)} selections)
   📈 Total Odds: {total_odds:.2f}x
   💰 Potential Return: Stake × {total_odds:.2f}
"""
    for i, m in enumerate(matches_list, 1):
        message += f"   {i}. {m['Match']} ({m['Play']}) @ {m['Home Odds']}\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

# ============================================================
# SEND TO TELEGRAM (SPLIT IF TOO LONG)
# ============================================================

telegram = TelegramIntegrator(
    bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
    chat_id=FilterConfig.TELEGRAM_CHAT_ID
)

# Telegram has 4096 character limit
if len(message) > 4000:
    # Split into multiple messages
    part1 = message[:3800]
    part2 = "📊 CONTINUED...\n" + message[3800:]
    
    telegram.send_telegram_message(part1)
    telegram.send_telegram_message(part2)
    print("✅ Sent in 2 parts")
else:
    telegram.send_telegram_message(message)
    print("✅ Sent in 1 part")

# Save results
results_df.head(20).to_csv('top_20_picks.csv', index=False)
print(f"\n📁 Saved top_20_picks.csv")
print(f"✅ Done! Processed {len(df)} matches -> {len(matches)} qualified -> Top 20 sent")
