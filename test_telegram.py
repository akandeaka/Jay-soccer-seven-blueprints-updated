"""
Quick test to verify Telegram bot is working
"""

import requests

BOT_TOKEN = "8634288532:AAEGeI0DaqNIklrx8jWrLnW7dzhc41_wrS4"
CHAT_ID = "401821398"

def test_bot():
    print("Testing Telegram Bot...")
    
    # Test 1: Get bot info
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('ok'):
            bot = data['result']
            print(f"✅ Bot connected: @{bot['username']}")
        else:
            print(f"❌ Bot error: {data}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to bot: {e}")
        return False
    
    # Test 2: Send a test message
    test_message = "🧪 Test message from Filter Engine! Bot is working."
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': test_message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        if result.get('ok'):
            print("✅ Test message sent successfully!")
            print("   Check your Telegram @JaySoccerBot")
            return True
        else:
            print(f"❌ Failed to send: {result}")
            return False
    except Exception as e:
        print(f"❌ Error sending: {e}")
        return False

if __name__ == "__main__":
    test_bot()
