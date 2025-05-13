# utils/api_helpers.py


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
