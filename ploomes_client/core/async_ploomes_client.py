import time
import math
import httpx
import logging
import asyncio
from urllib.parse import urlencode
from asyncio import Lock
from ploomes_client.core.response import Response

logger = logging.getLogger(__name__)
MAX_RETRIES = 5
MAX_NEXT_LINKS = 10  # Maximum number of next links to follow to prevent infinite loops


class RateLimiter:
    """
    A rate limiter class implementing a token bucket algorithm to control the rate of API requests.
    """

    def __init__(self, tokens, refresh_rate):
        self._lock = Lock()
        self.tokens = tokens
        self.refresh_rate = refresh_rate  # Tokens replenished per second
        self.max_tokens = tokens
        self.last_token_replenish_time = time.time()
        self.exponential_delay = 1
        self.hold_requests_flag = False
        self.hold_until = 0
        self.hold_retries = 0
        self.last_429_time = 0

    async def wait_for_token(self):
        async with self._lock:
            await self.check_hold_status()
            if self.hold_requests_flag:
                await self.hold_requests(self.hold_until - time.time())
            await self.replenish_tokens()
            while self.tokens < 1:
                sleep_time = max(1 / self.refresh_rate, 0.1)
                logger.warning(
                    "No tokens available, waiting for %f seconds", sleep_time
                )
                await asyncio.sleep(sleep_time)
                await self.replenish_tokens()
            self.tokens -= 1
            logger.debug(f"Token consumed, remaining tokens: {self.tokens}")

    async def replenish_tokens(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_token_replenish_time
        tokens_to_replenish = math.floor(elapsed_time * self.refresh_rate)
        if tokens_to_replenish > 0:
            self.tokens = min(self.tokens + tokens_to_replenish, self.max_tokens)
            self.last_token_replenish_time = current_time
            logger.debug(
                f"Tokens replenished: {tokens_to_replenish}, Total tokens: {self.tokens}"
            )

    async def hold_requests(self, delay):
        self.hold_requests_flag = True
        self.hold_until = time.time() + delay
        logger.info("Holding all requests for %d seconds", delay)
        await asyncio.sleep(delay)

    async def check_hold_status(self):
        if self.hold_requests_flag and time.time() > self.hold_until:
            self.hold_requests_flag = False
            self.hold_retries = 0
            self.exponential_delay = 1
            logger.info("Resuming requests")

    async def handle_too_many_requests(self):
        self.exponential_delay = min(self.exponential_delay * 2, 60)
        delay = self.exponential_delay
        self.last_429_time = time.time()
        self.hold_retries += 1
        await self.hold_requests(delay)


class APloomesClient:
    """
    An asynchronous client to interact with the Ploomes API using httpx for HTTP requests.
    """

    rate_limiter = RateLimiter(tokens=120, refresh_rate=2)

    def __init__(
        self,
        api_key,
        max_retries=MAX_RETRIES,
    ):
        self.base_url = "https://public-api2.ploomes.com"
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            headers={"User-Key": api_key}, timeout=httpx.Timeout(10.0)
        )
        self.max_retries = max_retries

    async def a_wait_for_token(self):
        await self.__class__.rate_limiter.wait_for_token()

    async def a_retry_request(self, method: str, url: str, **kwargs):
        retries = self.max_retries
        last_exception = None
        while retries > 0:
            await self.a_wait_for_token()
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                self.__class__.rate_limiter.exponential_delay = 1
                return response.json()
            except httpx.HTTPStatusError as exc:
                response = exc.response
                if response.status_code == 401:
                    logger.error("Unauthorized access. Check your API key.")
                    return {"@odata.context": None, "value": []}
                retries -= 1
                last_exception = exc
                if response.status_code == 429:
                    logger.warning("Received 429 Too Many Requests")
                    await self.__class__.rate_limiter.handle_too_many_requests()
                else:
                    logger.error(f"HTTP error {response.status_code}: {response.text}")
                    await asyncio.sleep(self.__class__.rate_limiter.exponential_delay)
            except httpx.RequestError as exc:
                retries -= 1
                last_exception = exc
                logger.error(f"Request error: {exc}")
                await asyncio.sleep(self.__class__.rate_limiter.exponential_delay)
            self.__class__.rate_limiter.exponential_delay = min(
                self.__class__.rate_limiter.exponential_delay * 2, 60
            )
        raise Exception(
            f"Maximum retries reached for request to {url}"
        ) from last_exception

    async def arequest(
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
            Response: Aggregated response from all pages, including context and values.
        """
        query_params = "?" + urlencode(filters) if filters else ""
        url = self.base_url + path + query_params

        response_values = []
        next_link_count = 0
        result = None
        while url and next_link_count < MAX_NEXT_LINKS:
            request_kwargs = {}
            if payload is not None:
                request_kwargs["json"] = payload
            if files is not None:
                request_kwargs["files"] = files
            request_kwargs.update(kwargs)
            result = await self.a_retry_request(method, url, **request_kwargs)
            if "value" in result:
                response_values.extend(result["value"])
            url = result.get("@odata.nextLink")
            next_link_count += 1

        return Response(
            {"@odata.context": result.get("@odata.context"), "value": response_values}
        )
