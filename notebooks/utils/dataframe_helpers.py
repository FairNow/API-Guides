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
    If control_type is 'company', returns framework-level aggregation.
    If control_type is 'application', returns application + framework-level details.
    """
    client = get_client(client_id) # Replace with your Client Id

    # Retrieve application data from the API
    apps_response = get_application_data(client)
    
    if not apps_response or 'applications' not in apps_response or not apps_response['applications']:
        print("No application data found")
        return pd.DataFrame()

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
            })
    apps_df = create_df(extracted_data)
    
    if apps_df.empty:
        print("No framework data found in applications")
        return pd.DataFrame()

    # Create a list of dictionaries for application_id and application_version
    app_version_df = apps_df[['application_id', 'application_version']].drop_duplicates().to_dict('records')

   # Collect controls data
    controls_list = []
    for app in app_version_df:
        controls_df = get_application_controls(client, app['application_id'], app['application_version'], control_type)
        if controls_df is not None:
            controls_df = controls_df.rename(columns={'framework': 'framework_id'})
            controls_list.append(controls_df)

    if not controls_list:
        print("No controls data found")
        return pd.DataFrame()

    # Combine all controls
    all_controls_df = pd.concat(controls_list, ignore_index=True)

    # Get controls for control_type 'company'
    if control_type == 'company':
        # Get unique controls per framework
        unique_controls = all_controls_df.drop_duplicates(['framework_id', 'control_id'])
        
        # Aggregate at framework level
        result = unique_controls.groupby(['framework_id']).agg(
            count_controls_ready=('ready', lambda x: sum(x == True)),
            total_controls=('ready', 'count')
        ).reset_index()

        # Get frameworks names
        frameworks_df = create_frameworks_df(client)
        if frameworks_df.empty:
            print("No frameworks data found")
            return pd.DataFrame()
            
        frameworks_df = frameworks_df[['framework_id', 'framework_name']]
        frameworks_df = frameworks_df.drop_duplicates()

        # Merge with frameworks_df
        result = pd.merge(
            result,
            frameworks_df[['framework_id', 'framework_name']],
            on='framework_id',
            how='left'
        )

        # Reorder columns
        result = result[['framework_id', 
                        'framework_name', 
                        'count_controls_ready', 
                        'total_controls']]

    # Get controls for control_type 'application'
    else:
        # Aggregate controls data with application details
        result = all_controls_df.groupby(['application_id', 'application_version', 'framework_id']).agg(
            count_controls_ready=('ready', lambda x: sum(x == True)),
            total_controls=('ready', 'count')
        ).reset_index()

        # Map application_name from apps_df using application_id and application_version
        app_names = apps_df[['application_id', 'application_version', 'application_name']].drop_duplicates()
        result = pd.merge(
            result,
            app_names,
            on=['application_id', 'application_version'],
            how='left'
        )

        # Map framework_name from frameworks_df using framework_id
        frameworks_df = create_frameworks_df(client)
        if frameworks_df.empty:
            print("No frameworks data found")
            return pd.DataFrame()
        result = pd.merge(
            result,
            frameworks_df[['framework_id', 'framework_name']],
            on='framework_id',
            how='left'
        )

        # Reorder columns
        result = result[['application_id', 
                        'application_name',
                        'application_version', 
                        'framework_id', 
                        'framework_name',
                        'count_controls_ready', 
                        'total_controls']]

    result = result.drop_duplicates()
    return result


def create_frameworks_df(client):
    """
    Create a pandas DataFrame from the frameworks data.
    """
    frameworks_response = get_frameworks(client)

    if not frameworks_response:
        print("No frameworks data received")
        return pd.DataFrame()
    else:
        df = pd.DataFrame(frameworks_response)
        if df.empty:
            print("No frameworks data found")
            return pd.DataFrame()
        return df[['framework_id', 'framework_name']]


def create_inventory_df(client_id):
    """
    Create a pandas DataFrame from the inventory data.
    Includes all applications, joining vendor info when available.
    """
    client = get_client(client_id) # Replace with your Client Id

    # Retrieve application data from the API
    apps_response = get_application_data(client)
    
    if not apps_response or 'applications' not in apps_response or not apps_response['applications']:
        print("No application data found")
        return pd.DataFrame()

    # Extract fields from response
    extracted_data = []
    for app in apps_response['applications']:
        app_id = app['application_id']
        app_name = app['application_name']
        vendor_id = app.get('vendor_id', '')
        risk_metadata = app.get('risk_metadata', {}) or {}
        application_risk = risk_metadata.get('risk_framework_level', '')
        application_source = app.get('application_source', '')
        application_development_status = app.get('application_development_status', '')
        application_approval_status = app.get('approval_status', '')
        extracted_data.append({
            'application_id': app_id,
            'application_name': app_name,
            'vendor_id': vendor_id,
            'application_risk': application_risk,
            'application_source': application_source,
            'application_development_status': application_development_status,
            'application_approval_status': application_approval_status,
        })

    # Convert to DataFrame
    apps_df = create_df(extracted_data)
    
    # Retrieve vendor data from the API
    response = get_vendor_data(client)
    
    if not response:
        print("No vendor data found")
        apps_df['vendor_name'] = ''
        apps_df['vendor_status'] = ''
        return apps_df

    # Extract fields from response
    extracted_data = []
    for vendor in response:
        vendor_id = vendor.get('vendor_id', '')
        vendor_name = vendor.get('vendor_name', '')
        vendor_status = vendor.get('status', '')
        extracted_data.append({
            'vendor_id': vendor_id,
            'vendor_name': vendor_name,
            'vendor_status': vendor_status,
        })

    # Convert to DataFrame
    vendors_df = create_df(extracted_data)
    
    # Merge DataFrames
    merged_df = pd.merge(
        apps_df,
        vendors_df,
        on='vendor_id',
        how='left'
    )
    merged_df = merged_df.drop_duplicates()

    merged_df = merged_df[[
        'application_id',
        'application_name',
        'application_source',
        'application_development_status',
        'application_approval_status',
        'application_risk',
        'vendor_id',
        'vendor_name',
        'vendor_status'
    ]]
    return merged_df


def create_risks_df(client_id):
    """
    Create a pandas DataFrame from the risks data.
    Returns all applications, with null values for those without risk information.
    """
    client = get_client(client_id) # Replace with your Client Id

    # Retrieve application data from the API
    apps_response = get_application_data(client)
    
    if not apps_response or 'applications' not in apps_response or not apps_response['applications']:
        print("No application data found")
        return pd.DataFrame()

    # First create a DataFrame with all applications
    all_apps_data = []
    for app in apps_response['applications']:
        risk_metadata = app.get('risk_metadata', {}) or {}
        application_risk_level = risk_metadata.get('risk_framework_level', None)
        all_apps_data.append({
            'application_id': app['application_id'],
            'application_name': app['application_name'],
            'application_risk_level': application_risk_level
        })
    all_apps_df = create_df(all_apps_data)

    # Create a DataFrame from the risk data
    risk_data = []
    for app in apps_response['applications']:
        app_id = app['application_id']
        risk_items = app.get('risk_item_list', []) or []
        for risk_item in risk_items:
            risk_data.append({
                'application_id': app_id,
                'risk_type': risk_item.get('risk_type_label', ''),
                'severity': risk_item.get('severity', ''),
                'probability': risk_item.get('probability', ''),
            })

    # Convert risk data to DataFrame
    risk_df = create_df(risk_data)
    
    if risk_df.empty:
        print("No risk data found")
        return pd.DataFrame()

    # Merge all applications with risk data
    result = pd.merge(
        all_apps_df,
        risk_df,
        on='application_id',
        how='left'
    )
    
    return result
