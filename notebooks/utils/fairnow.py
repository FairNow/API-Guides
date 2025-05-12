# utils/fairnow.py

from getpass import getpass

import httpx
import pandas as pd
from httpx_auth import OAuth2ClientCredentials

def get_client(client_id):
    """
    Create and return an authenticated FairNow API client.
    
    Note:
        Replace the client_id with your FairNow client ID.
        The client secret will be prompted for at runtime.   
    """
    # client_id = "{client_id}" # Replace with your Client Id
    client_secret = getpass("Client Secret: ")
    fairnow_token_endpoint = "https://auth.fairnow.ai/oauth2/token"

    auth = OAuth2ClientCredentials(
        token_url=fairnow_token_endpoint,
        client_id=client_id,
        client_secret=client_secret,
    )

    fairnow_base_url = "https://api.fairnow.ai/v2"
    client = httpx.Client(base_url=fairnow_base_url, auth=auth)
    return client


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


def create_df(api_response):
    """
    Create a pandasDataFrame from a JSON response.
    """
    # Convert to DataFrame
    df = pd.DataFrame(api_response)
    df = df.drop_duplicates()
    print(f"Created DataFrame from API response")
    return pd.DataFrame(df)
