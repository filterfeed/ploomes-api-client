import json


class Response:
    """A class to represent the response from a Ploomes request.

    Attributes:
        raw (dict): The raw data of the response request.
    """

    def __init__(self, raw):
        self.raw = raw

    @property
    def first(self):
        """Retrieve the first value from the "value" attribute.

        Returns:
            The first value if present; None otherwise.
        """
        values = self.raw.get("value")
        return values[0] if values else None

    @property
    def all(self):
        """Retrieve all values from the "value" attribute.

        Returns:
            list: All values in the "value" attribute; an empty list if not present.
        """
        return self.raw.get("value", [])

    def to_json(self):
        """Serialize the raw data to a JSON formatted string.

        Returns:
            str: A JSON formatted string representing the raw data.
        """
        return json.dumps(self.raw)
