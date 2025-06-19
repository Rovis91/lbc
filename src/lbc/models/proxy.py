from dataclasses import dataclass
from typing import Union, Optional

@dataclass
class Proxy:
    host: str
    port: Union[str, int]
    username: Optional[str] = None
    password: Optional[str] = None

    @property
    def url(self):
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        else:
            return f"http://{self.host}:{self.port}"