import time
import math
import requests
import logging
from urllib.parse import urlencode
from requests.exceptions import RequestException
from ploomes_client.sessions.session_manager import SessionManager
from ploomes_client.core.response import Response
from threading import Lock

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
MAX_RETRIES = 5
MAX_NEXT_LINKS = 10  # Maximum number of next links to follow to prevent infinite loops


class PloomesClient:
    """
    A client to interact with the Ploomes API.

    This class provides methods to make HTTP requests to the Ploomes service, handling authentication via an API key,
    managing sessions, and implementing a rate-limiting mechanism.

    Attributes:
        base_url (str): The base URL for the Ploomes API.
        api_key (str): The API key used for authentication.
        headers (dict): The default headers used in all requests.
        session_manager (SessionManager): Manages the HTTP session for the client.
    """

    _lock = (
        Lock()
    )  # Lock to ensure thread-safety when modifying shared rate-limiting variables
    _shared_rate_limit_tokens = (
        120  # The shared number of tokens available for rate limiting
    )
    _shared_last_request_time = time.time()  # Timestamp of the last request made
    _token_refresh_rate = 2  # Number of tokens replenished per second; 2 tokens per second results in 120 tokens per minute
    _shared_exponential_delay = 1  # Delay factor for exponential backoff
    _shared_hold_requests = (
        False  # Flag to indicate if requests should be temporarily held
    )
    _shared_hold_until = 0  # Timestamp until which requests are held
    _shared_hold_retries = 0  # Counter for hold retries
    _shared_last_429_time = 0  # Timestamp of the last 429 response received
    MAX_RATE_LIMIT_TOKENS = 120  # Maximum number of tokens allowed to prevent excessive accumulation during idle times

    def __init__(self, api_key, rate_limit_tokens=120, token_refresh_rate=2) -> None:
        """
        Initializes the PloomesClient with the given API key, rate limit tokens, and token refresh rate.

        Args:
            api_key (str): The API key for authentication.
            rate_limit_tokens (int): The number of tokens for rate limiting (default: 120).
            token_refresh_rate (int): The number of tokens to be replenished per second (default: 2).
        """
        self.base_url = "https://public-api2.ploomes.com"
        self.api_key = api_key
        self.headers = {"User-Key": api_key, "Content-Type": "application/json"}
        self.session_manager = SessionManager(self.headers)
        if rate_limit_tokens is not None:
            self.__class__._shared_rate_limit_tokens = rate_limit_tokens
        if token_refresh_rate is not None:
            self.__class__._token_refresh_rate = token_refresh_rate

    def _replenish_tokens(self):
        """
        Replenishes rate-limiting tokens based on the elapsed time since the last request.

        This method calculates the number of tokens to be replenished and ensures that the total does not exceed the maximum allowed.
        """
        elapsed_time = (
            time.time() - self._shared_last_request_time
        )  # Time since the last request
        tokens_to_replenish = math.floor(
            elapsed_time * self._token_refresh_rate
        )  # Number of tokens to replenish
        # Ensure that tokens do not exceed the maximum limit
        self._shared_rate_limit_tokens = min(
            self._shared_rate_limit_tokens + tokens_to_replenish,
            self.MAX_RATE_LIMIT_TOKENS,
        )

    def _hold_requests(self, delay):
        """
        Holds all requests for a specified delay period.

        Args:
            delay (int): The number of seconds to hold requests.
        """
        self._shared_hold_requests = True  # Set the flag to hold requests
        self._shared_hold_until = (
            time.time() + delay
        )  # Calculate the timestamp until which requests are held
        logger.warning("Holding all requests for %d seconds", delay)
        time.sleep(delay)  # Wait for the specified delay

    def _check_hold_status(self):
        """
        Checks the hold status and resumes requests if the hold period has ended.
        """
        if self._shared_hold_requests and time.time() > self._shared_hold_until:
            self._shared_hold_requests = False  # Clear the hold requests flag
            self._shared_hold_retries = 0  # Reset the hold retries counter
            logger.info("Resuming requests")

    def _handle_too_many_requests(self):
        """
        Handles the scenario when too many requests (HTTP status 429) are encountered.

        Implements an exponential backoff strategy, doubling the delay period with each subsequent 429 response, up to a maximum of 60 seconds.
        """
        if (
            self._shared_hold_retries >= 3
            and time.time() - self._shared_last_429_time < 60
        ):
            # Double the delay if there are more than 3 retries within 60 seconds, up to a maximum of 60 seconds
            delay = min(self._shared_exponential_delay * 2, 60)
            self._shared_exponential_delay = delay
        else:
            # Use the current exponential delay value
            delay = self._shared_exponential_delay

        self._shared_last_429_time = (
            time.time()
        )  # Update the timestamp of the last 429 response
        self._shared_hold_retries += 1  # Increment the hold retries counter
        self._hold_requests(delay)  # Hold requests for the calculated delay period

    def _wait_for_token(self):
        """
        Waits for a rate-limiting token to become available.

        This method replenishes tokens based on the time elapsed since the last request and the token refresh rate.
        If no tokens are available, it waits for a calculated duration based on the token_refresh_rate.
        """
        with self._lock:  # Ensuring thread safety when modifying shared rate-limiting variables
            # Check if requests are currently being held, and resume if the hold period has ended
            self._check_hold_status()

            # If a hold is currently in place, sleep for the remaining hold duration
            if self._shared_hold_requests:
                self._hold_requests(self._shared_hold_until - time.time())

            # Replenish tokens according to the token refresh rate and time since the last request
            self._replenish_tokens()

            # Wait for a token to become available if there are no tokens currently available
            while self._shared_rate_limit_tokens < 1:
                # Compute sleep time based on token refresh rate; sleep_time = 1 / 2 = 0.5 seconds
                sleep_time = 1 / self._token_refresh_rate
                logger.warning(
                    "No tokens available, waiting for %f seconds", sleep_time
                )
                time.sleep(sleep_time)  # Sleep for the calculated duration
                self._replenish_tokens()  # Replenish tokens after waiting

            # Update the last request time and decrement the available tokens by 1
            self._shared_last_request_time = time.time()
            self._shared_rate_limit_tokens -= 1

    def _retry_request(self, method: str, url: str, files=None, **kwargs):
        """
        Retries a request to the specified URL with exponential backoff.

        Args:
            method (str): HTTP method (e.g., GET, POST).
            url (str): The URL to request.
            files (Optional): Files to send with the request.
            **kwargs: Additional arguments passed to the request.

        Returns:
            The JSON response of the request.

        Raises:
            Exception: If the maximum number of retries is reached.
        """
        retries = MAX_RETRIES  # Number of retries allowed
        delay = (
            self._shared_exponential_delay
        ) = 1  # Initial delay for exponential backoff

        while retries > 0:
            self._wait_for_token()  # Wait for a rate-limiting token to become available
            response = None
            try:
                response = self.session_manager.session.request(
                    method, url, files=files, **kwargs
                )
                response.raise_for_status()
                self._shared_exponential_delay = (
                    1  # Reset the exponential delay after a successful request
                )
                return response.json()
            except RequestException as err:
                retries -= 1
                if (
                    response and response.status_code == 429
                ):  # HTTP status code for too many requests
                    self._handle_too_many_requests()  # Handle the 429 status by holding requests
                else:
                    delay = min(
                        delay * 2, 60
                    )  # Exponential backoff for other exceptions, with a maximum delay of 60 seconds
                logger.warning(
                    "Request to %s failed with error: %s. Retries remaining: %d",
                    url,
                    err,
                    retries,
                )
                time.sleep(delay)  # Sleep for the calculated delay period

        raise Exception(
            "Max retries reached"
        )  # Raise an exception if all retries are exhausted

    def request(
        self, method: str, path: str, filters=None, payload=None, files=None, **kwargs
    ):
        """
        Makes a request to the specified path and handles pagination via next links.

        Args:
            method (str): HTTP method (e.g., GET, POST).
            path (str): The path to request.
            files (Optional): Files to send with the request.
            filters (Optional): Query parameters to add to the request.
            **kwargs: Additional arguments passed to the request.

        Returns:
            A list containing the aggregated response from all pages.
        """
        query_params = (
            "?" + urlencode(filters) if filters else ""
        )  # Construct query parameters if filters are provided
        url = self.base_url + path + query_params
        headers = self.headers if not files else {"User-Key": self.api_key}

        response_values = []
        next_link_count = 0
        while (
            url and next_link_count < MAX_NEXT_LINKS
        ):  # Follow next links up to a maximum count to prevent infinite loops
            self._wait_for_token()
            result = self._retry_request(
                method, url, data=payload, files=files, headers=headers, **kwargs
            )
            if result.get("value"):
                response_values += result["value"]  # Aggregate response values
            url = result.get("@odata.nextLink")  # Get the next link for pagination
            next_link_count += 1

        return Response(
            {"@odata.context": result["@odata.context"], "value": response_values}
        )
