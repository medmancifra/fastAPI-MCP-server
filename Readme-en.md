# FastAPI MCP Server

MCP Server with Code Analyzer (AST parsing, metrics, suggestions) and File System tools.

## 🚀 Quick Start

`bash
# Clone & build
git clone <repo>
cd fastapi-mcp-server
docker build -t mcp-server .

# Run
docker run -p 8000:8000 mcp-server

# Or with docker-compose
docker-compose up --build

# Test code analyzer
curl -X POST http://localhost:8000/mcp/code_analyzer \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): print(\"Hello\")"}'

# Test file system
curl -X POST http://localhost:8000/mcp/file_system \
  -H "Content-Type: application/json" \
  -d '{"action": "list"}'

Smoke_Test_Checklist:

docker build -t mcp-server .
docker run -p 8000:8000 mcp-server &
sleep 3
curl http://localhost:8000/health
curl http://localhost:8000/mcp
docker stop $(docker ps -lq)

##testing_scenario


`bash
# 1. Build & run (30s)
docker build -t mcp-server .
docker run -d -p 8000:8000 --name mcp-test mcp-server

# 2. Smoke tests
curl http://localhost:8000/health | jq .status  # "healthy"
curl http://localhost:8000/mcp                

# MCP info

# 3. Real tool test
curl -X POST http://localhost:8000/mcp/code_analyzer \
  -H "Content-Type: application/json" \
  -d '{"code": "def fib(n): return n if n<2 else fib(n-1)+fib(n-2)"}' | jq .

# 4. Cleanup
docker stop mcp-test && docker rm mcp-test
