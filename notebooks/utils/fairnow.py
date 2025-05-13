# utils/fairnow.py

from getpass import getpass

import httpx
import pandas as pd
from httpx_auth import OAuth2ClientCredentials

__all__ = ['create_df', 'export_to_tsv', 'get_client', 'get_application_data']


def create_df(api_response):
    """
    Create a pandasDataFrame from a JSON response.
    """
    # Convert to DataFrame
    df = pd.DataFrame(api_response)
    df = df.drop_duplicates()
    return pd.DataFrame(df)


def create_compliance_df(client_id):
    """
    Create a pandas DataFrame from the compliance data.
    """
    client = get_client(client_id) # Replace with your Client Id

    # Retrieve application data from the API
    apps_response = get_application_data(client)

    # Extract fields from response
    extracted_data = []
    for app in apps_response['applications']:
        app_id = app['application_id']
        app_name = app['application_name']
        risk_assessment = app.get('risk_assessment', {})
        framework_items = risk_assessment.get('framework_assessment_items', []) or []
        for framework in framework_items:
            extracted_data.append({
                'application_id': app_id,
                'application_name': app_name,
                'framework_id': framework.get('framework_id', ''),
                'framework_name': framework.get('framework_name', ''),
            })

    # Convert to DataFrame
    apps_df=create_df(extracted_data)
    
    # Get Framework IDs for each entry in Applications DataFrame
    framework_ids = apps_df['framework_id'].unique()

    # Get controls for each framework
    controls_data = []
    for framework_id in framework_ids:
        controls = get_framework_controls(client, framework_id)
        if controls:
            # Add framework_id to each control record
            for control in controls:
                control['framework_id'] = framework_id
            controls_data.extend(controls)

    # Convert to DataFrame
    controls_df = create_df(controls_data)

    # Merge with the original DataFrame
    # This will add the control information to each framework row
    merged_df = pd.merge(
        apps_df[['application_id', 'application_name', 'framework_id', 'framework_name']],
        controls_df[['framework_id', 'applications_count', 'applications_ready']],
        on='framework_id',
        how='left'
    )
    merged_df = merged_df.drop_duplicates()
    print(f"Extracted {len(merged_df)} records")
    return merged_df


def create_inventory_df(client_id):
    """
    Create a pandas DataFrame from the inventory data.
    """
    client = get_client(client_id) # Replace with your Client Id

    # Retrieve application data from the API
    apps_response = get_application_data(client)

    # Extract fields from response
    extracted_data = []
    for app in apps_response['applications']:
        app_id = app['application_id']
        app_name = app['application_name']
        risk_level = app.get('risk_level', '')
        vendor_id = app.get('vendor_id', '')
        extracted_data.append({
            'application_id': app_id,
            'application_name': app_name,
            'risk_level': risk_level,
            'vendor_id': vendor_id,
        })

    # Convert to DataFrame
    apps_df = create_df(extracted_data)

    # Retrieve vendor data from the API
    response = get_vendor_data(client)

    # Extract fields from response
    extracted_data = []
    for vendor in response:
        # Get vendor information
        vendor_id = vendor.get('vendor_id', '')
        vendor_name = vendor.get('vendor_name', '')
        status = vendor.get('status', '')
        
        # Get governance information
        governance = vendor.get('governance', {})
        risk_program = governance.get('risk_program', '') if governance else ''
        
        # Get linked applications
        linked_apps = vendor.get('linked_applications', [])
        # Only include vendors with linked applications
        if linked_apps:
            for linked_app in linked_apps:
                extracted_data.append({
                    'application_id': linked_app.get('application_id', ''),
                    'vendor_id': vendor_id,
                    'vendor_name': vendor_name,
                    'status': status,
                    'risk_program': risk_program
                })

    # Convert to DataFrame
    vendors_df = create_df(extracted_data)

    # Merge DataFrames
    merged_df = pd.merge(
        apps_df[['application_id', 'application_name', 'risk_level', 'vendor_id']],
        vendors_df[['vendor_id', 'vendor_name', 'status', 'risk_program']],
        on='vendor_id',
        how='left'
    )
    merged_df = merged_df.drop_duplicates()
    print(f"Extracted {len(merged_df)} records")
    return merged_df


def create_risks_df(client_id):
    """
    Create a pandas DataFrame from the risks data.
    """
    client = get_client(client_id) # Replace with your Client Id

    # Retrieve application data from the API
    apps_response = get_application_data(client)

    # Create a DataFrame from the application data
    apps_data = []
    for app in apps_response['applications']:
        app_id = app['application_id']
        app_name = app['application_name']
        risk_items = app.get('risk_item_list', []) or []
        for risk_item in risk_items:
            apps_data.append({
                'application_id': app_id,
                'application_name': app_name,
                # 'risk_type': risk_item.get('risk_type', ''),
                'risk_type': risk_item.get('risk_type_label', ''),
                'severity': risk_item.get('severity', ''),
                'probability': risk_item.get('probability', ''),
            })

    # Convert to DataFrame
    apps_df = create_df(apps_data)
    print(f"Extracted {len(apps_df)} records")
    return apps_df


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

def get_application_data(client):
    """
    Get application data from the FairNow API.
    """
    application_route = "/applications"

    response = None
    try:
        response = client.get(application_route, timeout=None)
        if response.status_code == 200:
            response = response.json()
            return response
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)


def get_framework_controls(client, framework_id):
    """
    Get framework controls by framework ID from the FairNow API.
    """
    application_route = f"/controls/framework/"
    query_parameters = {"framework_id": framework_id}
    framework_response = None
    
    try:
        response = client.get(application_route, params=query_parameters, timeout=None)
        if response.status_code == 200:
            framework_response = response.json()
            return framework_response
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)
        return None
    

def get_vendor_data(client):
    """
    Get vendor data from the FairNow API.
    """
    application_route = "/vendors/"

    response = None
    try:
        response = client.get(application_route, timeout=None)
        if response.status_code == 200:
            response = response.json()
            return response
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)
    