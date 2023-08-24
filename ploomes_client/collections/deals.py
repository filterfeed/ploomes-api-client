import json
from ploomes_client.core.ploomes_client import PloomesClient


class Deals:
    def __init__(self, client: PloomesClient) -> None:
        self.client = client
        self.path = "/Deals"

    def get_deals(
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
        Retrieves deals based on the provided filters.

        Args:
            filter_ (str, optional): OData filter string.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.
            top (int, optional): Maximum number of results to return.
            expand (str, optional): Expand related entities.

        Returns:
            dict: The JSON response from the server containing the deals.
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
            self.path,
            filters={k: v for k, v in filters.items() if v is not None},
        )

    def post_deal(
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
        payload_json = json.dumps(payload)
        return self.client.request(
            "POST",
            self.path,
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload_json,
        )

    def patch_deal(
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
        Updates a deal by its ID with specific fields.

        Args:
            id_ (int): The ID of the deal to be updated.
            payload (dict): Fields to be updated in the deal.
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
        payload_json = json.dumps(payload)
        return self.client.request(
            "PATCH",
            self.path + f"({id_})",
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload_json,
        )

    def delete_deal(self, id_: int):
        """
        Deletes a deal by its ID.

        Args:
            id_ (int): The ID of the deal to be deleted.

        Returns:
            dict: The JSON response from the server.
        """
        return self.client.request(
            "DELETE",
            self.path + f"({id_})",
        )
