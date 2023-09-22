# Ploomes API Python Client

This package provides a simple Python client for interacting with the [Ploomes API](https://developers.ploomes.com/), designed with rate-limiting and exponential backoff strategies for improved resilience.

## Installation

You can install the package from PyPI:

```bash
pip install ploomes-api-client
```

## Basic Usage

### Contact Management

To manage contacts, first import the necessary classes and initialize them:

```python
from ploomes_client import PloomesClient as Ploomes
from ploomes_client.collections.contacts import Contacts
```

#### Initialize PloomesClient and Contacts Class

```python
ploomes = Ploomes(api_key='your_api_key_here')
contacts = Contacts(ploomes)
```

#### Creating a New Contact with Expanded Fields

Here is a synthetic example to demonstrate how to create a new contact with expanded `Phones` and `OtherProperties`:

```python
# Define the payload for the new contact
payload = {
    "Name": "Jane Doe",
    "Email": "janedoe@example.com",
    "Phones": [
        {"PhoneNumber": "1234567890", "Type": "Mobile"}
    ],
    "OtherProperties": {"FavoriteColor": "Blue", "Occupation": "Engineer"}
}

# Create the contact
response_json = contacts.post_contact(payload, expand="Phones,OtherProperties")
```

In this example, the `post_contact` method sends a POST request to create a new contact in Ploomes. The `payload` dictionary contains the data for the new contact, including fields like `Name`, `Email`, `Phones`, and `OtherProperties`. We also use the `expand` parameter to expand the `Phones` and `OtherProperties` fields.

By default, the `post_contact` method will return a JSON-formatted string as the response.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

# Uploading to PyPI with Two-Factor Authentication

1. Generate an API token for your PyPI account:

   - Go to the [PyPI account settings page](https://pypi.org/manage/account/token/) and log in.
   - Scroll down to the "API Tokens" section and click "Add API Token."
   - Provide a description for the token and click "Generate."
   - Copy the generated token.

2. Upload your package using the API token:

   - Open your terminal.
   - Navigate to your package directory.
   - Build the distribution files:

     ```bash
     python setup.py sdist bdist_wheel
     ```

   - Upload the distribution files using the `twine` tool and the generated API token:

     ```bash
     twine upload --verbose dist/* -u __token__ -p <API_TOKEN>
     ```

   Replace `<API_TOKEN>` with the copied API token.

3. Verify the upload:

   - Check the PyPI project page to ensure your new version is listed.

