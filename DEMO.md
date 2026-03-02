# DEMO.md — FastAPI MCP Server Demo Scenario

## Цель сценария

Продемонстрировать работу двух MCP-инструментов:
1. **OCR** (`optical-character-recognition`) — извлечение текста из изображения по URL
2. **Scan Barcode** (`scan-barcode`) — распознавание штрих-кода / QR-кода из изображения по URL

---

## Предусловия

1. Docker установлен и запущен.
2. Переменные окружения настроены (см. `.env.example` ниже).
3. Контейнер запущен:

```bash
# Клонировать репозиторий
git clone https://github.com/medmancifra/fastAPI-MCP-server.git
cd fastapi-mcp-server

# Создать .env файл с вашими Descope-реквизитами
cat > .env << 'EOF'
DESCOPE_PROJECT_ID=<your_descope_project_id>
DESCOPE_API_BASE_URL=https://api.descope.com
EOF

# Собрать и запустить
docker-compose up --build -d
```

4. URL MCP-сервера: `http://localhost:8000`
5. Инспектор или совместимый MCP-клиент открыт (например, MCP Inspector на `http://localhost:5173`, или curl).

---

## Шаги проверки

### Шаг 1: Проверка здоровья сервера

**Инструмент**: GET `/health`

```bash
curl http://localhost:8000/health
```

**Ожидаемый результат:**

```json
{
  "status": "healthy",
  "mcp_tools": ["ocr", "barcode"]
}
```

---

### Шаг 2: Получить список MCP-инструментов

**Инструмент**: GET `/mcp`

```bash
curl http://localhost:8000/mcp
```

**Ожидаемый результат:** JSON с описанием сервера и списком инструментов (`optical-character-recognition`, `scan-barcode`).

---

### Шаг 3: OCR — извлечение текста из изображения

**Инструмент**: `optical-character-recognition`
**Эндпоинт**: POST `/mcp/ocr`
**Аргументы**:

| Поле        | Тип    | Описание                              |
|-------------|--------|---------------------------------------|
| `image_url` | string | Публичный URL изображения с текстом   |

**Пример запроса:**

```bash
# Получить JWT-токен от Descope и передать в заголовке Authorization
TOKEN="<your_jwt_token>"

curl -X POST http://localhost:8000/mcp/ocr \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/640px-Camponotus_flavomarginatus_ant.jpg"
  }'
```

> Примечание: используйте изображение с читаемым текстом для наилучшего результата OCR. Пример с реальным текстом:
> `https://www.w3schools.com/css/img_5terre.jpg` или любое изображение с текстом.

**Ожидаемый результат:**

```json
{
  "text": "<распознанный текст из изображения>"
}
```

**Признаки успешной работы:**
- HTTP статус `200 OK`
- Поле `text` содержит распознанный текст (или пустую строку, если текст не найден)

---

### Шаг 4: Scan Barcode — распознавание штрих-кода

**Инструмент**: `scan-barcode`
**Эндпоинт**: POST `/mcp/scan-barcode`
**Аргументы**:

| Поле          | Тип    | Описание                                    |
|---------------|--------|---------------------------------------------|
| `barcode_url` | string | Публичный URL изображения со штрих-кодом    |

**Пример запроса:**

```bash
TOKEN="<your_jwt_token>"

curl -X POST http://localhost:8000/mcp/scan-barcode \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "barcode_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/UPC-A-036000291452.svg/440px-UPC-A-036000291452.svg.png"
  }'
```

**Ожидаемый результат:**

```json
{
  "success": true,
  "barcodes": [
    {
      "type": "EAN13",
      "data": "036000291452",
      "bounds": {"left": 10, "top": 10, "width": 420, "height": 100}
    }
  ]
}
```

**Признаки успешной работы:**
- HTTP статус `200 OK`
- `success: true`
- Массив `barcodes` содержит объекты с `type`, `data`, `bounds`
- `data` — раскодированное значение штрих-кода

---

## Ожидаемый результат (сводка)

| Шаг | Действие              | Признак успеха                                      |
|-----|-----------------------|-----------------------------------------------------|
| 1   | GET /health           | `{"status": "healthy", "mcp_tools": ["ocr", "barcode"]}` |
| 2   | GET /mcp              | JSON с описанием MCP сервера и tools                |
| 3   | POST /mcp/ocr         | `{"text": "<...>"}` с HTTP 200                      |
| 4   | POST /mcp/scan-barcode| `{"success": true, "barcodes": [...]}` с HTTP 200   |

---

## Использование через MCP Inspector

1. Открыть MCP Inspector: `npx @modelcontextprotocol/inspector`
2. Указать URL: `http://localhost:8000/mcp`
3. Выбрать инструмент `optical-character-recognition` или `scan-barcode`
4. Ввести аргументы и выполнить вызов
5. Проверить ответ в панели результатов

---

## Типичные проблемы / Troubleshooting

| Проблема | Причина | Решение |
|----------|---------|---------|
| `401 Unauthorized` | Отсутствует или истёк JWT-токен | Получите новый токен от Descope |
| `400 Failed to fetch image` | Некорректный или недоступный URL | Проверьте URL изображения, он должен быть публично доступен |
| `400 Provided URL does not point to an image` | URL указывает не на изображение | Убедитесь, что `Content-Type` ответа начинается с `image/` |
| `422 No barcode detected` | На изображении нет штрих-кода | Используйте изображение с чётким штрих-кодом |
| `500 OCR failed` | Tesseract не установлен или ошибка обработки | Убедитесь, что `tesseract-ocr` установлен в образе |
| Контейнер не запускается | Ошибка в `.env` или зависимости | Проверьте переменные `DESCOPE_PROJECT_ID` и `DESCOPE_API_BASE_URL` |

---

## Сноска по архитектуре

```
MCP Client / Inspector
        │
        ▼
FastAPI MCP Server (:8000)
  ├── /health            ← health check
  ├── /mcp               ← MCP metadata
  ├── /mcp/ocr           ← OCR tool (Tesseract + Pillow)
  └── /mcp/scan-barcode  ← Barcode tool (pyzbar + Pillow)
        │
        ▼
   Auth: Descope JWT (RS256)
```

**Инструменты задействованы в сценарии:**
- `optical-character-recognition` — извлечение текста из изображений
- `scan-barcode` — декодирование штрих-кодов и QR-кодов

Сценарий занимает **3–5 минут** и не требует специальных знаний о внутреннем коде.
