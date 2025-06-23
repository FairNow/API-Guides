# utils/api_helpers.py
import pandas as pd

def get_applications(client):
    """
    Get application data from the FairNow API.
    Returns a list of ApplicationRootResponse objects.
    """
    application_route = "/applications"

    try:
        response = client.get(application_route, timeout=None)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)
        return None


def get_application_by_id(client, application_id):
    """
    Get full application information by application ID.
    Returns application details for a specific application ID.
    """
    application_route = f"/applications/{application_id}"

    try:
        response = client.get(application_route, timeout=None)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)
        return None


def get_application_controls(client, application_id, control_type, application_version="1.0"):
    """
    Get framework controls by application ID from the FairNow API.
    Returns a DataFrame directly with essential fields.
    Note: application_version is still required by the API, defaults to "1.0".
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
                            'application_id': application_id
                        })
                else:
                    # For controls without frameworks, create a single row
                    flattened_data.append({
                        'control_id': control.get('control_id'),
                        'ready': control.get('ready'),
                        'framework': '',
                        'application_id': application_id
                    })
            
            # Create DataFrame 
            return pd.DataFrame(flattened_data)
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception in get_application_controls: {e}")
        return None


def get_frameworks(client):
    """
    Get framework data from the FairNow API.
    """
    application_route = "/frameworks"

    try:
        response = client.get(application_route, timeout=None)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)
        return None


def get_framework_controls(client, framework_id):
    """
    Get framework controls by framework ID from the FairNow API.
    """
    application_route = f"/controls/framework/"
    query_parameters = {"framework_id": framework_id}
    
    try:
        response = client.get(application_route, params=query_parameters, timeout=None)
        if response.status_code == 200:
            return response.json()
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

    try:
        response = client.get(application_route, timeout=None)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)
        return None
