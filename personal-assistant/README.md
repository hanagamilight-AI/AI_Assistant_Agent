# AI Personal Assistant Agent

A production-oriented AI Personal Assistant accessible via Telegram bot that acts as a central interface for your digital work and personal tasks.

## Features

- **Natural Language Understanding**: Understands and responds to natural-language requests
- **Task Management**: Create, update, and track tasks
- **Conversation Memory**: Maintains short-term and long-term context
- **Tool Integration**: Extensible tool system for calendar, email, documents, etc.
- **Telegram Bot Interface**: Access your assistant directly from Telegram
- **MCP Support**: Model Context Protocol for external tools and data sources
- **RAG Ready**: Document retrieval and semantic search capabilities

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- A Telegram account (for bot access)
- An LLM API key (OpenAI or compatible)

### 1. Clone and Configure

```bash
cd personal-assistant/backend
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
LLM_API_KEY=your-openai-api-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

### 2. Start with Docker

```bash
cd ../docker
docker-compose up -d
```

### 3. Set up Telegram Webhook

For local development using ngrok:

```bash
# In a new terminal
ngrok http 8000

# Copy the HTTPS URL and set webhook
curl -X POST http://localhost:8000/api/v1/telegram/set-webhook
```

Or if you have a public domain:

```bash
curl -X POST https://your-domain.com/api/v1/telegram/set-webhook
```

### 4. Chat with Your Bot

1. Open Telegram
2. Search for your bot by username
3. Start chatting! Try:
   - "Create a task to finish the API documentation tomorrow"
   - "What meetings do I have tomorrow?"
   - "Help me prepare for tomorrow's client meeting"

## Architecture

```
┌─────────────┐
│   Telegram  │
│     Bot     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  FastAPI    │
│   Backend   │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌─────┐ ┌──────┐
│Agent│ │ Tools│
└──┬──┘ └──┬───┘
   │       │
   ▼       ▼
┌─────┐ ┌──────┐
│ LLM │ │ MCP  │
└─────┘ └──────┘
```

## Project Structure

```
personal-assistant/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # REST API endpoints
│   │   ├── agent/           # Agent state and prompts
│   │   ├── tools/           # Tool implementations
│   │   ├── llm/             # LLM provider abstraction
│   │   ├── db/              # Database models and repositories
│   │   └── main.py          # Application entry point
│   ├── tests/               # Test suites
│   └── .env                 # Environment configuration
├── docker/
│   ├── docker-compose.yml   # Docker services
│   └── Dockerfile.backend   # Backend container
├── docs/                    # Documentation
└── README.md
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_API_KEY` | OpenAI or compatible API key | Yes |
| `LLM_MODEL` | Model name (e.g., gpt-4o-mini) | No (default: gpt-4o-mini) |
| `DATABASE_URL` | PostgreSQL connection string | No (Docker default provided) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | For Telegram access |
| `TELEGRAM_WEBHOOK_URL` | Public webhook URL | For production |

See `backend/.env.example` for all options.

## API Endpoints

### Chat
- `POST /api/v1/chat` - Send a message and get response

### Conversations
- `GET /api/v1/conversations` - List conversations
- `GET /api/v1/conversations/{id}` - Get conversation details
- `DELETE /api/v1/conversations/{id}` - Delete conversation

### Tasks
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks` - Create task
- `PATCH /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task

### Telegram
- `POST /api/v1/telegram/webhook` - Receive Telegram updates
- `POST /api/v1/telegram/set-webhook` - Configure webhook
- `GET /api/v1/telegram/webhook-info` - Get webhook status

### Health
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/ready` - Readiness check

## Development

### Local Setup (without Docker for app)

```bash
# Install dependencies
cd backend
pip install -e ".[dev]"

# Start PostgreSQL and Redis
docker-compose -f docker/docker-compose.yml up -d db redis

# Run migrations
alembic upgrade head

# Start backend
python -m app.main
```

### Running Tests

```bash
cd backend
pytest
```

### Code Quality

```bash
ruff check .
mypy .
```

## Documentation

- [Architecture](docs/architecture.md) - System design and components
- [Tools](docs/tools.md) - Tool system guide
- [Memory](docs/memory.md) - Memory architecture
- [Security](docs/security.md) - Security best practices
- [Telegram Setup](docs/telegram_setup.md) - Complete Telegram bot setup guide

## Roadmap

- [x] Core agent architecture
- [x] Telegram bot integration
- [x] Task management tools
- [ ] Calendar integration
- [ ] Email integration
- [ ] Document RAG system
- [ ] MCP server support
- [ ] Multi-step planning
- [ ] Advanced memory management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.
