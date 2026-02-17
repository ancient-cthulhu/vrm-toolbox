import os
import sys
import json
import requests
import logging
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC

# Configure logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vrm_script.log')
    ]
)
logger = logging.getLogger(__name__)

# Config & endpoints
API_BASE                = "https://api.veracode.com/risk-manager/api-server"
GRAPHQL_URL             = f"{API_BASE}/v1/graphql"
APPLICATIONS_URL        = f"{API_BASE}/v1/applications"
LINK_ASSET_URL          = f"{API_BASE}/v1/assets"

# GraphQL queries & pagination
ASSETS_QUERY = """
query FetchAssets($pageNumber: Int!, $pageSize: Int!) {
  assets(
    queryFilter: {filter: {operands: []}}
    pageNumber: $pageNumber
    pageSize: $pageSize
  ) {
    pageData { 
      id 
      name 
      assetTypeLabel
      uri
    }
  }
}
"""
ASSETS_VARS = {"pageNumber": 1, "pageSize": 100}

# Run a GraphQL query with HMAC authentication
def graphql_query(query, variables):
    auth = RequestsAuthPluginVeracodeHMAC()
    
    logger.info("Sending GraphQL request")
    
    try:
        resp = requests.post(
            GRAPHQL_URL,
            auth=auth,
            headers={"Content-Type": "application/json"},
            json={"query": query, "variables": variables}
        )
        
        logger.info(f"GraphQL response: {resp.status_code}")
        
        data = resp.json()
        resp.raise_for_status()
        
        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            sys.exit(f"GraphQL error: {data['errors']}")
        
        logger.info("GraphQL request successful")
        return data["data"]
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise

# Make REST API call with HMAC authentication
def rest_api_call(method, url, payload=None, params=None):
    auth = RequestsAuthPluginVeracodeHMAC()
    
    logger.info(f"REST API: {method} {url}")
    
    try:
        resp = requests.request(
            method,
            url,
            auth=auth,
            headers={"Content-Type": "application/json"},
            json=payload,
            params=params
        )
        
        logger.info(f"REST API response: {resp.status_code}")
        
        try:
            data = resp.json()
        except json.JSONDecodeError:
            logger.warning("Response is not JSON")
            data = None
        
        resp.raise_for_status()
        logger.info("REST API request successful")
        return data
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e} - {resp.text}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise

# Fetch assets via GraphQL
def fetch_assets():
    logger.info("Fetching assets")
    result = graphql_query(ASSETS_QUERY, ASSETS_VARS)["assets"]["pageData"]
    logger.info(f"Fetched {len(result)} assets")
    return result

# Create application using REST API
def create_application(name):
    logger.info(f"Creating application: {name}")
    payload = {
        "name": name,
        "owner": "",
        "applicationValue": "UNKNOWN"
    }
    result = rest_api_call("POST", APPLICATIONS_URL, payload=payload)
    
    # Extract application ID from response
    app_id = None
    if result:
        app_id = result.get("id") or result.get("applicationId") or result.get("application", {}).get("id")
    
    if not app_id:
        logger.error(f"Could not extract application ID from response")
        raise ValueError(f"Failed to get application ID from response")
    
    logger.info(f"Application created: {name} (ID: {app_id})")
    return app_id

# Link asset to application using REST API
def link_asset_to_application(asset_uri, app_id):
    logger.info(f"Linking asset {asset_uri} to application {app_id}")
    
    payload = {
        "queryFilter": {
            "filter": {
                "operator": "AND",
                "operands": [
                    {
                        "filter": {
                            "assets": {
                                "uris": {
                                    "values": [asset_uri]
                                }
                            }
                        }
                    }
                ]
            }
        },
        "applicationIds": [app_id]
    }
    
    params = {"action": "addToApplication"}
    
    result = rest_api_call("PUT", LINK_ASSET_URL, payload=payload, params=params)
    logger.info(f"Asset linked: {asset_uri} -> {app_id}")
    return result

# Create missing apps & link assets
def create_and_link_assets():
    logger.info("Starting create and link process")
    
    assets = fetch_assets()
    created, linked = 0, 0

    # Filter only Veracode Application Profile assets
    veracode_assets = [a for a in assets if a["assetTypeLabel"] == "Veracode Application Profile"]
    logger.info(f"Found {len(veracode_assets)} Veracode Application Profile assets")

    for asset in veracode_assets:
        name = asset["name"]
        asset_id = asset["id"]
        asset_uri = asset.get("uri", asset_id)
        
        print(f"\nProcessing: {name}")
        logger.info(f"Processing: {name} (ID: {asset_id}, URI: {asset_uri})")
        
        # Create the VRM application
        print(f"  → Creating VRM Application '{name}'...")
        try:
            app_id = create_application(name)
            created += 1
            print(f"  ✓ Created (ID: {app_id})")
        except Exception as e:
            logger.error(f"Failed to create application '{name}': {e}")
            print(f"  ✗ Error: {e}")
            continue

        # Link 1-1 veracode app profiles to vrm apps
        print(f"  → Linking asset to application...")
        try:
            link_asset_to_application(asset_uri, app_id)
            linked += 1
            print(f"  ✓ Linked")
        except Exception as e:
            logger.error(f"Failed to link asset {asset_uri}: {e}")
            print(f"  ✗ Error: {e}")

    print(f"\n{'='*60}")
    print(f"Summary: {created} apps created, {linked} assets linked")
    print(f"{'='*60}")
    logger.info(f"Process completed: {created} apps created, {linked} assets linked")

# CLI menu loop
def show_menu():
    while True:
        print("\n" + "=" * 60)
        print("VRM Script Toolbox")
        print("=" * 60)
        print("1) Create and link VRM Applications to Veracode App-profiles (1 to 1)")
        print("2) Exit")
        print("=" * 60)
        choice = input("Select an option: ").strip()
        logger.info(f"User selected option: {choice}")
        
        if choice == "1":
            create_and_link_assets()
        elif choice == "2":
            logger.info("User exited")
            print("Bye!")
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print("Invalid choice; please try again.")

# Main
def main():
    logger.info("=" * 80)
    logger.info("VRM Script Toolbox started")
    logger.info("=" * 80)
    
    try:
        print("Using Veracode API credentials from ~/.veracode/credentials")
        print("To generate API credentials, go to: https://web.analysiscenter.veracode.com/login/#APICredentialsGenerator")
        logger.info("Authentication configured via ~/.veracode/credentials")
        show_menu()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nError: {e}")
        print("\nMake sure you have configured your Veracode API credentials in ~/.veracode/credentials")
        print("Format:")
        print("[default]")
        print("veracode_api_key_id = YOUR_API_KEY_ID")
        print("veracode_api_key_secret = YOUR_API_KEY_SECRET")
        raise
    finally:
        logger.info("VRM Script Toolbox ended")
        logger.info("=" * 80)

if __name__ == "__main__":
    main()
