"""
FastAPI application for ContextPilot.
"""
from fastapi import FastAPI, HTTPException, status
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


app = FastAPI(
    title="ContextPilot API",
    description="AI-powered personal context engine",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
def create_context(context_create: ContextUnitCreate):
    """Create a new context unit."""
    context = ContextUnit(
        type=context_create.type,
        content=context_create.content,
        confidence=context_create.confidence,
        tags=context_create.tags,
        source=context_create.source
    )
    
    # Generate and store embedding
    embedding = relevance_engine.encode(context.content)
    context_store.add(context, embedding)
    
    return context


@app.get("/contexts", response_model=List[ContextUnit])
def list_contexts(include_superseded: bool = False):
    """List all context units."""
    return context_store.list_all(include_superseded=include_superseded)


@app.get("/contexts/{context_id}", response_model=ContextUnit)
def get_context(context_id: str):
    """Get a specific context unit by ID."""
    context = context_store.get(context_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context unit {context_id} not found"
        )
    return context


@app.put("/contexts/{context_id}", response_model=ContextUnit)
def update_context(context_id: str, context_update: ContextUnitUpdate):
    """Update a context unit."""
    # Get existing context
    existing = context_store.get(context_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context unit {context_id} not found"
        )
    
    # Prepare updates
    updates = context_update.dict(exclude_unset=True)
    
    # If content is updated, regenerate embedding
    if "content" in updates:
        new_content = updates["content"]
        embedding = relevance_engine.encode(new_content)
        context_store._embeddings[context_id] = embedding
    
    # Update the context
    updated = context_store.update(context_id, updates)
    
    return updated


@app.delete("/contexts/{context_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_context(context_id: str):
    """Delete a context unit."""
    success = context_store.delete(context_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context unit {context_id} not found"
        )
    return None


# Prompt generation endpoints

@app.post("/generate-prompt", response_model=GeneratedPrompt)
def generate_prompt(task_request: TaskRequest):
    """Generate a contextualized prompt for a task."""
    # Rank contexts by relevance
    ranked_contexts = relevance_engine.rank_with_keywords(
        task_request.task,
        context_store,
        max_results=task_request.max_context_units
    )
    
    # Update last_used timestamp for selected contexts
    current_time = datetime.utcnow()
    for ranked in ranked_contexts:
        ranked.context_unit.last_used = current_time
    
    # Compose the prompt
    generated = prompt_composer.compose(
        task_request.task,
        ranked_contexts
    )
    
    return generated


@app.post("/generate-prompt/compact", response_model=GeneratedPrompt)
def generate_prompt_compact(task_request: TaskRequest):
    """Generate a compact contextualized prompt for a task."""
    # Rank contexts by relevance
    ranked_contexts = relevance_engine.rank_with_keywords(
        task_request.task,
        context_store,
        max_results=task_request.max_context_units
    )
    
    # Update last_used timestamp
    current_time = datetime.utcnow()
    for ranked in ranked_contexts:
        ranked.context_unit.last_used = current_time
    
    # Compose compact prompt
    generated = prompt_composer.compose_compact(
        task_request.task,
        ranked_contexts
    )
    
    return generated


# Statistics endpoint

@app.get("/stats")
def get_stats():
    """Get statistics about the context store."""
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
        "contexts_with_embeddings": len(context_store._embeddings)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
