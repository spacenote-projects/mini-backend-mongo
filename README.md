# mini-backend-mongo

A minimal version of [spacenote-backend](https://github.com/spacenote-projects/spacenote-backend) designed to extract and preserve only the core functionality.

## Database Requirements

### 1. Human & AI-Readable Data Access

The system must support direct database access or convenient APIs that allow humans and AI agents to view notes as complete JSON documents. Notes should be represented in a clear, self-contained format:

```json
{
  "_id": {"$oid": "690ef262fedbb30ffadf1c67"},
  "space_slug": "tasks",
  "number": 2,
  "author_username": "admin",
  "created_at": {"$date": "2025-11-08T07:33:54.102Z"},
  "fields": {
    "title": "Design database schema",
    "body": "Create initial database schema...",
    "assignee": "alice",
    "status": "completed",
    "priority": "high",
    "tags": ["database", "design"]
  }
}
```

When documents contain nested objects (as in JSON), they are convenient for reading by both humans and AI agents. While the underlying storage implementation may vary, APIs should return notes in convenient JSON format that makes all data clear and understandable.

### 2. Flexible Schema Evolution

Notes must support flexible field additions without strict constraints:

- **Long-lived spaces**: Spaces evolve over time, and schema requirements change
- **Backward compatibility**: When new required fields are introduced, old notes must remain valid without those fields
- **Data preservation**: Field schemas may evolve, but existing data must never be lost
- **Flexibility**: By keeping `fields` as a flexible dictionary structure (`dict[str, Any]`), even old or undocumented data can be understood by humans or AI agents

This flexibility in `notes.fields` is critical for long-term data integrity.

## Project Purpose

This project is part of a database comparison experiment to help decide between **MongoDB** and **PostgreSQL** for the main SpaceNote project.

The original `spacenote-backend` has grown to ~8,000 lines of code across 14 modules. This minimal version strips away optional integrations (Telegram, LLM, image processing) and focuses on core data patterns (users, spaces, custom fields, notes, comments).

**Parallel implementations:**
- **mini-backend-mongo** (this repo) - MongoDB implementation
- **mini-backend-postgres** (planned) - PostgreSQL implementation with identical functionality

We'll compare code complexity, query patterns, performance, developer experience, and schema flexibility.

## Project Status

🚧 **In Development** - Features are being added incrementally.

## Technology Stack

- **Python 3.14+**
- **FastAPI** - Modern async web framework
- **MongoDB** - Document database with flexible schema
- **Pydantic** - Data validation and settings management

## Architecture Decisions

### Natural Keys vs Surrogate Keys

This implementation uses **natural keys** as primary identifiers (unlike the original UUID-based approach):

- `User` → identified by `username`
- `Space` → identified by `slug`
- `Note` → identified by `space_slug + number`

Benefits: readable URLs (`/spaces/my-project/notes/42`), semantic identifiers, simplified caching, and direct lookups.

### Project Constraints & Architecture

**Deployment & Scale:**
- Single server, single database instance, single application instance
- Max 10 users, 100 spaces, 1M notes

**Caching Strategy:**
- Users and spaces: fully cached in memory (~205KB total) for instant lookups
- Notes and comments: query-based access with MongoDB indexing and pagination

**Authentication:**
- Intentionally simplified token-based auth (focus is on data patterns, not production security)

## Core Features

- **User Management** - Authentication, user accounts
- **Space Management** - Workspaces with member access control
- **Custom Field System** - Dynamic schema with multiple field types
- **Note CRUD** - Create, read, update notes with custom fields
- **Comment System** - Discussions on notes


## Related Projects

- [spacenote-backend](https://github.com/spacenote-projects/spacenote-backend) - Full-featured backend
- mini-backend-postgres (coming soon) - PostgreSQL comparison implementation
