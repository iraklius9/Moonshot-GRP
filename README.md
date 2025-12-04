# Reverse Proxy Service

A generic Python reverse proxy service built with FastAPI that routes operations to external APIs (OpenLiga) with rate
limiting, exponential backoff, audit logging, and comprehensive error handling.

## Features

- **Single Entry Point**: POST `/proxy/execute` endpoint for all operations
- **Decision Mapper**: Schema-driven routing with payload validation
- **Adapter Pattern**: Provider-agnostic interface for easy provider swapping
- **Rate Limiting**: Token bucket algorithm with configurable limits (respects OpenLiga API: 1000 req/hour per IP)
- **Exponential Backoff**: Automatic retry with jitter on transient failures
- **Audit Logging**: Structured JSON logs with request correlation
- **Request/Response Middleware**: Safe logging with header sanitization
- **Error Handling**: Clear error messages with appropriate HTTP status codes

## Setup

### Prerequisites

- Python 3.10 or higher
- pip for dependency management
- Docker and Docker Compose (optional, for containerized deployment)

### Installation

1. Clone the repository and navigate to the project directory:

```bash
cd Moonshot-GRP
```

2. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. (Optional) Configure environment variables by copying `.env.example`:

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

### Running the Service

#### Option 1: Local Development (with Makefile)

```bash
# Install dependencies
make install

# Run the service
make run
```

#### Option 2: Direct uvicorn

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 3: Docker (Recommended for Production)

```bash
# Build and start the service
make docker-build
make docker-up

# View logs
make docker-logs

# Stop the service
make docker-down
```

The service will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Available Make Commands

The project includes a `Makefile` with common development tasks:

```bash
make help          # Show all available commands
make install       # Install Python dependencies
make run           # Run the service locally
make test          # Run pytest tests
make lint          # Run flake8 linter
make docker-build  # Build Docker image
make docker-up     # Start services with docker compose
make docker-down   # Stop services
make docker-logs   # View docker compose logs
make docker-restart # Restart services
make clean         # Clean Python cache files
```

## API Usage

### Endpoint

**POST** `/proxy/execute`

### Request Format

```json
{
  "operationType": "string",
  "payload": {
    // Operation-specific fields
  }
}
```

### Supported Operations

#### 1. ListLeagues

List all available leagues.

**Request:**

**Payload Schema:**

```json
{
  "operationType": "ListLeagues",
  "payload": {}
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "leagues": [
      ...
    ],
    "count": 5
  },
  "requestId": "my-request-id"
}
```

#### 2. GetLeagueMatches

Get matches for a specific league.

**Request:**

**Payload Schema:**

```json
{
  "operationType": "GetLeagueMatches",
  "payload": {
    "leagueId": "bl1"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "matches": [
      ...
    ],
    "count": 10
  },
  "requestId": "generated-uuid"
}
```

#### 3. GetTeam

Get team information by ID.

**Request:**

**Payload Schema:**

```json
{
  "operationType": "GetTeam",
  "payload": {
    "teamId": "100"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "team": {
      ...
    }
  },
  "requestId": "generated-uuid"
}
```

#### 4. GetMatch

Get match information by ID.

**Request:**

**Payload Schema:**

```json
{
  "operationType": "GetMatch",
  "payload": {
    "matchId": "12345"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "match": {
      ...
    }
  },
  "requestId": "generated-uuid"
}
```

## Payload Schemas

### Summary

| Operation          | Required Fields | Optional Fields |
|--------------------|-----------------|-----------------|
| `ListLeagues`      | None            | None            |
| `GetLeagueMatches` | `leagueId`      | None            |
| `GetTeam`          | `teamId`        | None            |
| `GetMatch`         | `matchId`       | None            |

### Normalized Response Fields

All successful responses follow this structure:

```json
{
  "success": true,
  "data": {
    // Operation-specific normalized data
  },
  "requestId": "string"
}
```

- **ListLeagues**: `data.leagues` (array), `data.count` (number)
- **GetLeagueMatches**: `data.matches` (array), `data.count` (number)
- **GetTeam**: `data.team` (object)
- **GetMatch**: `data.match` (object)

## Decision Mapper

The Decision Mapper (`app/decision_mapper.py`) is responsible for:

1. **Operation Routing**: Maps `operationType` to the appropriate handler
2. **Payload Validation**: Validates required fields per operation
3. **Provider Method Selection**: Routes to the correct provider adapter method
4. **Response Normalization**: Converts provider responses to a stable output schema

### How It Works

1. Receives `operationType` and `payload` from the request
2. Looks up the operation in the operations registry
3. Validates payload using operation-specific validation function
4. Executes the provider method with validated payload
5. Normalizes the response to a consistent format

### Adding New Operations

To add a new operation:

1. Add validation function: `_validate_<operation_name>`
2. Add execution function: `_execute_<operation_name>`
3. Add normalization function: `_normalize_<operation_name>`
4. Register in `self.operations` dictionary

## Adapter Pattern

### Interface Definition

The `SportsProvider` abstract interface (`app/providers/base.py`) defines:

```python
class SportsProvider(ABC):
    async def list_leagues() -> List[Dict[str, Any]]

        async def get_league_matches(league_id: str) -> List[Dict[str, Any]]

        async def get_team(team_id: str) -> Dict[str, Any]

        async def get_match(match_id: str) -> Dict[str, Any]
```

### OpenLiga Implementation

The `OpenLigaProvider` (`app/providers/openliga.py`) implements this interface:

- Maps abstract methods to OpenLiga API endpoints (see [API documentation](https://publicapi.dev/open-liga-db-api))
- Uses base URL: `https://api.openligadb.de` (endpoints are at root level, no `/api/` prefix needed)
- Handles all OpenLiga-specific URLs and parameters internally
- Implements rate limiting and exponential backoff
- Isolates provider-specific logic from the proxy layer

**Note on GetMatch**: The OpenLiga API doesn't have a direct endpoint to get a match by ID. The implementation searches
through league matches. For better performance, consider using `get_league_matches` with a specific `leagueId` and
filtering client-side.

### Swapping Providers

Provider selection is **configurable via environment variable** - no code changes needed!

#### Option 1: Environment Variable (Recommended)

Simply set the `PROVIDER` environment variable in your `.env` file:

```bash
PROVIDER=openliga
```

#### Option 2: Adding a New Provider

To add a new provider implementation:

1. **Create a new provider class** inheriting from `SportsProvider`:
   ```python
   # app/providers/newprovider.py
   from .base import SportsProvider
   
   class NewProvider(SportsProvider):
       async def list_leagues(self):
           # Implementation
           pass
       # ... implement other methods
   ```

2. **Register it in the provider factory** (`app/providers/__init__.py`):
   ```python
   from .newprovider import NewProvider
   
   provider_map = {
       "openliga": OpenLigaProvider,
       "newprovider": NewProvider,  # Add here
   }
   ```

3. **Use it** by setting `PROVIDER=newprovider` in your `.env` file

**No changes needed** to:

- `app/main.py` (uses factory function)
- Decision mapper code
- Proxy endpoint code

The provider is automatically selected based on the `PROVIDER` environment variable.

## Configuration

### Rate Limiting & Exponential Backoff

Configuration is managed via environment variables (see `.env.example`):

**Rate Limiting:**

- `RATE_LIMIT_RPS`: Requests per second (default: 0.25)
    - **Note**: OpenLiga API has a rate limit of 1000 requests/hour per IP (~0.28 RPS)
    - Default is set to 0.25 RPS (900 requests/hour) to stay safely under the limit
- `RATE_LIMIT_BURST`: Maximum burst size (default: 5)

**Exponential Backoff:**

- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `BACKOFF_BASE_SECONDS`: Base delay in seconds (default: 1.0)
- `BACKOFF_MAX_SECONDS`: Maximum delay cap (default: 30.0)
- `JITTER_ENABLED`: Enable jitter for backoff (default: true)

**Provider Settings:**

- `OPENLIGA_BASE_URL`: Base URL for OpenLiga API (default: https://www.openligadb.de)
- `REQUEST_TIMEOUT_SECONDS`: HTTP request timeout (default: 10)

**API Rate Limit**: The OpenLiga API enforces a rate limit of **1000 requests per hour per IP address**. The default
configuration (0.25 RPS = 900 requests/hour) is set to stay safely under this limit. Exceeding the limit will result in
429 errors that trigger exponential backoff retries.

### How Rate Limiting Works

Uses a token bucket algorithm:

- Tokens are added at the configured rate (RPS)
- Each request consumes one token
- Requests wait if no tokens are available
- Burst allows short bursts up to the burst limit

**Important**: The OpenLiga API enforces a rate limit of **1000 requests per hour per IP address**. The default rate
limit (0.25 RPS = 900 requests/hour) is configured to stay safely under this limit. If you need higher throughput, you
may need to:

- Use multiple IP addresses
- Contact OpenLiga for higher rate limits
- Adjust `RATE_LIMIT_RPS` carefully to avoid hitting the API limit

### How Exponential Backoff Works

On transient errors (429, 5xx, timeouts):

- Retry with exponential delay: `base * (2 ^ attempt)`
- Adds random jitter (10% of delay) if enabled
- Caps delay at `BACKOFF_MAX_SECONDS`
- Stops after `MAX_RETRIES` attempts

## Logging

### Audit Logs

Structured JSON logs are written to stdout with the following fields:

```json
{
  "requestId": "uuid",
  "timestamp": "2025-01-01T12:00:00Z",
  "operationType": "GetLeagueMatches",
  "validationOutcome": {
    "pass": true
  },
  "provider": "OpenLiga",
  "targetUrl": "https://publicapi.dev/open-liga-db-api/...",
  "upstreamStatusCode": 200,
  "latencyMs": 123.45,
  "finalOutcome": "success"
}
```

**Fields:**

- `requestId`: Unique request identifier (from header or generated)
- `timestamp`: ISO 8601 UTC timestamp
- `operationType`: The operation being executed
- `validationOutcome`: `{"pass": true}` or `{"pass": false, "reasons": [...]}`
- `provider`: Provider name (e.g., "OpenLiga")
- `targetUrl`: Upstream API URL (no secrets)
- `upstreamStatusCode`: HTTP status from upstream
- `latencyMs`: Request latency in milliseconds
- `finalOutcome`: "success" or "error"
- `error`: Error message (if applicable)

### Middleware Logs

Request/Response logs are also written to stdout:

**Request Log:**

```json
{
  "type": "request",
  "requestId": "uuid",
  "method": "POST",
  "path": "/proxy/execute",
  "headers": {
    ...
  },
  "bodySize": 123,
  "bodyPreview": "{\"operationType\":\"ListLeagues\"..."
}
```

**Response Log:**

```json
{
  "type": "response",
  "requestId": "uuid",
  "statusCode": 200,
  "bodySize": 456,
  "latencyMs": 123.45
}
```

**Security:**

- Sensitive headers (Authorization, API-Key, Cookie, etc.) are redacted
- Large bodies are truncated to first 500 characters
- No secrets are logged

### Sample Log Output

```
{"type":"request","requestId":"abc-123","method":"POST","path":"/proxy/execute","headers":{"host":"localhost:8000","content-type":"application/json"},"bodySize":45}
{"requestId":"abc-123","timestamp":"2025-01-01T12:00:00Z","operationType":"ListLeagues","validationOutcome":{"pass":true},"provider":"OpenLiga","targetUrl":"https://publicapi.dev/open-liga-db-api/...","upstreamStatusCode":200,"latencyMs":234.56,"finalOutcome":"success"}
{"type":"response","requestId":"abc-123","statusCode":200,"bodySize":1234,"latencyMs":234.56}
```

## Error Handling

### Error Responses

All errors follow this structure:

```json
{
  "error": "Error message",
  "details": {
    ...
  },
  // Optional
  "requestId": "uuid"
}
```

### Error Codes

| Status | Scenario              | Example                                                                    |
|--------|-----------------------|----------------------------------------------------------------------------|
| 400    | Unknown operationType | `{"error": "Unknown operationType: InvalidOp"}`                            |
| 400    | Validation failure    | `{"error": "Validation failed", "details": {"missing_field": "leagueId"}}` |
| 502    | Upstream API failure  | `{"error": "Upstream API failed"}`                                         |
| 500    | Internal server error | `{"error": "Internal server error"}`                                       |

### Error Flow

1. Unknown `operationType` → 400 immediately
2. Validation failure → 400 with details
3. Upstream errors after retries → 502
4. Unexpected errors → 500

All errors include `requestId` for correlation with logs.

## Project Structure

```
Moonshot-GRP/
├── app/                         # Main application package
│   ├── __init__.py
│   ├── main.py                  # FastAPI app and /proxy/execute endpoint
│   ├── models/                  # Pydantic models
│   │   ├── __init__.py
│   │   ├── request.py           # Request schemas (ProxyRequest, OperationPayload)
│   │   └── response.py          # Response schemas (ProxyResponse, ErrorResponse)
│   ├── decision_mapper.py       # Operation routing, validation, and normalization
│   ├── providers/               # Provider adapters
│   │   ├── __init__.py
│   │   ├── base.py             # SportsProvider abstract interface
│   │   ├── openliga.py         # OpenLiga API adapter with rate limiting & backoff
│   │   └── config.py           # Provider configuration (env vars)
│   ├── middleware/              # FastAPI middleware
│   │   ├── __init__.py
│   │   └── logging.py           # Request/response logging middleware
│   └── audit/                   # Audit logging
│       ├── __init__.py
│       └── logger.py            # Structured JSON audit logger
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_audit_logger.py    # Audit logger tests
│   ├── test_decision_mapper.py # Decision mapper tests
│   ├── test_main.py            # Main endpoint tests
│   ├── test_middleware.py      # Middleware tests
│   ├── test_models.py          # Model validation tests
│   └── test_provider.py        # Provider adapter tests
├── Dockerfile                   # Docker image definition
├── docker-compose.yml           # Docker Compose configuration
├── Makefile                     # Development commands
├── pytest.ini                   # Pytest configuration
├── .flake8                      # Flake8 linting configuration
├── .gitignore                   # Git ignore patterns
├── .env.example                 # Environment variables template
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Troubleshooting

### Common Issues

**Issue**: Docker build fails with permission errors

- **Solution**: Ensure Docker daemon is running and you have proper permissions

**Issue**: Rate limit errors (429) from OpenLiga API

- **Solution**: Reduce `RATE_LIMIT_RPS` in `.env` file or wait for rate limit window to reset

**Issue**: Tests fail with import errors

- **Solution**: Ensure virtual environment is activated and dependencies are installed: `make install`

**Issue**: Service doesn't start in Docker

- **Solution**: Check logs with `make docker-logs` and verify `.env` file exists (or remove `env_file` from
  docker-compose.yml)

### Getting Help

- Check logs: `make docker-logs` (for Docker) or check stdout (for local)
- Review configuration in `.env` file
- Check API documentation: https://publicapi.dev/open-liga-db-api
- Verify health endpoint: `curl http://localhost:8000/health`

### Key Components

- **`app/main.py`**: FastAPI application with single `/proxy/execute` endpoint
- **`app/decision_mapper.py`**: Routes operations, validates payloads, normalizes responses
- **`app/providers/openliga.py`**: OpenLiga API adapter with token bucket rate limiting and exponential backoff
- **`app/middleware/logging.py`**: Logs all requests/responses with header sanitization
- **`app/audit/logger.py`**: Structured JSON audit logging for all operations
- **`tests/`**: Comprehensive test suite with pytest

## Docker Deployment

### Building the Image

```bash
make docker-build
# or
docker compose build
```

### Running with Docker Compose

1. **Create `.env` file** (optional, uses defaults if not present):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Start the service**:
   ```bash
   make docker-up
   # or
   docker compose up -d
   ```

3. **View logs**:
   ```bash
   make docker-logs
   # or
   docker compose logs -f
   ```

4. **Stop the service**:
   ```bash
   make docker-down
   # or
   docker compose down
   ```

### Docker Features

- **Health Checks**: Built-in health check using `/health` endpoint
- **Environment Variables**: Configurable via `.env` file or docker-compose environment section
- **Port Mapping**: Service exposed on port 8000
- **Auto-restart**: Container restarts automatically unless stopped

### Dockerfile Details

- Base image: `python:3.10-slim`
- Installs dependencies from `requirements.txt`
- Copies application code
- Exposes port 8000
- Includes health check (checks `/health` endpoint every 30s)

## Testing

### Running Tests

```bash
# Run all tests
make test
# or
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_main.py

# Run with coverage (if pytest-cov is installed)
pytest tests/ --cov=app --cov-report=term-missing
```

### Test Configuration

Tests are configured in `pytest.ini`:

- Test discovery: `tests/` directory
- Async support: `pytest-asyncio` with auto mode
- Markers: `asyncio`, `unit`, `integration`

## Code Quality

### Linting

```bash
# Run flake8 linter
make lint
# or
flake8 app/ tests/ --max-line-length=100
```

Linting configuration is in `.flake8`:

- Max line length: 100 characters
- Excludes: `__pycache__`, `.venv`, build artifacts
- Ignores: E203, E501, W503 (common false positives)

## Development

### Setting Up Development Environment

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Moonshot-GRP
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   make install
   # or
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

5. **Run tests**:
   ```bash
   make test
   ```

6. **Start development server**:
   ```bash
   make run
   ```






