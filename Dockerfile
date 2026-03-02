FROM python:3.11-slim

WORKDIR /app

# System dependencies required by pytesseract (OCR), pyzbar (barcode scanning), and wget (smoke check)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libzbar0 \
    libzbar-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY tests/ ./tests/
COPY demo_project/ ./demo_project/
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

# Supports:
#   docker run IMAGE serve  — start MCP server on port 8000
#   docker run IMAGE smoke  — quick health/readiness check
ENTRYPOINT ["./entrypoint.sh"]
CMD ["serve"]
