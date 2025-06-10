import asyncio
import json
import httpx
import base64
from io import BytesIO
from ploomes_client.core.ploomes_client import PloomesClient
from ploomes_client.core.utils import get_file_url


class Contacts:
    def __init__(self, client: PloomesClient) -> None:
        self.client = client
        self.path = "/Contacts"

    async def aget_contacts(
        self,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        """
        Creates a new contact using the provided payload and filters.

        Args:
            payload (dict): The data for the contact to be created.
            filter_ (str, optional): OData filter string.
            expand (str, optional): Expand related entities.
            top (int, optional): Maximum number of results to return.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.

        Returns:
            Response: The response object containing the result of the POST request.
        """
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }

        response = await self.client.arequest(
            "GET",
            self.path,
            filters={k: v for k, v in filters.items() if v is not None},
        )
        return response

    def get_contacts(
        self,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        """
        Creates a new contact using the provided payload and filters.

        Args:
            payload (dict): The data for the contact to be created.
            filter_ (str, optional): OData filter string.
            expand (str, optional): Expand related entities.
            top (int, optional): Maximum number of results to return.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.

        Returns:
            Response: The response object containing the result of the POST request.
        """
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }

        response = self.client.request(
            "GET",
            self.path,
            filters={k: v for k, v in filters.items() if v is not None},
        )
        return response
    
    async def aget_contacts_products(
        self,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        """
        Creates a new contact using the provided payload and filters.

        Args:
            payload (dict): The data for the contact to be created.
            filter_ (str, optional): OData filter string.
            expand (str, optional): Expand related entities.
            top (int, optional): Maximum number of results to return.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.

        Returns:
            Response: The response object containing the result of the POST request.
        """
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }
        return await self.client.arequest(
            "GET",
            self.path + "@Products",
            filters={k: v for k, v in filters.items() if v is not None},
        )

    def get_contacts_products(
        self,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        """
        Creates a new contact using the provided payload and filters.

        Args:
            payload (dict): The data for the contact to be created.
            filter_ (str, optional): OData filter string.
            expand (str, optional): Expand related entities.
            top (int, optional): Maximum number of results to return.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.

        Returns:
            Response: The response object containing the result of the POST request.
        """
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }
        return self.client.request(
            "GET",
            self.path + "@Products",
            filters={k: v for k, v in filters.items() if v is not None},
        )

    async def aget_contacts_origins(
        self,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        """
        Creates a new contact using the provided payload and filters.

        Args:
            payload (dict): The data for the contact to be created.
            filter_ (str, optional): OData filter string.
            expand (str, optional): Expand related entities.
            top (int, optional): Maximum number of results to return.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.

        Returns:
            Response: The response object containing the result of the POST request.
        """
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }
        return await self.client.arequest(
            "GET",
            self.path + "@Origins",
            filters={k: v for k, v in filters.items() if v is not None},
        )


    async def apost_contact(
        self,
        payload,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }
        
        return await self.client.arequest(
            "POST",
            self.path,
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )
    

    def post_contact(
        self,
        payload,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }
        payload = json.dumps(payload)
        return self.client.request(
            "POST",
            self.path,
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )
    
    async def apost_contact_products(
        self,
        payload,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }
        
        return await self.client.arequest(
            "POST",
            self.path + "@Products",
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )

    async def apost_contact_origins(
        self,
        payload,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }
        
        return await self.client.arequest(
            "POST",
            self.path + "@Origins",
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )

    async def apatch_contact(
        self,
        id_: int,
        payload: dict,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        """
        Updates a contact by its ID with specific fields.

        Args:
            id_ (int): The ID of the contact to be updated.
            payload (dict): Fields to be updated in the contact.
            filter_ (str, optional): OData filter string.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.
            top (int, optional): Maximum number of results to return.
            expand (str, optional): Expand related entities.

        Returns:
            dict: The JSON response from the server.
        """
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }
        
        return await self.client.arequest(
            "PATCH",
            self.path + f"({id_})",
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )

    def patch_contact(
        self,
        id_: int,
        payload: dict,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        """
        Updates a contact by its ID with specific fields.

        Args:
            id_ (int): The ID of the contact to be updated.
            payload (dict): Fields to be updated in the contact.
            filter_ (str, optional): OData filter string.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.
            top (int, optional): Maximum number of results to return.
            expand (str, optional): Expand related entities.

        Returns:
            dict: The JSON response from the server.
        """
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }

        payload = json.dumps(payload)
        
        return self.client.request(
            "PATCH",
            self.path + f"({id_})",
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )

    async def apatch_contact_products(
        self,
        id_: int,
        payload: dict,
        filter_=None,
        expand=None,
        top=None,
        inlinecount=None,
        orderby=None,
        select=None,
        skip=None,
    ):
        """
        Updates a contact by its ID with specific fields.

        Args:
            id_ (int): The ID of the contact to be updated.
            payload (dict): Fields to be updated in the contact.
            filter_ (str, optional): OData filter string.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.
            top (int, optional): Maximum number of results to return.
            expand (str, optional): Expand related entities.

        Returns:
            dict: The JSON response from the server.
        """
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }
        
        return await self.client.arequest(
            "PATCH",
            self.path + f"@Products({id_})",
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )

    async def adelete_contact(self, id_: int):
        """
        Deletes a contact by its ID.

        Args:
            id_ (int): The ID of the contact to be deleted.

        Returns:
            dict: The JSON response from the server.
        """
        return await self.client.arequest("DELETE", self.path + f"({id_})")
    

    def delete_contact(self, id_: int):
        """
        Deletes a contact by its ID.

        Args:
            id_ (int): The ID of the contact to be deleted.

        Returns:
            dict: The JSON response from the server.
        """
        return self.client.request("DELETE", self.path + f"({id_})")

    async def adelete_contact_products(self, id_: int):
        """
        Deletes a contact by its ID.

        Args:
            id_ (int): The ID of the contact to be deleted.

        Returns:
            dict: The JSON response from the server.
        """
        return await self.client.arequest("DELETE", self.path + f"@Products({id_})")

    async def apost_contact_avatar(self, contact_id: int, image_url: str) -> dict:
        """
        Uploads an avatar for a specific contact.
        """
        filename = await get_file_url(
            image_url
        )  # Ensure this extracts the filename correctly
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()
            content = response.content

        files = [("file1", (filename, content, "image/jpeg"))]

        return await self.client.arequest(
            "POST", self.path + f"({contact_id})/UploadAvatar", files=files
        )

    async def apost_attachment(
        self, contact_id: int, file_url: str, filename: str
    ) -> dict:
        """
        Uploads an avatar for a specific contact.
        """
        response = await self._adownload_file(file_url)

        files = [("file1", (filename, response.content, response.headers["Content-Type"]))]

        return await self.client.arequest(
            "POST",
            self.path + f"({contact_id})/UploadFile?$expand=Attachments",
            files=files,
        )

    async def apost_attachment_from_base64(
        self, contact_id: int, base64_data: str, filename: str
    ) -> dict:
        """
        Uploads a file for a specific contact from base64 encoded data, determining the content type from the data itself.
        """
        # Extract content type and decode the base64 string to bytes
        content_type, base64_encoded = base64_data.split(";base64,")
        content_type = content_type.split(":")[1]  # Get only the type part
        file_data = base64.b64decode(base64_encoded)

        # Create a file-like object from bytes
        file_like_object = BytesIO(file_data)
        file_like_object.name = filename

        # Prepare the file tuple for the 'files' parameter in requests
        files = [("file1", (filename, file_like_object, content_type))]

        # Make the POST request to upload the file
        response = self.client.arequest(
            "POST",
            self.path + f"({contact_id})/UploadFile?$expand=Attachments",
            files=files,
        )

        return await response

    async def _adownload_file(
        self, file_url: str, retries: int = 3, timeout: int = 10
    ) -> httpx.Response:
        """Download the file from the provided URL with retry logic and error handling."""
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(file_url, timeout=timeout)
                    response.raise_for_status()
                    return response
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    raise httpx.HTTPStatusError(
                        f"Failed to download file from {file_url} after {retries} attempts"
                    ) from e

    async def acheck_duplicate_contact(self, payload: dict):
        """
        Checks for a duplicate contact by sending a POST request to the API.

        Args:
            payload (dict): Data containing the necessary parameters to check for duplicates.

        Returns:
            dict: The JSON response from the server containing the result.
        """
        
        return await self.client.arequest(
            "POST", self.path + "/IsDuplicate", payload=payload
        )

    def check_duplicate_contact(self, payload: dict):
        """
        Checks for a duplicate contact by sending a POST request to the API.

        Args:
            payload (dict): Data containing the necessary parameters to check for duplicates.

        Returns:
            dict: The JSON response from the server containing the result.
        """
        
        return self.client.request(
            "POST", self.path + "/IsDuplicate", payload=payload
        )
