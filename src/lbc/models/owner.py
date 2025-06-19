from dataclasses import dataclass

@dataclass
class Owner:
    store_id: str
    user_id: str
    type: str
    name: str
    no_salesmen: bool