# utils/api_helpers.py
import pandas as pd

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


def get_application_controls(client, application_id, application_version, control_type):
    """
    Get framework controls by framework ID from the FairNow API.
    Returns a DataFrame directly with essential fields.
    """
    application_route = f"/controls/application/"
    query_parameters = {
                        "application_id": application_id,
                        "application_version": application_version,
                        "control_type": control_type # application or company
                        }
    try:
        response = client.get(application_route, params=query_parameters, timeout=None)
        if response.status_code == 200:
            full_response = response.json()
            
            # Create flattened data for DataFrame
            flattened_data = []
            for control in full_response.get('controls', []):
                # For controls with frameworks, create a row for each framework
                frameworks = control.get('frameworks_in_scope', [])
                if frameworks:
                    for framework in frameworks:
                        flattened_data.append({
                            'control_id': control.get('control_id'),
                            'ready': control.get('ready'),
                            'framework': framework,
                            'application_id': application_id,
                            'application_version': application_version
                        })
                else:
                    # For controls without frameworks, create a single row
                    flattened_data.append({
                        'control_id': control.get('control_id'),
                        'ready': control.get('ready'),
                        'framework': '',
                        'application_id': application_id,
                        'application_version': application_version
                    })
            
            # Create DataFrame directly
            return pd.DataFrame(flattened_data)
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)
        return None


def get_frameworks(client):
    """
    Get framework data from the FairNow API.
    """
    application_route = "/frameworks"

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
