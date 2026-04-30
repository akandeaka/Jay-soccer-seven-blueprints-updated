#!/usr/bin/env python3
"""
PRODUCTION SYSTEM - YOUR ORIGINAL 7 BLUEPRINTS
TOP 20 ONLY + ACCUMULATORS (2x, 5x, 7x, 10x)
"""

import sys
import os
import pandas as pd
import itertools
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filter_engine import TelegramIntegrator, FilterConfig

print("="*60)
print("📊 PRODUCTION SYSTEM")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# ============================================================
# READ CSV (SAME AS YOUR WORKING VERSION)
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
# CLASSIFY USING YOUR ORIGINAL 7 BLUEPRINTS
# ============================================================

matches = []

for idx, row in df.iterrows():
    h = row['Odds Home']
    d = row['Odds Draw']
    a = row['Odds Away']
    
    # YOUR EXACT BLUEPRINT RULES
    if 1.20 <= h <= 1.29 and a >= 10.0:
        matches.append({
            'bp': 'BP1', 'name': 'THE ELITE HOME BANKER',
            'play': 'Straight Home Win', 'risk': 'Ultra-Low',
            'confidence': 95, 'color': '🟢'
        })
    elif 1.30 <= h <= 1.36 and a >= 9.0:
        matches.append({
            'bp': 'BP2', 'name': 'THE PRIMARY FAVORITE',
            'play': 'Home Win', 'risk': 'Low',
            'confidence': 90, 'color': '🟢'
        })
    elif 1.30 <= h <= 1.36 and 7.0 <= a <= 8.99:
        matches.append({
            'bp': 'BP3', 'name': 'THE MODERATE FAVORITE SAFETY',
            'play': '1X & Over 1.5 Goals', 'risk': 'Low-Moderate',
            'confidence': 85, 'color': '🟡'
        })
    elif 1.72 <= h <= 1.80:
        matches.append({
            'bp': 'BP4', 'name': 'THE GOAL ENGINE',
            'play': 'Over 1.5 Goals', 'risk': 'Moderate',
            'confidence': 75, 'color': '🟡'
        })
    elif 1.90 <= h <= 2.02:
        matches.append({
            'bp': 'BP5', 'name': 'THE DEFENSIVE TRAP',
            'play': '1X & Under 3.5 FT', 'risk': 'Moderate (Value Pick)',
            'confidence': 70, 'color': '🟡'
        })
    elif 2.75 <= d <= 3.39:
        matches.append({
            'bp': 'BP6', 'name': 'THE STRONG DRAW',
            'play': 'Full Time Draw (X) Potential', 'risk': 'High (Strategic)',
            'confidence': 50, 'color': '🔴'
        })
    elif 3.40 <= d <= 3.56:
        matches.append({
            'bp': 'BP7', 'name': 'THE HIGH-SCORING SIGNALS (A)',
            'play': 'GG / Over 2.5 Goals', 'risk': 'Moderate-High',
            'confidence': 60, 'color': '🟡'
        })
    elif 3.60 <= d <= 3.75:
        matches.append({
            'bp': 'BP7', 'name': 'THE HIGH-SCORING SIGNALS (B)',
            'play': 'HT 0.5 Goals / Over 2.5 Goals', 'risk': 'Moderate-High',
            'confidence': 60, 'color': '🟡'
        })
    else:
        continue
    
    # Add match data to the last appended match
    matches[-1]['home'] = row['Home Team']
    matches[-1]['away'] = row['Away Team']
    matches[-1]['league'] = row['Competition']
    matches[-1]['h_odds'] = h
    matches[-1]['d_odds'] = d
    matches[-1]['a_odds'] = a

print(f"✅ {len(matches)} matches qualified for blueprints")

if len(matches) == 0:
    print("❌ No matches qualified")
    sys.exit(1)

# ============================================================
# TAKE TOP 20
# ============================================================

matches = sorted(matches, key=lambda x: x['confidence'], reverse=True)
top_20 = matches[:20]
print(f"✅ Top 20 matches selected")

# ============================================================
# BUILD ACCUMULATORS (NO DUPLICATE TEAMS)
# ============================================================

def get_teams(m):
    return {m['home'], m['away']}

def build_acc(matches_list, target, min_num, max_num):
    best = None
    best_odds = 0
    best_diff = float('inf')
    
    for num in range(min_num, min(max_num, len(matches_list)) + 1):
        for combo in itertools.combinations(matches_list, num):
            teams = set()
            dup = False
            for m in combo:
                if get_teams(m) & teams:
                    dup = True
                    break
                teams.update(get_teams(m))
            if dup:
                continue
            
            total = 1.0
            for m in combo:
                total *= m['h_odds']
            
            diff = abs(total - target)
            if diff < best_diff:
                best_diff = diff
                best = combo
                best_odds = total
    
    return best, best_odds

used = set()
acc_results = {}

# 2x (2-3 matches)
remaining = [m for i, m in enumerate(top_20) if i not in used]
combo, odds = build_acc(remaining, 2.0, 2, 3)
if combo:
    acc_results['2x'] = {'matches': combo, 'odds': odds}
    for m in combo:
        for i, tm in enumerate(top_20):
            if tm['home'] == m['home'] and tm['away'] == m['away']:
                used.add(i)

# 5x (3-4 matches)
remaining = [m for i, m in enumerate(top_20) if i not in used]
combo, odds = build_acc(remaining, 5.0, 3, 4)
if combo:
    acc_results['5x'] = {'matches': combo, 'odds': odds}
    for m in combo:
        for i, tm in enumerate(top_20):
            if tm['home'] == m['home'] and tm['away'] == m['away']:
                used.add(i)

# 7x (4-5 matches)
remaining = [m for i, m in enumerate(top_20) if i not in used]
combo, odds = build_acc(remaining, 7.0, 4, 5)
if combo:
    acc_results['7x'] = {'matches': combo, 'odds': odds}
    for m in combo:
        for i, tm in enumerate(top_20):
            if tm['home'] == m['home'] and tm['away'] == m['away']:
                used.add(i)

# 10x (5-6 matches)
remaining = [m for i, m in enumerate(top_20) if i not in used]
combo, odds = build_acc(remaining, 10.0, 5, 6)
if combo:
    acc_results['10x'] = {'matches': combo, 'odds': odds}

# ============================================================
# BUILD TELEGRAM MESSAGE
# ============================================================

message = f"""
⚽ BLUEPRINT RESULTS - {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Total scanned: {len(df)}
✅ Blueprint qualified: {len(matches)}
🏆 Top 20 picks below

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 TOP 20 PICKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

for idx, m in enumerate(top_20, 1):
    if m['confidence'] >= 85:
        tier = "🔥 GOLD"
    elif m['confidence'] >= 70:
        tier = "✅ SILVER"
    else:
        tier = "⚠️ BRONZE"
    
    message += f"""
{idx}. {tier} {m['bp']}: {m['name']}
   🏟️ {m['home']} vs {m['away']}
   🏆 {m['league']}
   📊 {m['h_odds']} | {m['d_odds']} | {m['a_odds']}
   🎯 {m['play']}
   ⚠️ {m['risk']}
   📈 Confidence: {m['confidence']}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# Add accumulators
if acc_results:
    message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 ACCUMULATORS (No duplicate teams)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    for acc_name, acc_data in acc_results.items():
        message += f"""
🎯 {acc_name} ACCUMULATOR ({len(acc_data['matches'])} selections)
   📈 Total Odds: {acc_data['odds']:.2f}x
"""
        for i, m in enumerate(acc_data['matches'], 1):
            message += f"   {i}. {m['home']} vs {m['away']} - {m['play']} @ {m['h_odds']}\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

# ============================================================
# SEND TO TELEGRAM
# ============================================================

telegram = TelegramIntegrator(
    bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
    chat_id=FilterConfig.TELEGRAM_CHAT_ID
)

if len(message) > 4000:
    telegram.send_telegram_message(message[:3950])
    telegram.send_telegram_message("📊 CONTINUED...\n" + message[3950:])
    print("✅ Sent in 2 parts")
else:
    telegram.send_telegram_message(message)
    print("✅ Sent")

# Save results
pd.DataFrame(top_20).to_csv('top_20_picks.csv', index=False)
print(f"\n📁 Saved top_20_picks.csv")
print(f"✅ Done! Processed {len(df)} matches -> {len(matches)} qualified -> Top 20 sent")
