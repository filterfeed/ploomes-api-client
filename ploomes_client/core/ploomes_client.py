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


#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_user_account(self):
#         r = requests.get(f"{self.host}/Account", headers=self.headers)
#         if r.status_code == 401:
#             return None
#         response = r.json()
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_contact_products(self, filter=None):
#         if filter:
#             filter = f"?$filter={filter}"
#         r = requests.get(f"{self.host}/Contacts@Products{filter}", headers=self.headers)
#         response = r.json().get("value")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def update_contact_product(self, id_, fields):
#         payload = json.dumps(fields)
#         r = requests.patch(
#             f"{self.host}/Contacts@Products({id_})?$expand=OtherProperties",
#             data=payload,
#             headers=self.headers,
#         )
#         response = r.json()
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def post_contact_product(self, fields):
#         payload = json.dumps(fields)
#         r = requests.post(
#             f"{self.host}/Contacts@Products", data=payload, headers=self.headers
#         )
#         response = r.json()
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_products(
#         self,
#         _filter: Optional[str] = None,
#         top: int = 1000,
#         orderby: Optional[str] = None,
#     ) -> List[Dict]:
#         url = f"{self.host}/Products?$expand=OtherProperties"

#         if _filter:
#             url += f"&$filter={_filter}"

#         if top:
#             url += f"&$top={top}"

#         if orderby:
#             url += f"&$orderby={orderby}"
#         response = []
#         while url:
#             r = requests.get(url, headers=self.headers, timeout=5)
#             data = r.json()
#             if data.get("value"):
#                 response += data["value"]
#             url = data.get("@odata.nextLink")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_user_info(self, filter=None):
#         url = f"{self.host}/Users?"
#         if filter:
#             url += f"$filter={filter}"
#         r = requests.get(url, headers=self.headers)
#         response = r.json().get("value")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def create_contact(
#         self,
#         Name,
#         Email,
#         City,
#         State,
#         StreetAddress,
#         Neighborhood,
#         ZipCode,
#         Register,
#         StreetAddressNumber,
#         Phones,
#         OtherProperties,
#         TypeId=0,
#         OriginId=0,
#         CompanyId=4001214,
#     ):
#         """
#         This function creates a contact in a CRM system by sending a POST request to an API endpoint.
#         The function requires 7 mandatory parameters: Name, Neighborhood, ZipCode, Register, StreetAddressNumber, Phones, OtherProperties
#         and 2 optional parameters: TypeId, OriginId.
#         The function also uses a global variable api_key and self.host, which should be defined before calling this function.
#         :param Name: str, the name of the contact
#         :param Neighborhood: str, the neighborhood of the contact
#         :param ZipCode: str, the zip code of the contact
#         :param Register: str, the register of the contact
#         :param StreetAddressNumber: str, the street address number of the contact
#         :param Phones: list of dict, a list of phone numbers for the contact
#         :param OtherProperties: dict, other properties of the contact
#         :param TypeId: int, the type id of the contact. Defaults to 0.
#         :param OriginId: int, the origin id of the contact. Defaults to 0.
#         :param CompanyId: int, the company id of the contact. Defaults to 4001214.
#         :return: dict, the json response from the API
#         """
#         payload = json.dumps(
#             {
#                 "Name": Name,
#                 "Neighborhood": Neighborhood,
#                 "ZipCode": ZipCode,
#                 "Email": Email,
#                 "City": City,
#                 "State": State,
#                 "StreetAddress": StreetAddress,
#                 "Register": Register,
#                 "OriginId": OriginId,
#                 "CompanyId": CompanyId,
#                 "StreetAddressNumber": StreetAddressNumber,
#                 "TypeId": TypeId,
#                 "Phones": Phones,
#                 "OtherProperties": OtherProperties,
#             }
#         )
#         r = requests.post(
#             f"{self.host}/Contacts?$expand=Phones,OtherProperties",
#             data=payload,
#             headers=self.headers,
#         )
#         response = r.json()
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def create_simple_contact(self, payload):
#         """
#         This function creates a contact in a CRM system by sending a POST request to an API endpoint.
#         The function requires 7 mandatory parameters: Name, Neighborhood, ZipCode, Register, StreetAddressNumber, Phones, OtherProperties
#         and 2 optional parameters: TypeId, OriginId.
#         The function also uses a global variable api_key and self.host, which should be defined before calling this function.
#         :param Name: str, the name of the contact
#         :param Neighborhood: str, the neighborhood of the contact
#         :param ZipCode: str, the zip code of the contact
#         :param Register: str, the register of the contact
#         :param StreetAddressNumber: str, the street address number of the contact
#         :param Phones: list of dict, a list of phone numbers for the contact
#         :param OtherProperties: dict, other properties of the contact
#         :param TypeId: int, the type id of the contact. Defaults to 0.
#         :param OriginId: int, the origin id of the contact. Defaults to 0.
#         :param CompanyId: int, the company id of the contact. Defaults to 4001214.
#         :return: dict, the json response from the API
#         """
#         payload = json.dumps(payload)
#         r = requests.post(
#             f"{self.host}/Contacts?$expand=Phones,OtherProperties",
#             data=payload,
#             headers=self.headers,
#         )
#         response = r.json()
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def check_duplicate_contact(self, payload):
#         payload = json.dumps(payload)
#         r = requests.post(
#             f"{self.host}/Contacts/IsDuplicate", data=payload, headers=self.headers
#         )
#         response = r.json().get("value")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def post_image_as_url(self, image_url):
#         payload = {}
#         # Extract the filename from the URL
#         filename = get_file_url(image_url)
#         files = [("file1", (filename, requests.get(image_url).content, "image/jpeg"))]

#         headers = self.headers
#         del headers["Content-Type"]

#         r = requests.post(
#             f"{self.host}/Images", data=payload, files=files, headers=headers
#         )
#         response = r.json()
#         if response.get("value"):
#             return response["value"][0]["Url"]
#         return None

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def post_contact_avatar(self, contact_id, image_url):
#         payload = {}
#         # Extract the filename from the URL
#         filename = get_file_url(image_url)

#         files = [("file1", (filename, requests.get(image_url).content, "image/jpeg"))]

#         headers = {"User-Key": self.api_key}

#         r = requests.post(
#             f"{self.host}/Contacts({contact_id})/UploadAvatar",
#             data=payload,
#             files=files,
#             headers=headers,
#         )
#         response = r.json()
#         if response.get("value"):
#             return response["value"][0]["AvatarUrl"]
#         return None

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_contact_origins(
#         self,
#     ):
#         r = requests.get(
#             f"{self.host}/Contacts@Origins?$skip=0&$top=20&$select=Id,Name&$orderby=Name&$count=true",
#             headers=self.headers,
#         )
#         response = r.json().get("value")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def post_user_avatar(self, user_id, image_url):
#         payload = {}
#         # Extract the filename from the URL
#         filename = get_file_url(image_url)
#         print("filename: ", filename)

#         files = [("file1", (filename, requests.get(image_url).content, "image/jpeg"))]

#         headers = {"User-Key": self.api_key}

#         r = requests.post(
#             f"{self.host}/Users({user_id})/UploadAvatar",
#             data=payload,
#             files=files,
#             headers=headers,
#         )
#         response = r.json()
#         if response.get("value"):
#             return response["value"][0]["AvatarUrl"]
#         return None

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_roles(
#         self,
#     ):
#         r = requests.get(
#             f"{self.host}/Roles?$select=Id,Name&$orderby=Name&$count=true",
#             headers=self.headers,
#         )
#         response = r.json().get("value")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def post_new_role(self, payload):
#         r = requests.post(
#             f"{self.host}/Roles",
#             data=json.dumps(payload),
#             headers=self.headers,
#         )
#         response = r.json().get("value")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_contacts(self, _filter, select=None):
#         response = []
#         url = f"{self.host}/Contacts?$orderby=Id+desc,CNPJ&$expand=OtherProperties,Phones&$filter={_filter}"
#         if select:
#             url += f"&$select={select}"
#         while url:
#             r = requests.get(url, headers=self.headers)
#             data = r.json()
#             if data.get("value"):
#                 response += data["value"]
#             url = data.get("@odata.nextLink")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def delete_contact(self, id_):
#         r = requests.delete(f"{self.host}/Contacts({id_})", headers=self.headers)
#         response = r.json()
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def update_contact(self, id_, field):
#         payload = json.dumps(field)
#         r = requests.patch(
#             f"{self.host}/Contacts({id_})?$expand=OtherProperties,Phones",
#             data=payload,
#             headers=self.headers,
#         )
#         response = r.json()
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_fields(self, _filter, expand=None):
#         response = []
#         url = f"{self.host}/Fields?$filter={_filter}"
#         if expand:
#             url += f"&$expand={expand}"
#         while url:
#             r = requests.get(url, headers=self.headers, timeout=5)
#             data = r.json()
#             if data.get("value"):
#                 response += data["value"]
#             url = data.get("@odata.nextLink")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_field_options(self, table_id):
#         r = requests.get(
#             f"{self.host}/Fields@OptionsTables@Options?$filter=TableId+eq+{table_id}&$orderby=Name&$count=true&$skip=0",
#             headers=self.headers,
#         )
#         response = r.json().get("value")
#         if response:
#             return response
#         return None

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def create_field_option(self, option_name, table_id):
#         payload = json.dumps({"Name": option_name, "TableId": table_id})
#         r = requests.post(
#             f"{self.host}/Fields@OptionsTables@Options",
#             data=payload,
#             headers=self.headers,
#         )
#         response = r.json().get("value")
#         if response:
#             item = next(iter(response))
#             return item
#         return None

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def create_field(self, name, type_=1, options_table=None):
#         payload = {"Name": name, "EntityId": 1, "TypeId": type_, "Required": False}

#         if options_table:
#             payload["OptionsTable"] = options_table

#         payload = json.dumps(payload)

#         r = requests.post(
#             f"{self.host}/Fields?$expand=Type,OptionsTable($expand=Options)",
#             data=payload,
#             headers=self.headers,
#         )
#         print(r.json())
#         response = r.json().get("value")
#         if response:
#             item = next(iter(response))
#             return item
#         return None

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_city(self, _filter):
#         r = requests.get(
#             f"{self.host}/Cities?$expand=Country,State&$filter={_filter}",
#             headers=self.headers,
#         )
#         response = r.json().get("value")
#         if response:
#             return response
#         return None

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_country(self, region_code):
#         r = requests.get(
#             f"{self.host}/Cities@Countries?$top=1&$filter=Short2+eq+'{region_code}'",
#             headers=self.headers,
#         )
#         response = r.json().get("value")
#         return next(iter(response))

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def create_basic_contact(self, fields: Dict) -> Optional[Dict]:
#         """
#         Create a basic contact on Ploomes.

#         Args:
#             fields (Dict): The fields for the new contact.

#         Returns:
#             Optional[Dict]: The response from Ploomes, if successful. None otherwise.
#         """
#         url = f"{self.host}/Contacts?$expand=Phones,OtherProperties"

#         try:
#             r = requests.post(url, json=fields, headers=self.headers)
#             r.raise_for_status()
#             response = r.json()
#             return response.get("value")
#         except RequestException as e:
#             logger.error(f"Failed to create contact: {str(e)}")
#         except json.JSONDecodeError:
#             logger.error(f"Invalid JSON in response: {r.text}")

#         return None

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_deal_stage(self, filter=None):
#         r = requests.get(f"{self.host}/Deals@Stages?", headers=self.headers)
#         response = r.json().get("value")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_deals_at_pipelines(self, filter=None):
#         url = f"{self.host}/Deals@Pipelines?"
#         if filter:
#             url += f"$filter={filter}&"
#         url += "$expand=Tables,Stages,AllowedUsers,AllowedTeams"
#         r = requests.get(url, headers=self.headers)
#         response = r.json().get("value")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def create_deals_at_pipelines(self, data: Dict):
#         url = f"{self.host}/Deals@Pipelines?$expand=Tables,Stages,AllowedUsers,AllowedTeams"
#         r = requests.post(url, headers=self.headers, data=json.dumps(data))
#         response = r.json().get("value")
#         return response

#     @retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_instance(self, filter=None):
#         response = []
#         url = f"{self.host}/Products?"
#         if filter:
#             url += f"$filter={filter}&"
#         url += "$expand=OtherProperties&$orderby=Id+asc"

#         while url:
#             r = requests.get(url, headers=self.headers, timeout=5)
#             data = r.json()
#             if data.get("value"):
#                 response += data["value"]
#             url = data.get("@odata.nextLink")
#         return response
#         # response = r.json().get("value")
#         # data = self.format_product_response(response)
#         # return data

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_tables(self, _filter: str):
#         url = f"{self.host}/Tables?$filter={_filter}"
#         r = requests.get(url, headers=self.headers)
#         print(r.json())
#         response = r.json().get("value")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def create_expanded_tables(self, data: Dict):
#         url = f"{self.host}/Tables?$expand=AllowedUsers,AllowedTeams,Fields($expand=FieldPath),Filter($expand=AllowedUsers($expand=User),AllowedTeams($expand=Team),Fields($expand=Operation,Selector,FieldPath,Values))"
#         print(json.dumps(data))
#         r = requests.post(url, headers=self.headers, data=json.dumps(data))
#         if r.status_code == 200:
#             response = r.json().get("value")
#             return response
#         else:
#             error_message = f"Error creating expanded table: {r.status_code} - {r.text}"
#             print(error_message)
#             raise Exception(error_message)

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def post_product(self, payload):
#         payload = json.dumps(payload)
#         r = requests.post(
#             f"{self.host}/Products?Products?$expand=Currency,Group,Family,Lists($expand=List),Parts($expand=Group,OtherProperties,RequiredParts,SuggestedParts,BlockedParts,ProductPart,GroupPart,ListPart),OtherProperties",
#             headers=self.headers,
#             data=payload,
#         )
#         response = r.json()
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def post_filters(self, data: Dict):
#         print("This is data", data)
#         url = f"{self.host}/Filters?$expand=AllowedUsers($expand=User),AllowedTeams($expand=Team),Fields($expand=Operation,Selector,FieldPath,Values)"
#         r = requests.post(url, headers=self.headers, data=json.dumps(data))
#         if r.status_code == 200:
#             response = r.json().get("value")
#             return response
#         else:
#             return f"Error creating filter: {r.status_code} - {r.text}"

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def update_expanded_tables(self, tableId: int, data: Dict):
#         url = f"{self.host}/Tables({tableId})?$expand=AllowedUsers,AllowedTeams,Fields($expand=FieldPath),Filter($expand=AllowedUsers($expand=User),AllowedTeams($expand=Team),Fields($expand=Operation,Selector,FieldPath,Values))"
#         r = requests.patch(url, headers=self.headers, data=json.dumps(data))
#         if r.status_code == 200:
#             response = r.json().get("value")
#             return response
#         else:
#             return f"Error updating table {tableId}: {r.status_code} - {r.text}"

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def update_instance(self, id_, inUse=None, Authorized=None):
#         config = {"OtherProperties": []}
#         list_ = []

#         if inUse != None:
#             field_key = "product_5AC275B5-C0E4-4076-852E-782CC896439A"
#             dict_ = {
#                 "FieldKey": field_key,
#                 "BoolValue": inUse,
#             }
#             list_.append(dict_)

#         if Authorized != None:
#             field_key = "product_97F8B3A8-C827-4992-B314-9CBB7D72D39C"
#             dict_ = {
#                 "FieldKey": field_key,
#                 "BoolValue": Authorized,
#             }
#             list_.append(dict_)

#         config["OtherProperties"] = list_
#         print(config)

#         r = requests.patch(
#             f"{self.host}/Products({id_})",
#             data=json.dumps(config),
#             headers=self.headers,
#         )
#         response = r.json()
#         return response

#     def format_product_response(self, data):
#         result = {}
#         fields_to_find = {
#             "product_E44A0C6A-893C-447E-A391-4C574279977B",
#             "product_7D87390D-CA3E-4E56-A5DD-FE20ECDBF817",
#             "product_FFAC88DC-6FAC-4366-A10D-BE99AC7D2BB6",
#         }
#         for item in data:
#             result["id"] = item["Id"]
#             for prop in item["OtherProperties"]:
#                 field_key = prop["FieldKey"]
#                 if field_key in fields_to_find:
#                     if field_key == "product_E44A0C6A-893C-447E-A391-4C574279977B":
#                         result["client_id"] = prop["StringValue"]
#                     elif field_key == "product_7D87390D-CA3E-4E56-A5DD-FE20ECDBF817":
#                         result["token"] = prop["StringValue"]
#                     elif field_key == "product_FFAC88DC-6FAC-4366-A10D-BE99AC7D2BB6":
#                         result["source"] = prop["ObjectValueName"]
#                     fields_to_find.remove(field_key)
#                 if not fields_to_find:
#                     break
#             if not fields_to_find:
#                 break
#         return result

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_deals(self, filter):
#         response = []
#         url = f"{self.host}/Deals?$orderby=Id+desc&$filter={filter}&$expand=OtherProperties"
#         while url:
#             r = requests.get(url, headers=self.headers)
#             data = r.json()
#             if data.get("value"):
#                 response += data["value"]
#             url = data.get("@odata.nextLink")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def deal_exists(self, contact_id):
#         filter = f"ContactId+eq+{contact_id}"
#         deals = self.get_deals(filter)
#         if deals:
#             return deals[0]
#         return None

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def patch_deal(self, deal_id, payload):
#         r = requests.patch(
#             f"{self.host}/Deals({deal_id})?$expand=Stages,Tags,Products,Contacts,OtherProperties",
#             headers=self.headers,
#             data=json.dumps(payload),
#         )
#         return r.json()

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def upload_deal_attachment(self, deal_id: Union[str, int], file_path: str):
#         # Make sure the file exists
#         if not os.path.isfile(file_path):
#             raise FileNotFoundError(f"No file found at {file_path}")

#         # Open the file in binary mode
#         with open(file_path, "rb") as f:
#             # Define the headers for the request

#             # Define the files for the request
#             filename = os.path.basename(file_path)
#             files = [("file", (filename, f, "application/pdf"))]

#             headers = {"User-Key": self.api_key}

#             # Make the request
#             r = requests.post(
#                 f"{self.host}/Deals({deal_id})/UploadFile?$expand=Attachments",
#                 headers=headers,
#                 files=files,
#             )

#         # Return the response as JSON
#         return r.json()

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def delete_deal(self, id_):
#         r = requests.delete(f"{self.host}/Deals({id_})", headers=self.headers)
#         return None

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def post_deal(self, fields):
#         payload = json.dumps(fields)
#         r = requests.post(f"{self.host}/Deals", data=payload, headers=self.headers)
#         response = r.json().get("value")
#         print(response)
#         return next(iter(response))

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def post_deal_action(self, id_, status):
#         r = requests.post(f"{self.host}/Deals({id_})/{status}", headers=self.headers)
#         response = r.json()
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def get_interaction_records(self, _filter=None):
#         response = []
#         url = f"{self.host}/InteractionRecords?"
#         if _filter:
#             url += f"$filter={_filter}&"
#         url += "$expand=OtherProperties&$top=300&$orderby=Id+desc"
#         while url:
#             r = requests.get(url, headers=self.headers, timeout=5)
#             data = r.json()
#             if data.get("value"):
#                 response += data["value"]
#             url = data.get("@odata.nextLink")
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def patch_interaction_record(self, interaction_id, payload):
#         response = []
#         payload = json.dumps(payload)
#         url = f"{self.host}/InteractionRecords({interaction_id})"
#         r = requests.patch(url, headers=self.headers, data=payload, timeout=5)
#         data = r.json()
#         if data.get("value"):
#             response += data["value"]
#         return response

#     @retry
#     @sleep_and_retry
#     @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
#     def post_interaction_record(self, contact_id, content, date, type_id=7):
#         response = []
#         payload = json.dumps(
#             {
#                 "ContactId": contact_id,
#                 "Content": content,
#                 "Date": date,
#                 "TypeId": type_id,
#             }
#         )
#         r = requests.post(
#             f"{self.host}/InteractionRecords", data=payload, headers=self.headers
#         )
#         data = r.json()
#         if data.get("value"):
#             response += data["value"]
#         return response


# def get_file_url(url):
#     filename = url.split("/")[-1]  # get the filename from the URL
#     if "." not in filename:  # if there's no extension
#         return url  # return the original URL
#     else:
#         # return the URL up to the query string, if present
#         return url.split("?")[0]
