# demo_project — Demo Scripts and Test Assets for FastAPI MCP Server

This folder contains five demo scripts and lightweight test images used to
verify and showcase the FastAPI MCP Server's OCR and barcode-scanning tools.

---

## Contents

```
demo_project/
├── README.md               — this file
├── demo1.py                — CLI: health check & tool listing
├── demo2.py                — Dash: browser-based OCR/barcode UI
├── demo3.py                — Streamlit: interactive web app
├── demo4.py                — scikit-learn: ML pipeline using code analyzer
├── demo5.py                — AI agent bot (CLI)
└── images/
    ├── ocr_sample.png          — PNG with "Hello, MCP World! OCR Test 123"
    └── barcode_qr_sample.png   — QR code pointing to the repo URL
```

---

## Demo Scripts

### demo1.py — Health Check & Tool Listing

Verifies the server is running and prints the list of available MCP tools.
No authentication required for the health endpoint.

```bash
pip install requests
python demo_project/demo1.py --host localhost --port 8000
# With a token:
python demo_project/demo1.py --token "$TOKEN"
```

**Environment variables:** `MCP_HOST`, `MCP_PORT`, `MCP_TOKEN`

---

### demo2.py — Dash Web UI

Browser-based interface (Dash) for calling OCR and barcode tools interactively.
Opens at `http://localhost:8050` by default.

```bash
pip install dash requests
python demo_project/demo2.py --mcp-host localhost --mcp-port 8000
```

Open `http://localhost:8050` in your browser, paste your JWT token, enter an
image URL, and click **Run OCR** or **Scan Barcode**.

---

### demo3.py — Streamlit Web App

Streamlit equivalent of the Dash demo.
Opens at `http://localhost:8501` by default.

```bash
pip install streamlit requests
streamlit run demo_project/demo3.py -- --mcp-host localhost --mcp-port 8000
```

---

### demo4.py — scikit-learn Pipeline

Demonstrates using the MCP code analyzer as a feature extractor inside a
scikit-learn `Pipeline` to classify Python code snippets as "simple" or
"complex".  Falls back to local AST analysis when the MCP server is
unreachable, so it runs **offline** too.

```bash
pip install scikit-learn numpy requests
python demo_project/demo4.py
```

Sample output:

```
Training RandomForestClassifier on code complexity features...

Classification Report:
              precision    recall  f1-score
      complex       1.00      1.00      1.00
       simple       1.00      1.00      1.00

Feature Importances:
  loc           0.412  ################
  complexity    0.224  #########
  ...
```

---

### demo5.py — AI Agent Bot (CLI)

An interactive command-line agent that understands natural-language commands
and routes them to the correct MCP tool.

```bash
pip install requests
python demo_project/demo5.py --host localhost --port 8000 --token "$TOKEN"
```

Example session:

```
agent> check health
Server status: healthy
Available tools: optical-character-recognition, scan-barcode

agent> read text from http://localhost:8080/ocr_sample.png
Calling OCR tool for http://localhost:8080/ocr_sample.png ...
Extracted text:

Hello, MCP World! OCR Test 123

agent> scan barcode http://localhost:8080/barcode_qr_sample.png
Scanning barcode at http://localhost:8080/barcode_qr_sample.png ...
Found 1 barcode(s):
  [1] type=QRCODE  data=https://github.com/medmancifra/fastAPI-MCP-server

agent> exit
Goodbye!
```

---

## Test Images

| File | Purpose | Content |
|------|---------|---------|
| `images/ocr_sample.png` | OCR tool input | White background, black text: "Hello, MCP World! OCR Test 123" |
| `images/barcode_qr_sample.png` | Barcode tool input | QR code encoding `https://github.com/medmancifra/fastAPI-MCP-server` |

### Serving local images during testing

```bash
# From repo root — serves demo images on http://localhost:8080
python3 -m http.server 8080 --directory demo_project/images
```

Then call the OCR tool:

```bash
TOKEN="<your_jwt_token>"

curl -X POST http://localhost:8000/mcp/ocr \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"image_url": "http://localhost:8080/ocr_sample.png"}'
```

And the barcode tool:

```bash
curl -X POST http://localhost:8000/mcp/scan-barcode \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"barcode_url": "http://localhost:8080/barcode_qr_sample.png"}'
```

---

## Quick Start (all demos)

1. Start the server:

```bash
docker compose up
# or: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

2. Obtain a JWT token from your Descope project.

3. Run any demo:

```bash
export MCP_TOKEN="<your_jwt_token>"
python demo_project/demo1.py   # CLI health check
python demo_project/demo5.py   # Interactive agent bot
```

---

## No Secrets Required

The images in this folder contain no sensitive data, real tokens, passwords,
or private information.  They are safe to commit to the repository.
