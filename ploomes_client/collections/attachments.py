import httpx
import json
from ploomes_client.core.ploomes_client import PloomesClient


class Attachments:
    def __init__(self, client: PloomesClient) -> None:
        self.client = client
        self.path = "/Attachments"

    async def aget_attachments_folder(
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
        Retrieves attachments based on the provided filters.

        Args:
            filter_ (str, optional): OData filter string.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.
            top (int, optional): Maximum number of results to return.
            expand (str, optional): Expand related entities.

        Returns:
            dict: The JSON response from the server containing the attachments.
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
            self.path + "@Folders",
            filters={k: v for k, v in filters.items() if v is not None},
        )

    async def apost_attachments_folder(
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
            self.path + "@Folders",
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )

    async def apatch_attachment_folder(
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
        Updates a attachment by its ID with specific fields.

        Args:
            id_ (int): The ID of the attachment to be updated.
            payload (dict): Fields to be updated in the attachment.
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
            self.path + f"@Folders({id_})",
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )

    async def adelete_attachment_folder(self, id_: int):
        """
        Deletes a attachment by its ID.

        Args:
            id_ (int): The ID of the attachment to be deleted.

        Returns:
            dict: The JSON response from the server.
        """
        return await self.client.arequest("DELETE", self.path + f"@Folders({id_})")

    async def apost_attachment(self, file_url: str, folder_id: int):
        # Download the file from the URL
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url, stream=True)
            response.raise_for_status()

            # Extract filename
            filename = file_url.split("/")[-1]

            # Prepare multipart/form-data payload
            files = {
                "file": (
                    filename,
                    await response.aread(),
                    response.headers["Content-Type"],
                )
            }
            data = {"folderId": str(folder_id)}

            # Headers including the User-Key
            headers = {"User-Key": self.client.api_key}

            # POST request
            upload_response = await client.post(
                "https://public-api2.ploomes.com/Attachments@Items/FormData",
                files=files,
                data=data,
                headers=headers,
            )

            upload_response.raise_for_status()
            upload_response_json = upload_response.json()

            return {
                "@odata.context": upload_response_json["@odata.context"],
                "value": upload_response_json.get("value"),
            }

    async def apatch_attachment(
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
        Updates a attachment by its ID with specific fields.

        Args:
            id_ (int): The ID of the attachment to be updated.
            payload (dict): Fields to be updated in the attachment.
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
            self.path + f"@Items({id_})",
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )

    async def adelete_attachment(self, id_: int):
        """
        Deletes a attachment by its ID.

        Args:
            id_ (int): The ID of the attachment to be deleted.

        Returns:
            dict: The JSON response from the server.
        """
        return await self.client.arequest("DELETE", self.path + f"@Items({id_})")
