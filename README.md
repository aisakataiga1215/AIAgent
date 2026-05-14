# DevFlow AI

Multi-Agent Development Workflow System — automate code review, test generation, and documentation with AI.

## Architecture

```
CLI / Web UI → FastAPI → LangGraph Workflow Engine → Multi-Agent Core → Tool System
                                                          │
                                                    Memory / RAG / ChromaDB
```

### Agents
| Agent | Type | Tools | Status |
|-------|------|-------|--------|
| Orchestrator | Plan-Execute | FileRead | Done |
| Code Review | ReAct | Git, AST, File | Done |
| Test Gen | ReAct | TestRunner, Coverage | Planned |
| Doc Manager | ReAct | RepoScanner, APIDiff | Planned |
| Knowledge | ReAct | VectorSearch, WebSearch | Done |

### Tech Stack
- **Backend**: Python 3.12, FastAPI, LangGraph, Anthropic SDK
- **RAG**: ChromaDB + BM25 + RRF fusion
- **Memory**: Redis-style short-term + SQLite long-term
- **Frontend**: React 18, TypeScript, Vite, WebSocket
- **Observability**: structlog + Langfuse (optional)

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Anthropic API key

### Setup

```bash
# Clone & install
git clone https://github.com/aisakataiga1215/AIAgent.git
cd AIAgent
pip install -e .

# Configure
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY=sk-ant-xxx

# CLI usage
devflow review --repo ./           # Code review
devflow ingest --repo ./           # Index codebase for RAG
devflow workflow pr-review         # Run multi-agent workflow
devflow serve                      # Start API server
```

### Development

```bash
# Install dev dependencies
pip install -e ".[dev]"
pytest  # 53 tests

# Frontend
cd frontend && npm install && npm run dev
```

## Project Structure

```
src/
├── agents/     # Agent implementations (ReAct base, CodeReview, Orchestrator)
├── tools/      # MCP-compliant tool system (Git, File, AST, Shell, Web)
├── rag/        # RAG pipeline (chunker, embedder, ChromaDB, retriever)
├── memory/     # 3-tier memory (short-term, long-term, manager)
├── workflow/   # LangGraph workflow engine & templates
├── api/        # FastAPI routes + WebSocket
├── cli/        # Typer CLI
└── observability/  # logging, tracing, metrics
```

## License

MIT
