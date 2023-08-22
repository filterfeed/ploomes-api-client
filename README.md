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

# Uploading to PyPI with Two-Factor Authentication

If you're encountering the "two factor auth enabled" error while trying to upload your Python package to PyPI, follow these steps to resolve the issue.

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

By following these steps, you'll be able to upload your package to PyPI successfully even with two-factor authentication enabled.
