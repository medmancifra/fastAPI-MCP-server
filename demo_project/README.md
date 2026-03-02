# demo_project — Test Assets for FastAPI MCP Server

This folder contains lightweight test assets used to verify the MCP server's OCR and barcode-scanning tools.

## Contents

```
demo_project/
├── README.md            — this file
└── images/
    ├── ocr_sample.png       — small PNG with readable text (for OCR tool testing)
    └── barcode_qr_sample.png — QR code PNG (for scan-barcode tool testing)
```

## Image Details

| File | Purpose | Content |
|------|---------|---------|
| `ocr_sample.png` | OCR tool input | White background, black text: "Hello, MCP World! OCR Test 123" |
| `barcode_qr_sample.png` | Barcode tool input | QR code encoding `https://github.com/medmancifra/fastAPI-MCP-server` |

## How to Use

These images are available inside the Docker container at `/app/demo_project/images/`.

### Serving local images during testing

Start the server with `docker run IMAGE serve`, then in a separate terminal
run a simple static file server alongside it, or reference images via a
public URL. For quick local testing you can use Python's built-in HTTP server:

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

## No Secrets Required

The images in this folder contain no sensitive data, real tokens, passwords,
or private information. They are safe to commit to the repository.
