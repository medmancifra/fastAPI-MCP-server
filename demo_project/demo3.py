"""demo3.py — Streamlit web application demo for MCP OCR and Barcode tools.

This demo provides an interactive Streamlit UI that lets users:
  - Upload an image file or provide a URL.
  - Call the OCR tool and display the extracted text.
  - Call the Barcode/QR scanner tool and display decoded results.

Usage:
    pip install streamlit requests
    streamlit run demo3.py -- --mcp-host localhost --mcp-port 8000
"""

import argparse
import os

import requests

try:
    import streamlit as st
except ImportError:
    raise SystemExit(
        "Streamlit is required for this demo.\n"
        "Install it with:  pip install streamlit"
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments passed after the '--' separator for streamlit run."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mcp-host", default=os.getenv("MCP_HOST", "localhost"))
    parser.add_argument("--mcp-port", type=int, default=int(os.getenv("MCP_PORT", "8000")))
    # Streamlit passes its own args before '--'; ignore unknown args
    args, _ = parser.parse_known_args()
    return args


def get_mcp_base_url() -> str:
    args = parse_args()
    return f"http://{args.mcp_host}:{args.mcp_port}"


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
            return text if text else "(No text detected)"
        return f"Error {resp.status_code}: {resp.text}"
    except requests.ConnectionError:
        return "ERROR: Cannot connect to MCP server. Is it running?"
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
                return "(No barcodes detected)"
            lines = [f"Found {len(barcodes)} barcode(s):"]
            for i, bc in enumerate(barcodes, 1):
                lines.append(f"  [{i}] type={bc['type']}  data={bc['data']}")
            return "\n".join(lines)
        return f"Error {resp.status_code}: {resp.text}"
    except requests.ConnectionError:
        return "ERROR: Cannot connect to MCP server. Is it running?"
    except Exception as exc:
        return f"ERROR: {exc}"


def main() -> None:
    mcp_base_url = get_mcp_base_url()

    st.set_page_config(page_title="MCP Demo 3 — Streamlit", layout="centered")
    st.title("FastAPI MCP Server — Demo 3 (Streamlit)")
    st.write(
        "Use this app to test the OCR and Barcode/QR scanner tools "
        f"exposed by the MCP server at `{mcp_base_url}`."
    )

    # -------------------------------------------------------------------------
    # Settings sidebar
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.header("Settings")
        token = st.text_input("Bearer Token", type="password", placeholder="Paste JWT here")
        st.caption("Leave blank if authentication is disabled.")

    # -------------------------------------------------------------------------
    # OCR section
    # -------------------------------------------------------------------------
    st.header("OCR Tool")
    ocr_url = st.text_input(
        "Image URL",
        placeholder="https://example.com/image.png",
        key="ocr_url",
    )
    if st.button("Run OCR"):
        if not ocr_url:
            st.warning("Please provide an image URL.")
        else:
            with st.spinner("Calling OCR tool..."):
                result = call_ocr(mcp_base_url, ocr_url, token)
            st.subheader("Extracted Text")
            st.code(result, language=None)

    # -------------------------------------------------------------------------
    # Barcode section
    # -------------------------------------------------------------------------
    st.header("Barcode / QR Scanner")
    barcode_url = st.text_input(
        "Barcode Image URL",
        placeholder="https://example.com/barcode.png",
        key="barcode_url",
    )
    if st.button("Scan Barcode"):
        if not barcode_url:
            st.warning("Please provide a barcode image URL.")
        else:
            with st.spinner("Scanning barcode..."):
                result = call_barcode(mcp_base_url, barcode_url, token)
            st.subheader("Scan Results")
            st.code(result, language=None)

    # -------------------------------------------------------------------------
    # Health check
    # -------------------------------------------------------------------------
    st.divider()
    if st.button("Check Server Health"):
        try:
            resp = requests.get(f"{mcp_base_url}/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"Server is **{data.get('status', 'unknown')}**")
                st.json(data)
            else:
                st.error(f"Health check returned {resp.status_code}")
        except requests.ConnectionError:
            st.error("Cannot connect to MCP server. Is it running?")


if __name__ == "__main__":
    main()
