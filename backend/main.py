"""
FastAPI application for ContextPilot.
"""
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime

from models import (
    ContextUnit, ContextUnitCreate, ContextUnitUpdate,
    TaskRequest, GeneratedPrompt, ContextStatus
)
from storage import context_store
from relevance import relevance_engine
from composer import prompt_composer
from config import settings
from logger import logger
from security import verify_api_key
from validators import validate_content_length, validate_tags, sanitize_string


app = FastAPI(
    title="ContextPilot API",
    description="AI-powered personal context engine",
    version="1.0.0"
)

# Configure CORS with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting ContextPilot API")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info(f"Authentication enabled: {settings.enable_auth}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down ContextPilot API")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "ContextPilot API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Context CRUD endpoints

@app.post("/contexts", response_model=ContextUnit, status_code=status.HTTP_201_CREATED)
def create_context(
    context_create: ContextUnitCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a new context unit."""
    # Validate input
    validate_content_length(context_create.content)
    validate_tags(context_create.tags)
    
    # Sanitize content
    sanitized_content = sanitize_string(context_create.content)
    sanitized_tags = [sanitize_string(tag) for tag in context_create.tags]
    
    # Create context
    context = ContextUnit(
        type=context_create.type,
        content=sanitized_content,
        confidence=context_create.confidence,
        tags=sanitized_tags,
        source=context_create.source
    )
    
    # Generate and store embedding
    embedding = relevance_engine.encode(context.content)
    context_store.add(context, embedding)
    
    logger.info(f"Created context {context.id} of type {context.type}")
    return context


@app.get("/contexts", response_model=List[ContextUnit])
def list_contexts(
    include_superseded: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """List all context units."""
    contexts = context_store.list_all(include_superseded=include_superseded)
    logger.debug(f"Listed {len(contexts)} contexts")
    return contexts


@app.get("/contexts/{context_id}", response_model=ContextUnit)
def get_context(context_id: str, api_key: str = Depends(verify_api_key)):
    """Get a specific context unit by ID."""
    context = context_store.get(context_id)
    if not context:
        logger.warning(f"Context {context_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context unit {context_id} not found"
        )
    return context


@app.put("/contexts/{context_id}", response_model=ContextUnit)
def update_context(
    context_id: str,
    context_update: ContextUnitUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update a context unit."""
    # Get existing context
    existing = context_store.get(context_id)
    if not existing:
        logger.warning(f"Attempted to update non-existent context {context_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context unit {context_id} not found"
        )
    
    # Prepare updates
    updates = context_update.dict(exclude_unset=True)
    
    # Validate if content is being updated
    if "content" in updates:
        validate_content_length(updates["content"])
        updates["content"] = sanitize_string(updates["content"])
        
        # Regenerate embedding
        embedding = relevance_engine.encode(updates["content"])
        context_store.update_embedding(context_id, embedding)
    
    # Validate if tags are being updated
    if "tags" in updates:
        validate_tags(updates["tags"])
        updates["tags"] = [sanitize_string(tag) for tag in updates["tags"]]
    
    # Update the context
    updated = context_store.update(context_id, updates)
    
    logger.info(f"Updated context {context_id}")
    return updated


@app.delete("/contexts/{context_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_context(context_id: str, api_key: str = Depends(verify_api_key)):
    """Delete a context unit."""
    success = context_store.delete(context_id)
    if not success:
        logger.warning(f"Attempted to delete non-existent context {context_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context unit {context_id} not found"
        )
    logger.info(f"Deleted context {context_id}")
    return None


# Prompt generation endpoints

@app.post("/generate-prompt", response_model=GeneratedPrompt)
def generate_prompt(
    task_request: TaskRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate a contextualized prompt for a task."""
    # Validate input
    validate_content_length(task_request.task)
    
    # Sanitize task
    sanitized_task = sanitize_string(task_request.task)
    
    # Validate max_context_units
    if task_request.max_context_units > settings.max_contexts_per_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"max_context_units exceeds limit of {settings.max_contexts_per_request}"
        )
    
    # Rank contexts by relevance
    ranked_contexts = relevance_engine.rank_with_keywords(
        sanitized_task,
        context_store,
        max_results=task_request.max_context_units
    )
    
    # Update last_used timestamp for selected contexts
    current_time = datetime.utcnow()
    for ranked in ranked_contexts:
        ranked.context_unit.last_used = current_time
    
    # Compose the prompt
    generated = prompt_composer.compose(
        sanitized_task,
        ranked_contexts
    )
    
    logger.info(f"Generated prompt for task with {len(ranked_contexts)} contexts")
    return generated


@app.post("/generate-prompt/compact", response_model=GeneratedPrompt)
def generate_prompt_compact(
    task_request: TaskRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate a compact contextualized prompt for a task."""
    # Validate input
    validate_content_length(task_request.task)
    sanitized_task = sanitize_string(task_request.task)
    
    if task_request.max_context_units > settings.max_contexts_per_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"max_context_units exceeds limit of {settings.max_contexts_per_request}"
        )
    
    # Rank contexts by relevance
    ranked_contexts = relevance_engine.rank_with_keywords(
        sanitized_task,
        context_store,
        max_results=task_request.max_context_units
    )
    
    # Update last_used timestamp
    current_time = datetime.utcnow()
    for ranked in ranked_contexts:
        ranked.context_unit.last_used = current_time
    
    # Compose compact prompt
    generated = prompt_composer.compose_compact(
        sanitized_task,
        ranked_contexts
    )
    
    logger.info(f"Generated compact prompt for task with {len(ranked_contexts)} contexts")
    return generated


# Statistics endpoint

@app.get("/stats")
def get_stats(api_key: str = Depends(verify_api_key)):
    """Get statistics about the context store and prompt generation."""
    all_contexts = context_store.list_all(include_superseded=True)
    active_contexts = context_store.list_all(include_superseded=False)
    
    stats_by_type = {}
    for context in active_contexts:
        ctx_type = context.type.value
        if ctx_type not in stats_by_type:
            stats_by_type[ctx_type] = 0
        stats_by_type[ctx_type] += 1
    
    return {
        "total_contexts": len(all_contexts),
        "active_contexts": len(active_contexts),
        "superseded_contexts": len(all_contexts) - len(active_contexts),
        "contexts_by_type": stats_by_type,
        "contexts_with_embeddings": len([c for c in active_contexts if context_store.get_embedding(c.id) is not None])
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
