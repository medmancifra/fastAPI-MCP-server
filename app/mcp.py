"""FastAPI MCP Server — Image Tools (OCR and Barcode scanning).

This module defines the FastAPI sub-application that exposes two tools:
  - POST /ocr          — extracts text from an image URL using Tesseract OCR
  - POST /scan-barcode — decodes barcodes/QR codes from an image URL

Authentication is handled via JWT tokens verified against Descope JWKS.
The FastApiMCP wrapper registers these endpoints as MCP tools and mounts
the MCP transport at /mcp/mcp on the parent app.
"""

import urllib.request
from io import BytesIO

import requests
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.responses import JSONResponse
from httpx import AsyncClient, RequestError
from PIL import Image
from pydantic import BaseModel, HttpUrl
from pyzbar.pyzbar import decode as decode_barcode
import pytesseract

from fastapi_mcp import AuthConfig, FastApiMCP

from app.auth.auth import TokenVerifier
from app.auth.auth_config import get_settings


# Fix User-Agent for JWKS requests (required by some JWKS endpoints)
_opener = urllib.request.build_opener()
_opener.addheaders = [("User-agent", "Mozilla/5.0 (DescopeFastAPISampleApp)")]
urllib.request.install_opener(_opener)


config = get_settings()
auth = TokenVerifier()

# Sub-application — mounted at /mcp by the parent app in main.py
mcp_app = FastAPI(title="Image Tools MCP")


# =============================================================================
# Request models
# =============================================================================


class OCRRequest(BaseModel):
    image_url: HttpUrl


class BarcodeRequest(BaseModel):
    barcode_url: HttpUrl


# =============================================================================
# OCR endpoint
# =============================================================================


@mcp_app.post("/ocr", operation_id="optical-character-recognition")
async def perform_ocr(
    request: OCRRequest,
    auth_result: str = Security(auth),
):
    """Extract text from an image at the given URL using Tesseract OCR."""
    try:
        response = requests.get(str(request.image_url), timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {str(e)}")

    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Provided URL does not point to an image.",
        )

    try:
        image = Image.open(BytesIO(response.content))
        text = pytesseract.image_to_string(image)
        return JSONResponse(content={"text": text.strip()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


# =============================================================================
# Barcode / QR-code endpoint
# =============================================================================


@mcp_app.post("/scan-barcode", operation_id="scan-barcode")
async def scan_barcode(
    request: BarcodeRequest,
    auth_result: str = Security(auth),
):
    """Decode barcodes and QR codes from an image at the given URL."""
    try:
        async with AsyncClient(timeout=5.0) as client:
            response = await client.get(str(request.barcode_url))

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch image")

        try:
            image = Image.open(BytesIO(response.content)).convert("RGB")
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Provided URL is not a valid image",
            )

        decoded = decode_barcode(image)

        if not decoded:
            raise HTTPException(status_code=422, detail="No barcode detected")

        results = [
            {
                "type": item.type,
                "data": item.data.decode("utf-8"),
                "bounds": item.rect,
            }
            for item in decoded
        ]

        return {"success": True, "barcodes": results}

    except RequestError as e:
        raise HTTPException(status_code=400, detail=f"HTTP error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# =============================================================================
# MCP wrapper — registers endpoints as MCP tools and mounts MCP transport
# =============================================================================

mcp = FastApiMCP(
    mcp_app,
    name="Image Tools MCP Server",
    description="MCP Server for OCR and Barcode scanning",
    auth_config=AuthConfig(
        custom_oauth_metadata={
            "issuer": f"{config.descope_api_base_url}/v1/apps/{config.descope_project_id}",
            "jwks_uri": (
                f"{config.descope_api_base_url}"
                f"/{config.descope_project_id}/.well-known/jwks.json"
            ),
            "authorization_endpoint": (
                f"{config.descope_api_base_url}/oauth2/v1/apps/authorize"
            ),
            "token_endpoint": f"{config.descope_api_base_url}/oauth2/v1/apps/token",
            "userinfo_endpoint": f"{config.descope_api_base_url}/oauth2/v1/apps/userinfo",
            "revocation_endpoint": f"{config.descope_api_base_url}/oauth2/v1/apps/revoke",
            "end_session_endpoint": f"{config.descope_api_base_url}/oauth2/v1/apps/logout",
            "response_types_supported": ["code"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "code_challenge_methods_supported": ["S256"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_methods_supported": ["client_secret_post"],
            "scopes_supported": ["openid"],
        },
        dependencies=[Depends(auth)],
    ),
)

mcp.setup_server()
mcp.mount()
