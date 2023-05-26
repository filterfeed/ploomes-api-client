# Ploomes API Python Client

This package provides a simple Python client for the [Ploomes API](https://developers.ploomes.com/).

## Installation

You can install the package from PyPI:

```bash
pip install ploomes-api-client
```

## Usage

First, import the `PloomesClient` class:

```python
from ploomes_client import PloomesClient
```

Next, create an instance of the `PloomesClient` class, passing your API key as a parameter:

```python
ploomes = PloomesClient('your_api_key_here')
```

Now you can use the methods of the `PloomesClient` class to interact with the API.

```python
# Get user account
user_account = ploomes.get_user_account()

# Create a contact
response = ploomes.create_contact(
    Name='John Doe',
    Email='johndoe@example.com',
    City='City',
    State='State',
    StreetAddress='Street Address',
    Neighborhood='Neighborhood',
    ZipCode='ZipCode',
    Register='Register',
    StreetAddressNumber='StreetAddressNumber',
    Phones=[{'PhoneNumber': '1234567890'}],
    OtherProperties={'Property': 'Value'}
)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
