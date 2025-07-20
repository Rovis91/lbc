#!/usr/bin/env python3
"""
LeBonCoin Scraper Orchestrator

This script orchestrates the scraping of real estate listings from LeBonCoin
and stores them in a Supabase database. It follows a specific workflow:

1. Get cities that need scraping from database
2. For each city/type combination, scrape listings
3. Store new listings in database
4. Link listings to interested users
5. Send completion report via Telegram

Environment variables required:
- VITE_SUPABASE_URL
- VITE_SUPABASE_ANON_KEY  
- TELEGRAM_BOT_TOKEN
- TELEGRAM_USER_ID
"""

import time
import traceback
from datetime import datetime
from typing import Dict, List

from db import DatabaseManager
from scraper import LeboncoinScraper
from telegram import TelegramNotifier

class ScrapingOrchestrator:
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = LeboncoinScraper()
        self.telegram = TelegramNotifier()
        
        # Statistics counters
        self.stats = {
            'cities_success': 0,
            'cities_errors': 0,
            'cities_warnings': 0,
            'total_new_listings': 0,
            'total_duplicates': 0,
            'start_time': None,
            'total_cities': 0
        }
    
    def run(self):
        """Main orchestration method following the flowchart logic."""
        print("🏁 Starting LeBonCoin scraping orchestration...")
        self.stats['start_time'] = datetime.now()
        
        try:
            # Step 1: Get cities that need scraping
            cities_to_scrape = self.db.get_cities_to_scrape(scrape_interval_hours=24)
            
            if not cities_to_scrape:
                print("📨 No cities require scraping")
                self.telegram.send_no_cities_message()
                return
            
            self.stats['total_cities'] = len(cities_to_scrape)
            print(f"📋 Found {len(cities_to_scrape)} cities to scrape")
            
            # Step 2: Process each city
            for city_data in cities_to_scrape:
                self._process_city(city_data)
                
                # Rate limiting between cities
                time.sleep(5)
            
            # Step 3: Send final report
            self._send_final_report()
            
        except Exception as e:
            print(f"❌ Critical error in orchestration: {e}")
            traceback.print_exc()
            self._send_error_report(str(e))
    
    def _process_city(self, city_data: Dict):
        """Process a single city for scraping."""
        city_id = city_data['city_id']
        city_name = city_data['city_name']
        postal_code = city_data['postal_code']
        lat = city_data['latitude']
        lng = city_data['longitude']
        
        print(f"\n🏙️ Processing {city_name} ({postal_code})")
        
        # Check what types need scraping
        needs_sale = city_data['needs_sale_scrape']
        needs_rent = city_data['needs_rent_scrape']
        
        city_success = True
        city_new_listings = 0
        city_duplicates = 0
        
        try:
            # Scrape sales if needed
            if needs_sale:
                print(f"  🏠 Scraping sales...")
                new_listings, duplicates, _ = self.scraper.scrape_city_listings(
                    city_name=city_name,
                    lat=lat,
                    lng=lng,
                    city_id=city_id,
                    listing_type='sale',
                    max_listings=100
                )
                
                # Store listings in database
                stored_count, duplicate_count = self._store_listings(new_listings, city_id, 'sale')
                city_new_listings += stored_count
                city_duplicates += duplicate_count + duplicates
                
                # Update timestamp
                self.db.update_city_scrape_timestamp(city_id, 'sale')
                
                print(f"    ✅ Found {len(new_listings)} sales listings, stored {stored_count}")
            
            # Scrape rentals if needed
            if needs_rent:
                print(f"  🏢 Scraping rentals...")
                new_listings, duplicates, _ = self.scraper.scrape_city_listings(
                    city_name=city_name,
                    lat=lat,
                    lng=lng,
                    city_id=city_id,
                    listing_type='rental',
                    max_listings=100
                )
                
                # Store listings in database
                stored_count, duplicate_count = self._store_listings(new_listings, city_id, 'rental')
                city_new_listings += stored_count
                city_duplicates += duplicate_count + duplicates
                
                # Update timestamp
                self.db.update_city_scrape_timestamp(city_id, 'rent')
                
                print(f"    ✅ Found {len(new_listings)} rental listings, stored {stored_count}")
            
            # Update statistics
            if city_new_listings > 0:
                self.stats['cities_success'] += 1
                self.stats['total_new_listings'] += city_new_listings
                self.stats['total_duplicates'] += city_duplicates
            elif city_new_listings == 0 and (needs_sale or needs_rent):
                self.stats['cities_warnings'] += 1
                print(f"    ⚠️ No new listings found")
            
        except Exception as e:
            print(f"    ❌ Error processing {city_name}: {e}")
            self.stats['cities_errors'] += 1
            city_success = False
    
    def _store_listings(self, listings: List[Dict], city_id: int, listing_type: str) -> tuple[int, int]:
        """
        Store listings in database using batched approach.
        Returns (stored_count, duplicate_count)
        """
        if not listings:
            return 0, 0
        
        print(f"    📦 Processing {len(listings)} listings in batch...")
        
        # Use the new batched insert method
        stored_count, duplicate_count = self.db.insert_listings_batch(listings, city_id, listing_type)
        
        return stored_count, duplicate_count
    
    def _send_final_report(self):
        """Send the final scraping report via Telegram."""
        if not self.stats['start_time']:
            return
        
        # Calculate duration
        end_time = datetime.now()
        duration = end_time - self.stats['start_time']
        duration_minutes = int(duration.total_seconds() // 60)
        duration_seconds = int(duration.total_seconds() % 60)
        
        # Prepare report data
        report_data = {
            'cities_success': self.stats['cities_success'],
            'cities_errors': self.stats['cities_errors'],
            'cities_warnings': self.stats['cities_warnings'],
            'total_new_listings': self.stats['total_new_listings'],
            'total_duplicates': self.stats['total_duplicates'],
            'duration_minutes': duration_minutes,
            'duration_seconds': duration_seconds,
            'total_cities': self.stats['total_cities'],
            'finished_at': end_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Send report
        success = self.telegram.send_scraping_report(report_data)
        
        if success:
            print(f"\n📨 Final report sent successfully")
        else:
            print(f"\n❌ Failed to send final report")
        
        # Print summary to console
        print(f"\n🏆 SCRAPING COMPLETED")
        print(f"─────────────────────")
        print(f"✅ Successful cities: {report_data['cities_success']}/{report_data['total_cities']}")
        print(f"❌ Errors: {report_data['cities_errors']} cities")
        print(f"⚠️ Warnings: {report_data['cities_warnings']} cities (0 listings)")
        print(f"⏱️ Duration: {duration_minutes}min {duration_seconds}s")
        print(f"📊 New listings: {report_data['total_new_listings']}")
        print(f"🔄 Duplicates avoided: {report_data['total_duplicates']}")
        print(f"🗓️ Finished: {report_data['finished_at']}")
    
    def _send_error_report(self, error_message: str):
        """Send error report via Telegram."""
        message = f"❌ <b>SCRAPING FAILED</b>\n\nError: {error_message}"
        self.telegram.send_message(message)

def main():
    """Main entry point."""
    try:
        orchestrator = ScrapingOrchestrator()
        orchestrator.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        # Try to send error notification
        try:
            telegram = TelegramNotifier()
            telegram.send_message(f"❌ <b>FATAL ERROR</b>\n\n{str(e)}")
        except:
            pass

if __name__ == "__main__":
    main() 