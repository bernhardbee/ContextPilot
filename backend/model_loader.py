"""
Centralized model loader - synchronizes model lists across the application.

This module provides a single source of truth for available models by loading
from valid_models.json. Both backend providers and frontend use this.
"""
import json
from pathlib import Path
from typing import Dict, List, Any
from logger import logger


def load_models_from_json() -> Dict[str, List[str]]:
    """
    Load model lists from valid_models.json (single source of truth).
    
    Returns:
        Dict mapping provider names to list of available models.
    """
    models_file = Path(__file__).parent / "valid_models.json"
    
    try:
        with open(models_file, "r") as f:
            models = json.load(f)
        logger.debug(f"Loaded models from {models_file}")
        return models
    except Exception as e:
        logger.error(f"Failed to load models from {models_file}: {e}")
        raise


def build_model_info(provider_name: str, models: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Build MODEL_INFO dictionary from model list for a provider.
    
    Args:
        provider_name: Name of provider (openai, anthropic, ollama)
        models: List of available model names
        
    Returns:
        Dict mapping model names to their info dictionaries
    """
    model_info = {}
    
    for model in models:
        model_info[model] = {
            "name": format_model_name(model),
            "context_window": get_context_window(provider_name, model),
            "supports_temperature": supports_temperature(provider_name, model),
            "description": get_model_description(provider_name, model)
        }
    
    return model_info


def format_model_name(model: str) -> str:
    """Format model ID to display name."""
    # GPT models
    if model.startswith("gpt-"):
        if "5.2" in model or "5-turbo" in model or model == "gpt-5":
            return model.replace("gpt-", "GPT-").replace("-turbo", " Turbo")
        elif "4o" in model:
            return model.replace("gpt-4o", "GPT-4 Optimized").replace("-mini", " Mini")
        elif model == "gpt-3.5-turbo":
            return "GPT-3.5 Turbo"
        return model.upper()
    
    # Claude models
    if model.startswith("claude-"):
        if "opus-4-5" in model:
            return "Claude Opus 4.5"
        elif "sonnet-4-5" in model:
            return "Claude Sonnet 4.5"
        elif "haiku-4-5" in model:
            return "Claude Haiku 4.5"
        elif "3-5-sonnet" in model:
            return "Claude 3.5 Sonnet"
        elif "3-5-haiku" in model:
            return "Claude 3.5 Haiku"
        elif "3-opus" in model:
            return "Claude 3 Opus"
        elif "3-sonnet" in model:
            return "Claude 3 Sonnet"
        elif "3-haiku" in model:
            return "Claude 3 Haiku"
        return model.replace("claude-", "Claude ").title()
    
    # O-series models
    if model.startswith("o"):
        return model.replace("o1", "O1").replace("o3", "O3").title()
    
    # Ollama models
    if model.endswith(":latest"):
        base = model.replace(":latest", "").title()
        return f"{base} (Latest)"
    
    return model


def get_context_window(provider: str, model: str) -> int:
    """Get context window size for a model."""
    # GPT-4o and 4o-mini
    if model in ["gpt-4o", "gpt-4o-mini", "gpt-5", "gpt-5.2", "gpt-5-turbo"]:
        return 128000
    
    # GPT-4 Turbo
    if model == "gpt-4-turbo":
        return 128000
    
    # GPT-4 standard
    if model == "gpt-4":
        return 8192
    
    # GPT-3.5
    if model == "gpt-3.5-turbo":
        return 16385
    
    # O-series (extended thinking)
    if model in ["o1", "o3"]:
        return 200000
    
    # O-mini
    if model in ["o1-mini", "o3-mini"]:
        return 128000
    
    # All Claude models have 200k context
    if provider == "anthropic":
        return 200000
    
    # Ollama default
    if provider == "ollama":
        return 4096
    
    return 100000  # Default fallback


def supports_temperature(provider: str, model: str) -> bool:
    """Check if model supports temperature parameter."""
    # O-series doesn't support temp (has fixed reasoning mode)
    if model.startswith("o1") or model.startswith("o3"):
        return False
    
    # Everything else supports temperature
    return True


def get_model_description(provider: str, model: str) -> str:
    """Get description for a model."""
    descriptions = {
        # GPT-5 series
        "gpt-5.2": "Latest GPT-5.2 model with enhanced capabilities",
        "gpt-5": "Latest GPT-5 model",
        "gpt-5-turbo": "Optimized GPT-5 model for speed",
        
        # GPT-4 series  
        "gpt-4o": "Most capable GPT-4 model, optimized for speed and cost",
        "gpt-4o-mini": "Smaller, faster GPT-4 model",
        "gpt-4-turbo": "Enhanced GPT-4 with vision capabilities",
        "gpt-4": "Standard GPT-4 model",
        "gpt-3.5-turbo": "Fast and efficient model",
        
        # Claude series
        "claude-opus-4-5-20251101": "Latest Claude Opus 4.5 with enhanced reasoning",
        "claude-opus-4-5": "Latest Claude Opus 4.5 model",
        "claude-sonnet-4-5-20250929": "Balanced Claude Sonnet with strong capabilities",
        "claude-sonnet-4-5": "Latest Claude Sonnet 4.5 model",
        "claude-haiku-4-5-20251001": "Fast, efficient Claude Haiku model",
        "claude-haiku-4-5": "Latest Claude Haiku 4.5 model",
        
        # O-series
        "o1": "Advanced reasoning model with fixed temperature",
        "o1-mini": "Smaller reasoning model",
        "o3": "Next-generation reasoning model",
        "o3-mini": "Efficient reasoning model",
        
        # Ollama
        "llama3.2:latest": "Latest Llama 3.2 model (local)",
    }
    
    return descriptions.get(model, f"{model} model")
