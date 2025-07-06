from .models import Proxy

from curl_cffi import requests, BrowserTypeLiteral
from typing import Optional
import random

class Session:
    def __init__(self, proxy: Optional[Proxy] = None, impersonate: BrowserTypeLiteral = None):
        self._session = self._init_session(proxy=proxy, impersonate=impersonate)
        self._proxy = proxy
        self._impersonate = impersonate

    def _init_session(self, proxy: Optional[Proxy] = None, impersonate: BrowserTypeLiteral = None) -> requests.Session:
        """
        Initializes an HTTP session with optional proxy configuration and browser impersonation.

        If no `impersonate` value is provided, a random browser type will be selected among common options.

        Args:
            proxy (Optional[Proxy], optional): Proxy configuration to use for the session. If provided, it will be applied to both HTTP and HTTPS traffic. Defaults to None.
            impersonate (BrowserTypeLiteral, optional): Browser type to impersonate for requests (e.g., "firefox", "chrome", "edge", "safari", "safari_ios", "chrome_android"). If None, a random browser type will be chosen.            
        
        Returns:
            requests.Session: A configured session instance ready to send requests.
        """
        if impersonate == None: # Pick a random browser client
            impersonate: BrowserTypeLiteral = random.choice(
                [
                    "chrome",
                    "edge",
                    "safari",
                    "safari_ios",
                    "chrome_android",
                    "firefox"
                ]
            )

        session = requests.Session(
            impersonate=impersonate,
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

        session.get("https://www.leboncoin.fr/") # Init cookies

        return session

    @property
    def session(self) -> requests.Session:
        return self._session
    
    @session.setter
    def session(self, value: requests.Session):
        if isinstance(value, requests.Session):
            self._session = value
        else:
            raise TypeError("Session must be an instance of the curl_cffi.requests.Session")
    
    @property
    def proxy(self) -> Proxy:
        return self._proxy
    
    @proxy.setter
    def proxy(self, value: Proxy):
        if isinstance(value, Proxy):
            self._session.proxies = {
                "http": value.url,
                "https": value.url
            }
        else:
            raise TypeError("Proxy must be an instance of the Proxy class")
