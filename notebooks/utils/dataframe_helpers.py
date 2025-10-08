import pandas as pd
from utils.api_helpers import get_application_data, get_frameworks, get_vendor_data, get_application_by_id, get_controls
from utils.fairnow import get_client
from concurrent.futures import ThreadPoolExecutor, as_completed


def create_df(api_response):
    """
    Create a pandas DataFrame from a JSON response.
    """
    # Convert to DataFrame
    df = pd.DataFrame(api_response)
    df = df.drop_duplicates()
    return pd.DataFrame(df)


def create_application_compliance_df(client_id) -> pd.DataFrame:
    """
    Create a pandas DataFrame from the application compliance data.
    """
    client = get_client(client_id)

    def build_raw_application_controls(client) -> pd.DataFrame:
        applications_list = get_application_data(client)

        if not applications_list:
            print("[DEBUG] No applications returned from API.")
            return pd.DataFrame()

        all_rows = []

        def process_app(app):
            app_id = app.get("id")
            app_name = app.get("name")

            app_json = get_application_by_id(client, app_id)
            if not app_json:
                return []

            controls_dict = {c.get("id"): c for c in app_json.get("controls", [])}
            frameworks = app_json.get("frameworks", [])

            rows = []

            if not frameworks:
                # No frameworks attached: still include a placeholder row for application_id
                rows.append({
                    "application_id": app_id,
                    "application_name": app_name,
                    "framework_id": pd.NA,
                    "framework_name": pd.NA,
                    "control_id": pd.NA,
                    "control_status": pd.NA,
                    "control_implemented": pd.NA,
                })
                return rows

            for fw in frameworks:
                fw_id = fw.get("id")
                fw_name = fw.get("name")
                for req in fw.get("requirements", []):
                    for ctrl_link in req.get("control_links", []):
                        ctrl_id = ctrl_link.get("id")
                        ctrl = controls_dict.get(ctrl_id, {})
                        status = ctrl.get("status", {})
                        rows.append({
                            "application_id": app_id,
                            "application_name": app_name,
                            "framework_id": fw_id,
                            "framework_name": fw_name,
                            "control_id": ctrl_id,
                            "control_status": status.get("control_state"),
                            "control_implemented": status.get("is_complete"),
                        })
            return rows

        # Parallelize fetching
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(process_app, app): app for app in applications_list}
            for future in as_completed(futures):
                rows = future.result()
                if rows:
                    all_rows.extend(rows)

        raw_df = pd.DataFrame(all_rows)

        if not raw_df.empty:
            raw_df = raw_df.drop_duplicates(subset=["application_id", "framework_id", "control_id"])

        return raw_df


    def aggregate_compliance(raw_df: pd.DataFrame) -> pd.DataFrame:
        if raw_df.empty:
            return pd.DataFrame()

        # Keep only ACTIVE controls
        active_df = raw_df[raw_df["control_status"] == "ACTIVE"].copy()

        # Standard aggregation per application + framework
        summary_df = (
            active_df.groupby(
                ["application_id", "application_name", "framework_id", "framework_name"],
                as_index=False
            )
            .agg(
                count_controls_ready=("control_implemented", lambda x: x.sum(skipna=True)),
                count_controls_total=("control_implemented", "count"),
            )
        )

        # Find apps that had no frameworks (framework_id is pd.NA)
        apps_with_no_frameworks = raw_df[raw_df["framework_id"].isna()][["application_id", "application_name"]].drop_duplicates()
        if not apps_with_no_frameworks.empty:
            for _, row in apps_with_no_frameworks.iterrows():
                summary_df = pd.concat([
                    summary_df,
                    pd.DataFrame([{
                        "application_id": row["application_id"],
                        "application_name": row["application_name"],
                        "framework_id": pd.NA,
                        "framework_name": pd.NA,
                        "count_controls_ready": pd.NA,
                        "count_controls_total": pd.NA,
                    }])
                ], ignore_index=True)

        # Ensure integer type for counts where applicable
        summary_df["count_controls_ready"] = summary_df["count_controls_ready"].astype("Int64")
        summary_df["count_controls_total"] = summary_df["count_controls_total"].astype("Int64")

        summary_df = summary_df.sort_values(by="application_name", ascending=True).reset_index(drop=True)

        return summary_df

    raw_df = build_raw_application_controls(client)
    final_df = aggregate_compliance(raw_df)
    return final_df


def create_company_compliance_df(client_id) -> pd.DataFrame:
    """
    Create a pandas DataFrame summarizing company-level compliance by framework.
    Only frameworks with at least one ACTIVE company-level control are included.
    """
    client = get_client(client_id)

    def build_raw_company_controls(client) -> pd.DataFrame:
        frameworks_list = get_frameworks(client)
        controls_list = get_controls(client)

        if not frameworks_list:
            return pd.DataFrame()

        # Only COMPANY type controls
        controls_dict = {c["id"]: c for c in controls_list if c.get("type") == "COMPANY"}

        all_rows = []

        def process_framework(fw):
            fw_id = fw.get("id")
            fw_name = fw.get("name")
            rows = []

            for req in fw.get("requirements", []):
                for ctrl_link in req.get("control_links", []):
                    ctrl_id = ctrl_link.get("id")
                    ctrl = controls_dict.get(ctrl_id)
                    if not ctrl:
                        continue
                    status = ctrl.get("status", {})
                    rows.append({
                        "framework_id": fw_id,
                        "framework_name": fw_name,
                        "control_id": ctrl_id,
                        "control_status": status.get("control_state"),
                        "control_implemented": status.get("is_complete"),
                    })

            # Only keep frameworks with at least one ACTIVE control
            active_rows = [r for r in rows if r.get("control_status") == "ACTIVE"]
            if active_rows:
                return active_rows
            else:
                return []

        # Parallelize per framework
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(process_framework, fw): fw for fw in frameworks_list}
            for future in as_completed(futures):
                rows = future.result()
                if rows:
                    all_rows.extend(rows)

        raw_df = pd.DataFrame(all_rows)
        if not raw_df.empty:
            raw_df = raw_df.drop_duplicates(subset=["framework_id", "control_id"])

        return raw_df

    def aggregate_company_compliance(raw_df: pd.DataFrame) -> pd.DataFrame:
        if raw_df.empty:
            print("[DEBUG] No raw data to aggregate.")
            return pd.DataFrame()

        summary_df = (
            raw_df.groupby(
                ["framework_id", "framework_name"],
                as_index=False
            )
            .agg(
                count_controls_ready=("control_implemented", lambda x: x.sum(skipna=True)),
                count_controls_total=("control_implemented", "count"),
            )
        )

        summary_df["count_controls_ready"] = summary_df["count_controls_ready"].astype("Int64")
        summary_df["count_controls_total"] = summary_df["count_controls_total"].astype("Int64")

        summary_df = summary_df.sort_values(by="framework_name", ascending=True).reset_index(drop=True)
        return summary_df

    raw_df = build_raw_company_controls(client)
    final_df = aggregate_company_compliance(raw_df)
    return final_df


def create_inventory_df(client_id):
    """
    Create a pandas DataFrame from the inventory data.
    Includes all applications, joining vendor info when available.
    """
    
    client = get_client(client_id) # Replace with your Client Id

    # Retrieve application data from the API
    applications = get_application_data(client)

    if not applications:
        print("ERROR: No applications found")
        return pd.DataFrame()

    # Extract fields from response
    extracted_data = []
    for app in applications:
        app_id = app['id']
        app_name = app['name']
        vendor_id = ''
        # Extract vendor_id from vendor_links if present
        vendor_links = app.get('vendor_links', [])
        if vendor_links:
            vendor_id = vendor_links[0].get('vendor_id', '')
        
        application_source = app.get('source', '')
        application_development_status = app.get('development_status', '')
        
        # Extract approval status
        approval_statuses = app.get('approval_statuses', [])
        application_approval_status = ''
        if approval_statuses:
            application_approval_status = approval_statuses[0].get('status', '')
        
        extracted_data.append({
            'application_id': app_id,
            'application_name': app_name,
            'vendor_id': vendor_id,
            'application_source': application_source,
            'application_development_status': application_development_status,
            'application_approval_status': application_approval_status,
        })

    # Convert to DataFrame
    apps_df = create_df(extracted_data)
    
    # Retrieve vendor data from the API
    vendors_response = get_vendor_data(client)
    
    if not vendors_response:
        print("WARNING: No vendor data found, adding empty vendor columns")
        apps_df['vendor_name'] = ''
        apps_df['vendor_status'] = ''
        return apps_df

    # Extract fields from response
    vendor_data = []
    for vendor in vendors_response:
        vendor_id = vendor.get('id', '')
        vendor_name = vendor.get('name', '')
        vendor_status = vendor.get('status', '')
        vendor_data.append({
            'vendor_id': vendor_id,
            'vendor_name': vendor_name,
            'vendor_status': vendor_status,
        })

    # Convert to DataFrame
    vendors_df = create_df(vendor_data)
    
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
    applications = get_application_data(client)
    
    if not applications:
        print("ERROR: No applications found")
        return pd.DataFrame()

    # First create a DataFrame with all applications
    all_apps_data = []
    for app in applications:
        assessed_risk_level = app.get('assessed_risk_level', None)
        all_apps_data.append({
            'application_id': app['id'],
            'application_name': app['name'],
            'assessed_risk_level': assessed_risk_level
        })
    all_apps_df = create_df(all_apps_data)

    # Create a DataFrame from the risk data
    risk_data = []
    for app in applications:
        app_id = app['id']
        risk_items = app.get('assigned_risk_items', []) or []
        for risk_item in risk_items:
            risk_data.append({
                'application_id': app_id,
                'risk_type': risk_item.get('risk_type', ''),
                'severity': risk_item.get('severity', ''),
                'probability': risk_item.get('probability', ''),
                'description': risk_item.get('description', '')
            })

    # Convert risk data to DataFrame
    risk_df = create_df(risk_data)
    
    if risk_df.empty:
        print("WARNING: No risk data found")
        return all_apps_df  # Return apps without risk data

    # Merge all applications with risk data
    result = pd.merge(
        all_apps_df,
        risk_df,
        on='application_id',
        how='left'
    )
    return result
