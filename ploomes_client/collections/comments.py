import json
from ploomes_client.core.ploomes_client import PloomesClient


class Comments:
    def __init__(self, client: PloomesClient) -> None:
        self.client = client
        self.path = "/Comments"

    async def apatch_comment(
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
        Updates an interaction record by its ID with specific fields.

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

    async def adelete_comment(self, id_: int):
        """
        Deletes a contact by its ID.

        Args:
            id_ (int): The ID of the contact to be deleted.

        Returns:
            dict: The JSON response from the server.
        """
        return await self.client.arequest(
            "DELETE",
            self.path + f"({id_})",
        )
