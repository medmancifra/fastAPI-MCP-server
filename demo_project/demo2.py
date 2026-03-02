"""demo2.py — Dash web application demo for MCP OCR and Barcode tools.

This demo provides a browser-based UI (built with Dash) that lets users:
  - Enter an image URL and a Bearer token.
  - Call the OCR tool and display the extracted text.
  - Call the Barcode/QR scanner tool and display decoded results.

Usage:
    pip install dash requests
    python demo2.py [--host HOST] [--port PORT] [--mcp-host MCP_HOST] [--mcp-port MCP_PORT]

Then open http://localhost:8050 in your browser.
"""

import argparse
import os

import requests

try:
    import dash
    from dash import Input, Output, State, dcc, html
    from dash.exceptions import PreventUpdate
except ImportError:
    raise SystemExit(
        "Dash is required for this demo.\n"
        "Install it with:  pip install dash"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demo 2: Dash UI for MCP OCR & Barcode")
    parser.add_argument("--host", default="0.0.0.0", help="Dash app host")
    parser.add_argument("--port", type=int, default=8050, help="Dash app port")
    parser.add_argument("--mcp-host", default=os.getenv("MCP_HOST", "localhost"))
    parser.add_argument("--mcp-port", type=int, default=int(os.getenv("MCP_PORT", "8000")))
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

_LABEL_STYLE = {"fontWeight": "bold", "marginTop": "12px", "display": "block"}
_INPUT_STYLE = {"width": "100%", "padding": "6px", "boxSizing": "border-box"}
_BTN_STYLE = {
    "marginTop": "10px",
    "padding": "8px 18px",
    "cursor": "pointer",
    "backgroundColor": "#4A90D9",
    "color": "white",
    "border": "none",
    "borderRadius": "4px",
}
_RESULT_STYLE = {
    "marginTop": "12px",
    "padding": "10px",
    "backgroundColor": "#f4f4f4",
    "borderRadius": "4px",
    "whiteSpace": "pre-wrap",
    "fontFamily": "monospace",
}


def build_layout() -> html.Div:
    return html.Div(
        style={"maxWidth": "700px", "margin": "40px auto", "fontFamily": "sans-serif"},
        children=[
            html.H1("FastAPI MCP Server — Demo 2 (Dash)"),
            html.P("Interact with the MCP OCR and Barcode tools via a browser UI."),

            # Common settings
            html.H2("Settings"),
            html.Label("Bearer Token", style=_LABEL_STYLE),
            dcc.Input(
                id="token-input",
                type="password",
                placeholder="Paste your JWT token here",
                style=_INPUT_STYLE,
                debounce=False,
            ),

            html.Hr(),

            # OCR section
            html.H2("OCR Tool"),
            html.Label("Image URL", style=_LABEL_STYLE),
            dcc.Input(
                id="ocr-url-input",
                type="url",
                placeholder="https://example.com/image.png",
                style=_INPUT_STYLE,
                debounce=False,
            ),
            html.Button("Run OCR", id="ocr-btn", n_clicks=0, style=_BTN_STYLE),
            html.Div(id="ocr-result", style=_RESULT_STYLE),

            html.Hr(),

            # Barcode section
            html.H2("Barcode / QR Scanner"),
            html.Label("Barcode Image URL", style=_LABEL_STYLE),
            dcc.Input(
                id="barcode-url-input",
                type="url",
                placeholder="https://example.com/barcode.png",
                style=_INPUT_STYLE,
                debounce=False,
            ),
            html.Button("Scan Barcode", id="barcode-btn", n_clicks=0, style=_BTN_STYLE),
            html.Div(id="barcode-result", style=_RESULT_STYLE),

            # Store MCP base URL as hidden state
            dcc.Store(id="mcp-base-url"),
        ],
    )


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(mcp_base_url: str) -> dash.Dash:
    app = dash.Dash(__name__, title="MCP Demo 2 — Dash")
    app.layout = build_layout()

    @app.callback(
        Output("ocr-result", "children"),
        Input("ocr-btn", "n_clicks"),
        State("ocr-url-input", "value"),
        State("token-input", "value"),
        prevent_initial_call=True,
    )
    def run_ocr(n_clicks, image_url, token):
        if not image_url:
            raise PreventUpdate
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
                return f"Extracted text:\n{text}" if text else "(No text detected)"
            return f"Error {resp.status_code}: {resp.text}"
        except requests.ConnectionError:
            return "ERROR: Cannot connect to MCP server. Is it running?"
        except Exception as exc:
            return f"ERROR: {exc}"

    @app.callback(
        Output("barcode-result", "children"),
        Input("barcode-btn", "n_clicks"),
        State("barcode-url-input", "value"),
        State("token-input", "value"),
        prevent_initial_call=True,
    )
    def run_barcode(n_clicks, barcode_url, token):
        if not barcode_url:
            raise PreventUpdate
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

    return app


def main() -> None:
    args = parse_args()
    mcp_base_url = f"http://{args.mcp_host}:{args.mcp_port}"
    print(f"MCP server: {mcp_base_url}")
    print(f"Dash UI:    http://{args.host}:{args.port}")
    app = create_app(mcp_base_url)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
