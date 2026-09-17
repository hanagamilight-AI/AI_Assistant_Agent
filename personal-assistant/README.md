# AI Personal Assistant Agent

A production-oriented AI Personal Assistant Agent that acts as a central interface for a user's digital work and personal tasks.

## Features

- **Natural Language Understanding**: Understand and process natural-language requests
- **Context Management**: Maintain short-term and long-term context
- **Information Retrieval**: Retrieve information from connected data sources via RAG
- **Tool Execution**: Use tools to perform actions with proper validation
- **Multi-step Planning**: Break complex requests into multiple steps
- **Verification**: Verify important tool results before responding
- **Confirmation System**: Ask for confirmation before sensitive or irreversible actions
- **Audit Trail**: Keep an auditable record of important actions
- **Extensible Architecture**: Add new tools and data sources without rewriting the core agent

## Architecture

```
                         ┌─────────────────────┐
                         │        User         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   API / Chat UI     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Assistant Service  │
                         └──────────┬──────────┘
                                    │
                   ┌────────────────┼────────────────┐
                   │                │                │
                   ▼                ▼                ▼
             ┌───────────┐   ┌────────────┐   ┌────────────┐
             │  Memory   │   │   Agent    │   │   RAG      │
             │  Service  │   │  Runtime   │   │  Service   │
             └───────────┘   └─────┬──────┘   └────────────┘
                                   │
                      ┌────────────┼────────────┐
                      │            │            │
                      ▼            ▼            ▼
                 ┌────────┐   ┌────────┐   ┌──────────┐
                 │ Tools  │   │  MCP   │   │ Planner  │
                 └────┬───┘   └────┬───┘   └──────────┘
                      │            │
             ┌────────┼────────────┼───────────────┐
             │        │            │               │
             ▼        ▼            ▼               ▼
          Calendar   Email      Database       Documents
```

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Redis (optional for caching/session state)

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS

### Agent/LLM
- Pluggable LLM provider abstraction
- Support for OpenAI-compatible providers and local models

## Project Structure

```
personal-assistant/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agent/
│   │   ├── tools/
│   │   ├── mcp/
│   │   ├── memory/
│   │   ├── rag/
│   │   ├── llm/
│   │   ├── security/
│   │   ├── db/
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   ├── migrations/
│   ├── pyproject.toml
│   └── .env.example
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env.example
│
├── docker/
│   └── docker-compose.yml
│
├── docs/
│
├── README.md
└── .gitignore
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Docker (optional)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
cp .env.example .env
# Edit .env with your configuration
python -m uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Docker Setup

```bash
docker-compose up -d
```

## Configuration

See `.env.example` files in both backend and frontend directories for required environment variables.

Key configuration options:
- `DATABASE_URL`: PostgreSQL connection string
- `LLM_PROVIDER`: LLM provider name
- `LLM_API_KEY`: API key for LLM provider
- `LLM_MODEL`: Model identifier
- `JWT_SECRET`: Secret for JWT authentication

## Documentation

- [Architecture](docs/architecture.md)
- [Tools](docs/tools.md)
- [Memory System](docs/memory.md)
- [Security](docs/security.md)

## Development

### Running Tests

```bash
cd backend
pytest
ruff check .
mypy .
```

### Frontend Development

```bash
cd frontend
npm run lint
npm run build
```

## License

MIT
