#!/usr/bin/env python3
"""
Test the database function directly
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def test_function():
    """Test the get_cities_to_scrape function directly."""
    url = os.getenv("VITE_SUPABASE_URL")
    key = os.getenv("VITE_SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return
    
    supabase: Client = create_client(url, key)
    
    print("🧪 Testing get_cities_to_scrape function...")
    
    try:
        # Test with 1 hour interval
        result = supabase.rpc(
            'get_cities_to_scrape',
            {'scrape_interval_hours': 1}
        ).execute()
        
        print(f"✅ Function call successful")
        print(f"📊 Result: {result.data}")
        
        if result.data:
            print(f"🏙️ Found {len(result.data)} cities to scrape:")
            for city in result.data:
                print(f"  - {city['city_name']} ({city['postal_code']})")
                print(f"    Sale: {city['needs_sale_scrape']}, Rent: {city['needs_rent_scrape']}")
        else:
            print("📭 No cities returned")
            
    except Exception as e:
        print(f"❌ Error calling function: {e}")

if __name__ == "__main__":
    test_function() 