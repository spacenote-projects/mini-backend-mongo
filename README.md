# mini-backend-mongo

A minimal version of [spacenote-backend](https://github.com/spacenote-projects/spacenote-backend) designed to extract and preserve only the core functionality.

## Project Purpose

This project is part of a database comparison experiment to help decide between **MongoDB** and **PostgreSQL** for the main SpaceNote project.

### Why This Project Exists

The original `spacenote-backend` has grown to include many features (~8,000 lines of code, 14 modules). To make an informed decision about the database choice, we need:

1. **Simplified codebase** - Strip away optional integrations (Telegram, LLM, advanced image processing) and keep only essential features
2. **Clear comparison baseline** - A minimal MongoDB implementation that can be directly compared with `mini-backend-postgres`
3. **Focus on core patterns** - Highlight how MongoDB handles the fundamental data structures (users, spaces, custom fields, notes, comments, filters)

### Parallel Projects

- **mini-backend-mongo** (this repo) - MongoDB implementation
- **mini-backend-postgres** (planned) - PostgreSQL implementation with identical functionality

After implementing both versions, we'll compare:
- Code complexity
- Query patterns
- Performance characteristics
- Developer experience
- Schema flexibility vs. structure

## Project Status

🚧 **In Development** - Features are being added incrementally.

This README will be updated as functionality is implemented.

## Technology Stack

- **Python 3.14+**
- **FastAPI** - Modern async web framework
- **MongoDB** - Document database with flexible schema
- **Pydantic** - Data validation and settings management

## Architecture Decisions

### Natural Keys vs Surrogate Keys

Unlike the original `spacenote-backend` which uses UUID-based IDs throughout the API, this implementation uses **natural keys** as the primary identifiers:

- **Technical ID**: Every collection has `_id: ObjectId` for MongoDB's internal use
- **API/Code**: We use natural keys as primary identifiers:
  - `User` → identified by `username` (string)
  - `Space` → identified by `slug` (string)
  - `Note` → identified by `space_slug + number` (composite key)

**Benefits**:
- More readable URLs and API responses
- Semantic identifiers that have business meaning
- Simplified caching (no need to map IDs to entities)
- Direct lookups without additional index queries

**Example**:
```
GET /spaces/my-project/notes/42  # Natural keys
vs
GET /spaces/a1b2c3d4.../notes/e5f6g7h8...  # UUID-based
```

### Project Constraints & Architecture Rationale

This project is designed with specific constraints that inform architectural decisions:

#### Deployment Model
- **Single server deployment** - No distributed setup or horizontal scaling
- **Single database instance** - No replication, sharding, or multi-region deployment
- **Single application instance** - No load balancing or multi-instance coordination

#### Data Scale Limits
- **Max 10 users** - Small, stable user base
- **Max 100 spaces** - Bounded workspace count
- **Max 1,000,000 notes** - Primary scaling dimension

#### Architecture Implications

**In-Memory Caching Strategy**

Users and spaces are fully cached in memory at application startup:
- With max 10 users (~5KB) and 100 spaces (~200KB), memory footprint is negligible
- Cache invalidation complexity is avoided since single-instance deployment guarantees cache consistency
- Eliminates database queries for user/space lookups (most frequent operations)
- Trade-off: Requires application restart for manual database changes

**Simplified Authentication**

Token-based authentication is intentionally simplified:
- Focus is on MongoDB data patterns, not production-grade security
- Suitable for comparison/experimentation purposes
- Not intended as a security reference implementation

**Notes and Comments: Query-Based Access**

Unlike users/spaces, notes and comments are NOT cached:
- Large dataset (up to 1M notes) makes full caching impractical
- Access patterns benefit from MongoDB's indexing and querying capabilities
- Pagination and filtering are essential at this scale

## Core Features (Planned)

The minimal version will include:

- **User Management** - Authentication, user accounts
- **Space Management** - Workspaces with member access control
- **Custom Field System** - Dynamic schema with multiple field types
- **Note CRUD** - Create, read, update notes with custom fields
- **Comment System** - Discussions on notes


## Related Projects

- [spacenote-backend](https://github.com/spacenote-projects/spacenote-backend) - Full-featured backend
- mini-backend-postgres (coming soon) - PostgreSQL comparison implementation
