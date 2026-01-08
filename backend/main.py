"""
FastAPI application for ContextPilot.
"""
from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from models import (
    ContextUnit, ContextUnitCreate, ContextUnitUpdate,
    TaskRequest, GeneratedPrompt, ContextStatus,
    AIRequest, AIResponse
)
from error_models import ErrorResponse
from exceptions import (
    ContextPilotException, ValidationError, ResourceNotFoundError,
    StorageError, AIServiceError, AuthenticationError
)
from config import settings
from logger import logger
from security import verify_api_key
from validators import validate_content_length, validate_tags, sanitize_string

# Import storage based on configuration
if settings.use_database:
    from db_storage import db_context_store as context_store
    logger.info("Using database storage")
else:
    from storage import context_store
    logger.info("Using in-memory storage")

from relevance import relevance_engine
from composer import prompt_composer
from ai_service import ai_service
from request_tracking import RequestTrackingMiddleware
from response_cache import response_cache

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Replaces deprecated @app.on_event decorators.
    """
    # Startup
    logger.info("Starting ContextPilot API")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info(f"Authentication enabled: {settings.enable_auth}")
    
    # Verify embedding model is loaded
    try:
        logger.info("Verifying embedding model...")
        test_embedding = relevance_engine.encode("test")
        logger.info(f"Embedding model ready (dimension: {len(test_embedding)})")
    except Exception as e:
        logger.error(f"Failed to verify embedding model: {e}")
        raise RuntimeError("Embedding model not available") from e
    
    yield
    
    # Shutdown
    logger.info("Shutting down ContextPilot API")
    response_cache.clear()
    logger.info("Cleared response cache")


app = FastAPI(
    title="ContextPilot API",
    description="AI-powered personal context engine",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Custom exception handlers
@app.exception_handler(ContextPilotException)
async def contextpilot_exception_handler(request: Request, exc: ContextPilotException):
    """Handle custom ContextPilot exceptions."""
    logger.error(f"{exc.error_code}: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions with standard format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": "HTTP_ERROR",
            "message": exc.detail,
            "details": {}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {}
        }
    )


# Configure CORS with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add request tracking middleware
app.add_middleware(RequestTrackingMiddleware)


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
    """
    Health check endpoint with component status.
    
    Returns:
        Health status of API and all critical components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check embedding model
    try:
        test_embedding = relevance_engine.encode("health check")
        health_status["components"]["embedding_model"] = {
            "status": "healthy",
            "dimension": len(test_embedding)
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["embedding_model"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check storage
    try:
        context_store.list_contexts(limit=1)
        health_status["components"]["storage"] = {"status": "healthy"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["storage"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check AI service
    try:
        # Just check if it's initialized
        if ai_service:
            health_status["components"]["ai_service"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["ai_service"] = {
            "status": "degraded",
            "error": str(e)
        }
    
    return health_status


# Context CRUD endpoints

@app.post("/contexts", response_model=ContextUnit, status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute")
def create_context(
    request: Request,
    context_create: ContextUnitCreate,
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new context unit.
    
    Creates a new context entry with the specified type, content, and tags.
    The context will be assigned a unique ID and timestamp automatically.
    
    Args:
        context_create: Context data including type, content, confidence, and tags
        
    Returns:
        The created context unit with generated ID and timestamp
        
    Raises:
        400: Invalid input data (empty content, too many tags, etc.)
        401: Missing or invalid API key
        429: Rate limit exceeded (100 requests per minute)
    """
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
    
    # Invalidate relevant caches
    response_cache.invalidate("contexts")
    response_cache.invalidate("stats")
    
    logger.info(f"Created context {context.id} of type {context.type}")
    return context


@app.get("/contexts", response_model=List[ContextUnit])
def list_contexts(
    include_superseded: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """
    List all context units.
    
    Retrieves all context units, optionally including superseded ones.
    By default, only returns active contexts.
    
    Args:
        include_superseded: If True, includes contexts that have been superseded
        
    Returns:
        List of context units
        
    Raises:
        401: Missing or invalid API key
    """
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
@limiter.limit("50/minute")
def generate_prompt(
    request: Request,
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
@limiter.limit("50/minute")
def generate_prompt_compact(
    request: Request,
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
    
    # Get embedding cache stats
    embedding_cache_stats = relevance_engine.cache.stats()
    
    # Get response cache stats
    response_cache_stats = response_cache.stats()
    
    return {
        "total_contexts": len(all_contexts),
        "active_contexts": len(active_contexts),
        "superseded_contexts": len(all_contexts) - len(active_contexts),
        "contexts_by_type": stats_by_type,
        "contexts_with_embeddings": len([c for c in active_contexts if context_store.get_embedding(c.id) is not None]),
        "embedding_cache": embedding_cache_stats,
        "response_cache": response_cache_stats
    }


# AI Integration Endpoints

@app.post("/ai/chat", response_model=AIResponse)
@limiter.limit("10/minute")
def ai_chat(
    request: Request,
    ai_request: AIRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate an AI response with relevant context.
    This endpoint:
    1. Finds relevant contexts for the task
    2. Generates a contextualized prompt
    3. Sends it to the AI provider (OpenAI/Anthropic)
    4. Returns the AI response
    5. Stores the conversation history
    
    Note: This is a synchronous endpoint as AI API calls are blocking.
    """
    # Validate input
    validate_content_length(ai_request.task)
    sanitized_task = sanitize_string(ai_request.task)
    
    if ai_request.max_context_units > settings.max_contexts_per_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"max_context_units exceeds limit of {settings.max_contexts_per_request}"
        )
    
    # Rank contexts by relevance
    ranked_contexts = relevance_engine.rank_with_keywords(
        sanitized_task,
        context_store,
        max_results=ai_request.max_context_units
    )
    
    # Update last_used timestamp
    current_time = datetime.utcnow()
    for ranked in ranked_contexts:
        ranked.context_unit.last_used = current_time
    
    # Compose prompt (full or compact)
    if ai_request.use_compact:
        generated = prompt_composer.compose_compact(sanitized_task, ranked_contexts)
    else:
        generated = prompt_composer.compose(sanitized_task, ranked_contexts)
    
    # Extract context IDs
    context_ids = [rc.context_unit.id for rc in ranked_contexts]
    
    try:
        # Generate AI response (synchronous call)
        response_text, conversation = ai_service.generate_response(
            task=sanitized_task,
            generated_prompt=generated,
            context_ids=context_ids,
            provider=ai_request.provider,
            model=ai_request.model,
            temperature=ai_request.temperature,
            max_tokens=ai_request.max_tokens
        )
        
        logger.info(f"AI response generated for conversation {conversation.id}")
        
        return AIResponse(
            conversation_id=conversation.id,
            task=sanitized_task,
            response=response_text,
            provider=conversation.provider,
            model=conversation.model,
            context_ids=context_ids,
            prompt_used=generated.generated_prompt
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI response"
        )


@app.get("/ai/conversations")
def list_conversations(
    limit: int = 50,
    offset: int = 0,
    api_key: str = Depends(verify_api_key)
):
    """List recent AI conversations."""
    conversations = ai_service.list_conversations(limit=limit, offset=offset)
    return {
        "conversations": conversations,
        "limit": limit,
        "offset": offset,
        "count": len(conversations)
    }


@app.get("/ai/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a specific conversation with all messages."""
    conversation = ai_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )
    return conversation


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
