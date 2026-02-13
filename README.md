# AI Research Assistant

A full-stack AI-powered research assistant that fetches, analyzes, and synthesizes academic papers into structured research reports.

## Overview

This application combines a multi-agent backend system with a modern React frontend to provide an end-to-end research experience. Users can enter a research query, and the system will automatically fetch relevant papers, analyze them using AI, and generate a comprehensive report with citations.

## Project Structure

```
├── backend/            # FastAPI backend with multi-agent system
│   ├── src/            # Application source code
│   │   ├── agents/     # Multi-agent pipeline (Planner, Fetcher, Analyzer, Writer)
│   │   ├── api/        # FastAPI REST endpoints
│   │   ├── llm/        # LLM integration (LiteLLM, Embeddings)
│   │   ├── retrieval/  # Academic paper sources (arXiv, Semantic Scholar, etc.)
│   │   ├── storage/    # MinIO, Vespa clients
│   │   └── utils/      # Config, logging utilities
│   ├── models/         # Database models and schemas
│   ├── tests/          # Unit and integration tests
│   ├── docker-compose.yml
│   └── README.md       # Backend documentation
│
├── Frontend/           # React + TypeScript frontend
│   ├── src/
│   │   ├── components/ # UI components (shadcn/ui)
│   │   ├── lib/        # API client, utilities
│   │   └── types/      # TypeScript definitions
│   ├── docker-compose.yml
│   └── README.md       # Frontend documentation
│
└── README.md           # This file
```

## Tech Stack

### Backend
- **Framework**: FastAPI + Uvicorn
- **Multi-Agent Pipeline**: Planner → Fetcher → Analyzer → Writer
- **LLM Gateway**: LiteLLM (supports OpenAI, Anthropic, Ollama)
- **Vector Search**: Vespa (BM25 + ANN hybrid search)
- **Database**: PostgreSQL 16
- **Object Storage**: MinIO (S3-compatible)
- **Container**: Docker Compose

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui, Radix UI
- **State Management**: React hooks
- **Server**: Nginx (production)

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key (or Anthropic/Ollama)

### 1. Clone & Configure

```bash
git clone <repository-url>
cd AI-Research-Assistant
```

**Required: Create environment file**

```bash
cd backend

# Create .env file from example
cp .env.example .env

# Edit .env and add your API keys
# Minimum required: OPENAI_API_KEY=sk-your-key-here
```

**Files to create before first run:**
| File | Source | Required Values |
|------|--------|-----------------|
| `backend/.env` | Copy from `.env.example` | `OPENAI_API_KEY` (or Anthropic/Ollama keys) |

### 2. Start the Full Stack

From the `backend` directory:

```bash
docker-compose up -d
```

This starts:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **MinIO**: http://localhost:9000 (console: 9001)
- **Vespa**: http://localhost:8080

### 3. Verify Services

```bash
docker ps

# Should show:
# - research-frontend
# - research-assistant
# - research-postgres
# - research-minio
# - research-vespa
```

### 4. Access the Application

1. Open **http://localhost:3000** in your browser
2. Enter a research query (e.g., "Recent advances in transformer architectures")
3. Click "Research" and wait for the AI to generate your report

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/research` | Execute research query (JSON body) |
| `POST` | `/research/stream` | Streaming research with progress updates |
| `GET` | `/reports` | List all research reports |
| `GET` | `/reports/{id}` | Get specific report |
| `DELETE` | `/reports/{id}` | Delete a report |
| `GET` | `/reports/{id}/export/{format}` | Export report (md, pdf, docx) |

## Development

### Backend Development

```bash
cd backend

# Install dependencies (local development)
pip install -r requirements.txt

# Run tests
docker-compose exec app pytest tests/ -v

# CLI mode
docker-compose exec app python -m src.main --query "your query" --max-papers 10
```

See [backend/README.md](backend/README.md) for detailed backend documentation.

### Frontend Development

```bash
cd Frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build
```

See [Frontend/README.md](Frontend/README.md) for detailed frontend documentation.

## Features

- **Multi-Agent AI Pipeline**: Intelligent orchestration of specialized agents
- **Academic Paper Search**: Aggregates papers from arXiv, Semantic Scholar, PubMed, OpenAlex
- **Hybrid Vector Search**: BM25 + semantic similarity for ranking papers
- **Theme Extraction**: AI-powered identification of research themes
- **Citation Management**: Automatic citation generation in multiple formats
- **Report Export**: Download reports as Markdown, PDF, or Word documents
- **Real-time Progress**: Streaming updates during research execution
- **Report History**: Persistent storage of all research queries and reports

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Planner   │────▶│   Fetcher   │────▶│   Analyzer  │────▶│   Writer    │
│    Agent    │     │    Agent    │     │    Agent    │     │    Agent    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                    │                    │                    │
   LiteLLM              arXiv API            Vespa ANN           LiteLLM
   (Planning)       Semantic Scholar       Embeddings         (Synthesis)
                      PubMed/OpenAlex
                           │
                    ┌──────┴──────┐
                    │  PostgreSQL │
                    │    MinIO    │
                    │    Vespa    │
                    └─────────────┘
```

## Configuration

Key environment variables in `backend/.env`:

```env
# LLM Provider (openai, anthropic, ollama)
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here

# Optional: Enable Ollama for local LLMs
ENABLE_OLLAMA=false
OLLAMA_MODEL=llama3.2

# Database
DATABASE_URL=postgresql+asyncpg://research_user:research_pass_2026@postgres:5432/research_assistant

# Optional: Vespa for advanced vector search
VESPA_HOST=http://vespa
```

## License

MIT License
