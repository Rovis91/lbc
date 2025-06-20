from .models import Proxy

from curl_cffi import requests
from typing import Optional

class Session:
    def __init__(self, proxy: Optional[Proxy] = None):
        self._session = self._init_session(proxy=proxy)
        self._proxy = proxy

    def _init_session(self, proxy: Optional[Proxy] = None) -> requests.Session:
        """
        Initializes an HTTP session with optional proxy and browser impersonation.

        Args:
            proxy (Optional[Proxy], optional): Proxy configuration to use for the session. If provided, it will be applied to both HTTP and HTTPS traffic.

        Returns:
            requests.Session: A configured session instance ready to send requests.
        """
        session = requests.Session(
            impersonate="firefox",
        )

        session.headers.update(
            {
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
            }
        )

        if proxy:
            session.proxies = {
                "http": proxy.url,
                "https": proxy.url
            }

        return session

    @property
    def session(self):
        return self._session
    
    @property
    def proxy(self):
        return self._proxy