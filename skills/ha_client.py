#!/usr/bin/env python3
"""
Home Assistant REST API Client Skill.
Allows programmatic retrieval and modification of Home Assistant states and actions.
"""

import os
import sys
import json
import requests

CONFIG_PATH = "/root/.gemini/antigravity-cli/mcp_config.json"

def load_credentials():
    """Loads Home Assistant API URL and Token from mcp_config.json."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            ha_api = config.get("mcpServers", {}).get("ha_api", {})
            server_url = ha_api.get("serverUrl", "")
            # Convert https://ha.flamingotter.com/api/mcp to https://ha.flamingotter.com/api
            if server_url.endswith("/mcp"):
                api_url = server_url[:-4]
            elif server_url.endswith("/"):
                api_url = server_url[:-1]
            else:
                api_url = server_url
            
            auth_header = ha_api.get("headers", {}).get("Authorization", "")
            token = auth_header.replace("Bearer ", "").strip()
            return api_url, token
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to load config from {CONFIG_PATH}: {e}\n")
    
    # Fallbacks from environment variables
    api_url = os.environ.get("SUPERVISOR_TOKEN", "https://ha.flamingotter.com/api")
    token = os.environ.get("HASSIO_TOKEN", "")
    return api_url, token

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def get_entity_state(api_url, token, entity_id):
    """Retrieves the state and attributes of a specific entity."""
    url = f"{api_url}/states/{entity_id}"
    response = requests.get(url, headers=get_headers(token), verify=True)
    if response.status_code == 200:
        return response.json()
    else:
        sys.stderr.write(f"Error fetching state: {response.status_code} - {response.text}\n")
        sys.exit(1)

def set_entity_state(api_url, token, entity_id, state, attributes_json=None):
    """Manually updates the state and attributes of an entity."""
    url = f"{api_url}/states/{entity_id}"
    payload = {"state": state}
    if attributes_json:
        try:
            attributes = json.loads(attributes_json)
            payload["attributes"] = attributes
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Error parsing attributes JSON: {e}\n")
            sys.exit(1)
            
    response = requests.post(url, headers=get_headers(token), json=payload, verify=True)
    if response.status_code in (200, 201):
        return response.json()
    else:
        sys.stderr.write(f"Error setting state: {response.status_code} - {response.text}\n")
        sys.exit(1)

def call_action(api_url, token, domain, action, data_json=None):
    """Calls a native Home Assistant action (service)."""
    url = f"{api_url}/services/{domain}/{action}"
    payload = {}
    if data_json:
        try:
            payload = json.loads(data_json)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Error parsing data JSON: {e}\n")
            sys.exit(1)
            
    response = requests.post(url, headers=get_headers(token), json=payload, verify=True)
    if response.status_code == 200:
        return response.json()
    else:
        sys.stderr.write(f"Error calling action: {response.status_code} - {response.text}\n")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  ha_client.py get <entity_id>")
        print("  ha_client.py set <entity_id> <state> [attributes_json]")
        print("  ha_client.py action <domain> <action> [data_json]")
        sys.exit(1)
        
    api_url, token = load_credentials()
    if not token:
        sys.stderr.write("Error: Bearer token not found in config or environment.\n")
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == "get":
        if len(sys.argv) < 3:
            sys.stderr.write("Error: entity_id required for 'get' command.\n")
            sys.exit(1)
        entity_id = sys.argv[2]
        res = get_entity_state(api_url, token, entity_id)
        print(json.dumps(res, indent=2))
        
    elif cmd == "set":
        if len(sys.argv) < 4:
            sys.stderr.write("Error: entity_id and state required for 'set' command.\n")
            sys.exit(1)
        entity_id = sys.argv[2]
        state = sys.argv[3]
        attributes_json = sys.argv[4] if len(sys.argv) > 4 else None
        res = set_entity_state(api_url, token, entity_id, state, attributes_json)
        print(json.dumps(res, indent=2))
        
    elif cmd == "action":
        if len(sys.argv) < 4:
            sys.stderr.write("Error: domain and action required for 'action' command.\n")
            sys.exit(1)
        domain = sys.argv[2]
        action = sys.argv[3]
        data_json = sys.argv[4] if len(sys.argv) > 4 else None
        res = call_action(api_url, token, domain, action, data_json)
        print(json.dumps(res, indent=2))
        
    else:
        sys.stderr.write(f"Unknown command: {cmd}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
