# utils/dataframe_helpers.py

import pandas as pd
from utils.api_helpers import get_application_data, get_application_controls, get_frameworks, get_vendor_data
from utils.fairnow import get_client

def create_df(api_response):
    """
    Create a pandasDataFrame from a JSON response.
    """
    # Convert to DataFrame
    df = pd.DataFrame(api_response)
    df = df.drop_duplicates()
    return pd.DataFrame(df)


def create_compliance_df(client_id, control_type):
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
        application_name = app['application_name']
        application_version = app.get('application_version', '')
        risk_assessment = app.get('risk_assessment', {})
        framework_items = risk_assessment.get('framework_assessment_items', []) or []
        for framework in framework_items:
            extracted_data.append({
                'application_id': app_id,
                'application_name': application_name,
                'application_version': application_version,
                'framework_id': framework.get('framework_id', ''),
                'framework_name': framework.get('framework_name', ''),
            })
    apps_df = create_df(extracted_data)

    # Create a list of dictionaries for application_id and application_version
    app_version_df = apps_df[['application_id', 'application_version']].drop_duplicates().to_dict('records')

   # Collect controls data
    controls_list = []
    for app in app_version_df:
        controls_df = get_application_controls(client, app['application_id'], app['application_version'], control_type)
        if controls_df is not None:
            controls_df = controls_df.rename(columns={'framework': 'framework_id'})
            controls_list.append(controls_df)

    # Combine all controls
    all_controls_df = pd.concat(controls_list, ignore_index=True)

    # Aggregate controls data
    result = all_controls_df.groupby(['application_id', 'application_version', 'framework_id']).agg(
        count_controls=('ready', lambda x: sum(x == False)),
        count_controls_ready=('ready', lambda x: sum(x == True)),
        total_controls=('ready', 'count')
    ).reset_index()

    # Get frameworks names
    frameworks_df = create_frameworks_df(client)
    frameworks_df = frameworks_df[['framework_id', 'framework_name']]
    frameworks_df = frameworks_df.drop_duplicates()

    # Merge with frameworks_df
    result = pd.merge(
        result,
        frameworks_df[['framework_id', 'framework_name']],
        on='framework_id',
        how='left'
    )

    # Merge with apps_df to get application_name
    result = pd.merge(
        result,
        apps_df[['application_id', 'application_name', 'application_version']],
        on=['application_id', 'application_version'],
        how='left'
    )

    # Reorder columns
    result = result[['application_id', 
                     'application_name',
                     'application_version', 
                     'framework_id', 
                     'framework_name', 
                     'count_controls', 
                     'count_controls_ready', 
                     'total_controls']]

    result = result.drop_duplicates()
    return result


def create_frameworks_df(client):
    """
    Create a pandas DataFrame from the frameworks data.
    """
    # client = get_client(client_id) # Replace with your Client Id
    frameworks_response = get_frameworks(client)

    if not frameworks_response:
        print("No frameworks data received")
        return pd.DataFrame()
    else:
        df = pd.DataFrame(frameworks_response)
        return df[['framework_id', 'framework_name']]


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
