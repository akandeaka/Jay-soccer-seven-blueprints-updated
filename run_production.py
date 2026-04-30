import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filter_engine import TelegramIntegrator, FilterConfig

print("="*60)
print("📊 PRODUCTION SYSTEM - REFINED DRAW BLUEPRINTS")
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

# Store all qualified matches
all_matches = []

for _, row in df.iterrows():
    h = row['Odds Home']
    d = row['Odds Draw']
    a = row['Odds Away']
    
    # ============================================================
    # DRAW BLUEPRINTS (BP6 AND BP7) - CHECKED FIRST
    # ============================================================
    
    # BP6: STRONG DRAW - Draw odds 2.75 to 3.39
    if 2.75 <= d <= 3.39:
        all_matches.append({
            'bp': 'BP6',
            'name': 'THE STRONG DRAW',
            'play': 'Full Time Draw (X)',
            'risk': 'High (Strategic)',
            'confidence': 55,
            'row': row,
            'key_odds': d,
            'odds_type': 'Draw'
        })
    
    # BP7A: HIGH-SCORING SIGNALS - Draw odds 3.40 to 3.56
    elif 3.40 <= d <= 3.56:
        all_matches.append({
            'bp': 'BP7',
            'name': 'THE HIGH-SCORING SIGNALS (A)',
            'play': 'GG / Over 2.5 Goals',
            'risk': 'Moderate-High',
            'confidence': 60,
            'row': row,
            'key_odds': d,
            'odds_type': 'Draw'
        })
    
    # BP7B: HIGH-SCORING SIGNALS - Draw odds 3.60 to 3.75
    elif 3.60 <= d <= 3.75:
        all_matches.append({
            'bp': 'BP7',
            'name': 'THE HIGH-SCORING SIGNALS (B)',
            'play': 'HT 0.5 Goals / Over 2.5 Goals',
            'risk': 'Moderate-High',
            'confidence': 60,
            'row': row,
            'key_odds': d,
            'odds_type': 'Draw'
        })
    
    # ============================================================
    # HOME WIN BLUEPRINTS (BP1-BP5)
    # ============================================================
    
    # BP1: ELITE HOME BANKER - Home 1.20-1.29, Away >= 10.0
    elif 1.20 <= h <= 1.29 and a >= 10.0:
        all_matches.append({
            'bp': 'BP1',
            'name': 'THE ELITE HOME BANKER',
            'play': 'Straight Home Win',
            'risk': 'Ultra-Low',
            'confidence': 95,
            'row': row,
            'key_odds': h,
            'odds_type': 'Home'
        })
    
    # BP2: PRIMARY FAVORITE - Home 1.30-1.36, Away >= 9.0
    elif 1.30 <= h <= 1.36 and a >= 9.0:
        all_matches.append({
            'bp': 'BP2',
            'name': 'THE PRIMARY FAVORITE',
            'play': 'Home Win',
            'risk': 'Low',
            'confidence': 90,
            'row': row,
            'key_odds': h,
            'odds_type': 'Home'
        })
    
    # BP3: MODERATE FAVORITE SAFETY - Home 1.30-1.36, Away 7.0-8.99
    elif 1.30 <= h <= 1.36 and 7.0 <= a <= 8.99:
        all_matches.append({
            'bp': 'BP3',
            'name': 'THE MODERATE FAVORITE SAFETY',
            'play': '1X & Over 1.5 Goals',
            'risk': 'Low-Moderate',
            'confidence': 85,
            'row': row,
            'key_odds': h,
            'odds_type': 'Home'
        })
    
    # BP4: GOAL ENGINE - Home 1.72-1.80
    elif 1.72 <= h <= 1.80:
        all_matches.append({
            'bp': 'BP4',
            'name': 'THE GOAL ENGINE',
            'play': 'Over 1.5 Goals',
            'risk': 'Moderate',
            'confidence': 75,
            'row': row,
            'key_odds': h,
            'odds_type': 'Home'
        })
    
    # BP5: DEFENSIVE TRAP - Home 1.90-2.02
    elif 1.90 <= h <= 2.02:
        all_matches.append({
            'bp': 'BP5',
            'name': 'THE DEFENSIVE TRAP',
            'play': '1X & Under 3.5 FT',
            'risk': 'Moderate (Value Pick)',
            'confidence': 70,
            'row': row,
            'key_odds': h,
            'odds_type': 'Home'
        })

print(f"\n📊 TOTAL QUALIFIED: {len(all_matches)}")

# Count by blueprint
bp_counts = {}
for m in all_matches:
    bp = m['bp']
    bp_counts[bp] = bp_counts.get(bp, 0) + 1

print("\n📊 BREAKDOWN BY BLUEPRINT:")
for bp in ['BP6', 'BP7', 'BP1', 'BP2', 'BP3', 'BP4', 'BP5']:
    count = bp_counts.get(bp, 0)
    if count > 0:
        print(f"   {bp}: {count} matches")

# Sort by confidence (higher first, but draws will be lower)
all_matches.sort(key=lambda x: x['confidence'], reverse=True)

# Take top 25
top_matches = all_matches[:25]

# Build message
msg = f"⚽ BLUEPRINT RESULTS - DRAW INCLUDED\n"
msg += f"📅 {datetime.now().strftime('%Y-%m-%d')}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
msg += f"📊 Total qualified: {len(all_matches)} | Showing TOP {len(top_matches)}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

for i, m in enumerate(top_matches, 1):
    row = m['row']
    
    # Set tier based on confidence
    if m['confidence'] >= 85:
        tier = "🔥 GOLD"
    elif m['confidence'] >= 70:
        tier = "✅ SILVER"
    else:
        tier = "⚠️ BRONZE"
    
    # Highlight draw plays
    if m['bp'] in ['BP6', 'BP7']:
        draw_indicator = " 🎯 DRAW SIGNAL"
    else:
        draw_indicator = ""
    
    msg += f"{i}. {tier} {m['bp']}: {m['name']}{draw_indicator}\n"
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

print("\n✅ Done!")
