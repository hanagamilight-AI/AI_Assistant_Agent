# Tools Documentation

## Overview

Tools are the mechanism by which the AI assistant performs actions and retrieves information from external systems. Each tool follows a standard interface and includes metadata for permission checking and audit logging.

## Tool Interface

All tools implement the `Tool` protocol:

```python
class Tool(Protocol):
    metadata: ToolMetadata
    
    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        ...
```

## Tool Metadata

Each tool defines metadata that controls its behavior:

```python
@dataclass
class ToolMetadata:
    name: str                    # Unique identifier
    description: str             # Human-readable description
    requires_confirmation: bool  # Whether user confirmation is needed
    risk_level: RiskLevel        # LOW, MEDIUM, or HIGH
    reversible: bool             # Whether the action can be undone
    timeout_seconds: int         # Maximum execution time
    max_retries: int             # Number of retry attempts
```

## Risk Levels

### Low Risk
- Read-only operations
- No side effects
- Examples: search documents, read calendar, get tasks

### Medium Risk
- Create operations
- Reversible changes
- Examples: create task, create calendar event, draft email

### High Risk
- Destructive operations
- External side effects
- Examples: send email, delete data, make purchases

**High-risk tools always require explicit user confirmation.**

## Built-in Tools

### Task Tools

#### `create_task`
Create a new task for the user.

**Input:**
- `title` (string, required): Task title
- `description` (string, optional): Task description
- `due_date` (datetime, optional): When the task is due
- `priority` (string, optional): low, medium, or high

**Output:**
```json
{
  "task_id": "uuid",
  "title": "Task title",
  "status": "pending",
  "created_at": "ISO timestamp"
}
```

**Risk Level:** LOW  
**Requires Confirmation:** No

#### `get_tasks`
Retrieve user's tasks.

**Input:**
- `status` (string, optional): Filter by status
- `limit` (int, optional): Maximum tasks to return

**Output:**
```json
{
  "tasks": [...],
  "count": 10
}
```

**Risk Level:** LOW  
**Requires Confirmation:** No

## Creating Custom Tools

### Step 1: Define Input Schema

```python
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    param1: str = Field(..., description="Description")
    param2: int | None = Field(None, description="Optional parameter")
```

### Step 2: Implement Tool Class

```python
from app.tools.registry import BaseTool, ToolMetadata, RiskLevel, ToolContext, ToolResult

class MyCustomTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="my_custom_tool",
            description="What this tool does",
            requires_confirmation=False,
            risk_level=RiskLevel.LOW,
            reversible=True,
        )
    
    @property
    def input_schema(self) -> type[BaseModel]:
        return MyToolInput
    
    async def _execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        # Implement tool logic here
        try:
            validated = MyToolInput(**arguments)
            
            # Do something useful
            result = await self.do_something(validated.param1)
            
            return ToolResult.ok(data={"result": result})
        except Exception as e:
            return ToolResult.fail(error=str(e))
```

### Step 3: Register Tool

```python
from app.tools.registry import tool_registry

tool_registry.register(MyCustomTool())
```

## Tool Execution Flow

```
User Request
    │
    ▼
Agent identifies tool need
    │
    ▼
Tool selected from registry
    │
    ▼
Arguments validated against schema
    │
    ▼
Permission check (risk level, user settings)
    │
    ├── HIGH RISK ──► Request Confirmation ──► User approves?
    │                        │                      │
    │                        │                      ├── Yes ──► Continue
    │                        │                      │
    │                        │                      └── No ──► Abort
    │                        │
    │                        └── LOW/MEDIUM ──► Continue
    │
    ▼
Tool executes with timeout
    │
    ▼
Result verified
    │
    ├── Success ──► Log execution ──► Return to agent
    │
    └── Failure ──► Retry (if configured)
                       │
                       ├── Max retries reached ──► Return error
                       │
                       └── Retry successful ──► Continue
```

## Error Handling

Tools should handle errors gracefully:

```python
async def _execute(self, arguments, context) -> ToolResult:
    try:
        # Tool logic
        pass
    except ValidationError as e:
        return ToolResult.fail(error=f"Invalid arguments: {e}")
    except TimeoutError as e:
        return ToolResult.fail(error="Operation timed out")
    except ConnectionError as e:
        return ToolResult.fail(error="External service unavailable")
    except Exception as e:
        return ToolResult.fail(error=f"Unexpected error: {e}")
```

## Best Practices

1. **Validate Input**: Always validate arguments using Pydantic schemas
2. **Handle Errors**: Catch and report errors clearly
3. **Log Executions**: All tool calls are logged for auditing
4. **Respect Timeouts**: Long-running operations should have timeouts
5. **Idempotency**: Design tools to be safely retryable when possible
6. **Clear Descriptions**: Write clear descriptions for the LLM to understand when to use the tool
7. **Minimal Permissions**: Tools should only access what they need

## Security Considerations

- Never expose sensitive credentials in tool outputs
- Validate all external data before processing
- Implement rate limiting for expensive operations
- Audit all tool executions
- Respect user data isolation boundaries
