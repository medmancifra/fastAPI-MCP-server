"""FastAPI MCP Server — application entry point.

The parent FastAPI app mounts the Image Tools MCP sub-application at /mcp,
which exposes:
  - POST /mcp/ocr          — OCR text extraction
  - POST /mcp/scan-barcode — Barcode/QR-code decoding
  - /mcp/mcp               — MCP protocol transport (SSE)

A /health endpoint is available for liveness checks (e.g. Docker smoke tests).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .mcp import mcp_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="FastAPI MCP Server",
    description="MCP Server with Image Tools (OCR and Barcode scanning)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Image Tools MCP sub-application
app.mount("/mcp", mcp_app)


@app.get("/health")
async def health_check():
    """Liveness probe — returns server status and available MCP tools."""
    return {
        "status": "healthy",
        "mcp_tools": ["optical-character-recognition", "scan-barcode"],
    }
