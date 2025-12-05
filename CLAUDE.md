# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Airweave is an open-source context retrieval layer for AI agents. It connects to apps, productivity tools, databases, or document stores and transforms their contents into searchable knowledge bases, accessible through a standardized interface (REST API or MCP).

**Architecture**: Monorepo with Python FastAPI backend, React/TypeScript frontend, Python Temporal workers, and Node.js MCP server.

## Commands

### Development Setup

```bash
# Initial setup (builds and runs all services with Docker)
./start.sh

# For ongoing development, use VS Code launch configurations:
# - "FastAPI" - run backend only
# - "Debug React" - run frontend only
# - "FastAPI + ARQ Worker" - full stack development
```

### Backend Development

```bash
cd backend

# Install dependencies
poetry install

# Run backend locally (for debugging)
poetry run uvicorn airweave.main:app --reload --host 0.0.0.0 --port 8001

# Linting and formatting
ruff check .                    # Check for linting errors
ruff format .                   # Auto-format code
ruff check --fix .              # Auto-fix linting errors

# Database migrations
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                              # Apply migrations
alembic downgrade -1                              # Rollback one migration

# Run tests
pytest                          # Run all tests
pytest tests/unit              # Run unit tests only
pytest tests/integration       # Run integration tests only
pytest -k test_name            # Run specific test
pytest --cov=airweave          # Run with coverage report
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev                    # Runs on http://localhost:8080

# Build
npm run build                  # Production build
npm run build:dev              # Development build

# Linting
npm run lint                   # Run ESLint
```

### Monke Testing (E2E Connector Tests)

```bash
# Run end-to-end tests for a specific connector
./monke.sh <connector_short_name>

# Run with verbose logging
MONKE_VERBOSE=1 ./monke.sh <connector_short_name>
```

## Architecture

### Backend Structure

```
backend/airweave/
├── api/                    # FastAPI routes and endpoints
│   ├── v1/endpoints/      # REST API endpoints (by resource)
│   ├── deps.py            # Dependency injection (auth, db, logging)
│   ├── auth.py            # Auth0 integration
│   └── middleware.py      # Request processing, CORS, exception handling
├── models/                # SQLAlchemy ORM models
├── schemas/               # Pydantic validation schemas
├── crud/                  # Database operations (per entity)
├── platform/              # Core sync and integration logic
│   ├── sources/          # Source connectors (external API integrations)
│   ├── entities/         # Entity schemas (data models from sources)
│   ├── destinations/     # Vector database adapters (Qdrant, etc.)
│   ├── transformers/     # Data transformation processors
│   ├── embedding_models/ # Text vectorization services
│   ├── sync/            # Sync orchestration and worker pool
│   └── temporal/        # Workflow definitions and activities
├── search/               # Search service and query processing
├── core/                 # Configuration, logging, exceptions
└── db/                   # Database session management
```

### Key Backend Concepts

**Data Flow**: Source → Transformation (DAG) → Embedding → Destination (Vector DB)

**Sync Architecture** (pull-based concurrency):
- `AsyncWorkerPool`: Semaphore-controlled concurrency (default: 20 workers)
- `AsyncSourceStream`: Bounded queue with backpressure control
- `EntityProcessor`: Multi-stage pipeline (enrich → transform → vectorize → persist)
- `SyncDAGRouter`: Routes entities through transformation pipeline
- `SyncProgress`: Real-time progress tracking via Redis PubSub

**Authentication**:
- Auth0 (production) or mock auth (development with `AUTH_ENABLED=false`)
- API keys via `X-API-Key` header
- Organization context via `X-Organization-ID` header

**API Context**: `ApiContext` (from `deps.get_context`) provides unified access to:
- `organization_id`: Current organization
- `user`: Authenticated user (or None for API keys)
- `logger`: Contextual logger with request metadata
- `auth_method`: Auth method used (system/auth0/api_key)

### Frontend Structure

```
frontend/src/
├── components/            # React components
│   ├── ui/               # ShadCN UI primitives
│   ├── shared/           # Shared business components
│   └── [feature]/        # Feature-specific components
├── pages/                # Route-level components
├── lib/                  # Core utilities
│   ├── api.ts            # API client with auth integration
│   ├── stores/           # Zustand state stores
│   └── auth-context.tsx  # Auth provider
├── hooks/                # Custom React hooks
├── services/             # Business logic services
└── config/               # Configuration files
```

**Key Frontend Patterns**:
- **API Client** (`lib/api.ts`): Auto-injects auth tokens, organization context, session ID; handles token refresh on 401/403
- **State Management**: Zustand for global state, React Query for server state
- **Auth Flow**: PostHogProvider → ThemeProvider → BrowserRouter → Auth0Provider → AuthProvider → ApiAuthConnector
- **Organization Store**: Manages org switching with automatic state cleanup
- **Sync State Store**: Real-time sync progress via SSE
- **Toast Notifications**: Sonner library with custom styling (see `styles/toast.css`)

### Source Connector Implementation

Source connectors extract data from external services. Every connector requires:

1. **Entity schemas** (`platform/entities/{short_name}.py`)
   - Extend `ChunkEntity` (text) or `FileEntity` (files)
   - Use `AirweaveField(..., embeddable=True)` for searchable fields
   - Include `created_at`/`modified_at` with `is_created_at`/`is_updated_at` flags
   - Set breadcrumbs for entity relationships

2. **Source implementation** (`platform/sources/{short_name}.py`)
   - Decorate with `@source(name, short_name, auth_methods, oauth_type, config_class, labels)`
   - Implement `create()`, `generate_entities()`, `validate()`
   - Use `_get_with_auth()` pattern for API requests with token refresh
   - Use `process_file_entity()` for file attachments

3. **Auth config** (`platform/configs/auth.py`)
   - Extend `OAuth2WithRefreshAuthConfig`, `OAuth2AuthConfig`, or `AuthConfig`
   - Reference in source decorator via `auth_config_class`

4. **OAuth configuration** (`platform/auth/yaml/dev.integrations.yaml`)
   - Define client credentials and scopes

**Federated Search Sources** (for APIs with strict rate limits):
- Set `federated_search=True` in `@source` decorator
- Implement `search(query, limit)` instead of full sync
- Queries run at search time, not during sync

## Development Practices

### Backend Code Style

- Python 3.11+, FastAPI, SQLAlchemy async ORM
- **Formatting**: Ruff with 100 char line length, Google docstrings
- **Typing**: Typed parameters and returns (avoid `any`)
- **Functions**: Keep under 50 lines
- **Async**: Use async/await for all I/O operations
- **Logging**: Use contextual logger from `ctx.logger` (injected via DI)
  - INFO: High-level milestones
  - DEBUG: Detailed progress
  - WARNING: Recoverable errors
  - ERROR: Unrecoverable errors

### Frontend Code Style

- **TypeScript**: Strict typing, interfaces in `/types/index.ts`
- **Components**: Hooks first, effects next, handlers, then render
- **State**: Zustand for global, React Query for server, local for UI-only
- **Styling**: TailwindCSS with `cn()` utility
- **API Calls**: Always use `apiClient` from `lib/api.ts`, never fetch directly

### Common Patterns

**API Endpoint Structure**:
```python
@router.post("/", response_model=schemas.ResponseModel)
async def create_resource(
    resource_in: schemas.ResourceCreate,
    db: AsyncSession = Depends(deps.get_db),
    ctx: ApiContext = Depends(deps.get_context),
) -> schemas.ResponseModel:
    """Clear description."""
    # Validate → Delegate to CRUD/Service → Return schema
    return await crud.resource.create(db, obj_in=resource_in, ctx=ctx)
```

**Source Connector Token Refresh**:
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _get_with_auth(self, client: httpx.AsyncClient, url: str):
    access_token = await self.get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await client.get(url, headers=headers)

    if response.status_code == 401 and self.token_manager:
        new_token = await self.token_manager.refresh_on_unauthorized()
        headers = {"Authorization": f"Bearer {new_token}"}
        response = await client.get(url, headers=headers)

    response.raise_for_status()
    return response.json()
```

**Breadcrumb Tracking** (CRITICAL - often forgotten):
```python
from airweave.platform.entities._base import Breadcrumb

# Parent entity
yield WorkspaceEntity(entity_id=ws_id, breadcrumbs=[], name=name)

# Child entity - include parent breadcrumb
breadcrumbs = [Breadcrumb(entity_id=ws_id, name=ws_name, entity_type="WorkspaceEntity")]
yield ProjectEntity(entity_id=proj_id, breadcrumbs=breadcrumbs, name=name)
```

### Testing with Monke

Monke is the E2E testing framework for source connectors. Tests verify that entities sync correctly.

**Structure**:
- **Bongo** (`monke/bongos/{short_name}.py`): Creates/updates/deletes test data via external API
- **Generation schemas** (`monke/generation/schemas/{short_name}.py`): Pydantic schemas for LLM content generation
- **Generation adapter** (`monke/generation/{short_name}.py`): LLM-powered content generation
- **Test config** (`monke/configs/{short_name}.yaml`): Test flow definition

**Key principle**: Create and verify ALL entity types from your source connector (tasks, comments, files, etc.), not just top-level entities.

## Critical Implementation Details

### Backend

1. **Entity Embeddability**: Mark most user-visible, content-rich fields with `embeddable=True` for semantic search. Only exclude internal IDs and binary metadata.

2. **Breadcrumbs**: Always set breadcrumbs when entities have parent relationships. This is frequently forgotten but critical for entity context.

3. **Timestamps**: Include `created_at` or `modified_at` with proper flags (`is_created_at=True`, `is_updated_at=True`) for incremental sync.

4. **Token Refresh**: Use `_get_with_auth()` pattern to handle 401 errors and refresh tokens automatically.

5. **Database Sessions**: Create sparingly (only when needed) to minimize connection usage.

6. **Sync Performance**: Pre-load transformer cache with `sync_context.router.initialize_transformer_cache(db)` to avoid 1.5s database lookups per entity.

### Frontend

1. **API Client**: Always use `apiClient` from `lib/api.ts`. It handles token injection, organization context, session tracking, and auto-retry.

2. **Organization Context**: API automatically scopes to current org via `X-Organization-ID` header. State is cleared on organization switch.

3. **Error Handling**: Use `toast.error()` for user-facing errors. Check `response.ok` before parsing JSON.

4. **Auth Token**: Never expose tokens in URLs or localStorage. Use Auth0 secure storage.

## Important Notes

- The codebase uses a **pull-based concurrency model** for syncs (workers pull entities when ready, preventing system overload)
- **OAuth2 token types**: `with_refresh` (standard), `with_rotating_refresh` (rotating tokens), `access_only` (no refresh)
- **Temporal workflows** self-destruct when orphaned (sync/connection deleted during execution)
- **Rate limiting**: Distributed via Redis sorted sets with sliding window algorithm, plan-based limits
- **Context caching**: Redis-backed cache for organizations (5min TTL), users (3min TTL), API keys (10min TTL)
- **Session replay**: Frontend sends PostHog session ID via `X-Airweave-Session-ID` header to link backend events to frontend sessions

## Resources

- **Documentation**: https://docs.airweave.ai/
- **API Docs**: http://localhost:8001/docs (when running locally)
- **Discord**: https://discord.gg/gDuebsWGkn
- **Contributing**: See CONTRIBUTING.md for fork/PR workflow and commit message format
