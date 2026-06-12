#!/usr/bin/env python3
"""
Home Assistant Jinja Template Sandbox Skill.
Renders template strings or files through the live Home Assistant API.
"""

import os
import sys
import argparse
import requests
from ha_client import load_credentials, get_headers

def render_template(api_url, token, template_string):
    """Renders a Jinja template using Home Assistant's POST /api/template endpoint."""
    url = f"{api_url}/template"
    payload = {"template": template_string}
    
    response = requests.post(url, headers=get_headers(token), json=payload, verify=True)
    if response.status_code == 200:
        return response.text
    else:
        sys.stderr.write(f"Error rendering template: {response.status_code} - {response.text}\n")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Home Assistant Jinja Sandbox")
    parser.add_argument("template", nargs="?", help="Jinja template string to render")
    parser.add_argument("-f", "--file", help="Path to a file containing the Jinja template")
    
    args = parser.parse_args()
    
    if not args.template and not args.file:
        parser.print_help()
        sys.exit(1)
        
    template_content = ""
    if args.file:
        try:
            with open(args.file, "r") as f:
                template_content = f.read()
        except Exception as e:
            sys.stderr.write(f"Error reading file {args.file}: {e}\n")
            sys.exit(1)
    else:
        template_content = args.template
        
    api_url, token = load_credentials()
    if not token:
        sys.stderr.write("Error: Bearer token not found.\n")
        sys.exit(1)
        
    result = render_template(api_url, token, template_content)
    print(result)

if __name__ == "__main__":
    main()
