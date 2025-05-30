# PromptHub Technical Specification Document

## Executive Summary

PromptHub is a centralized prompt management system designed to create, store, version, test, and serve prompts for Large Language Model (LLM) applications. The system features a Streamlit frontend interface, FastAPI backend, PostgreSQL database, and comprehensive prompt lifecycle management capabilities.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Design](#database-design)
3. [API Design](#api-design)

## System Architecture

### High-Level Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  Streamlit UI   │────▶│  FastAPI Backend │────▶│  PostgreSQL DB  │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                        │                        
         │                        ▼                        
         │              ┌──────────────────┐              
         │              │                  │              
         └─────────────▶│  LLM Providers   │              
                        │ (OpenAI, Claude) │              
                        └──────────────────┘              
```

### Technology Stack

- **Frontend**: Streamlit 1.32+
- **Backend**: FastAPI 0.110+
- **Database**: MongoDB 7.0+
- **Vector Store**: MongoDB Atlas Vector Search
- **Cache**: Redis 7+
- **Authentication**: JWT with python-jose
- **LLM Integration**: OpenAI, Anthropic, LangChain
- **Embeddings**: sentence-transformers
- **Validation**: Pydantic v2
- **ODM**: Motor (async MongoDB driver) with Beanie
- **Testing**: pytest, pytest-asyncio
- **Deployment**: Docker, Docker Compose

## Database Design

### MongoDB Schema Design

```python
# MongoDB Collections and Document Schemas

# users collection
{
    "_id": ObjectId,
    "email": str,  # unique index
    "password_hash": str,
    "full_name": str,
    "is_active": bool = True,
    "is_superuser": bool = False,
    "created_at": datetime,
    "updated_at": datetime
}

# applications collection
{
    "_id": ObjectId,
    "name": str,
    "description": str,
    "api_key_hash": str,  # unique index
    "owner_id": ObjectId,  # reference to users
    "created_at": datetime,
    "updated_at": datetime
}

# prompts collection
{
    "_id": ObjectId,
    "prompt_id": str,  # Human-readable ID like "faq-bot"
    "name": str,
    "description": str,
    "application_id": ObjectId,  # reference to applications
    "created_by": ObjectId,  # reference to users
    "is_active": bool = True,
    "created_at": datetime,
    "current_version": str,  # Latest published version
    "tags": [str],
    # Compound unique index on (prompt_id, application_id)
}

# prompt_versions collection
{
    "_id": ObjectId,
    "prompt_id": ObjectId,  # reference to prompts
    "version": str,  # Semantic versioning: "1.0.0"
    "content": str,
    "system_prompt": str,
    "metaprompt": str,
    "required_fields": [
        {
            "name": str,
            "type": str,  # "string", "number", "boolean", "array", "object"
            "required": bool,
            "description": str,
            "default": Any
        }
    ],
    "model_params": {
        "temperature": float,
        "max_tokens": int,
        "top_p": float,
        "frequency_penalty": float,
        "presence_penalty": float
    },
    "guardrail_config": {
        "pre_validation": {
            "enabled": bool,
            "threshold": float,
            "validators": [str]
        },
        "post_validation": {
            "enabled": bool,
            "prohibited_terms": [str],
            "required_elements": [str],
            "format_schema": dict
        }
    },
    "embedding": [float],  # Vector embedding for similarity search
    "is_published": bool = False,
    "created_by": ObjectId,  # reference to users
    "created_at": datetime,
    "metadata": dict,
    # Compound unique index on (prompt_id, version)
}

# prompt_dependencies collection
{
    "_id": ObjectId,
    "prompt_version_id": ObjectId,  # reference to prompt_versions
    "dependency_type": str,  # 'system_prompt', 'metaprompt', 'guardrail', etc.
    "dependency_id": ObjectId,  # reference to another prompt_version
    "config": dict,
    "created_at": datetime
}

# execution_logs collection
{
    "_id": ObjectId,
    "prompt_version_id": ObjectId,  # reference to prompt_versions
    "application_id": ObjectId,  # reference to applications
    "model_provider": str,  # 'openai', 'anthropic', etc.
    "model_name": str,
    "input_data": dict,
    "output_data": dict,
    "latency_ms": int,
    "token_count": int,
    "cost_usd": float,
    "status": str,  # 'success', 'failed', 'timeout'
    "error_message": str,
    "metadata": dict,  # Additional tracking data
    "created_at": datetime,
    # Index on created_at for time-based queries
}

# feedback collection
{
    "_id": ObjectId,
    "prompt_version_id": ObjectId,  # reference to prompt_versions
    "user_id": ObjectId,  # reference to users
    "rating": int,  # 1-5
    "comment": str,
    "improvement_suggestion": str,
    "created_at": datetime
}

# prompt_sources collection
{
    "_id": ObjectId,
    "prompt_id": ObjectId,  # reference to prompts
    "source_type": str,  # 'web', 'pdf', 'manual'
    "source_url": str,
    "source_content": str,  # Can be GridFS reference for large content
    "extracted_by": str,  # Which LLM extracted it
    "extraction_metadata": dict,
    "created_at": datetime
}

# MongoDB Indexes
# users: email (unique)
# applications: api_key_hash (unique)
# prompts: (prompt_id, application_id) compound unique
# prompt_versions: (prompt_id, version) compound unique
# prompt_versions: embedding (vector index for similarity search)
# execution_logs: created_at, prompt_version_id
# feedback: prompt_version_id

# MongoDB Vector Search Index Configuration (Atlas)
{
    "name": "vector_index",
    "type": "vectorSearch",
    "definition": {
        "fields": [{
            "type": "vector",
            "path": "embedding",
            "numDimensions": 768,
            "similarity": "cosine"
        }]
    }
}
```

## API Design

### FastAPI Backend Structure

```python
# Directory Structure
prompthub/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── prompts.py
│   │   ├── execution.py
│   │   ├── feedback.py
│   │   └── extraction.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── dependencies.py
│   │   └── exceptions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── prompt.py
│   │   └── execution.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── prompt.py
│   │   └── execution.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── prompt_service.py
│   │   ├── llm_service.py
│   │   ├── validation_service.py
│   │   ├── extraction_service.py
│   │   └── metaprompt_service.py
│   └── utils/
│       ├── __init__.py
│       ├── embeddings.py
│       └── validators.py
├── streamlit_app/
│   ├── __init__.py
│   ├── app.py
│   ├── pages/
│   │   ├── prompt_editor.py
│   │   ├── prompt_testing.py
│   │   ├── execution_logs.py
│   │   └── feedback.py
│   └── components/
│       ├── auth.py
│       ├── prompt_viewer.py
│       └── model_comparison.py
├── tests/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Key API Endpoints

```python
# Authentication Endpoints
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me

# Application Management
POST   /api/v1/applications
GET    /api/v1/applications
GET    /api/v1/applications/{app_id}
PUT    /api/v1/applications/{app_id}
DELETE /api/v1/applications/{app_id}
POST   /api/v1/applications/{app_id}/regenerate-key

# Prompt Management
POST   /api/v1/prompts
GET    /api/v1/prompts
GET    /api/v1/prompts/{prompt_id}
PUT    /api/v1/prompts/{prompt_id}
DELETE /api/v1/prompts/{prompt_id}

# Prompt Versions
POST   /api/v1/prompts/{prompt_id}/versions
GET    /api/v1/prompts/{prompt_id}/versions
GET    /api/v1/prompts/{prompt_id}/versions/{version}
PUT    /api/v1/prompts/{prompt_id}/versions/{version}
POST   /api/v1/prompts/{prompt_id}/versions/{version}/publish

# Prompt Execution
POST   /api/v1/execute/{prompt_id}/{version}
POST   /api/v1/execute/{prompt_id}/latest
POST   /api/v1/test-prompt

# Prompt Enhancement
POST   /api/v1/prompts/{prompt_id}/versions/{version}/boost
POST   /api/v1/prompts/{prompt_id}/versions/{version}/validate

# Feedback
POST   /api/v1/prompts/{prompt_id}/versions/{version}/feedback
GET    /api/v1/prompts/{prompt_id}/versions/{version}/feedback

# Extraction
POST   /api/v1/extract/url
POST   /api/v1/extract/pdf
POST   /api/v1/extract/bulk

# Search
GET    /api/v1/prompts/search
POST   /api/v1/prompts/semantic-search

# Analytics
GET    /api/v1/analytics/usage
GET    /api/v1/analytics/performance
GET    /api/v1/analytics/costs
```