# utils/fairnow.py
from getpass import getpass
import httpx
from httpx_auth import OAuth2ClientCredentials

def get_client():

    client_id = "{client_id}" # Replace with your Client Id
    client_secret = getpass("Client Secret: ")
    fairnow_token_endpoint = "https://auth.fairnow.dev/oauth2/token"

    auth = OAuth2ClientCredentials(
        token_url=fairnow_token_endpoint,
        client_id=client_id,
        client_secret=client_secret,
    )

    fairnow_base_url = "https://api.fairnow.dev/v2"
    client = httpx.Client(base_url=fairnow_base_url, auth=auth)
    return client
