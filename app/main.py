from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .mcp import mcp_app
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (if needed)
    yield
    # Shutdown logic (if needed)


app = FastAPI(
    title="FastAPI MCP Server",
    description="MCP Server with Image Tools",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount MCP app
app.mount("/mcp", mcp_app)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mcp_tools": ["ocr", "barcode"]
    }
