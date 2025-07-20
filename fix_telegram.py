#!/usr/bin/env python3
"""
Fix Telegram bot configuration
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_telegram_bot():
    """Test the Telegram bot and find the correct user ID."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment")
        return False
    
    print(f"🤖 Testing bot token: {bot_token[:10]}...")
    
    # Test bot info
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            print(f"✅ Bot connected: {bot_info['result']['first_name']}")
            print(f"   Username: @{bot_info['result']['username']}")
        else:
            print(f"❌ Bot connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing bot: {e}")
        return False
    
    # Test with different user ID formats
    test_user_ids = [
        "6469066137",  # Current user ID
        "@6469066137",  # With @ prefix
        "-6469066137",  # Negative (group chat)
        "6469066137",   # As string
        6469066137,     # As integer
    ]
    
    for user_id in test_user_ids:
        print(f"\n🧪 Testing user ID: {user_id}")
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": user_id,
                "text": f"🧪 Test message - user ID: {user_id}",
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Success with user ID: {user_id}")
                return user_id
            else:
                print(f"❌ Failed with user ID: {user_id}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Error with user ID {user_id}: {e}")
    
    print("\n❌ No working user ID found")
    print("\nTo fix this:")
    print("1. Start a chat with your bot on Telegram")
    print("2. Send /start to the bot")
    print("3. Get your chat ID by visiting: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
    print("4. Update the TELEGRAM_USER_ID in your .env file")
    
    return False

def get_updates():
    """Get recent updates to find the correct chat ID."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            updates = response.json()
            print(f"📋 Recent updates: {len(updates.get('result', []))}")
            
            for update in updates.get('result', []):
                if 'message' in update:
                    message = update['message']
                    chat = message.get('chat', {})
                    print(f"  Chat ID: {chat.get('id')} | Type: {chat.get('type')} | Title: {chat.get('title', chat.get('first_name', 'Unknown'))}")
        else:
            print(f"❌ Failed to get updates: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error getting updates: {e}")

if __name__ == "__main__":
    print("🔧 Fixing Telegram Configuration")
    print("=" * 40)
    
    working_user_id = test_telegram_bot()
    
    if not working_user_id:
        print("\n🔍 Getting recent updates to find correct chat ID...")
        get_updates() 