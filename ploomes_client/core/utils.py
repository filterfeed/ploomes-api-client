import secrets
import string


def get_file_url(url):
    filename = url.split("/")[-1]  # get the filename from the URL
    if "." not in filename:  # if there's no extension
        return url  # return the original URL
    # return the URL up to the query string, if present
    return url.split("?")[0]


def generate_random_alphanumeric_string(length: int) -> str:
    """
    Generates a random alphanumeric string of the specified length.

    Args:
        length (int): The desired length of the random alphanumeric string.

    Returns:
        str: A random alphanumeric string of the specified length.
    """
    alphabet = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    random_string = "".join(secrets.choice(alphabet) for i in range(length))
    return random_string


def generate_email() -> str:
    """
    Generates an email address with a long random alphanumeric string.

    The email will have the format: user{longrandomalphanumstrin}@filterfeed.pro

    Returns:
        str: The generated email address.
    """
    random_string = generate_random_alphanumeric_string(
        20
    )  # Example: length of 20 characters
    email = f"user{random_string}@filterfeed.pro"
    return email


async def aget_file_url(url):
    filename = url.split("/")[-1]  # get the filename from the URL
    if "." not in filename:  # if there's no extension
        return url  # return the original URL
    # return the URL up to the query string, if present
    return url.split("?")[0]


async def agenerate_random_alphanumeric_string(length: int) -> str:
    """
    Generates a random alphanumeric string of the specified length.

    Args:
        length (int): The desired length of the random alphanumeric string.

    Returns:
        str: A random alphanumeric string of the specified length.
    """
    alphabet = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    random_string = "".join(secrets.choice(alphabet) for i in range(length))
    return random_string


async def agenerate_email() -> str:
    """
    Generates an email address with a long random alphanumeric string.

    The email will have the format: user{longrandomalphanumstrin}@filterfeed.pro

    Returns:
        str: The generated email address.
    """
    random_string = agenerate_random_alphanumeric_string(
        20
    )  # Example: length of 20 characters
    email = f"user{random_string}@filterfeed.pro"
    return email
