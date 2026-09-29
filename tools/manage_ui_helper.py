#!/usr/bin/env python3
"""Manage Home Assistant UI Helper Entities via WebSocket API.

Allows creating, listing, and deleting UI helpers (input_text, input_boolean,
input_number, input_datetime, timer, etc.) so they are natively registered in
.storage/<domain> and core.entity_registry with editable=true.
"""

import argparse
import asyncio
import json
import os
import sys
import aiohttp

TOKEN_PATHS = [
    "/opt/docker/secrets/hub/ha_mcp_token",
    os.path.expanduser("~/.gemini/antigravity/ha_mcp_token"),
]

def get_token() -> str:
    for path in TOKEN_PATHS:
        if os.path.exists(path):
            with open(path) as f:
                return f.read().strip()
    env_token = os.environ.get("HA_TOKEN")
    if env_token:
        return env_token.strip()
    sys.stderr.write("Error: HA access token not found in secrets or HA_TOKEN env.\n")
    sys.exit(1)

async def ws_request(payload: dict) -> dict:
    token = get_token()
    url = os.environ.get("HA_WS_URL", "http://127.0.0.1:8123/api/websocket")
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            # 1. Auth required
            await ws.receive_json()
            # 2. Authenticate
            await ws.send_json({"type": "auth", "access_token": token})
            auth_resp = await ws.receive_json()
            if auth_resp.get("type") != "auth_ok":
                raise RuntimeError(f"Auth failed: {auth_resp}")
            # 3. Send payload
            payload["id"] = 1
            await ws.send_json(payload)
            resp = await ws.receive_json()
            return resp

async def cmd_list(domain: str):
    resp = await ws_request({"type": f"{domain}/list"})
    if not resp.get("success"):
        print(f"Failed to list {domain}: {resp}")
        return
    items = resp.get("result", [])
    print(f"Found {len(items)} UI helpers for domain '{domain}':")
    for item in items:
        print(f" - [{item.get('id')}] {item.get('name')} (config: {item})")

async def cmd_create(domain: str, args):
    payload = {
        "type": f"{domain}/create",
        "name": args.name,
    }
    if args.icon:
        payload["icon"] = args.icon
    if domain == "input_text":
        payload["min"] = args.min if args.min is not None else 0
        payload["max"] = args.max if args.max is not None else 255
        payload["mode"] = args.mode or "text"
    elif domain == "input_number":
        payload["min"] = args.min if args.min is not None else 0
        payload["max"] = args.max if args.max is not None else 100
        payload["step"] = args.step if args.step is not None else 1
    elif domain == "timer":
        if args.duration:
            payload["duration"] = args.duration

    resp = await ws_request(payload)
    if resp.get("success"):
        print(f"Successfully created UI helper in '{domain}':")
        print(json.dumps(resp.get("result"), indent=2))
    else:
        print(f"Failed to create UI helper: {resp}")

async def cmd_delete(domain: str, helper_id: str):
    key = f"{domain}_id"
    resp = await ws_request({
        "type": f"{domain}/delete",
        key: helper_id,
    })
    if resp.get("success"):
        print(f"Successfully deleted {domain} helper '{helper_id}'.")
    else:
        print(f"Failed to delete helper: {resp}")

def main():
    parser = argparse.ArgumentParser(description="HA UI Helper Manager")
    subparsers = parser.add_subparsers(dest="action", required=True)

    # list
    p_list = subparsers.add_parser("list", help="List UI helpers for a domain")
    p_list.add_argument("domain", help="Helper domain (input_text, input_boolean, timer, etc.)")

    # create
    p_create = subparsers.add_parser("create", help="Create a new UI helper")
    p_create.add_argument("domain", help="Helper domain (input_text, input_boolean, timer, etc.)")
    p_create.add_argument("--name", required=True, help="Friendly name for helper")
    p_create.add_argument("--icon", help="Icon (e.g. mdi:door)")
    p_create.add_argument("--min", type=int, help="Min value / length")
    p_create.add_argument("--max", type=int, help="Max value / length")
    p_create.add_argument("--step", type=float, help="Step for input_number")
    p_create.add_argument("--mode", choices=["text", "password"], help="Mode for input_text")
    p_create.add_argument("--duration", help="Duration for timer (e.g. 00:00:30)")

    # delete
    p_del = subparsers.add_parser("delete", help="Delete a UI helper")
    p_del.add_argument("domain", help="Helper domain (input_text, input_boolean, etc.)")
    p_del.add_argument("id", help="ID of helper to delete")

    args = parser.parse_args()

    if args.action == "list":
        asyncio.run(cmd_list(args.domain))
    elif args.action == "create":
        asyncio.run(cmd_create(args.domain, args))
    elif args.action == "delete":
        asyncio.run(cmd_delete(args.domain, args.id))

if __name__ == "__main__":
    main()
