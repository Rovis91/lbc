import os
from typing import List, Dict, Optional, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        url = os.getenv("VITE_SUPABASE_URL")
        key = os.getenv("VITE_SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            raise ValueError("Missing Supabase credentials in environment variables")
        
        self.supabase: Client = create_client(url, key)
    
    def get_cities_to_scrape(self, scrape_interval_hours: int = 24) -> List[Dict]:
        """
        Get cities that need scraping based on user preferences and last scrape time.
        Uses the get_cities_to_scrape function from the database.
        """
        try:
            result = self.supabase.rpc(
                'get_cities_to_scrape',
                {'scrape_interval_hours': scrape_interval_hours}
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting cities to scrape: {e}")
            return []
    
    def get_city_id(self, name: str, zipcode: str) -> Optional[int]:
        """Get city ID by name and zipcode."""
        try:
            result = self.supabase.table('cities').select('id').eq('name', name).eq('zipcode', zipcode).execute()
            if result.data:
                return result.data[0]['id']
            return None
        except Exception as e:
            print(f"Error getting city ID for {name} {zipcode}: {e}")
            return None
    
    def insert_listings_batch(self, listings_data: List[Dict], city_id: int, listing_type: str) -> Tuple[int, int]:
        """
        Insert multiple listings in a batch for a specific city and listing type.
        Uses URL-based deduplication to ensure only unique listings are sent to the database.
        Returns (stored_count, duplicate_count)
        """
        if not listings_data:
            return 0, 0
        
        stored_count = 0
        duplicate_count = 0
        failed_listings = []
        
        print(f"    🔍 Validating {len(listings_data)} listings for duplicates...")
        
        # Step 1: Extract all URLs from the batch
        urls = [listing['url'] for listing in listings_data if listing.get('url')]
        
        if not urls:
            print(f"    ⚠️ No valid URLs found in batch")
            return 0, len(listings_data)
        
        # Step 2: Check for existing URLs using the dedicated function
        existing_urls = self._get_existing_urls(urls)
        
        # Step 3: Filter out duplicates and prepare clean listings
        new_listings = []
        for listing in listings_data:
            listing_url = listing.get('url')
            
            if not listing_url:
                duplicate_count += 1
                continue
                
            if listing_url in existing_urls:
                duplicate_count += 1
            else:
                new_listings.append(listing)
        
        print(f"    📊 Found {duplicate_count} duplicates, {len(new_listings)} new listings to process")
        
        if not new_listings:
            return stored_count, duplicate_count
        
        # Step 4: Clean and validate data before batch insert
        cleaned_listings = []
        for listing in new_listings:
            try:
                cleaned_listing = self._clean_listing_data(listing)
                if cleaned_listing:
                    cleaned_listings.append(cleaned_listing)
                else:
                    failed_listings.append(listing)
            except Exception as e:
                print(f"    ⚠️ Error cleaning listing {listing.get('id', 'unknown')}: {e}")
                failed_listings.append(listing)
        
        if not cleaned_listings:
            print(f"    ⚠️ No valid listings after cleaning")
            return stored_count, duplicate_count
        
        print(f"    🧹 Cleaned {len(cleaned_listings)} listings for batch insert")
        
        # Step 5: Perform batch insert
        try:
            result = self.supabase.table('prospection_estates').insert(cleaned_listings).execute()
            stored_count = len(result.data) if result.data else 0
            print(f"    ✅ Batch insert successful: {stored_count} listings stored")
            
            # Link all successful listings to users
            if stored_count > 0:
                self._link_listings_batch(result.data, city_id, listing_type)
                
        except Exception as e:
            print(f"    ❌ Batch insert failed: {e}")
            print(f"    🔄 Falling back to individual inserts...")
            
            # Fallback to individual inserts
            stored_count, individual_failed = self._insert_listings_individual(cleaned_listings, city_id, listing_type)
            failed_listings.extend(individual_failed)
        
        # Handle any listings that failed during cleaning
        if failed_listings:
            print(f"    ⚠️ {len(failed_listings)} listings failed validation and were skipped")
        
        return stored_count, duplicate_count
    
    def _get_existing_urls(self, urls: List[str]) -> set:
        """
        Get existing URLs from the database using the dedicated function.
        Returns a set of existing URLs.
        """
        try:
            # Use the dedicated function for URL validation
            result = self.supabase.rpc('get_existing_urls', {'urls': urls}).execute()
            return {item['existing_url'] for item in result.data} if result.data else set()
        except Exception as e:
            print(f"    ⚠️ Error checking existing URLs: {e}")
            # Fallback to direct query if function fails
            try:
                existing_result = self.supabase.table('prospection_estates').select('url').in_('url', urls).execute()
                return {item['url'] for item in existing_result.data} if existing_result.data else set()
            except Exception as e2:
                print(f"    ❌ Fallback URL check also failed: {e2}")
                return set()
    
    def _clean_listing_data(self, listing_data: Dict) -> Optional[Dict]:
        """
        Clean and validate listing data to match Supabase schema.
        Returns None if the listing should be skipped.
        """
        try:
            # Create a clean copy to avoid modifying the original
            cleaned_data = listing_data.copy()
            
            # Remove the ID field - let Supabase generate UUID
            if 'id' in cleaned_data:
                del cleaned_data['id']
            
            # Ensure required fields are present and valid
            if not cleaned_data.get('price') or cleaned_data['price'] is None:
                return None  # Skip listings without price
            
            if not cleaned_data.get('title'):
                cleaned_data['title'] = 'Sans titre'
            
            if not cleaned_data.get('url'):
                return None  # Skip listings without URL
            
            # Ensure enum values are valid
            if cleaned_data.get('type') not in ['sale', 'rental']:
                cleaned_data['type'] = 'sale'  # Default to sale
            
            if cleaned_data.get('property_type') not in ['apartment', 'house', 'land', 'commercial', 'other']:
                cleaned_data['property_type'] = 'other'
            
            if cleaned_data.get('property_condition') not in ['new', 'good', 'to_be_renovated', 'to_be_restored', 'to_be_demolished']:
                cleaned_data['property_condition'] = 'good'
            
            if cleaned_data.get('energy_rating') not in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
                cleaned_data['energy_rating'] = None
            
            if cleaned_data.get('heating_type') not in ['electric', 'gas', 'oil', 'wood', 'solar', 'heat_pump', 'other']:
                cleaned_data['heating_type'] = 'other'
            
            # Ensure numeric fields are properly formatted
            if cleaned_data.get('price'):
                cleaned_data['price'] = float(cleaned_data['price'])
            
            if cleaned_data.get('surface_area'):
                cleaned_data['surface_area'] = int(cleaned_data['surface_area']) if cleaned_data['surface_area'] else None
            
            if cleaned_data.get('rooms'):
                cleaned_data['rooms'] = int(cleaned_data['rooms']) if cleaned_data['rooms'] else None
            
            if cleaned_data.get('bedrooms'):
                cleaned_data['bedrooms'] = int(cleaned_data['bedrooms']) if cleaned_data['bedrooms'] else None
            
            if cleaned_data.get('bathrooms'):
                cleaned_data['bathrooms'] = int(cleaned_data['bathrooms']) if cleaned_data['bathrooms'] else None
            
            if cleaned_data.get('floor_number'):
                cleaned_data['floor_number'] = int(cleaned_data['floor_number']) if cleaned_data['floor_number'] else None
            
            if cleaned_data.get('building_year'):
                cleaned_data['building_year'] = int(cleaned_data['building_year']) if cleaned_data['building_year'] else None
            
            if cleaned_data.get('monthly_charges'):
                cleaned_data['monthly_charges'] = float(cleaned_data['monthly_charges']) if cleaned_data['monthly_charges'] else None
            
            if cleaned_data.get('security_deposit'):
                cleaned_data['security_deposit'] = float(cleaned_data['security_deposit']) if cleaned_data['security_deposit'] else None
            
            if cleaned_data.get('rent_excluding_charges'):
                cleaned_data['rent_excluding_charges'] = float(cleaned_data['rent_excluding_charges']) if cleaned_data['rent_excluding_charges'] else None
            
            if cleaned_data.get('parking_spaces'):
                cleaned_data['parking_spaces'] = int(cleaned_data['parking_spaces']) if cleaned_data['parking_spaces'] else None
            
            if cleaned_data.get('land_plot_surface'):
                cleaned_data['land_plot_surface'] = float(cleaned_data['land_plot_surface']) if cleaned_data['land_plot_surface'] else None
            
            # Ensure boolean fields are properly formatted
            for bool_field in ['furnished', 'charges_included', 'elevator', 'district_visibility']:
                if bool_field in cleaned_data:
                    cleaned_data[bool_field] = bool(cleaned_data[bool_field]) if cleaned_data[bool_field] is not None else False
            
            # Ensure images is a list
            if not cleaned_data.get('images') or not isinstance(cleaned_data['images'], list):
                cleaned_data['images'] = []
            
            return cleaned_data
            
        except Exception as e:
            print(f"Error cleaning listing data: {e}")
            return None
    
    def _insert_listings_individual(self, listings_data: List[Dict], city_id: int, listing_type: str) -> Tuple[int, List[Dict]]:
        """
        Insert listings one by one as fallback when batch insert fails.
        Returns (stored_count, failed_listings)
        """
        stored_count = 0
        failed_listings = []
        
        print(f"    🔄 Processing {len(listings_data)} listings individually...")
        
        for listing in listings_data:
            try:
                # Insert new listing (duplicates already filtered out)
                result = self.supabase.table('prospection_estates').insert(listing).execute()
                if result.data:
                    stored_count += 1
                    
                    # Link to users
                    self._link_single_listing(result.data[0]['id'], city_id, listing_type)
                else:
                    failed_listings.append(listing)
                    
            except Exception as e:
                print(f"    ❌ Error inserting listing {listing.get('id', 'unknown')}: {e}")
                failed_listings.append(listing)
        
        print(f"    ✅ Individual inserts completed: {stored_count} successful, {len(failed_listings)} failed")
        return stored_count, failed_listings
    
    def _link_listings_batch(self, inserted_listings: List[Dict], city_id: int, listing_type: str):
        """Link multiple listings to users in a batch."""
        if not inserted_listings:
            return
        
        try:
            # Get users who want this type of listing in this city
            scrape_field = 'scrape_sale' if listing_type == 'sale' else 'scrape_rent'
            
            users_result = self.supabase.table('user_cities').select(
                'user_id'
            ).eq('city_id', city_id).eq(scrape_field, True).execute()
            
            if not users_result.data:
                return
            
            # Create user_prospections entries for all listings
            user_prospections = []
            for listing in inserted_listings:
                for user_data in users_result.data:
                    user_prospections.append({
                        'user_id': user_data['user_id'],
                        'prospection_id': listing['id']
                    })
            
            if user_prospections:
                self.supabase.table('user_prospections').insert(user_prospections).execute()
                print(f"      🔗 Linked {len(inserted_listings)} listings to {len(users_result.data)} users")
                
        except Exception as e:
            print(f"Error linking listings batch: {e}")
    
    def _link_single_listing(self, listing_id: int, city_id: int, listing_type: str):
        """Link a single listing to users."""
        try:
            # Get users who want this type of listing in this city
            scrape_field = 'scrape_sale' if listing_type == 'sale' else 'scrape_rent'
            
            users_result = self.supabase.table('user_cities').select(
                'user_id'
            ).eq('city_id', city_id).eq(scrape_field, True).execute()
            
            if not users_result.data:
                return
            
            # Create user_prospections entries
            user_prospections = []
            for user_data in users_result.data:
                user_prospections.append({
                    'user_id': user_data['user_id'],
                    'prospection_id': listing_id
                })
            
            if user_prospections:
                self.supabase.table('user_prospections').insert(user_prospections).execute()
                
        except Exception as e:
            print(f"Error linking listing {listing_id} to users: {e}")
    
    def insert_listing(self, listing_data: Dict) -> bool:
        """
        Insert a single listing (kept for backward compatibility).
        Returns True if successful, False if duplicate or error.
        """
        stored_count, _ = self.insert_listings_batch([listing_data], listing_data.get('city_id', 0), listing_data.get('type', 'sale'))
        return stored_count > 0
    
    def link_listing_to_users(self, listing_id: int, city_id: int, listing_type: str) -> int:
        """
        Link a listing to users (kept for backward compatibility).
        Returns the number of users linked.
        """
        try:
            # Get users who want this type of listing in this city
            scrape_field = 'scrape_sale' if listing_type == 'sale' else 'scrape_rent'
            
            users_result = self.supabase.table('user_cities').select(
                'user_id'
            ).eq('city_id', city_id).eq(scrape_field, True).execute()
            
            if not users_result.data:
                return 0
            
            # Create user_prospections entries
            user_prospections = []
            for user_data in users_result.data:
                user_prospections.append({
                    'user_id': user_data['user_id'],
                    'prospection_id': listing_id
                })
            
            if user_prospections:
                self.supabase.table('user_prospections').insert(user_prospections).execute()
            
            return len(user_prospections)
        except Exception as e:
            print(f"Error linking listing {listing_id} to users: {e}")
            return 0
    
    def update_city_scrape_timestamp(self, city_id: int, listing_type: str):
        """Update the last scrape timestamp for a city."""
        try:
            timestamp_field = f'last_scraped_{listing_type}_at'
            self.supabase.table('cities').update({
                timestamp_field: 'now()'
            }).eq('id', city_id).execute()
        except Exception as e:
            print(f"Error updating scrape timestamp for city {city_id}: {e}")
    
    def get_city_coordinates(self, name: str, zipcode: str) -> Optional[Tuple[float, float]]:
        """Get city coordinates from database."""
        try:
            result = self.supabase.table('cities').select('latitude, longitude').eq('name', name).eq('zipcode', zipcode).execute()
            if result.data:
                data = result.data[0]
                return (data['latitude'], data['longitude'])
            return None
        except Exception as e:
            print(f"Error getting coordinates for {name} {zipcode}: {e}")
            return None 