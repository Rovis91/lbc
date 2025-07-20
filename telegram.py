import os
import requests
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.user_id = os.getenv("TELEGRAM_USER_ID")
        
        if not self.bot_token or not self.user_id:
            raise ValueError("Missing Telegram credentials in environment variables")
    
    def send_message(self, message: str) -> bool:
        """Send a message via Telegram Bot API."""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.user_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            # For now, just print the message to console instead of failing
            print(f"📨 Telegram message (not sent): {message}")
            return False
    
    def send_scraping_report(self, stats: Dict) -> bool:
        """
        Send a formatted scraping report.
        
        Args:
            stats: Dictionary containing:
                - cities_success: int
                - cities_errors: int  
                - cities_warnings: int
                - total_new_listings: int
                - total_duplicates: int
                - duration_minutes: int
                - duration_seconds: int
                - total_cities: int
        """
        try:
            # Format duration
            duration_str = f"{stats['duration_minutes']}min {stats['duration_seconds']}s"
            
            # Calculate success rate
            total_cities = stats['total_cities']
            success_rate = f"{stats['cities_success']}/{total_cities}"
            
            # Build message
            message = f"""🏆 <b>SCRAPING COMPLETED</b>
─────────────────────
✅ Successful cities: {success_rate}
❌ Errors: {stats['cities_errors']} cities
⚠️ Warnings: {stats['cities_warnings']} cities (0 listings)
⏱️ Duration: {duration_str}
📊 New listings: {stats['total_new_listings']}
🔄 Duplicates avoided: {stats['total_duplicates']}
🗓️ Finished: {stats['finished_at']}"""
            
            return self.send_message(message)
        except Exception as e:
            print(f"Error formatting scraping report: {e}")
            return False
    
    def send_no_cities_message(self) -> bool:
        """Send message when no cities need scraping."""
        message = "📨 <b>No cities to scrape</b>\nNo cities require scraping at this time."
        return self.send_message(message) 