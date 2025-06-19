from dataclasses import dataclass

@dataclass
class Location:
    country_id: str
    region_id: str
    region_name: str
    department_id: str
    department_name: str
    city_label: str
    city: str
    zipcode: str
    lat: float
    lng: float
    source: str
    provider: str
    is_shape: bool