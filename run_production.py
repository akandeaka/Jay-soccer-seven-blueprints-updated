import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filter_engine import TelegramIntegrator, FilterConfig

print("="*60)
print("📊 PRODUCTION SYSTEM - ALL 7 BLUEPRINTS + TOP 4 ELITE DRAWS")
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

# Elite leagues for high probability draws
ELITE_LEAGUES = [
    'Champions League', 'Europa League', 'Conference League',
    'Premier League', 'LaLiga', 'Serie A', 'Bundesliga', 'Ligue 1',
    'Eredivisie', 'Primeira Liga', 'Copa Libertadores', 'Copa Sudamericana'
]

def is_elite_league(league):
    if not isinstance(league, str):
        return False
    for elite in ELITE_LEAGUES:
        if elite.lower() in league.lower():
            return True
    return False

# Store all matches by blueprint
bp1_matches = []
bp2_matches = []
bp3_matches = []
bp4_matches = []
bp5_matches = []
bp6_matches = []
bp7_matches = []

for _, row in df.iterrows():
    h = row['Odds Home']
    d = row['Odds Draw']
    a = row['Odds Away']
    league = row['Competition']
    
    # BP1: ELITE HOME BANKER
    if 1.20 <= h <= 1.29 and a >= 10.0:
        bp1_matches.append({
            'bp': 'BP1', 'name': 'THE ELITE HOME BANKER',
            'play': 'Straight Home Win', 'risk': 'Ultra-Low',
            'confidence': 95, 'row': row
        })
    
    # BP2: PRIMARY FAVORITE
    elif 1.30 <= h <= 1.36 and a >= 9.0:
        bp2_matches.append({
            'bp': 'BP2', 'name': 'THE PRIMARY FAVORITE',
            'play': 'Home Win', 'risk': 'Low',
            'confidence': 90, 'row': row
        })
    
    # BP3: MODERATE FAVORITE SAFETY
    elif 1.30 <= h <= 1.36 and 7.0 <= a <= 8.99:
        bp3_matches.append({
            'bp': 'BP3', 'name': 'THE MODERATE FAVORITE SAFETY',
            'play': '1X & Over 1.5 Goals', 'risk': 'Low-Moderate',
            'confidence': 85, 'row': row
        })
    
    # BP4: GOAL ENGINE
    elif 1.72 <= h <= 1.80:
        bp4_matches.append({
            'bp': 'BP4', 'name': 'THE GOAL ENGINE',
            'play': 'Over 1.5 Goals', 'risk': 'Moderate',
            'confidence': 75, 'row': row
        })
    
    # BP5: DEFENSIVE TRAP
    elif 1.90 <= h <= 2.02:
        bp5_matches.append({
            'bp': 'BP5', 'name': 'THE DEFENSIVE TRAP',
            'play': '1X & Under 3.5 FT', 'risk': 'Moderate',
            'confidence': 70, 'row': row
        })
    
    # BP6: STRONG DRAW - SWEET SPOT 3.00 to 3.39
    elif 3.00 <= d <= 3.39:
        bp6_matches.append({
            'bp': 'BP6', 'name': 'THE STRONG DRAW',
            'play': 'Full Time Draw (X)', 'risk': 'High (Strategic)',
            'confidence': 70,  # Higher confidence for sweet spot
            'row': row, 'league': league,
            'is_elite': is_elite_league(league)
        })
    
    # BP6 also includes 2.75-2.99 but with lower priority
    elif 2.75 <= d <= 2.99:
        bp6_matches.append({
            'bp': 'BP6', 'name': 'THE STRONG DRAW',
            'play': 'Full Time Draw (X)', 'risk': 'High (Strategic)',
            'confidence': 60,
            'row': row, 'league': league,
            'is_elite': is_elite_league(league)
        })
    
    # BP7: HIGH SCORING SIGNALS (3.40-3.75)
    elif 3.40 <= d <= 3.56:
        bp7_matches.append({
            'bp': 'BP7', 'name': 'THE HIGH-SCORING SIGNALS (A)',
            'play': 'GG / Over 2.5 Goals', 'risk': 'Moderate-High',
            'confidence': 60, 'row': row
        })
    elif 3.60 <= d <= 3.75:
        bp7_matches.append({
            'bp': 'BP7', 'name': 'THE HIGH-SCORING SIGNALS (B)',
            'play': 'HT 0.5 Goals / Over 2.5 Goals', 'risk': 'Moderate-High',
            'confidence': 60, 'row': row
        })

print(f"\n📊 BLUEPRINT BREAKDOWN:")
print(f"   BP1 (Elite Home Banker): {len(bp1_matches)}")
print(f"   BP2 (Primary Favorite): {len(bp2_matches)}")
print(f"   BP3 (Moderate Favorite): {len(bp3_matches)}")
print(f"   BP4 (Goal Engine): {len(bp4_matches)}")
print(f"   BP5 (Defensive Trap): {len(bp5_matches)}")
print(f"   BP6 (Strong Draw 3.00-3.39 sweet spot): {len([m for m in bp6_matches if 3.00 <= m['row']['Odds Draw'] <= 3.39])}")
print(f"   BP6 (Draw 2.75-2.99): {len([m for m in bp6_matches if 2.75 <= m['row']['Odds Draw'] <= 2.99])}")
print(f"   BP7 (High Scoring): {len(bp7_matches)}")

# ============================================================
# SELECT TOP 4 ELITE DRAWS FROM BP6
# PRIORITIZE SWEET SPOT (3.00-3.39) OVER LOWER ODDS
# ============================================================

# Separate sweet spot draws (3.00-3.39) from lower draws (2.75-2.99)
sweet_spot_draws = [m for m in bp6_matches if m['is_elite'] and 3.00 <= m['row']['Odds Draw'] <= 3.39]
other_elite_draws = [m for m in bp6_matches if m['is_elite'] and m not in sweet_spot_draws]
non_elite_draws = [m for m in bp6_matches if not m['is_elite']]

# Sort sweet spot draws by draw odds (higher is better within range)
sweet_spot_draws.sort(key=lambda x: x['row']['Odds Draw'], reverse=True)
other_elite_draws.sort(key=lambda x: x['row']['Odds Draw'], reverse=True)
non_elite_draws.sort(key=lambda x: x['row']['Odds Draw'], reverse=True)

# Take top 4 from sweet spot first, then other elites
top_4_draws = sweet_spot_draws[:4]
if len(top_4_draws) < 4:
    needed = 4 - len(top_4_draws)
    top_4_draws.extend(other_elite_draws[:needed])

remaining_draws = sweet_spot_draws[4:] + other_elite_draws + non_elite_draws

print(f"\n🎯 TOP 4 ELITE DRAWS (Sweet Spot 3.00-3.39 preferred):")
for i, m in enumerate(top_4_draws[:4], 1):
    row = m['row']
    sweet_marker = " ✓ SWEET SPOT" if 3.00 <= row['Odds Draw'] <= 3.39 else ""
    print(f"   {i}. {row['Home Team']} vs {row['Away Team']} - Draw: {row['Odds Draw']}{sweet_marker} ({row['Competition']})")

# ============================================================
# BUILD TOP 25 - ALL BLUEPRINTS REPRESENTED
# ============================================================

top_25 = []

# STEP 1: Add top 4 elite draws (BP6) - sweet spot prioritized
top_25.extend(top_4_draws)

# STEP 2: Add remaining BP6 draws
top_25.extend(remaining_draws[:3])

# STEP 3: Add BP7 matches
bp7_sorted = sorted(bp7_matches, key=lambda x: x['confidence'], reverse=True)
top_25.extend(bp7_sorted[:4])

# STEP 4: Add BP1
bp1_sorted = sorted(bp1_matches, key=lambda x: x['confidence'], reverse=True)
top_25.extend(bp1_sorted[:4])

# STEP 5: Add BP2
bp2_sorted = sorted(bp2_matches, key=lambda x: x['confidence'], reverse=True)
top_25.extend(bp2_sorted[:3])

# STEP 6: Add BP3
bp3_sorted = sorted(bp3_matches, key=lambda x: x['confidence'], reverse=True)
top_25.extend(bp3_sorted[:3])

# STEP 7: Add BP4
bp4_sorted = sorted(bp4_matches, key=lambda x: x['confidence'], reverse=True)
top_25.extend(bp4_sorted[:2])

# STEP 8: Add BP5
bp5_sorted = sorted(bp5_matches, key=lambda x: x['confidence'], reverse=True)
top_25.extend(bp5_sorted[:2])

top_25 = top_25[:25]

print(f"\n📊 FINAL TOP 25 COMPOSITION:")
bp_final = {}
for m in top_25:
    bp = m['bp']
    bp_final[bp] = bp_final.get(bp, 0) + 1
for bp in ['BP6', 'BP7', 'BP1', 'BP2', 'BP3', 'BP4', 'BP5']:
    count = bp_final.get(bp, 0)
    if count > 0:
        print(f"   {bp}: {count} matches")

# ============================================================
# BUILD TELEGRAM MESSAGE
# ============================================================

msg = f"⚽ ALL 7 BLUEPRINTS RESULTS - {datetime.now().strftime('%Y-%m-%d')}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
msg += f"📊 TOP 25 PICKS (All 7 Blueprints)\n"
msg += f"🎯 BP6 Draw Sweet Spot: 3.00 - 3.39\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

for i, m in enumerate(top_25, 1):
    row = m['row']
    
    if m['bp'] == 'BP1':
        tier = "🔥 GOLD"
    elif m['bp'] in ['BP2', 'BP3']:
        tier = "✅ SILVER"
    else:
        tier = "⚠️ BRONZE"
    
    # Mark sweet spot draws
    if i <= 4 and m['bp'] == 'BP6' and 3.00 <= row['Odds Draw'] <= 3.39:
        draw_marker = " 🎯 SWEET SPOT DRAW"
    elif i <= 4 and m['bp'] == 'BP6':
        draw_marker = " 🎯 ELITE DRAW"
    else:
        draw_marker = ""
    
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

print("\n✅ Done!")
