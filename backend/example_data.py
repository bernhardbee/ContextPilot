"""
Example data and initialization script for ContextPilot.
"""
from models import ContextUnit, ContextType
from storage import context_store
from relevance import relevance_engine


def load_example_data():
    """Load example context units."""
    
    example_contexts = [
        {
            "type": ContextType.PREFERENCE,
            "content": "I prefer concise, technical explanations without excessive verbosity",
            "confidence": 0.95,
            "tags": ["communication", "style", "technical"],
        },
        {
            "type": ContextType.PREFERENCE,
            "content": "I like code examples in Python and TypeScript",
            "confidence": 0.9,
            "tags": ["programming", "languages"],
        },
        {
            "type": ContextType.GOAL,
            "content": "Building an AI-powered context management system called ContextPilot",
            "confidence": 1.0,
            "tags": ["project", "ai", "context"],
        },
        {
            "type": ContextType.DECISION,
            "content": "Using FastAPI for backend instead of Django for better async support",
            "confidence": 0.85,
            "tags": ["architecture", "backend", "fastapi"],
        },
        {
            "type": ContextType.DECISION,
            "content": "Using React with TypeScript for the frontend",
            "confidence": 0.9,
            "tags": ["architecture", "frontend", "react", "typescript"],
        },
        {
            "type": ContextType.FACT,
            "content": "I work primarily on macOS with VS Code as my IDE",
            "confidence": 1.0,
            "tags": ["environment", "tools"],
        },
        {
            "type": ContextType.FACT,
            "content": "I have experience with vector databases and embeddings",
            "confidence": 0.8,
            "tags": ["skills", "ai", "embeddings"],
        },
        {
            "type": ContextType.PREFERENCE,
            "content": "I prefer minimal UI design with Tailwind CSS over heavy component libraries",
            "confidence": 0.85,
            "tags": ["design", "ui", "tailwind"],
        },
        {
            "type": ContextType.GOAL,
            "content": "Create an MVP that demonstrates value quickly without over-engineering",
            "confidence": 0.95,
            "tags": ["project", "mvp", "strategy"],
        },
        {
            "type": ContextType.DECISION,
            "content": "Using sentence-transformers for embeddings instead of OpenAI API to avoid external dependencies",
            "confidence": 0.8,
            "tags": ["architecture", "embeddings", "ai"],
        },
    ]
    
    for example in example_contexts:
        context = ContextUnit(**example)
        embedding = relevance_engine.encode(context.content)
        context_store.add(context, embedding)
    
    print(f"✓ Loaded {len(example_contexts)} example context units")
    return len(example_contexts)


if __name__ == "__main__":
    load_example_data()
