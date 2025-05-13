# utils/fairnow.py

from getpass import getpass

import httpx
from httpx_auth import OAuth2ClientCredentials


def export_to_tsv(df, output_file='export.tsv'):
    """
    Export a DataFrame to a TSV file.
    
    Args:
        df: pandas DataFrame to export
        output_file (str): Name of the output file (default: 'export.tsv')
    """
    if df is not None and not df.empty:
        df.to_csv(output_file, sep='\t', index=False)
        print(f"\nData exported to {output_file}")
    else:
        print("No data to export")


def get_client(client_id):
    """
    Create and return an authenticated FairNow API client.
    
    Note:
        Replace the client_id with your FairNow client ID.
        The client secret will be prompted for at runtime.   
    """
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
