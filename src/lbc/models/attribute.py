from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Attribute:
    key: str
    key_label: Optional[str]
    value: str
    value_label: str
    values: List[str]
    values_label: Optional[List[str]]
    value_label_reader: Optional[str]
    generic: bool