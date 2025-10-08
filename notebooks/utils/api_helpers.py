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


def get_application_by_id(client, application_id: str):
    route = f"/applications/{application_id}"
    try:
        response = client.get(route, timeout=None)
        if response.status_code == 200:
            response = response.json()
            return response
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[EXCEPTION] Error fetching application {application_id}: {e}")
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


def get_controls(client):
    """
    Get framework data from the FairNow API.
    """
    application_route = "/controls"

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


def get_vendor_data(client):
    """
    Get vendor data from the FairNow API.
    """
    application_route = "/vendors"

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
