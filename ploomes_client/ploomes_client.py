import os
import base64
import math
import time
import requests
import json
from ratelimit import limits, sleep_and_retry
import pandas as pd
import random
from typing import Dict, Optional, List, Union
import logging
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


"""https://learn.microsoft.com/en-us/dynamics-nav/using-filter-expressions-in-odata-uris"""


MAX_REQUESTS_PER_SECOND = 2


class PloomesClient:
    def __init__(self, api_key) -> None:
        self.host = "https://public-api2.ploomes.com"
        self.api_key = api_key
        self.headers = {"User-Key": api_key, "Content-Type": "application/json"}

    def retry(func):
        MAX_RETRIES = 3  # maximum number of retries
        TIMEOUT = 5  # time to wait before retrying (in seconds)

        def wrapper(*args, **kwargs):
            retries = 0  # current number of retries

            while retries < MAX_RETRIES:
                try:
                    # execute the function and return its result
                    return func(*args, **kwargs)
                except Exception as e:  # Catch all exceptions
                    print(func, *args, e)
                    retries += 1
                    # calculate the timeout value using the min() function
                    timeout = min(math.pow(TIMEOUT, retries), 300)
                    # sleep for the calculated timeout value
                    time.sleep(timeout)

        return wrapper

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_user_account(self):
        r = requests.get(f"{self.host}/Account", headers=self.headers)
        if r.status_code == 401:
            return None
        response = r.json()
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_contact_products(self, filter=None):
        if filter:
            filter = f"?$filter={filter}"
        r = requests.get(f"{self.host}/Contacts@Products{filter}", headers=self.headers)
        response = r.json().get("value")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def update_contact_product(self, id_, fields):
        payload = json.dumps(fields)
        r = requests.patch(
            f"{self.host}/Contacts@Products({id_})?$expand=OtherProperties",
            data=payload,
            headers=self.headers,
        )
        response = r.json()
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def post_contact_product(self, fields):
        payload = json.dumps(fields)
        r = requests.post(
            f"{self.host}/Contacts@Products", data=payload, headers=self.headers
        )
        response = r.json()
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_products(
        self,
        _filter: Optional[str] = None,
        top: int = 1000,
        orderby: Optional[str] = None,
    ) -> List[Dict]:
        url = f"{self.host}/Products?$expand=OtherProperties"

        if _filter:
            url += f"&$filter={_filter}"

        if top:
            url += f"&$top={top}"

        if orderby:
            url += f"&$orderby={orderby}"
        response = []
        while url:
            r = requests.get(url, headers=self.headers, timeout=5)
            data = r.json()
            if data.get("value"):
                response += data["value"]
            url = data.get("@odata.nextLink")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_user_info(self, filter=None):
        url = f"{self.host}/Users?"
        if filter:
            url += f"$filter={filter}"
        r = requests.get(url, headers=self.headers)
        response = r.json().get("value")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def create_contact(
        self,
        Name,
        Email,
        City,
        State,
        StreetAddress,
        Neighborhood,
        ZipCode,
        Register,
        StreetAddressNumber,
        Phones,
        OtherProperties,
        TypeId=0,
        OriginId=0,
        CompanyId=4001214,
    ):
        """
        This function creates a contact in a CRM system by sending a POST request to an API endpoint.
        The function requires 7 mandatory parameters: Name, Neighborhood, ZipCode, Register, StreetAddressNumber, Phones, OtherProperties
        and 2 optional parameters: TypeId, OriginId.
        The function also uses a global variable api_key and self.host, which should be defined before calling this function.
        :param Name: str, the name of the contact
        :param Neighborhood: str, the neighborhood of the contact
        :param ZipCode: str, the zip code of the contact
        :param Register: str, the register of the contact
        :param StreetAddressNumber: str, the street address number of the contact
        :param Phones: list of dict, a list of phone numbers for the contact
        :param OtherProperties: dict, other properties of the contact
        :param TypeId: int, the type id of the contact. Defaults to 0.
        :param OriginId: int, the origin id of the contact. Defaults to 0.
        :param CompanyId: int, the company id of the contact. Defaults to 4001214.
        :return: dict, the json response from the API
        """
        payload = json.dumps(
            {
                "Name": Name,
                "Neighborhood": Neighborhood,
                "ZipCode": ZipCode,
                "Email": Email,
                "City": City,
                "State": State,
                "StreetAddress": StreetAddress,
                "Register": Register,
                "OriginId": OriginId,
                "CompanyId": CompanyId,
                "StreetAddressNumber": StreetAddressNumber,
                "TypeId": TypeId,
                "Phones": Phones,
                "OtherProperties": OtherProperties,
            }
        )
        r = requests.post(
            f"{self.host}/Contacts?$expand=Phones,OtherProperties",
            data=payload,
            headers=self.headers,
        )
        response = r.json()
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def create_simple_contact(self, payload):
        """
        This function creates a contact in a CRM system by sending a POST request to an API endpoint.
        The function requires 7 mandatory parameters: Name, Neighborhood, ZipCode, Register, StreetAddressNumber, Phones, OtherProperties
        and 2 optional parameters: TypeId, OriginId.
        The function also uses a global variable api_key and self.host, which should be defined before calling this function.
        :param Name: str, the name of the contact
        :param Neighborhood: str, the neighborhood of the contact
        :param ZipCode: str, the zip code of the contact
        :param Register: str, the register of the contact
        :param StreetAddressNumber: str, the street address number of the contact
        :param Phones: list of dict, a list of phone numbers for the contact
        :param OtherProperties: dict, other properties of the contact
        :param TypeId: int, the type id of the contact. Defaults to 0.
        :param OriginId: int, the origin id of the contact. Defaults to 0.
        :param CompanyId: int, the company id of the contact. Defaults to 4001214.
        :return: dict, the json response from the API
        """
        payload = json.dumps(payload)
        r = requests.post(
            f"{self.host}/Contacts?$expand=Phones,OtherProperties",
            data=payload,
            headers=self.headers,
        )
        response = r.json()
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def check_duplicate_contact(self, payload):
        payload = json.dumps(payload)
        r = requests.post(
            f"{self.host}/Contacts/IsDuplicate", data=payload, headers=self.headers
        )
        response = r.json().get("value")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def post_image_as_url(self, image_url):
        payload = {}
        # Extract the filename from the URL
        filename = get_file_url(image_url)
        files = [("file1", (filename, requests.get(image_url).content, "image/jpeg"))]

        headers = self.headers
        del headers["Content-Type"]

        r = requests.post(
            f"{self.host}/Images", data=payload, files=files, headers=headers
        )
        response = r.json()
        if response.get("value"):
            return response["value"][0]["Url"]
        return None

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def post_contact_avatar(self, contact_id, image_url):
        payload = {}
        # Extract the filename from the URL
        filename = get_file_url(image_url)

        files = [("file1", (filename, requests.get(image_url).content, "image/jpeg"))]

        headers = {"User-Key": self.api_key}

        r = requests.post(
            f"{self.host}/Contacts({contact_id})/UploadAvatar",
            data=payload,
            files=files,
            headers=headers,
        )
        response = r.json()
        if response.get("value"):
            return response["value"][0]["AvatarUrl"]
        return None

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_contact_origins(
        self,
    ):
        r = requests.get(
            f"{self.host}/Contacts@Origins?$skip=0&$top=20&$select=Id,Name&$orderby=Name&$count=true",
            headers=self.headers,
        )
        response = r.json().get("value")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def post_user_avatar(self, user_id, image_url):
        payload = {}
        # Extract the filename from the URL
        filename = get_file_url(image_url)
        print("filename: ", filename)

        files = [("file1", (filename, requests.get(image_url).content, "image/jpeg"))]

        headers = {"User-Key": self.api_key}

        r = requests.post(
            f"{self.host}/Users({user_id})/UploadAvatar",
            data=payload,
            files=files,
            headers=headers,
        )
        response = r.json()
        if response.get("value"):
            return response["value"][0]["AvatarUrl"]
        return None

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_roles(
        self,
    ):
        r = requests.get(
            f"{self.host}/Roles?$select=Id,Name&$orderby=Name&$count=true",
            headers=self.headers,
        )
        response = r.json().get("value")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def post_new_role(self, payload):
        r = requests.post(
            f"{self.host}/Roles",
            data=json.dumps(payload),
            headers=self.headers,
        )
        response = r.json().get("value")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_contacts(self, _filter, select=None):
        response = []
        url = f"{self.host}/Contacts?$orderby=Id+desc,CNPJ&$expand=OtherProperties,Phones&$filter={_filter}"
        if select:
            url += f"&$select={select}"
        while url:
            r = requests.get(url, headers=self.headers)
            data = r.json()
            if data.get("value"):
                response += data["value"]
            url = data.get("@odata.nextLink")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def delete_contact(self, id_):
        r = requests.delete(f"{self.host}/Contacts({id_})", headers=self.headers)
        response = r.json()
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def update_contact(self, id_, field):
        payload = json.dumps(field)
        r = requests.patch(
            f"{self.host}/Contacts({id_})?$expand=OtherProperties,Phones",
            data=payload,
            headers=self.headers,
        )
        response = r.json()
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_fields(self, _filter, expand=None):
        response = []
        url = f"{self.host}/Fields?$filter={_filter}"
        if expand:
            url += f"&$expand={expand}"
        while url:
            r = requests.get(url, headers=self.headers, timeout=5)
            data = r.json()
            if data.get("value"):
                response += data["value"]
            url = data.get("@odata.nextLink")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_field_options(self, table_id):
        r = requests.get(
            f"{self.host}/Fields@OptionsTables@Options?$filter=TableId+eq+{table_id}&$orderby=Name&$count=true&$skip=0",
            headers=self.headers,
        )
        response = r.json().get("value")
        if response:
            return response
        return None

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def create_field_option(self, option_name, table_id):
        payload = json.dumps({"Name": option_name, "TableId": table_id})
        r = requests.post(
            f"{self.host}/Fields@OptionsTables@Options",
            data=payload,
            headers=self.headers,
        )
        response = r.json().get("value")
        if response:
            item = next(iter(response))
            return item
        return None

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def create_field(self, name, type_=1, options_table=None):
        payload = {"Name": name, "EntityId": 1, "TypeId": type_, "Required": False}

        if options_table:
            payload["OptionsTable"] = options_table

        payload = json.dumps(payload)

        r = requests.post(
            f"{self.host}/Fields?$expand=Type,OptionsTable($expand=Options)",
            data=payload,
            headers=self.headers,
        )
        print(r.json())
        response = r.json().get("value")
        if response:
            item = next(iter(response))
            return item
        return None

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_city(self, _filter):
        r = requests.get(
            f"{self.host}/Cities?$expand=Country,State&$filter={_filter}",
            headers=self.headers,
        )
        response = r.json().get("value")
        if response:
            return response
        return None

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_country(self, region_code):
        r = requests.get(
            f"{self.host}/Cities@Countries?$top=1&$filter=Short2+eq+'{region_code}'",
            headers=self.headers,
        )
        response = r.json().get("value")
        return next(iter(response))

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def create_basic_contact(self, fields: Dict) -> Optional[Dict]:
        """
        Create a basic contact on Ploomes.

        Args:
            fields (Dict): The fields for the new contact.

        Returns:
            Optional[Dict]: The response from Ploomes, if successful. None otherwise.
        """
        url = f"{self.host}/Contacts?$expand=Phones,OtherProperties"

        try:
            r = requests.post(url, json=fields, headers=self.headers)
            r.raise_for_status()
            response = r.json()
            return response.get("value")
        except RequestException as e:
            logger.error(f"Failed to create contact: {str(e)}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in response: {r.text}")

        return None



    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_deal_stage(self, filter=None):
        r = requests.get(f"{self.host}/Deals@Stages?", headers=self.headers)
        response = r.json().get("value")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_deals_at_pipelines(self, filter=None):
        url = f"{self.host}/Deals@Pipelines?"
        if filter:
            url += f"$filter={filter}&"
        url += "$expand=Tables,Stages,AllowedUsers,AllowedTeams"
        r = requests.get(url, headers=self.headers)
        response = r.json().get("value")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def create_deals_at_pipelines(self, data: Dict):
        url = f"{self.host}/Deals@Pipelines?$expand=Tables,Stages,AllowedUsers,AllowedTeams"
        r = requests.post(url, headers=self.headers, data=json.dumps(data))
        response = r.json().get("value")
        return response

    @retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_instance(self, filter=None):
        response = []
        url = f"{self.host}/Products?"
        if filter:
            url += f"$filter={filter}&"
        url += "$expand=OtherProperties&$orderby=Id+asc"

        while url:
            r = requests.get(url, headers=self.headers, timeout=5)
            data = r.json()
            if data.get("value"):
                response += data["value"]
            url = data.get("@odata.nextLink")
        return response
        # response = r.json().get("value")
        # data = self.format_product_response(response)
        # return data

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_tables(self, _filter: str):
        url = f"{self.host}/Tables?$filter={_filter}"
        r = requests.get(url, headers=self.headers)
        print(r.json())
        response = r.json().get("value")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def create_expanded_tables(self, data: Dict):
        url = f"{self.host}/Tables?$expand=AllowedUsers,AllowedTeams,Fields($expand=FieldPath),Filter($expand=AllowedUsers($expand=User),AllowedTeams($expand=Team),Fields($expand=Operation,Selector,FieldPath,Values))"
        print(json.dumps(data))
        r = requests.post(url, headers=self.headers, data=json.dumps(data))
        if r.status_code == 200:
            response = r.json().get("value")
            return response
        else:
            error_message = f"Error creating expanded table: {r.status_code} - {r.text}"
            print(error_message)
            raise Exception(error_message)

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def post_product(self, payload):
        payload = json.dumps(payload)
        r = requests.post(
            f"{self.host}/Products?Products?$expand=Currency,Group,Family,Lists($expand=List),Parts($expand=Group,OtherProperties,RequiredParts,SuggestedParts,BlockedParts,ProductPart,GroupPart,ListPart),OtherProperties",
            headers=self.headers,
            data=payload,
        )
        response = r.json()
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def post_filters(self, data: Dict):
        print("This is data", data)
        url = f"{self.host}/Filters?$expand=AllowedUsers($expand=User),AllowedTeams($expand=Team),Fields($expand=Operation,Selector,FieldPath,Values)"
        r = requests.post(url, headers=self.headers, data=json.dumps(data))
        if r.status_code == 200:
            response = r.json().get("value")
            return response
        else:
            return f"Error creating filter: {r.status_code} - {r.text}"

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def update_expanded_tables(self, tableId: int, data: Dict):
        url = f"{self.host}/Tables({tableId})?$expand=AllowedUsers,AllowedTeams,Fields($expand=FieldPath),Filter($expand=AllowedUsers($expand=User),AllowedTeams($expand=Team),Fields($expand=Operation,Selector,FieldPath,Values))"
        r = requests.patch(url, headers=self.headers, data=json.dumps(data))
        if r.status_code == 200:
            response = r.json().get("value")
            return response
        else:
            return f"Error updating table {tableId}: {r.status_code} - {r.text}"

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def update_instance(self, id_, inUse=None, Authorized=None):
        config = {"OtherProperties": []}
        list_ = []

        if inUse != None:
            field_key = "product_5AC275B5-C0E4-4076-852E-782CC896439A"
            dict_ = {
                "FieldKey": field_key,
                "BoolValue": inUse,
            }
            list_.append(dict_)

        if Authorized != None:
            field_key = "product_97F8B3A8-C827-4992-B314-9CBB7D72D39C"
            dict_ = {
                "FieldKey": field_key,
                "BoolValue": Authorized,
            }
            list_.append(dict_)

        config["OtherProperties"] = list_
        print(config)

        r = requests.patch(
            f"{self.host}/Products({id_})",
            data=json.dumps(config),
            headers=self.headers,
        )
        response = r.json()
        return response

    def format_product_response(self, data):
        result = {}
        fields_to_find = {
            "product_E44A0C6A-893C-447E-A391-4C574279977B",
            "product_7D87390D-CA3E-4E56-A5DD-FE20ECDBF817",
            "product_FFAC88DC-6FAC-4366-A10D-BE99AC7D2BB6",
        }
        for item in data:
            result["id"] = item["Id"]
            for prop in item["OtherProperties"]:
                field_key = prop["FieldKey"]
                if field_key in fields_to_find:
                    if field_key == "product_E44A0C6A-893C-447E-A391-4C574279977B":
                        result["client_id"] = prop["StringValue"]
                    elif field_key == "product_7D87390D-CA3E-4E56-A5DD-FE20ECDBF817":
                        result["token"] = prop["StringValue"]
                    elif field_key == "product_FFAC88DC-6FAC-4366-A10D-BE99AC7D2BB6":
                        result["source"] = prop["ObjectValueName"]
                    fields_to_find.remove(field_key)
                if not fields_to_find:
                    break
            if not fields_to_find:
                break
        return result

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_deals(self, filter):
        response = []
        url = f"{self.host}/Deals?$orderby=Id+desc&$filter={filter}&$expand=OtherProperties"
        while url:
            r = requests.get(url, headers=self.headers)
            data = r.json()
            if data.get("value"):
                response += data["value"]
            url = data.get("@odata.nextLink")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def deal_exists(self, contact_id):
        filter = f"ContactId+eq+{contact_id}"
        deals = self.get_deals(filter)
        if deals:
            return deals[0]
        return None

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def patch_deal(self, deal_id, payload):
        r = requests.patch(
            f"{self.host}/Deals({deal_id})?$expand=Stages,Tags,Products,Contacts,OtherProperties",
            headers=self.headers,
            data=json.dumps(payload),
        )
        return r.json()

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def upload_deal_attachment(self, deal_id: Union[str, int], file_path: str):
        # Make sure the file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"No file found at {file_path}")

        # Open the file in binary mode
        with open(file_path, "rb") as f:
            # Define the headers for the request

            # Define the files for the request
            filename = os.path.basename(file_path)
            files = [("file", (filename, f, "application/pdf"))]

            headers = {"User-Key": self.api_key}

            # Make the request
            r = requests.post(
                f"{self.host}/Deals({deal_id})/UploadFile?$expand=Attachments",
                headers=headers,
                files=files,
            )

        # Return the response as JSON
        return r.json()

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def delete_deal(self, id_):
        r = requests.delete(f"{self.host}/Deals({id_})", headers=self.headers)
        return None

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def post_deal(self, fields):
        payload = json.dumps(fields)
        r = requests.post(f"{self.host}/Deals", data=payload, headers=self.headers)
        response = r.json().get("value")
        print(response)
        return next(iter(response))

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def post_deal_action(self, id_, status):
        r = requests.post(f"{self.host}/Deals({id_})/{status}", headers=self.headers)
        response = r.json()
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def get_interaction_records(self, _filter=None):
        response = []
        url = f"{self.host}/InteractionRecords?"
        if _filter:
            url += f"$filter={_filter}&"
        url += "$expand=OtherProperties&$top=300&$orderby=Id+desc"
        while url:
            r = requests.get(url, headers=self.headers, timeout=5)
            data = r.json()
            if data.get("value"):
                response += data["value"]
            url = data.get("@odata.nextLink")
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def patch_interaction_record(self, interaction_id, payload):
        response = []
        payload = json.dumps(payload)
        url = f"{self.host}/InteractionRecords({interaction_id})"
        r = requests.patch(url, headers=self.headers, data=payload, timeout=5)
        data = r.json()
        if data.get("value"):
            response += data["value"]
        return response

    @retry
    @sleep_and_retry
    @limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
    def post_interaction_record(self, contact_id, content, date, type_id=7):
        response = []
        payload = json.dumps(
            {
                "ContactId": contact_id,
                "Content": content,
                "Date": date,
                "TypeId": type_id,
            }
        )
        r = requests.post(
            f"{self.host}/InteractionRecords", data=payload, headers=self.headers
        )
        data = r.json()
        if data.get("value"):
            response += data["value"]
        return response


def get_file_url(url):
    filename = url.split("/")[-1]  # get the filename from the URL
    if "." not in filename:  # if there's no extension
        return url  # return the original URL
    else:
        # return the URL up to the query string, if present
        return url.split("?")[0]
