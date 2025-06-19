from .models import Category, AdType, OwnerType, Sort, Region, Department, City
from .exceptions import InvalidValue

from typing import Optional, Union, List

def build_search_payload_with_args(
    text: Optional[str] = None,
    category: Category = Category.TOUTES_CATEGORIES,
    sort: Sort = Sort.RELEVANCE,
    locations: Optional[Union[List[Union[Region, Department, City]], Union[Region, Department, City]]] = None, 
    limit: int = 35, 
    limit_alu: int = 3, 
    page: int = 1, 
    ad_type: AdType = AdType.OFFER,
    owner_type: Optional[OwnerType] = None,
    search_in_title_only: bool = False,
    **kwargs
) -> dict:
    payload = {
        "filters": {
            "category": {
                "id": category.value
            },
            "enums": {
                "ad_type": [
                    ad_type.value
                ]
            },
            "keywords": {
                "text": text
            },
            "location": {}
        },
        "limit": limit,
        "limit_alu": limit_alu,
        "offset": limit * (page - 1),
        "disable_total": True,
        "extend": True,
        "listing_source": "direct-search" if page == 1 else "pagination"
    }   

    # Text
    if text:
        payload["filters"]["keywords"] = {
            "text": text
        }  

    # Owner Type
    if owner_type:
        payload["owner_type"] = owner_type.value

    # Sort
    sort_by, sort_order = sort.value
    payload["sort_by"] = sort_by
    if sort_order:
        payload["sort_order"] = sort_order
        
    # Location
    if locations and not isinstance(locations, list):
        locations = [locations]
        
    if locations:
        payload["filters"]["location"] = {
            "locations": []
        }
        for location in locations:
            match location:
                case Region():
                    payload["filters"]["location"]["locations"].append(
                        {
                            "locationType": "region",
                            "region_id": location.value[0]
                        }
                    )
                case Department():
                    payload["filters"]["location"]["locations"].append(
                        {
                            "locationType": "department",
                            "region_id": location.value[0],
                            "department_id": location.value[2]
                        }
                    )
                case City():
                    payload["filters"]["location"]["locations"].append(
                        {
                            "area": {
                                "lat": location.lat,
                                "lng": location.lng,
                                "radius": location.radius
                            },
                            "city": location.city,
                            "label": f"{location.city} (toute la ville)" if location.city else None,
                            "locationType": "city"
                        }
                    )
                case _:
                    raise InvalidValue("The provided location is invalid. It must be an instance of Region, Department, or City.")

    # Search in title only
    if text:
        if search_in_title_only:
            payload["filters"]["keywords"]["type"] = "subject"  

    if kwargs:
        for key, value in kwargs.items():
            if not isinstance(value, (list, tuple)):
                raise InvalidValue(f"The value of '{key}' must be a list or a tuple.")  
            # Range
            if all(isinstance(x, int) for x in value):
                if len(value) == 1:
                    raise InvalidValue(f"The value of '{key}' must be a list or tuple with at least two elements.")

                if not "ranges" in payload["filters"]:
                    payload["filters"]["ranges"] = {}

                payload["filters"]["ranges"][key] = {
                    "min": value[0],
                    "max": value[1]
                }   
            # Enum
            elif all(isinstance(x, str) for x in value):
                payload["filters"]["enums"]["key"] = value
            else:
                raise InvalidValue(f"The value of '{key}' must be a list or tuple containing only integers or only strings.")

    return payload