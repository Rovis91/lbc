from .session import Session
from .models import Proxy, Search, Category, AdType, OwnerType, Sort, Region, Department, City
from .exceptions import DatadomeError, RequestError
from .utils import build_search_payload_with_args, build_search_payload_with_url

from typing import Optional, List, Union

class Client(Session):
    def __init__(self, proxy: Optional[Proxy] = None):
        super().__init__(proxy=proxy)

    def _fetch(self, method: str, url: str, payload: Optional[dict] = None, timeout: int = 30) -> dict:
        """
        Internal method to send an HTTP request using the configured session.

        Args:
            method (staticmethod): HTTP method to use (e.g., `GET`, `POST`).
            url (str): Full URL of the API endpoint.
            payload (Optional[dict], optional): JSON payload to send with the request. Used for POST/PUT methods. Defaults to None.
            timeout (int, optional): Timeout for the request, in seconds. Defaults to 30.

        Raises:
            DatadomeError: Raised when the request is blocked by Datadome protection (HTTP 403).
            RequestError: Raised for any other non-successful HTTP response.

        Returns:
            dict: Parsed JSON response from the server.
        """
        response = self.session.request(
            method=method,
            url=url, 
            json=payload,
            timeout=timeout
        )
        if response.ok:
            return response.json()
        elif response.status_code == 403:
            if self.proxy:
                raise DatadomeError(f"Access blocked by Datadome: your proxy appears to have a poor reputation, try to change it.")
            else:
                raise DatadomeError(f"Access blocked by Datadome: your activity was flagged as suspicious. Please avoid sending excessive requests.")
        else:
            raise RequestError(f"Request failed with status code {response.status_code}.")

    def search(
        self,
        url: Optional[str] = None,
        text: Optional[str] = None,
        category: Category = Category.TOUTES_CATEGORIES,
        sort: Sort = Sort.RELEVANCE,
        locations: Optional[Union[List[Union[Region, Department, City]], Union[Region, Department, City]]] = None, 
        limit: int = 35, 
        limit_alu: int = 3, 
        page: int = 1, 
        ad_type: AdType = AdType.OFFER,
        owner_type: Optional[OwnerType] = None,
        shippable: Optional[bool] = None,
        search_in_title_only: bool = False,
        **kwargs
    ) -> Search:
        """
        Perform a classified ads search on Leboncoin with the specified criteria.

        You can either:
        - Provide a full `url` from a Leboncoin search to replicate the search directly.
        - Or use the individual parameters (`text`, `category`, `locations`, etc.) to construct a custom search.

        Args:
            url (Optional[str], optional): A full Leboncoin search URL. If provided, all other parameters will be ignored and the search will replicate the results from the URL.            
            text (Optional[str], optional): Search keywords. If None, returns all matching ads without filtering by keyword. Defaults to None.
            category (Category, optional): Category to search in. Defaults to Category.TOUTES_CATEGORIES.
            sort (Sort, optional): Sorting method for results (e.g., relevance, date, price). Defaults to Sort.RELEVANCE.
            locations (Optional[Union[List[Union[Region, Department, City]], Union[Region, Department, City]]], optional): One or multiple locations (region, department, or city) to filter results. Defaults to None.
            limit (int, optional): Maximum number of results to return. Defaults to 35.
            limit_alu (int, optional): Number of ALU (Annonces Lu / similar ads) suggestions to include. Defaults to 3.
            page (int, optional): Page number to retrieve for paginated results. Defaults to 1.
            ad_type (AdType, optional): Type of ad (offer or request). Defaults to AdType.OFFER.
            owner_type (Optional[OwnerType], optional): Filter by seller type (individual, professional, or all). Defaults to None.
            shippable (Optional[bool], optional): If True, only includes ads that offer shipping. Defaults to None.
            search_in_title_only (bool, optional): If True, search will only be performed on ad titles. Defaults to False.
            **kwargs: Additional advanced filters such as price range (`price=(min, max)`), surface area (`square=(min, max)`), property type, and more.

        Returns:
            Search: A `Search` object containing the parsed search results.
        """
        if url:
            payload = build_search_payload_with_url(
                url=url, limit=limit, page=page
            )
        else:
            payload = build_search_payload_with_args(
                text=text, category=category, sort=sort, locations=locations, 
                limit=limit, limit_alu=limit_alu, page=page, ad_type=ad_type,
                owner_type=owner_type, shippable=shippable, search_in_title_only=search_in_title_only, **kwargs
            )

        body = self._fetch(method="POST", url="https://api.leboncoin.fr/finder/search", payload=payload)
        return Search.build(raw=body)
