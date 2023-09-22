import json
from ploomes_client.core.ploomes_client import PloomesClient


class Tasks:
    def __init__(self, client: PloomesClient) -> None:
        self.client = client
        self.path = "/Tasks"

    def get_tasks(
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
        Retrieves tasks based on the provided filters.

        Args:
            filter_ (str, optional): OData filter string.
            inlinecount (str, optional): Option for inline count.
            orderby (str, optional): Order by clause.
            select (str, optional): Select specific properties.
            skip (int, optional): Number of results to skip.
            top (int, optional): Maximum number of results to return.
            expand (str, optional): Expand related entities.

        Returns:
            dict: The JSON response from the server containing the tasks.
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

    def post_task(
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
        """
        Creates a new task.

        Args:
            payload (dict): The task data.
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
            "POST",
            self.path,
            filters={k: v for k, v in filters.items() if v is not None},
            payload=payload_json,
        )

    def patch_task(
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
        Updates a task by its ID.

        Args:
            id_ (int): The ID of the task.
            payload (dict): The new data for the task.
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

    def delete_task(self, id_: int):
        """
        Deletes a task by its ID.

        Args:
            id_ (int): The ID of the task.

        Returns:
            dict: The JSON response from the server.
        """
        return self.client.request(
            "DELETE",
            self.path + f"({id_})",
        )
