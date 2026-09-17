# Architecture Documentation

## Overview

The AI Personal Assistant Agent is built with a modular architecture that separates concerns and allows for easy extension.

## Core Components

### 1. API Layer (`app/api/`)

The API layer handles HTTP requests and responses using FastAPI.

- **Routes**: Define RESTful endpoints
- **Dependencies**: Provide shared dependencies (database sessions, authentication)
- **Schemas**: Pydantic models for request/response validation

### 2. Agent Runtime (`app/agent/`)

The agent runtime manages the conversation flow and decision-making.

- **State**: Explicit state object tracking conversation context
- **Graph**: State machine for agent execution flow
- **Planner**: Breaks complex requests into steps
- **Executor**: Executes tool calls and handles results
- **Prompts**: Template system for LLM interactions

### 3. Tools (`app/tools/`)

Tools provide the agent with capabilities to interact with external systems.

- **Registry**: Central registration and discovery
- **Base Tool**: Common interface and error handling
- **Concrete Tools**: Task management, calendar, email, etc.

### 4. Memory System (`app/memory/`)

Three-layer memory architecture:

1. **Conversation Memory**: Short-term context within a conversation
2. **Long-term Memory**: Durable user preferences and facts
3. **Semantic Memory**: Vector-based retrieval via RAG

### 5. RAG Service (`app/rag/`)

Retrieval-Augmented Generation for document search.

- **Ingestion**: Parse and process documents
- **Chunking**: Split documents into retrievable segments
- **Embeddings**: Generate vector representations
- **Retriever**: Find relevant content

### 6. LLM Abstraction (`app/llm/`)

Provider-agnostic LLM interface.

- **Protocol**: Define common interface
- **Providers**: OpenAI, Anthropic, local models
- **Structured Output**: JSON schema enforcement

### 7. MCP Integration (`app/mcp/`)

Model Context Protocol for external tool servers.

- **Client**: Connect to MCP servers
- **Manager**: Handle multiple server connections
- **Adapters**: Translate MCP tools to internal format

### 8. Database (`app/db/`)

PostgreSQL data layer with SQLAlchemy.

- **Models**: ORM definitions
- **Session**: Async session management
- **Repositories**: Data access patterns

## Data Flow

```
User Request
    │
    ▼
API Route → Authentication → Validation
    │
    ▼
Agent Runtime
    │
    ├── Load Conversation Context
    │
    ├── Retrieve Memories
    │
    ├── Classify Intent
    │
    ├── Plan (if complex)
    │
    ├── Execute Tools
    │       │
    │       ├── Local Tools
    │       │
    │       └── MCP Tools
    │
    ├── Verify Results
    │
    ├── Generate Response
    │
    └── Update Memory
    │
    ▼
API Response → User
```

## State Management

The agent uses an explicit state object (`AgentState`) to track:

- User and conversation identifiers
- Message history
- Retrieved context and memories
- Execution plan and current step
- Tool calls and results
- Confirmation requirements
- Final response
- Errors

This prevents arbitrary state mutation and makes the execution flow traceable.

## Security Model

### Authentication
- JWT-based authentication (to be implemented)
- User-level data isolation

### Authorization
- Role-based access control
- Tool-level permissions

### Data Protection
- User data never crosses user boundaries
- Secrets managed via environment variables
- Audit logging for sensitive operations

### Prompt Injection Protection
- Retrieved content treated as untrusted data
- Clear separation between system instructions and user/retrieved content
- Policy checks enforced at application level, not just LLM level

## Extension Points

### Adding New Tools
1. Create tool class implementing `BaseTool`
2. Define metadata (name, description, risk level)
3. Implement `_execute` method
4. Register with `tool_registry`

### Adding New LLM Providers
1. Implement `LLMProvider` protocol
2. Add to provider factory
3. Configure via environment variables

### Adding MCP Servers
1. Configure in MCP config file
2. Implement server following MCP specification
3. Agent discovers tools automatically

## Testing Strategy

### Unit Tests
- Tool schemas and validation
- Permission rules
- Memory extraction logic
- Chunking and retrieval

### Integration Tests
- Database operations
- MCP connections
- Tool registry
- API endpoints

### Functional Tests
- Mocked database scenarios
- Deterministic tool responses
- End-to-end workflows

### Evaluation Suite
- Correctness measurement
- Groundedness checking
- Hallucination detection
- Safety verification
