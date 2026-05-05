from datetime import datetime
from telegram_integrator import TelegramIntegrator  # your existing import
from filter_config import FilterConfig

# ... (your existing match filtering logic) ...

top_matches = all_matches[:25]

print(f"\n📊 BREAKDOWN OF TOP 25:")
bp_count = {}
for m in top_matches:
    bp = m[0]
    bp_count[bp] = bp_count.get(bp, 0) + 1
for bp, count in sorted(bp_count.items()):
    print(f"   {bp}: {count} matches")

# Build message with clean Unicode
msg = f"⚽ BLUEPRINT RESULTS - {datetime.now().strftime('%Y-%m-%d')}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
msg += f"📊 Total qualified: {len(all_matches)} | Showing TOP 25\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

for i, m in enumerate(top_matches, 1):
    bp, name, play, risk, conf, row = m

    if conf >= 85:
        tier = "🔥 GOLD"
    elif conf >= 70:
        tier = "✅ SILVER"
    else:
        tier = "⚠️ BRONZE"

    msg += f"\n{i}. {tier} {bp}: {name}\n"
    msg += f"   🏟️ {row['Home Team']} vs {row['Away Team']}\n"
    msg += f"   🏆 {row['Competition']}\n"
    msg += f"   📊 {row['Odds Home']} | {row['Odds Draw']} | {row['Odds Away']}\n"
    msg += f"   🎯 {play}\n"
    msg += f"   ⚠️ {risk}\n"
    msg += f"   📈 Confidence: {conf}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

# Send to Telegram
telegram = TelegramIntegrator(
    bot_token=FilterConfig.TELEGRAM_BOT_TOKEN,
    chat_id=FilterConfig.TELEGRAM_CHAT_ID
)

if len(msg) > 4000:
    telegram.send_telegram_message(msg[:3900])
    telegram.send_telegram_message("CONTINUED...\n" + msg[3900:])
    print("Sent in 2 parts")
else:
    telegram.send_telegram_message(msg)
    print("Sent successfully")

print("\n✅ Done!")
