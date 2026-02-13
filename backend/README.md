# AI Research Assistant - Backend

FastAPI-based backend with multi-agent AI system for automated research report generation.

## Overview

The backend orchestrates a pipeline of specialized AI agents that:
1. **Plan** research strategy from user queries
2. **Fetch** academic papers from multiple sources
3. **Analyze** and rank papers using embeddings + vector search
4. **Write** comprehensive research reports with citations

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **API Framework** | FastAPI + Uvicorn |
| **LLM Gateway** | LiteLLM (OpenAI/Anthropic/Ollama) |
| **Vector Search** | Vespa (BM25 + ANN) with cosine fallback |
| **Database** | PostgreSQL 16 + SQLAlchemy |
| **Object Storage** | MinIO (S3-compatible) |
| **Embeddings** | OpenAI/Ollama |
| **Container** | Docker Compose |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key (or Anthropic/Ollama)

### 1. Configure

```bash
cd backend
cp .env.example .env
# Edit .env — add your LLM API key
```

### 2. Start Services

```bash
docker-compose up -d
```

Services started:
- **API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **MinIO**: http://localhost:9000 (console: 9001)
- **Vespa**: http://localhost:8080 (optional)
- **Frontend** (via nginx proxy): http://localhost:3000

### 3. Verify

```bash
docker ps
# Should show: research-assistant, research-postgres, research-minio, research-vespa, research-frontend

# Health check
curl http://localhost:8000/health
```

## API Documentation

### Interactive Documentation

FastAPI provides built-in interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs — Interactive API explorer with try-it functionality
- **ReDoc**: http://localhost:8000/redoc — Alternative documentation interface

### OpenAPI Specification

The complete OpenAPI 3.0.3 specification is available at:
- **File**: `openapi.yaml` in the backend directory
- **JSON Endpoint**: http://localhost:8000/openapi.json

This specification can be imported into:
- Postman
- Swagger Editor (https://editor.swagger.io)
- Insomnia
- Any OpenAPI-compatible tool

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check |
| `POST` | `/research` | Execute research (standard) |
| `POST` | `/research/stream` | Execute research (streaming) |
| `GET` | `/reports` | List all reports |
| `GET` | `/reports/{id}` | Get specific report |
| `DELETE` | `/reports/{id}` | Delete report |
| `GET` | `/reports/{id}/export/{format}` | Export report (md/pdf/docx) |

---

### Health Check

```
GET /health
```

Returns service status and configuration.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "research-assistant",
  "version": "1.0.0",
  "llm_provider": "openai",
  "model": "gpt-4o-mini"
}
```

---

### Execute Research (Standard)

```
POST /research
```

Execute a research query and return the complete report.

**Request Body:**
```json
{
  "query": "Recent advances in transformer architectures",
  "max_papers": 10
}
```

**Response (200 OK):**
```json
{
  "report_id": "abc123",
  "query": "Recent advances in transformer architectures",
  "papers_analyzed": 10,
  "themes": [
    {
      "name": "Attention Mechanisms",
      "description": "Novel attention variants in transformers",
      "relevance_score": 0.95,
      "paper_ids": ["arxiv:1234", "arxiv:5678"]
    }
  ],
  "citations": [
    "[1] Vaswani et al (2017). \"Attention Is All You Need\". arXiv. https://arxiv.org/abs/1706.03762"
  ],
  "markdown_report": "# Research Report: Recent advances in transformer architectures\n\n## Executive Summary...",
  "top_papers": [
    {
      "id": "arxiv:1234",
      "title": "Attention Is All You Need",
      "authors": ["Vaswani", "Shazeer", "Parmar"],
      "relevance_score": 0.98
    }
  ],
  "minio_url": "s3://reports/abc123.md"
}
```

**Error Response (500):**
```json
{
  "detail": "Research failed: Error message"
}
```

---

### Execute Research (Streaming)

```
POST /research/stream
```

Execute research with Server-Sent Events (SSE) for real-time progress updates.

**Request Body:** Same as `/research`

**Response:** SSE stream with JSON events

```
data: {"status": "starting", "message": "Initializing research for: transformer architectures..."}

data: {"status": "planning", "message": "Creating search plan..."}

data: {"status": "planned", "message": "Plan: 3 keywords, sources=['arxiv']"}

data: {"status": "fetching", "message": "Searching for papers max=10..."}

data: {"status": "fetched", "message": "Fetched 10 unique papers", "papers_count": 10}

data: {"status": "analyzing", "message": "Analyzing 10 papers & extracting themes..."}

data: {"status": "analyzed", "message": "Identified 4 key themes from 10 top papers."}

data: {"status": "writing", "message": "Synthesizing final research report..."}

data: {"status": "complete", "report_id": "abc123", "query": "transformer architectures", "papers_analyzed": 10, "themes": [...], "citations": [...], "markdown_report": "..."}
```

**Client Example (JavaScript):**
```javascript
const response = await fetch('/research/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'neural networks', max_papers: 10 })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const lines = decoder.decode(value).split('\n');
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      console.log(data.status, data.message);
    }
  }
}
```

---

### List Reports

```
GET /reports
```

Returns list of all past research reports from PostgreSQL.

**Response (200 OK):**
```json
[
  {
    "id": "abc123de",
    "query_text": "Recent advances in transformer architectures",
    "created_at": "2024-01-15T10:30:00",
    "papers_count": 10,
    "themes_count": 4,
    "citations_count": 15
  },
  {
    "id": "def456gh",
    "query_text": "Graph neural networks applications",
    "created_at": "2024-01-14T15:20:00",
    "papers_count": 8,
    "themes_count": 3,
    "citations_count": 12
  }
]
```

---

### Get Report

```
GET /reports/{id}
```

Returns full details of a specific report including markdown content.

**Path Parameters:**
- `id` (string): Report ID (UUID or short 8-char)

**Response (200 OK):**
```json
{
  "id": "abc123de",
  "query_text": "Recent advances in transformer architectures",
  "created_at": "2024-01-15T10:30:00",
  "markdown_content": "# Research Report...",
  "minio_path": "s3://reports/abc123de.md",
  "papers_count": 10,
  "themes": [
    {
      "name": "Attention Mechanisms",
      "description": "Novel attention variants",
      "relevance_score": 0.95,
      "paper_ids": ["arxiv:1234"]
    }
  ],
  "citations": ["[1] Vaswani et al (2017)..."],
  "top_papers": [
    {
      "id": "arxiv:1234",
      "title": "Attention Is All You Need",
      "authors": ["Vaswani", "Shazeer", "Parmar"],
      "url": "https://arxiv.org/abs/1706.03762"
    }
  ]
}
```

**Error Response (404):**
```json
{
  "detail": "Report not found"
}
```

---

### Delete Report

```
DELETE /reports/{id}
```

Deletes a report from the database.

**Path Parameters:**
- `id` (string): Report ID

**Response (200 OK):**
```json
{
  "message": "Report deleted successfully"
}
```

---

### Export Report

```
GET /reports/{id}/export/{format}
```

Export report in specified format. Returns file download.

**Path Parameters:**
- `id` (string): Report ID
- `format` (string): One of `md`, `pdf`, `docx`

**Response:**
- Content-Type varies by format:
  - `md`: `text/markdown`
  - `pdf`: `application/pdf`
  - `docx`: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Content-Disposition: `attachment; filename="research-report-{id}.{format}"`

**Error Response (400):**
```json
{
  "detail": "Invalid format. Supported: md, pdf, docx"
}
```

---

## Multi-Agent Architecture

### Agent Pipeline

```
Query → Planner → Fetcher → Analyzer → Writer → Report
         ↓          ↓          ↓         ↓
      LiteLLM    arXiv API   Vespa/    LiteLLM
                 PubMed      Cosine
                 Semantic    Fallback
                 Scholar
```

### 1. Planner Agent (`src/agents/planner_agent.py`)

**Purpose:** Analyze query and create search strategy

**Process:**
- Extract keywords using LLM
- Select data sources based on query domain
- Determine optimal paper count

**Output:**
```python
SearchPlan(
    keywords=["transformer", "attention", "architecture"],
    sources=["arxiv", "semantic_scholar"],
    max_papers=10
)
```

### 2. Fetcher Agent (`src/agents/fetcher_agent.py`)

**Purpose:** Retrieve papers from academic sources

**Sources:**
| Source | Status | Description |
|--------|--------|-------------|
| arXiv | ✅ Full | Primary source, well-implemented |
| Semantic Scholar | ✅ Full | Academic search with citations |
| PubMed | 🔧 Basic | Biomedical literature |
| OpenAlex | 🔧 Basic | Open academic graph |

**Features:**
- Deduplication by paper ID
- Parallel source querying
- PDF download to MinIO (best-effort)
- Source aggregation

### 3. Analyzer Agent (`src/agents/analyzer_agent.py`)

**Purpose:** Rank papers and extract themes

**Ranking Strategy:**
1. Generate embeddings for all abstracts
2. **If Vespa available:** Hybrid BM25 + ANN search
3. **Fallback:** In-memory cosine similarity

**Theme Extraction:**
- K-means clustering on embeddings (2-4 clusters)
- LLM generates theme names/descriptions
- Relevance scoring per cluster

### 4. Writer Agent (`src/agents/writer_agent.py`)

**Purpose:** Generate final research report

**Output Format:**
- Markdown with structured sections
- Executive summary
- Theme-based organization
- Citations in standard format
- References section

## Request/Response Schemas

### ResearchRequest

```python
{
  "query": string,          # Required: Research query text
  "max_papers": integer     # Optional: Max papers to analyze (default: 10)
}
```

### ResearchResponse

```python
{
  "report_id": string,
  "query": string,
  "papers_analyzed": integer,
  "themes": Theme[],
  "citations": string[],
  "markdown_report": string,
  "top_papers": Paper[],
  "minio_url": string?
}
```

### Theme

```python
{
  "name": string,
  "description": string,
  "relevance_score": float,  # 0.0 - 1.0
  "paper_ids": string[]
}
```

### Paper

```python
{
  "id": string,
  "title": string,
  "authors": string[],
  "abstract": string,
  "published_date": string,  # ISO 8601
  "url": string,
  "pdf_url": string?,
  "citations": integer,
  "source": string  # arxiv, semantic_scholar, etc.
}
```

### ReportSummary

```python
{
  "id": string,
  "query_text": string,
  "created_at": string,      # ISO 8601
  "papers_count": integer,
  "themes_count": integer,
  "citations_count": integer
}
```

## Data Storage

### PostgreSQL Schema

```sql
-- Research queries table
CREATE TABLE research_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    papers_fetched INTEGER,
    papers_analyzed INTEGER,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Reports table
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID REFERENCES research_queries(id),
    query_text TEXT NOT NULL,
    markdown_content TEXT,
    minio_path VARCHAR(500),
    papers_count INTEGER,
    themes JSONB,
    citations JSONB,
    top_papers JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### MinIO Buckets

- `research-papers`: PDF storage
- `research-reports`: Generated markdown reports

## Testing

### Test Structure

```
tests/
├── conftest.py              # Pytest fixtures
├── mocks/                   # Mock data
├── unit/                    # Unit tests
│   ├── test_planner.py      # Planner agent tests
│   ├── test_fetcher.py      # Fetcher agent tests
│   ├── test_analyzer.py     # Analyzer agent tests
│   └── test_writer.py       # Writer agent tests
└── integration/
    └── test_end_to_end.py   # Full pipeline tests
```

### Running Tests

```bash
# All tests
docker-compose exec app pytest tests/ -v

# Unit tests only
docker-compose exec app pytest tests/unit/ -v

# Integration tests (requires services)
docker-compose exec app pytest tests/integration/ -v

# With coverage
docker-compose exec app pytest --cov=src tests/ -v

# Specific test
docker-compose exec app pytest tests/unit/test_analyzer.py -v
```

### Manual API Testing

```bash
# Health
curl http://localhost:8000/health

# Research (standard)
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer architectures", "max_papers": 5}'

# Research (streaming)
curl -N -X POST http://localhost:8000/research/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "neural networks", "max_papers": 5}' | \
  while read line; do
    if [[ $line == data:* ]]; then
      echo "$line" | sed 's/data: //'
    fi
  done

# List reports
curl http://localhost:8000/reports

# Get report
curl http://localhost:8000/reports/abc123

# Export PDF
curl -O -J http://localhost:8000/reports/abc123/export/pdf

# Delete report
curl -X DELETE http://localhost:8000/reports/abc123
```

## Configuration

### Environment Variables

```env
# Required
LLM_PROVIDER=openai                    # openai, anthropic, ollama
OPENAI_API_KEY=sk-...                  # Your API key

# Optional LLM Settings
LITELLM_MODEL=gpt-4o-mini
TOP_K_PAPERS=10
MAX_PAPERS_TOTAL=50

# Optional: Enable local LLM
ENABLE_OLLAMA=false
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Database (default works with docker-compose)
DATABASE_URL=postgresql+asyncpg://research_user:research_pass_2026@postgres:5432/research_assistant

# MinIO (default works with docker-compose)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# Optional: Vespa vector search
ENABLE_VESPA=false
VESPA_HOST=http://vespa
VESPA_PORT=8080
VESPA_DEPLOY_PORT=19071

# Embedding
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_TIMEOUT=30
```

## CLI Usage

```bash
# Single query
docker-compose exec app python -m src.main \
  --query "transformer architectures" \
  --max-papers 10

# Interactive mode
docker-compose exec app python -m src.main --interactive

# Save to file
docker-compose exec app python -m src.main \
  -q "neural networks" \
  -o data/outputs/reports/nn_report.md

# With specific provider override
docker-compose exec app python -m src.main \
  --query "quantum computing" \
  --provider anthropic \
  --model claude-3-haiku-20240307
```

## Troubleshooting

### Database Issues
```bash
# Check logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### LLM Errors
- Verify API key in `.env`
- Check provider service status
- Try alternative provider

### Vector Search Fallback
If Vespa is unavailable, the system automatically uses in-memory cosine similarity. No action needed.

### MinIO Not Working
- Check endpoint configuration
- Verify credentials
- Check if bucket exists: `docker-compose exec minio mc ls local/`

## License

MIT License
