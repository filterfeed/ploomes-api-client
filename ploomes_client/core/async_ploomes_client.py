import time
import math
import httpx
import logging
import asyncio
from threading import Lock
from urllib.parse import urlencode

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
MAX_RETRIES = 5
MAX_NEXT_LINKS = 10  # Maximum number of next links to follow to prevent infinite loops


class PloomesClient:
    """
    An asynchronous client to interact with the Ploomes API using httpx for HTTP requests.
    """

    _lock = Lock()
    _shared_rate_limit_tokens = 120
    _shared_last_request_time = time.time()
    _token_refresh_rate = 2
    _shared_exponential_delay = 1
    _shared_hold_requests = False
    _shared_hold_until = 0
    _shared_hold_retries = 0
    _shared_last_429_time = 0
    MAX_RATE_LIMIT_TOKENS = 120

    def __init__(
        self,
        api_key,
        rate_limit_tokens=120,
        token_refresh_rate=2,
        max_retries=MAX_RETRIES,
    ):
        self.base_url = "https://public-api2.ploomes.com"
        self.api_key = api_key
        self.client = httpx.AsyncClient(headers={"User-Key": api_key})
        self.max_retries = max_retries
        if rate_limit_tokens is not None:
            self.__class__._shared_rate_limit_tokens = rate_limit_tokens
        if token_refresh_rate is not None:
            self.__class__._token_refresh_rate = token_refresh_rate

    async def _replenish_tokens(self):
        elapsed_time = time.time() - self._shared_last_request_time
        tokens_to_replenish = math.floor(elapsed_time * self._token_refresh_rate)
        self._shared_rate_limit_tokens = min(
            self._shared_rate_limit_tokens + tokens_to_replenish,
            self.MAX_RATE_LIMIT_TOKENS,
        )

    async def _hold_requests(self, delay):
        self._shared_hold_requests = True
        self._shared_hold_until = time.time() + delay
        logger.info("Holding all requests for %d seconds", delay)
        await asyncio.sleep(delay)

    async def _check_hold_status(self):
        if self._shared_hold_requests and time.time() > self._shared_hold_until:
            self._shared_hold_requests = False
            self._shared_hold_retries = 0
            logger.info("Resuming requests")

    async def _handle_too_many_requests(self):
        if (
            self._shared_hold_retries >= 3
            and time.time() - self._shared_last_429_time < 60
        ):
            delay = min(self._shared_exponential_delay * 2, 60)
        else:
            delay = self._shared_exponential_delay

        self._shared_last_429_time = time.time()
        self._shared_hold_retries += 1
        await self._hold_requests(delay)

    async def _wait_for_token(self):
        with self._lock:
            await self._check_hold_status()
            if self._shared_hold_requests:
                await self._hold_requests(self._shared_hold_until - time.time())
            await self._replenish_tokens()
            while self._shared_rate_limit_tokens < 1:
                sleep_time = 1 / self._token_refresh_rate
                logger.warning(
                    "No tokens available, waiting for %f seconds", sleep_time
                )
                await asyncio.sleep(sleep_time)
                await self._replenish_tokens()
            self._shared_last_request_time = time.time()
            self._shared_rate_limit_tokens -= 1

    async def _retry_request(self, method: str, url: str, **kwargs):
        retries = self.max_retries
        while retries > 0:
            await self._wait_for_token()
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                self._shared_exponential_delay = 1
                return response.json()
            except httpx.HTTPStatusError:
                if response.status_code == 401:
                    return {"@odata.context": None, "@odata.value": []}
                retries -= 1
                if response.status_code == 429:
                    await self._handle_too_many_requests()
                await asyncio.sleep(min(self._shared_exponential_delay * 2, 60))
            except httpx.RequestError:
                retries -= 1
                await asyncio.sleep(min(self._shared_exponential_delay * 2, 60))
        raise httpx.HTTPStatusError(
            "Maximum retries reached for request to {}".format(url)
        )

    async def request(
        self, method: str, path: str, filters=None, payload=None, files=None, **kwargs
    ):
        """
        Makes an asynchronous HTTP request to the specified path and handles pagination via next links.

        Args:
            method (str): HTTP method (e.g., GET, POST).
            path (str): The path to request.
            filters (dict, optional): Query parameters to add to the request.
            payload (dict, optional): JSON payload for POST, PUT, PATCH methods.
            files (dict, optional): Files to send with the request.
            **kwargs: Additional arguments passed to the HTTP client.

        Returns:
            dict: Aggregated response from all pages, including context and values.
        """
        query_params = "?" + urlencode(filters) if filters else ""
        url = self.base_url + path + query_params

        response_values = []
        next_link_count = 0
        while url and next_link_count < MAX_NEXT_LINKS:
            await self._wait_for_token()
            result = await self._retry_request(
                method, url, headers=None, json=payload, files=files, **kwargs
            )
            if "value" in result:
                response_values.extend(result["value"])
            url = result.get("@odata.nextLink")
            next_link_count += 1

        return {
            "@odata.context": result.get("@odata.context"),
            "value": response_values,
        }
