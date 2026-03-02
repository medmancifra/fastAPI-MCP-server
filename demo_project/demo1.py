"""demo1.py — Basic MCP server connectivity and health check demo.

This script demonstrates how to connect to the FastAPI MCP Server and verify
it is running correctly by:

1. Checking the /health endpoint.
2. Fetching the MCP tool list from the SSE transport.
3. Printing a summary of available tools.

Usage:
    python demo1.py [--host HOST] [--port PORT] [--token TOKEN]

Environment variables (alternative to CLI args):
    MCP_HOST   — server hostname (default: localhost)
    MCP_PORT   — server port    (default: 8000)
    MCP_TOKEN  — Bearer token for authenticated requests
"""

import argparse
import os
import sys

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Demo 1: FastAPI MCP Server health check and tool listing"
    )
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MCP_PORT", "8000")))
    parser.add_argument("--token", default=os.getenv("MCP_TOKEN", ""))
    return parser.parse_args()


def check_health(base_url: str) -> dict:
    """Call /health and return the parsed JSON response."""
    url = f"{base_url}/health"
    print(f"[1] Checking health at {url} ...")
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    print(f"    Status  : {data.get('status')}")
    print(f"    MCP Tools: {data.get('mcp_tools')}")
    return data


def list_mcp_tools(base_url: str, token: str) -> None:
    """Fetch MCP server info from the OpenAPI spec and print tool names."""
    url = f"{base_url}/mcp/openapi.json"
    print(f"\n[2] Fetching MCP OpenAPI spec at {url} ...")

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        spec = resp.json()
        paths = spec.get("paths", {})
        print(f"    Available MCP endpoints ({len(paths)}):")
        for path in sorted(paths):
            methods = list(paths[path].keys())
            print(f"      {', '.join(m.upper() for m in methods)}  {path}")
    except requests.HTTPError as exc:
        print(f"    [WARN] Could not fetch OpenAPI spec: {exc}")


def main() -> int:
    args = parse_args()
    base_url = f"http://{args.host}:{args.port}"
    print("=== Demo 1: FastAPI MCP Server — Health Check & Tool Listing ===")
    print(f"Server: {base_url}\n")

    try:
        health = check_health(base_url)
    except requests.ConnectionError:
        print(f"ERROR: Cannot connect to {base_url}. Is the server running?")
        return 1
    except requests.HTTPError as exc:
        print(f"ERROR: Health check failed: {exc}")
        return 1

    if health.get("status") != "healthy":
        print("ERROR: Server reported unhealthy status.")
        return 1

    list_mcp_tools(base_url, args.token)

    print("\n=== Done — server is healthy and ready to accept MCP requests. ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
