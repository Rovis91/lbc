from .attribute import Attribute
from .location import Location
from .owner import Owner

from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Ad:
    id: int
    first_publication_date: datetime
    expiration_date: datetime
    index_date: datetime
    status: str
    category_id: str
    category_name: str
    subject: str
    body: str
    brand: str
    ad_type: str
    url: str
    price: float
    images: List[str]
    attributes: List[Attribute]
    location: Location
    owner: Owner
    has_phone: bool

    @property
    def title(self) -> str:
        return self.subject