"""_summary_
from mcp.server.fastapi import FastMCP
from .tools.code_analyzer import CodeAnalyzerTool
from .tools.file_system import FileSystemTool

mcp_app = FastMCP("FastAPI MCP Server")

@mcp_app.tool()
async def list_tools() -> str:
    List available MCP tools
    tools = [tool.name for tool in mcp_app.tools]
    return f"Available tools: {', '.join(tools)}"

mcp_app.add_tool(CodeAnalyzerTool())
mcp_app.add_tool(FileSystemTool())
    """

from fastapi import FastAPI, Depends, Security, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from httpx import AsyncClient, RequestError
from typing import List
from PIL import Image
import pytesseract
from io import BytesIO
import requests
from pyzbar.pyzbar import decode as decode_barcode
import urllib.request

from app.auth.auth import TokenVerifier
from app.auth.auth_config import get_settings

from fastapi_mcp import FastApiMCP, AuthConfig


# Fix User-Agent for JWKS requests
opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (DescopeFastAPISampleApp)')]
urllib.request.install_opener(opener)


# ⚠️ ВАЖНО: это НЕ главный app
mcp_app = FastAPI(title="Image Tools MCP")

auth = TokenVerifier()
config = get_settings()


# =========================
# OCR
# =========================

class OCRRequest(BaseModel):
    image_url: HttpUrl


@mcp_app.post("/ocr", operation_id="optical-character-recognition")
async def perform_ocr(
    request: OCRRequest,
    auth_result: str = Security(auth)
):
    try:
        response = requests.get(str(request.image_url), timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {str(e)}")

    if not response.headers.get("Content-Type", "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Provided URL does not point to an image.")

    try:
        image = Image.open(BytesIO(response.content))
        text = pytesseract.image_to_string(image)
        return JSONResponse(content={"text": text.strip()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


# =========================
# Barcode
# =========================

class BarcodeRequest(BaseModel):
    barcode_url: HttpUrl


@mcp_app.post("/scan-barcode", operation_id="scan-barcode")
async def scan_barcode(
    request: BarcodeRequest,
    auth_result: str = Security(auth)
):
    try:
        async with AsyncClient(timeout=5.0) as client:
            response = await client.get(str(request.barcode_url))

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch image")

        try:
            image = Image.open(BytesIO(response.content)).convert("RGB")
        except Exception:
            raise HTTPException(status_code=400, detail="Provided URL is not a valid image")

        decoded = decode_barcode(image)

        if not decoded:
            raise HTTPException(status_code=422, detail="No barcode detected")

        results = []
        for item in decoded:
            results.append({
                "type": item.type,
                "data": item.data.decode("utf-8"),
                "bounds": item.rect
            })

        return {"success": True, "barcodes": results}

    except RequestError as e:
        raise HTTPException(status_code=400, detail=f"HTTP error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# =========================
# MCP Wrapper
# =========================

mcp = FastApiMCP(
    mcp_app,
    name="Image Tools MCP Server",
    description="MCP Server for OCR and Barcode scanning",
    auth_config=AuthConfig(
        custom_oauth_metadata={
            "issuer": f"{config.descope_api_base_url}/v1/apps/{config.descope_project_id}",
            "jwks_uri": f"{config.descope_api_base_url}/{config.descope_project_id}/.well-known/jwks.json",
            "authorization_endpoint": f"{config.descope_api_base_url}/oauth2/v1/apps/authorize",
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
