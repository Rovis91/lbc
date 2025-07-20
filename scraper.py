import time
import lbc
from typing import List, Dict, Optional, Tuple
from datetime import datetime

class LeboncoinScraper:
    def __init__(self):
        self.client = lbc.Client()
    
    def build_search_url(self, city: str, lat: float, lng: float, category: str) -> str:
        """
        Build a Leboncoin search URL based on city coordinates and category.
        
        Args:
            city: City name
            lat: Latitude
            lng: Longitude  
            category: "9" for sales, "10" for rentals
        """
        # Build location string: City__lat_lng_radius
        location_str = f"{city}__{lat}_{lng}_10000"
        
        # Build URL with required parameters
        url = (
            f"https://www.leboncoin.fr/recherche?"
            f"category={category}&"
            f"locations={location_str}&"
            f"owner_type=private&"
            f"sort=published_at_desc"
        )
        
        return url
    
    def extract_listing_data(self, ad, listing_type: str, city_id: int) -> Dict:
        """Extract and format listing data from LBC ad object."""
        # Extract basic attributes
        attributes = {}
        for attr in ad.attributes:
            if attr.key and attr.value:
                attributes[attr.key] = {
                    'key_label': attr.key_label,
                    'value': attr.value,
                    'value_label': attr.value_label
                }
        
        # Extract property details from attributes
        property_type = attributes.get('real_estate_type', {}).get('value_label', 'other')
        surface_area = attributes.get('square', {}).get('value')
        rooms = attributes.get('rooms', {}).get('value')
        bedrooms = attributes.get('bedrooms', {}).get('value')
        bathrooms = attributes.get('bathrooms', {}).get('value')
        floor_number = attributes.get('floor', {}).get('value')
        building_year = attributes.get('construction_year', {}).get('value')
        property_condition = attributes.get('condition', {}).get('value_label')
        energy_rating = attributes.get('energy_rating', {}).get('value_label')
        heating_type = attributes.get('heating_type', {}).get('value_label')
        
        # Rental-specific fields
        furnished = None
        monthly_charges = None
        security_deposit = None
        charges_included = None
        rent_excluding_charges = None
        
        if listing_type == 'rental':
            furnished = attributes.get('furnished', {}).get('value_label') == 'Meublé'
            monthly_charges = attributes.get('charges', {}).get('value')
            security_deposit = attributes.get('deposit', {}).get('value')
            charges_included = attributes.get('charges_included', {}).get('value_label') == 'Charges comprises'
            rent_excluding_charges = attributes.get('rent_excluding_charges', {}).get('value')
        
        return {
            'id': ad.id,
            'type': listing_type,
            'title': ad.subject,
            'price': ad.price,
            'url': ad.url,
            'first_publication_date': ad.first_publication_date,
            'description': ad.body,
            'images': ad.images or [],
            'city_id': city_id,
            
            # Property details
            'property_type': self._map_property_type(property_type),
            'surface_area': self._parse_int(surface_area),
            'rooms': self._parse_int(rooms),
            'bedrooms': self._parse_int(bedrooms),
            'bathrooms': self._parse_int(bathrooms),
            'floor_number': self._parse_int(floor_number),
            'building_year': self._parse_int(building_year),
            'property_condition': self._map_condition(property_condition),
            'energy_rating': self._map_energy_rating(energy_rating),
            'heating_type': self._map_heating_type(heating_type),
            
            # Rental-specific fields
            'furnished': furnished,
            'monthly_charges': self._parse_float(monthly_charges),
            'security_deposit': self._parse_float(security_deposit),
            'charges_included': charges_included,
            'rent_excluding_charges': self._parse_float(rent_excluding_charges),
            
            # Additional fields
            'elevator': attributes.get('elevator', {}).get('value_label') == 'Oui',
            'parking_spaces': self._parse_int(attributes.get('parking', {}).get('value')),
            'land_plot_surface': self._parse_float(attributes.get('land_plot_surface', {}).get('value')),
            
            # Seller information (if available)
            'seller_first_name': None,  # Would need to fetch user details
            'seller_last_name': None,
            'seller_phone': None,
            'seller_email': None,
            'seller_description': None,
            'seller_profile_picture_url': None,
            'seller_rating_score': None,
            'seller_rating_count': None,
        }
    
    def _map_property_type(self, property_type: str) -> str:
        """Map LBC property types to our enum values."""
        mapping = {
            'Appartement': 'apartment',
            'Maison': 'house',
            'Terrain': 'land',
            'Local commercial': 'commercial',
            'Bureau': 'commercial'
        }
        return mapping.get(property_type, 'other')
    
    def _map_condition(self, condition: str) -> str:
        """Map LBC condition to our enum values."""
        mapping = {
            'Neuf': 'new',
            'Bon état': 'good',
            'À rénover': 'to_be_renovated',
            'À restaurer': 'to_be_restored',
            'À démolir': 'to_be_demolished'
        }
        return mapping.get(condition, 'good')
    
    def _map_energy_rating(self, rating: str) -> str:
        """Map energy rating."""
        if rating and rating.upper() in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            return rating.upper()
        return None
    
    def _map_heating_type(self, heating: str) -> str:
        """Map heating type."""
        mapping = {
            'Électrique': 'electric',
            'Gaz': 'gas',
            'Fioul': 'oil',
            'Bois': 'wood',
            'Solaire': 'solar',
            'Pompe à chaleur': 'heat_pump'
        }
        return mapping.get(heating, 'other')
    
    def _parse_int(self, value) -> Optional[int]:
        """Safely parse integer values."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_float(self, value) -> Optional[float]:
        """Safely parse float values."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def scrape_city_listings(
        self, 
        city_name: str, 
        lat: float, 
        lng: float, 
        city_id: int,
        listing_type: str,
        max_listings: int = 100
    ) -> Tuple[List[Dict], int, int]:
        """
        Scrape listings for a specific city and listing type.
        
        Returns:
            Tuple of (new_listings, duplicates_found, total_processed)
        """
        new_listings = []
        duplicates_found = 0
        total_processed = 0
        
        # Map listing type to category
        category = "10" if listing_type == "rental" else "9"
        
        # Build search URL
        url = self.build_search_url(city_name, lat, lng, category)
        
        page = 1
        max_pages = 10  # Safety limit
        
        while len(new_listings) < max_listings and page <= max_pages:
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
                    if len(new_listings) >= max_listings:
                        break
                    
                    total_processed += 1
                    
                    # Extract listing data
                    listing_data = self.extract_listing_data(ad, listing_type, city_id)
                    new_listings.append(listing_data)
                
                # Check if we've reached the end
                if page >= result.max_pages:
                    break
                
                page += 1
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"    Error on page {page}: {str(e)}")
                break
        
        return new_listings, duplicates_found, total_processed 