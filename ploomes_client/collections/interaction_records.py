import json
from ploomes_client.core.ploomes_client import PloomesClient


class InteractionRecords:
    def __init__(self, client: PloomesClient) -> None:
        self.client = client
        self.path = "/InteractionRecords"

    async def get_interaction_records(
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
        Retrieves interaction records based on the provided filters.

        Args:
            filter_ (str, optional): OData filter string.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.
            top (int, optional): Maximum number of results to return.
            expand (str, optional): Expand related entities.

        Returns:
            dict: The JSON response from the server containing the interaction records.
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
        return await self.client.request(
            "GET",
            self.path,
            filters={k: v for k, v in filters.items() if v is not None},
        )

    async def post_interaction_record(
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
        
        return await self.client.request(
            "POST",
            self.path,
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )

    async def post_interaction_record_comment(
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
        filters = {
            "$filter": filter_,
            "$inlinecount": inlinecount,
            "$orderby": orderby,
            "$select": select,
            "$skip": skip,
            "$top": top,
            "$expand": expand,
        }
        
        return await self.client.request(
            "POST",
            self.path + f"({id_})" + "/NewComment",
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )

    async def patch_interaction_record(
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
            id_ (int): The ID of the interaction record to be updated.
            payload (dict): Fields to be updated in the interaction record.
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
        
        return await self.client.request(
            "PATCH",
            self.path + f"({id_})",
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload,
        )

    async def delete_interaction_record(self, id_: int):
        """
        Deletes a interaction record by its ID.

        Args:
            id_ (int): The ID of the interaction record to be deleted.

        Returns:
            dict: The JSON response from the server.
        """
        return await self.client.request(
            "DELETE",
            self.path + f"({id_})",
        )
