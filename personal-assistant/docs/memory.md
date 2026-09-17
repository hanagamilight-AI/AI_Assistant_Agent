# Memory System Documentation

## Overview

The memory system provides the AI assistant with context about the user across three layers:

1. **Conversation Memory** - Short-term context within a conversation
2. **Long-term Memory** - Durable user information
3. **Semantic Memory (RAG)** - Document-based knowledge retrieval

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  User Request                        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              Conversation Memory                     │
│  - Current conversation messages                     │
│  - Tool calls and results                            │
│  - Stored in PostgreSQL                              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│               Long-term Memory                       │
│  - User preferences                                  │
│  - Important facts                                   │
│  - Explicit instructions                             │
│  - Extracted from conversations                      │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              Semantic Memory (RAG)                   │
│  - Document chunks                                   │
│  - Vector embeddings                                 │
│  - Metadata-filtered retrieval                       │
└─────────────────────────────────────────────────────┘
```

## 1. Conversation Memory

### Purpose
Maintain context within an active conversation session.

### Storage
- PostgreSQL `messages` table
- Linked to conversation via foreign key
- Ordered by creation timestamp

### Schema
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    role TEXT NOT NULL,          -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB,              -- Optional tool call info
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Usage
```python
from app.db.repositories import MessageRepository

repo = MessageRepository(session)

# Add message
await repo.create(
    conversation_id=conv_id,
    role="user",
    content="Hello",
)

# Get recent history
messages = await repo.get_by_conversation(conv_id, limit=50)
```

### Lifecycle
- Created when user sends message
- Retained for conversation lifetime
- Deleted when conversation is deleted

## 2. Long-term Memory

### Purpose
Store durable information that should persist across conversations.

### Types
- **Preference**: User preferences (e.g., "prefers morning meetings")
- **Fact**: Important facts (e.g., "works at Company X")
- **Instruction**: Explicit instructions (e.g., "always summarize emails")
- **Context**: Project or work context (e.g., "working on Project Y migration")

### Storage
- PostgreSQL `memories` table
- Associated with user ID
- Includes importance score for ranking

### Schema
```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL,   -- preference, fact, instruction, context
    importance_score FLOAT,
    source TEXT,                 -- conversation, manual, extracted
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Memory Extraction

Memories are extracted from conversations using the LLM:

```python
async def extract_memories(conversation: str) -> list[Memory]:
    prompt = get_memory_extraction_prompt(conversation)
    
    response = await llm.generate_structured(
        messages=[LLMMessage(role="user", content=prompt)],
        response_schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "memory_type": {"type": "string"},
                    "importance_score": {"type": "number"}
                }
            }
        }
    )
    
    return response.data
```

### Importance Filtering

Not all information should be memorized. The system filters based on:

- **Importance Score**: Threshold (e.g., > 0.7)
- **Relevance**: Is this generally useful or just conversation-specific?
- **Policy**: Does this violate any privacy or security policies?

### Usage
```python
from app.db.repositories import MemoryRepository

repo = MemoryRepository(session)

# Get relevant memories
memories = await repo.get_by_user(
    user_id=user_id,
    memory_type="preference",
    limit=20
)

# Store new memory
await repo.create(
    user_id=user_id,
    content="Prefers concise responses",
    memory_type="preference",
    importance_score=0.8,
    source="extracted"
)
```

## 3. Semantic Memory (RAG)

### Purpose
Enable retrieval of information from documents and other text sources.

### Pipeline

```
Documents
    │
    ▼
┌─────────────────┐
│    Parser       │  Extract text from files
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Chunker      │  Split into retrievable segments
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Embedding     │  Generate vector representations
│     Model       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Vector Store  │  Store embeddings with metadata
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Retriever    │  Find relevant chunks
└─────────────────┘
```

### Supported Formats
- PDF
- TXT
- Markdown
- DOCX
- CSV
- JSON

### Chunking Strategy

Intelligent chunking preserves context:

```python
def chunk_document(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind('.', start, end)
            if last_period > start:
                end = last_period + 1
        
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks
```

### Metadata Filters

Retrieval respects user boundaries and access control:

```python
results = await retriever.search(
    query="project requirements",
    filters={
        "user_id": current_user_id,
        "access_level": {"$gte": "read"},
        "created_after": "2024-01-01"
    },
    top_k=5
)
```

### Citation

Responses include source citations:

```json
{
  "content": "The project deadline is March 15.",
  "sources": [
    {
      "document_id": "uuid",
      "filename": "project_plan.pdf",
      "chunk_index": 3,
      "relevance_score": 0.92
    }
  ]
}
```

## Memory Policies

### Privacy
- Never store sensitive data (passwords, API keys, PII)
- User data never crosses user boundaries
- Users can view and delete their memories

### Security
- Validate extracted memories before storage
- Audit memory access
- Encrypt sensitive fields at rest

### Quality
- Filter low-importance extractions
- Deduplicate similar memories
- Periodically review and prune outdated memories

## Integration Points

### Agent Runtime
The agent queries all memory layers before responding:

```python
async def process_request(state: AgentState):
    # Load conversation context
    state.messages = await load_conversation(state.conversation_id)
    
    # Retrieve relevant long-term memories
    state.memories = await retrieve_memories(
        user_id=state.user_id,
        query=state.user_request
    )
    
    # Search semantic memory
    state.retrieved_context = await rag_search(
        query=state.user_request,
        user_id=state.user_id
    )
    
    # Generate response with full context
    response = await generate_response(state)
```

### Memory Updates

After successful interactions:

```python
async def update_memory(state: AgentState):
    # Extract potential new memories
    candidates = await extract_memories(state.messages)
    
    # Filter and store important ones
    for candidate in candidates:
        if candidate.importance_score > THRESHOLD:
            await store_memory(candidate)
```

## Best Practices

1. **Be Selective**: Not everything should be memorized
2. **Respect Boundaries**: User data isolation is critical
3. **Provide Citations**: Always indicate information sources
4. **Handle Conflicts**: Recent information may override old
5. **Allow Control**: Users should manage their memories
6. **Audit Access**: Log all memory operations
