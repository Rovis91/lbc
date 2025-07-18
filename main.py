import json
import lbc
import time
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CitySearch:
    city: str
    postal_code: str
    search_type: str  # "rental", "sale", or "both"

class LeboncoinScraper:
    def __init__(self):
        self.client = lbc.Client()
        
        # City coordinates mapping
        self.COORDINATES = {
            "75001": {"lat": 48.86, "lng": 2.34},  # Paris
            "63000": {"lat": 45.78, "lng": 3.08},  # Clermont-Ferrand
            "15100": {"lat": 45.03, "lng": 3.10},  # Saint-Flour
        }
    
    def get_city_coordinates(self, postal_code: str) -> Dict[str, float]:
        """Get coordinates for a city by postal code."""
        if postal_code not in self.COORDINATES:
            raise ValueError(f"No coordinates found for postal code {postal_code}")
        return self.COORDINATES[postal_code]
    
    def build_search_url(self, city: str, postal_code: str, category: str) -> str:
        """
        Build a Leboncoin search URL based on city and category.
        
        Args:
            city: City name
            postal_code: Postal code
            category: "9" for sales, "10" for rentals
        """
        coords = self.get_city_coordinates(postal_code)
        
        # Build location string: City__lat_lng_radius
        location_str = f"{city}__{coords['lat']}_{coords['lng']}_10000"
        
        # Build URL with required parameters
        url = (
            f"https://www.leboncoin.fr/recherche?"
            f"category={category}&"
            f"locations={location_str}&"
            f"owner_type=private&"
            f"sort=published_at_desc"
        )
        
        return url
    
    def search_with_pagination(
        self, 
        city: str, 
        postal_code: str, 
        search_type: str, 
        max_listings: int = 50
    ) -> Dict:
        """
        Search for listings with pagination support.
        
        Args:
            city: City name
            postal_code: Postal code
            search_type: "rental", "sale", or "both"
            max_listings: Maximum number of listings to retrieve
        
        Returns:
            Dictionary with search results
        """
        all_listings = []
        total_found = 0
        
        # Determine which categories to search
        categories = []
        if search_type in ["rental", "both"]:
            categories.append(("10", "rental"))
        if search_type in ["sale", "both"]:
            categories.append(("9", "sale"))
        
        for category_id, listing_type in categories:
            print(f"  Searching for {listing_type} listings...")
            
            url = self.build_search_url(city, postal_code, category_id)
            page = 1
            listings_for_type = []
            
            while len(listings_for_type) < max_listings:
                try:
                    # Search with URL-based approach
                    result = self.client.search(
                        url=url,
                        page=page,
                        limit=20  # Leboncoin's default page size
                    )
                    
                    if not result.ads:
                        break  # No more results
                    
                    # Process listings for this page
                    for ad in result.ads:
                        if len(listings_for_type) >= max_listings:
                            break
                        
                        listing = {
                            "id": ad.id,
                            "type": listing_type,
                            "title": ad.subject,
                            "price": ad.price,
                            "url": ad.url,
                            "first_publication_date": ad.first_publication_date,
                            "location": {
                                "city": ad.location.city,
                                "zipcode": ad.location.zipcode,
                                "lat": ad.location.lat,
                                "lng": ad.location.lng,
                                "department_name": ad.location.department_name,
                                "region_name": ad.location.region_name
                            },
                            "images": ad.images,
                            "body": ad.body,
                            "attributes": [
                                {
                                    "key": attr.key,
                                    "key_label": attr.key_label,
                                    "value": attr.value,
                                    "value_label": attr.value_label
                                }
                                for attr in ad.attributes
                            ]
                        }
                        listings_for_type.append(listing)
                    
                    # Check if we've reached the end
                    if page >= result.max_pages:
                        break
                    
                    page += 1
                    
                    # Rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"    Error on page {page}: {str(e)}")
                    break
            
            all_listings.extend(listings_for_type)
            total_found += len(listings_for_type)
            print(f"    Found {len(listings_for_type)} {listing_type} listings")
        
        return {
            "city": city,
            "postal_code": postal_code,
            "search_type": search_type,
            "total_listings": total_found,
            "listings": all_listings
        }
    
    def search_multiple_cities(
        self, 
        cities: List[CitySearch], 
        max_listings_per_city: int = 50
    ) -> List[Dict]:
        """
        Search multiple cities and return results.
        
        Args:
            cities: List of CitySearch objects
            max_listings_per_city: Maximum listings per city
        
        Returns:
            List of search results for each city
        """
        results = []
        
        for city_search in cities:
            print(f"\nSearching {city_search.city} ({city_search.postal_code})")
            print(f"Search type: {city_search.search_type}")
            
            try:
                result = self.search_with_pagination(
                    city=city_search.city,
                    postal_code=city_search.postal_code,
                    search_type=city_search.search_type,
                    max_listings=max_listings_per_city
                )
                
                results.append(result)
                
                # Save individual result
                filename = f"results/{city_search.city.lower().replace(' ', '_')}_{city_search.search_type}.json"
                Path("results").mkdir(exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"  Saved to {filename}")
                
                # Rate limiting between cities
                time.sleep(5)
                
            except Exception as e:
                print(f"  Error searching {city_search.city}: {str(e)}")
                continue
        
        return results

def main():
    """Main function simulating a real use case."""
    
    # Mock input data
    cities = [
        CitySearch("Paris", "75001", "both"),
        CitySearch("Clermont-Ferrand", "63000", "rental"),
        CitySearch("Saint-Flour", "15100", "sale"),
    ]
    
    # Initialize scraper
    scraper = LeboncoinScraper()
    
    # Search all cities
    print("Starting Leboncoin scraper test...")
    print("=" * 50)
    
    results = scraper.search_multiple_cities(
        cities=cities,
        max_listings_per_city=30  # Limit to 30 listings per city
    )
    
    # Summary
    print("\n" + "=" * 50)
    print("SEARCH SUMMARY")
    print("=" * 50)
    
    total_listings = 0
    for result in results:
        print(f"{result['city']} ({result['postal_code']}): {result['total_listings']} listings")
        total_listings += result['total_listings']
    
    print(f"\nTotal listings found: {total_listings}")
    
    # Save combined results
    combined_filename = "results/combined_results.json"
    with open(combined_filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Combined results saved to: {combined_filename}")

if __name__ == "__main__":
    main() 