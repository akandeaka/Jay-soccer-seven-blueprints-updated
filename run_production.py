import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filter_engine import TelegramIntegrator, FilterConfig

print("="*60)
print("📊 PRODUCTION SYSTEM - BP6 DRAWS COMPULSORY")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

CSV_FILE = "matches_today.csv"

if not os.path.exists(CSV_FILE):
    print(f"ERROR: {CSV_FILE} not found")
    sys.exit(1)

df = pd.read_csv(CSV_FILE)
print(f"Loaded {len(df)} rows")

# Filter valid odds
df = df[df['Odds Home'] != '-']
df = df[df['Odds Draw'] != '-']
df = df[df['Odds Away'] != '-']

df['Odds Home'] = df['Odds Home'].astype(float)
df['Odds Draw'] = df['Odds Draw'].astype(float)
df['Odds Away'] = df['Odds Away'].astype(float)

print(f"Matches with odds: {len(df)}")

# Separate collections
bp6_matches = []      # Draw odds 2.75-3.39
bp7_matches = []      # Draw odds 3.40-3.75
bp1_5_matches = []    # Home win blueprints

for _, row in df.iterrows():
    h = row['Odds Home']
    d = row['Odds Draw']
    a = row['Odds Away']
    
    # BP6: STRONG DRAW - Draw 2.75-3.39 (COMPULSORY)
    if 2.75 <= d <= 3.39:
        bp6_matches.append({
            'bp': 'BP6',
            'name': 'THE STRONG DRAW',
            'play': 'Full Time Draw (X)',
            'risk': 'High (Strategic)',
            'confidence': 85,  # High confidence for forced placement
            'row': row,
            'sort_odds': d
        })
    
    # BP7: HIGH SCORING - Draw 3.40-3.75
    elif 3.40 <= d <= 3.56:
        bp7_matches.append({
            'bp': 'BP7',
            'name': 'THE HIGH-SCORING SIGNALS (A)',
            'play': 'GG / Over 2.5 Goals',
            'risk': 'Moderate-High',
            'confidence': 70,
            'row': row,
            'sort_odds': d
        })
    elif 3.60 <= d <= 3.75:
        bp7_matches.append({
            'bp': 'BP7',
            'name': 'THE HIGH-SCORING SIGNALS (B)',
            'play': 'HT 0.5 Goals / Over 2.5 Goals',
            'risk': 'Moderate-High',
            'confidence': 70,
            'row': row,
            'sort_odds': d
        })
    
    # BP1-BP5: Home Win Blueprints
    elif 1.20 <= h <= 1.29 and a >= 10.0:
        bp1_5_matches.append({
            'bp': 'BP1',
            'name': 'THE ELITE HOME BANKER',
            'play': 'Straight Home Win',
            'risk': 'Ultra-Low',
            'confidence': 95,
            'row': row,
            'sort_odds': h
        })
    elif 1.30 <= h <= 1.36 and a >= 9.0:
        bp1_5_matches.append({
            'bp': 'BP2',
            'name': 'THE PRIMARY FAVORITE',
            'play': 'Home Win',
            'risk': 'Low',
            'confidence': 90,
            'row': row,
            'sort_odds': h
        })
    elif 1.30 <= h <= 1.36 and 7.0 <= a <= 8.99:
        bp1_5_matches.append({
            'bp': 'BP3',
            'name': 'THE MODERATE FAVORITE SAFETY',
            'play': '1X & Over 1.5 Goals',
            'risk': 'Low-Moderate',
            'confidence': 85,
            'row': row,
            'sort_odds': h
        })
    elif 1.72 <= h <= 1.80:
        bp1_5_matches.append({
            'bp': 'BP4',
            'name': 'THE GOAL ENGINE',
            'play': 'Over 1.5 Goals',
            'risk': 'Moderate',
            'confidence': 75,
            'row': row,
            'sort_odds': h
        })
    elif 1.90 <= h <= 2.02:
        bp1_5_matches.append({
            'bp': 'BP5',
            'name': 'THE DEFENSIVE TRAP',
            'play': '1X & Under 3.5 FT',
            'risk': 'Moderate',
            'confidence': 70,
            'row': row,
            'sort_odds': h
        })

print(f"\n📊 BREAKDOWN:")
print(f"   BP6 (Draw 2.75-3.39): {len(bp6_matches)} matches")
print(f"   BP7 (Draw 3.40-3.75): {len(bp7_matches)} matches")
print(f"   BP1-BP5 (Home Wins): {len(bp1_5_matches)} matches")

# ============================================================
# BUILD TOP 25 - WITH BP6 COMPULSORY (MIN 4)
# ============================================================

top_25 = []

# STEP 1: Add ALL BP6 matches first (compulsory)
bp6_sorted = sorted(bp6_matches, key=lambda x: x['sort_odds'])  # Lower draw odds first
top_25.extend(bp6_sorted[:4])  # Minimum 4 BP6 matches

# STEP 2: Add remaining BP6 matches if any
if len(bp6_sorted) > 4:
    top_25.extend(bp6_sorted[4:])

# STEP 3: Add BP7 matches (high scoring signals)
bp7_sorted = sorted(bp7_matches, key=lambda x: x['confidence'], reverse=True)
top_25.extend(bp7_sorted)

# STEP 4: Add BP1-BP5 matches (home wins) sorted by confidence
bp1_5_sorted = sorted(bp1_5_matches, key=lambda x: x['confidence'], reverse=True)
top_25.extend(bp1_5_sorted)

# Take only first 25
top_25 = top_25[:25]

print(f"\n📊 TOP 25 COMPOSITION:")
bp_count = {}
for m in top_25:
    bp = m['bp']
    bp_count[bp] = bp_count.get(bp, 0) + 1
for bp in ['BP6', 'BP7', 'BP1', 'BP2', 'BP3', 'BP4', 'BP5']:
    count = bp_count.get(bp, 0)
    if count > 0:
        print(f"   {bp}: {count} matches")

# ============================================================
# BUILD TELEGRAM MESSAGE
# ============================================================

msg = f"⚽ BLUEPRINT RESULTS - {datetime.now().strftime('%Y-%m-%d')}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
msg += f"📊 Total qualified: {len(bp6_matches) + len(bp7_matches) + len(bp1_5_matches)}\n"
msg += f"🎯 BP6 Draws: {len(bp6_matches)} | Showing TOP 25\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

for i, m in enumerate(top_25, 1):
    row = m['row']
    
    # Set tier
    if m['bp'] == 'BP1':
        tier = "🔥 GOLD"
    elif m['bp'] in ['BP2', 'BP3', 'BP4', 'BP5']:
        tier = "✅ SILVER"
    else:
        tier = "⚠️ BRONZE"
    
    # Highlight BP6 draws
    draw_marker = " 🎯 DRAW PICK" if m['bp'] == 'BP6' else ""
    
    msg += f"{i}. {tier} {m['bp']}: {m['name']}{draw_marker}\n"
    msg += f"   🏟️ {row['Home Team']} vs {row['Away Team']}\n"
    msg += f"   🏆 {row['Competition']}\n"
    msg += f"   📊 {row['Odds Home']} | {row['Odds Draw']} | {row['Odds Away']}\n"
    msg += f"   🎯 {m['play']}\n"
    msg += f"   ⚠️ {m['risk']}\n"
    msg += f"   📈 Confidence: {m['confidence']}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

# Send to Telegram
telegram = TelegramIntegrator(bot_token=FilterConfig.TELEGRAM_BOT_TOKEN, chat_id=FilterConfig.TELEGRAM_CHAT_ID)

if len(msg) > 4000:
    telegram.send_telegram_message(msg[:3900])
    telegram.send_telegram_message("CONTINUED...\n" + msg[3900:])
    print("Sent in 2 parts")
else:
    telegram.send_telegram_message(msg)
    print("Sent successfully")

print("\n✅ Done! BP6 draws are compulsory in top 25")
