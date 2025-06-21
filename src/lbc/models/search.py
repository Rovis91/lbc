from .ad import Ad
from .attribute import Attribute
from .location import Location
from .owner import Owner

from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class Search:
    total: int
    total_all: int
    total_pro: int
    total_private: int
    total_active: int
    total_inactive: int
    total_shippable: int
    max_pages: int
    ads: List[Ad]

    @staticmethod
    def build(raw: dict) -> "Search":
        ads: List[Ad] = []

        for raw_ad in raw.get("ads", []):
            attributes: List[Attribute] = []
            for raw_attribute in raw_ad.get("attributes", []):
                attributes.append(
                    Attribute(
                        key=raw_attribute.get("key"),
                        key_label=raw_attribute.get("key_label"),
                        value=raw_attribute.get("value"),
                        value_label=raw_attribute.get("value_label"),
                        values=raw_attribute.get("values"),
                        values_label=raw_attribute.get("values_label"),
                        value_label_reader=raw_attribute.get("value_label_reader"),
                        generic=raw_attribute.get("generic")
                    )
                )
            
            raw_location: dict = raw_ad.get("location", {})
            location = Location(
                country_id=raw_location.get("country_id"),
                region_id=raw_location.get("region_id"),
                region_name=raw_location.get("region_name"),
                department_id=raw_location.get("department_id"),
                department_name=raw_location.get("department_name"),
                city_label=raw_location.get("city_label"),
                city=raw_location.get("city"),
                zipcode=raw_location.get("zipcode"),
                lat=raw_location.get("lat"),
                lng=raw_location.get("lng"),
                source=raw_location.get("source"),
                provider=raw_location.get("provider"),
                is_shape=raw_location.get("is_shape")
            )
            
            raw_owner: dict = raw_ad.get("owner", {})
            owner = Owner(
                store_id=raw_owner.get("store_id"),
                user_id=raw_owner.get("user_id"),
                type=raw_owner.get("type"),
                name=raw_owner.get("name"),
                no_salesmen=raw_owner.get("no_salesmen")
            )

            ads.append(
                Ad(
                    id=raw_ad.get("list_id"),
                    first_publication_date=datetime.strptime(raw_ad.get("first_publication_date"), "%Y-%m-%d %H:%M:%S") if raw_ad.get("first_publication_date") else None,
                    expiration_date=datetime.strptime(raw_ad.get("expiration_date"), "%Y-%m-%d %H:%M:%S") if raw_ad.get("expiration_date") else None,
                    index_date=datetime.strptime(raw_ad.get("index_date"), "%Y-%m-%d %H:%M:%S") if raw_ad.get("index_date") else None,
                    status=raw_ad.get("status"),
                    category_id=raw_ad.get("category_id"),
                    category_name=raw_ad.get("category_name"),
                    subject=raw_ad.get("subject"),
                    body=raw_ad.get("body"),
                    brand=raw_ad.get("brand"),
                    ad_type=raw_ad.get("ad_type"),
                    url=raw_ad.get("url"),
                    price=raw_ad.get("price_cents") / 100 if raw_ad.get("price_cents") else None,
                    images=raw_ad.get("images", {}).get("urls_large"),
                    attributes=attributes,
                    location=location,
                    owner=owner,
                    has_phone=raw_ad.get("has_phone")
                )
            )

        return Search(
            total=raw.get("total"),
            total_all=raw.get("total_all"),
            total_pro=raw.get("total_pro"),
            total_private=raw.get("total_private"),
            total_active=raw.get("total_active"),
            total_inactive=raw.get("total_inactive"),
            total_shippable=raw.get("total_shippable"),
            max_pages=raw.get("max_pages"),
            ads=ads
        )