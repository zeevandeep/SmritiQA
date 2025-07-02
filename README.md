# Smriti API

An AI-powered emotional and cognitive journaling assistant using graph-based analysis and reflection generation.

## Overview

Smriti helps users gain insights from their journaling by:

1. Capturing journal entries as voice or text
2. Extracting cognitive and emotional patterns
3. Building a knowledge graph of connected thoughts
4. Generating personalized reflections

## API Documentation

### Health Check

```
GET /api/v1/health
```

Returns the health status of the API.

### User Profiles

```
POST /api/v1/users
```

Create a new user profile.

**Request Body:**
```json
{
  "display_name": "John Doe",
  "birthdate": "1990-01-01",
  "gender": "male",
  "language": "en"
}
```

```
GET /api/v1/users/{user_id}
```

Get a user profile by ID.

### Sessions

```
POST /api/v1/sessions
```

Create a new journaling session.

**Request Body:**
```json
{
  "user_id": "uuid-of-user",
  "duration_seconds": 120,
  "raw_transcript": "I've been thinking about my career lately. I'm not sure if I'm on the right path. Sometimes I feel excited about my work, but other times I feel stuck."
}
```

```
GET /api/v1/sessions/{session_id}
```

Get a session by ID.

```
GET /api/v1/users/{user_id}/sessions
```

Get all sessions for a user.

### Processing

```
POST /api/v1/sessions/{session_id}/process
```

Process a session to extract nodes.

```
GET /api/v1/sessions/{session_id}/nodes
```

Get all nodes extracted from a session.

### Edge Processing

```
POST /api/v1/edges/process
```

Process unprocessed nodes to create edges between them based on semantic similarity.

```
POST /api/v1/edges/process/{user_id}
```

Process unprocessed nodes for a specific user to create edges.

```
POST /api/v1/edges/chain_process
```

Process edges to identify and mark those that form potential thought chains (Phase 3.25).

```
POST /api/v1/edges/chain_process/{user_id}
```

Process edges for a specific user to identify and mark thought chains.

### Reflections

```
POST /api/v1/reflections/generate
```

Generate reflections for all users from unprocessed edges.

```
POST /api/v1/users/{user_id}/reflections/generate
```

Generate reflections for a specific user from unprocessed edges.

```
GET /api/v1/users/{user_id}/reflections
```

Get all reflections for a user.

```
POST /api/v1/reflections/{reflection_id}/feedback
```

Provide feedback on a reflection.

**Request Body:**
```json
{
  "feedback": true
}
```

```
POST /api/v1/reflections/{reflection_id}/mark-reflected
```

Mark a reflection as having been reflected upon by the user.

## Architecture

Smriti is built with a layered architecture:

- **Models**: SQLAlchemy ORM models for PostgreSQL database
- **Services**: Core business logic 
- **API Routes**: RESTful endpoints using Flask

### Key Components

- **Node Processing**: Extracts cognitive and emotional units from transcripts
- **Edge Formation**: Creates semantic connections between nodes
- **Edge Postprocessing**: Identifies and marks edges that form potential thought chains
- **Reflection Generation**: Creates AI-powered insights from connected nodes

## Development

### Prerequisites

- Python 3.10+
- PostgreSQL
- Neo4j (for future graph capabilities)
- OpenAI API Key (for AI-powered analysis)

### Setup

1. Clone the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in your configuration
5. Run the API: `gunicorn --bind 0.0.0.0:5000 main:app`

## Implementation Phases

### Phase 1: Core Infrastructure
- Basic user profiles
- Session recording and transcript storage
- Simple node extraction

### Phase 2: Node Creation
- OpenAI integration for sophisticated node extraction
- Emotion, theme, and cognition classification
- Embedding generation for semantic analysis

### Phase 3: Edge Creation
- Advanced edge formation with semantic similarity
- Directional connections (older to newer nodes)
- Matching algorithm with boosting factors

### Phase 3.25: Edge Postprocessing
- Identification of chain-linked edges
- Marking edges where to_node connects to from_node of other edges
- Preparation for reflection generation

### Phase 5: Reflection Generation
- AI-powered insights from connected nodes
- Personalized reflections based on cognitive patterns
- Feedback mechanism for reflection quality