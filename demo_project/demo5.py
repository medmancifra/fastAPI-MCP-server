"""demo5.py — AI agent bot demo using the MCP OCR and Barcode tools.

This demo implements a simple command-line AI agent bot that:
  - Accepts natural-language commands from the user.
  - Decides which MCP tool to invoke (OCR or barcode scanner).
  - Calls the tool against the FastAPI MCP Server.
  - Returns a human-readable answer.

The agent uses a rule-based intent classifier (no external LLM required),
but its architecture mirrors how a real AI agent would integrate with MCP.

Usage:
    pip install requests
    python demo5.py [--host HOST] [--port PORT] [--token TOKEN]

Interactive commands (examples):
    read text from https://example.com/image.png
    scan barcode https://example.com/qr.png
    check health
    help
    exit
"""

import argparse
import os
import re
import sys

import requests


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def call_ocr(mcp_base_url: str, image_url: str, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.post(
            f"{mcp_base_url}/mcp/ocr",
            json={"image_url": image_url},
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            text = resp.json().get("text", "")
            return f"Extracted text:\n\n{text}" if text else "(No text detected in image)"
        return f"OCR tool error {resp.status_code}: {resp.text}"
    except requests.ConnectionError:
        return "ERROR: Cannot connect to MCP server."
    except Exception as exc:
        return f"ERROR: {exc}"


def call_barcode(mcp_base_url: str, barcode_url: str, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.post(
            f"{mcp_base_url}/mcp/scan-barcode",
            json={"barcode_url": barcode_url},
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            barcodes = data.get("barcodes", [])
            if not barcodes:
                return "(No barcodes/QR codes detected)"
            lines = [f"Found {len(barcodes)} barcode(s):"]
            for i, bc in enumerate(barcodes, 1):
                lines.append(f"  [{i}] type={bc['type']}  data={bc['data']}")
            return "\n".join(lines)
        return f"Barcode tool error {resp.status_code}: {resp.text}"
    except requests.ConnectionError:
        return "ERROR: Cannot connect to MCP server."
    except Exception as exc:
        return f"ERROR: {exc}"


def call_health(mcp_base_url: str) -> str:
    try:
        resp = requests.get(f"{mcp_base_url}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            tools = ", ".join(data.get("mcp_tools", []))
            return f"Server status: {data.get('status')}\nAvailable tools: {tools}"
        return f"Health check returned {resp.status_code}"
    except requests.ConnectionError:
        return "ERROR: Cannot connect to MCP server."


# ---------------------------------------------------------------------------
# Intent classifier
# ---------------------------------------------------------------------------

_URL_PATTERN = re.compile(r"https?://\S+")

# Keywords that suggest each intent
_OCR_KEYWORDS = re.compile(
    r"\b(ocr|read|extract|text|words?|scan\s+text|recognize)\b", re.IGNORECASE
)
_BARCODE_KEYWORDS = re.compile(
    r"\b(barcode|qr|scan|decode|qr.?code|bar.?code)\b", re.IGNORECASE
)
_HEALTH_KEYWORDS = re.compile(
    r"\b(health|status|ping|alive|check)\b", re.IGNORECASE
)
_HELP_KEYWORDS = re.compile(r"\bhelp\b|\?", re.IGNORECASE)
_EXIT_KEYWORDS = re.compile(r"\b(exit|quit|bye|q)\b", re.IGNORECASE)


def classify_intent(user_input: str) -> str:
    if _EXIT_KEYWORDS.search(user_input):
        return "exit"
    if _HELP_KEYWORDS.search(user_input):
        return "help"
    if _HEALTH_KEYWORDS.search(user_input):
        return "health"
    if _BARCODE_KEYWORDS.search(user_input):
        return "barcode"
    if _OCR_KEYWORDS.search(user_input):
        return "ocr"
    # Default: if a URL is present, try OCR
    if _URL_PATTERN.search(user_input):
        return "ocr"
    return "unknown"


def extract_url(user_input: str) -> str | None:
    m = _URL_PATTERN.search(user_input)
    return m.group(0) if m else None


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

HELP_TEXT = """
Available commands:
  read text from <URL>      — Extract text from image using OCR
  scan barcode <URL>        — Decode barcode/QR code from image
  check health              — Check server health and list tools
  help                      — Show this help message
  exit / quit               — Quit the bot

Examples:
  read text from https://example.com/image.png
  scan barcode https://example.com/qr.png
""".strip()


def run_agent(mcp_base_url: str, token: str) -> None:
    print("=== Demo 5: FastAPI MCP Server — AI Agent Bot ===")
    print(f"Connected to: {mcp_base_url}")
    print("Type 'help' for available commands or 'exit' to quit.\n")

    while True:
        try:
            user_input = input("agent> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        intent = classify_intent(user_input)

        if intent == "exit":
            print("Goodbye!")
            break

        elif intent == "help":
            print(HELP_TEXT)

        elif intent == "health":
            result = call_health(mcp_base_url)
            print(result)

        elif intent == "ocr":
            url = extract_url(user_input)
            if not url:
                print("Please provide an image URL. Example: read text from https://...")
            else:
                print(f"Calling OCR tool for {url} ...")
                print(call_ocr(mcp_base_url, url, token))

        elif intent == "barcode":
            url = extract_url(user_input)
            if not url:
                print("Please provide a barcode image URL. Example: scan barcode https://...")
            else:
                print(f"Scanning barcode at {url} ...")
                print(call_barcode(mcp_base_url, url, token))

        else:
            print(
                "I didn't understand that. Type 'help' for a list of commands.\n"
                "Tip: mention 'ocr', 'barcode', or 'health' along with a URL."
            )

        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demo 5: AI agent bot for FastAPI MCP Server")
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MCP_PORT", "8000")))
    parser.add_argument("--token", default=os.getenv("MCP_TOKEN", ""))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mcp_base_url = f"http://{args.host}:{args.port}"
    run_agent(mcp_base_url, args.token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
