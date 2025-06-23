# utils/dataframe_helpers.py

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.api_helpers import get_applications, get_application_by_id, get_application_controls, get_frameworks, get_vendor_data
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
    client = get_client(client_id)

    # Retrieve application data from the API
    apps_response = get_applications(client)
    
    if not apps_response:
        print("No application data found")
        return pd.DataFrame()

    # Create master list of all applications
    master_apps = []
    for app in apps_response:
        app_id = app['application_id']
        application_name = app['application_name']
        frameworks_in_scope = app.get('frameworks_in_scope', []) or []
        
        # If no frameworks in scope, still include the application
        if not frameworks_in_scope:
            master_apps.append({
                'application_id': app_id,
                'application_name': application_name,
                'framework_id': '',
            })
        else:
            # Create a row for each framework
            for framework in frameworks_in_scope:
                master_apps.append({
                    'application_id': app_id,
                    'application_name': application_name,
                    'framework_id': framework,
                })
    
    master_apps_df = create_df(master_apps)
    
    if master_apps_df.empty:
        print("No application data found")
        return pd.DataFrame()

    # Create a list of dictionaries for application_id
    app_list = master_apps_df[['application_id']].drop_duplicates().to_dict('records')

    # Collect controls data
    controls_list = []
    
    def get_controls_for_app(app):
        """Helper function to get controls for a single application"""
        try:
            controls_df = get_application_controls(client, app['application_id'], control_type, application_version="1.0")
            if controls_df is not None and not controls_df.empty:
                controls_df = controls_df.rename(columns={'framework': 'framework_id'})
                return controls_df
            return None
        except Exception as e:
            print(f"Error getting controls for app {app['application_id']}: {e}")
            return None
    
    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_app = {executor.submit(get_controls_for_app, app): app for app in app_list}
        
        # Collect results as they complete
        for future in as_completed(future_to_app):
            app = future_to_app[future]
            try:
                controls_df = future.result()
                if controls_df is not None:
                    controls_list.append(controls_df)
            except Exception as e:
                print(f"Error processing controls for app {app['application_id']}: {e}")

    if not controls_list:
        print("No controls data found")
        # Return empty DataFrame with correct columns based on control_type
        if control_type == 'company':
            return pd.DataFrame(columns=['framework_id', 'framework_name', 'count_controls_ready', 'total_controls'])
        else:
            return pd.DataFrame(columns=['application_id', 'application_name', 
                                       'framework_id', 'framework_name', 'count_controls_ready', 'total_controls'])

    # Combine all controls
    all_controls_df = pd.concat(controls_list, ignore_index=True)
    
    # Check if we have the required columns for grouping
    required_columns = ['application_id', 'framework_id', 'ready']
    missing_columns = [col for col in required_columns if col not in all_controls_df.columns]
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        print("Available columns:", all_controls_df.columns.tolist())
        # Return empty DataFrame with correct columns based on control_type
        if control_type == 'company':
            return pd.DataFrame(columns=['framework_id', 'framework_name', 'count_controls_ready', 'total_controls'])
        else:
            return pd.DataFrame(columns=['application_id', 'application_name', 
                                       'framework_id', 'framework_name', 'count_controls_ready', 'total_controls'])

    # Get frameworks names
    frameworks_df = create_frameworks_df(client)
    if frameworks_df.empty:
        print("No frameworks data found")
        return pd.DataFrame()
    frameworks_df = frameworks_df[['framework_id', 'framework_name']].drop_duplicates()

    # Get controls for control_type 'company'
    if control_type == 'company':
        # Filter out controls with empty framework_id
        valid_controls = all_controls_df[all_controls_df['framework_id'].notna() & (all_controls_df['framework_id'] != '')]
        
        if valid_controls.empty:
            print("No controls with valid frameworks found")
            return pd.DataFrame(columns=['framework_id', 'framework_name', 'count_controls_ready', 'total_controls'])
        
        # Get unique controls per framework
        unique_controls = valid_controls.drop_duplicates(['framework_id', 'control_id'])
        
        # Aggregate at framework level
        result = unique_controls.groupby(['framework_id']).agg(
            count_controls_ready=('ready', lambda x: sum(x == True)),
            total_controls=('ready', 'count')
        ).reset_index()

        # Merge with frameworks_df
        result = pd.merge(
            result,
            frameworks_df,
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
        result = all_controls_df.groupby(['application_id', 'framework_id']).agg(
            count_controls_ready=('ready', lambda x: sum(x == True)),
            total_controls=('ready', 'count')
        ).reset_index()

        # Map framework_name from frameworks_df
        result = pd.merge(
            result,
            frameworks_df,
            on='framework_id',
            how='left'
        )

        # Join back to master_apps_df to include all applications
        result = pd.merge(
            master_apps_df[['application_id', 'application_name']].drop_duplicates(),
            result,
            on=['application_id'],
            how='left'
        )

        # Reorder columns
        result = result[['application_id', 
                        'application_name',
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
    apps_response = get_applications(client)
    
    if not apps_response:
        print("No application data found")
        return pd.DataFrame()

    # Extract fields from response
    extracted_data = []
    for app in apps_response:
        extracted_data.append({
            'application_id': app['application_id'],
            'application_name': app['application_name'],
            'vendor_id': app.get('vendor_id', ''),
            'application_risk': app.get('assigned_risk_level', ''),
            'application_source': app.get('application_source', ''),
            'application_development_status': app.get('application_development_status', ''),
            'application_approval_status': app.get('approval_status', '')
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
    apps_response = get_applications(client)
    
    if not apps_response:
        print("No application data found")
        return pd.DataFrame()

    # First create a DataFrame with all applications
    all_apps_data = []
    risk_data = []
    
    for app in apps_response:
        app_id = app['application_id']
        app_name = app['application_name']
        
        all_apps_data.append({
            'application_id': app_id,
            'application_name': app_name,
            'application_risk_level': app.get('assigned_risk_level', None)
        })
    
    all_apps_df = create_df(all_apps_data)
    
    # Get detailed application information using parallel processing
    def get_app_details(app):
        """Helper function to get detailed application information"""
        try:
            app_id = app['application_id']
            app_details = get_application_by_id(client, app_id)
            return app_id, app_details
        except Exception as e:
            print(f"Error getting details for app {app['application_id']}: {e}")
            return app['application_id'], None
    
    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_app = {executor.submit(get_app_details, app): app for app in apps_response}
        
        # Collect results as they complete
        for future in as_completed(future_to_app):
            app = future_to_app[future]
            try:
                app_id, app_details = future.result()
                
                # Process risk data from full application details
                if app_details and app_details.get('risk_item_list'):
                    for risk_item in app_details['risk_item_list']:
                        risk_data.append({
                            'application_id': app_id,
                            'risk_type': risk_item.get('risk_type_label', ''),
                            'severity': risk_item.get('severity', ''),
                            'probability': risk_item.get('probability', ''),
                        })
            except Exception as e:
                print(f"Error processing details for app {app['application_id']}: {e}")

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
