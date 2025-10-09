def get_applications(client):
    """
    Get applications data from the FairNow API.
    """
    route = "/applications"

    response = None
    try:
        response = client.get(route, timeout=None)
        if response.status_code == 200:
            response = response.json()
            return response
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)


def get_application_by_id(client, application_id: str):
    """
    Get individual application data from the FairNow API.
    """
    route = f"/applications/{application_id}"

    response = None
    try:
        response = client.get(route, timeout=None)
        if response.status_code == 200:
            response = response.json()
            return response
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)


def get_frameworks(client):
    """
    Get framework data from the FairNow API.
    """
    route = "/frameworks"

    response = None
    try:
        response = client.get(route, timeout=None)
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
    Get controls data from the FairNow API.
    """
    route = "/controls"

    response = None
    try:
        response = client.get(route, timeout=None)
        if response.status_code == 200:
            response = response.json()
            return response
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)


def get_vendors(client):
    """
    Get vendor data from the FairNow API.
    """
    route = "/vendors"

    response = None
    try:
        response = client.get(route, timeout=None)
        if response.status_code == 200:
            response = response.json()
            return response
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(e)
