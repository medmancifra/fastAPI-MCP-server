import pytest
from httpx import AsyncClient
import asyncio

@pytest.mark.asyncio
async def test_mcp_server():
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Health check
        resp = await client.get("/health")
        assert resp.status_code == 200
        
        # MCP endpoints
        resp = await client.get("/mcp")
        assert resp.status_code == 200
