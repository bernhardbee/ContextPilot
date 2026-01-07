"""
Relevance engine using sentence embeddings for similarity search.
"""
from typing import List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from models import ContextUnit, RankedContextUnit
from storage import ContextStore


class RelevanceEngine:
    """Engine for ranking context units by relevance to a task."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the relevance engine.
        
        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model = SentenceTransformer(model_name)
    
    def encode(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        return self.model.encode(text, convert_to_numpy=True)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        return float(np.dot(embedding1, embedding2) / 
                    (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))
    
    def rank_contexts(
        self, 
        task: str, 
        context_store: ContextStore,
        max_results: int = 5
    ) -> List[RankedContextUnit]:
        """
        Rank context units by relevance to the given task.
        
        Args:
            task: The user's task description
            context_store: Store containing context units
            max_results: Maximum number of results to return
            
        Returns:
            List of ranked context units with relevance scores
        """
        # Generate embedding for the task
        task_embedding = self.encode(task)
        
        # Get all active contexts with embeddings
        contexts_with_embeddings = context_store.list_with_embeddings()
        
        if not contexts_with_embeddings:
            return []
        
        # Compute similarities
        ranked = []
        for context, embedding in contexts_with_embeddings:
            similarity = self.compute_similarity(task_embedding, embedding)
            
            # Adjust score by confidence
            adjusted_score = similarity * context.confidence
            
            ranked.append(RankedContextUnit(
                context_unit=context,
                relevance_score=adjusted_score
            ))
        
        # Sort by relevance score (descending)
        ranked.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Return top N
        return ranked[:max_results]
    
    def rank_with_keywords(
        self,
        task: str,
        context_store: ContextStore,
        max_results: int = 5,
        keyword_weight: float = 0.3
    ) -> List[RankedContextUnit]:
        """
        Rank contexts using both embeddings and keyword matching.
        
        Args:
            task: The user's task description
            context_store: Store containing context units
            max_results: Maximum number of results to return
            keyword_weight: Weight for keyword matching (0-1)
            
        Returns:
            List of ranked context units with relevance scores
        """
        # Get embedding-based ranking
        ranked = self.rank_contexts(task, context_store, max_results=max_results * 2)
        
        # Extract keywords from task (simple approach)
        task_lower = task.lower()
        task_words = set(task_lower.split())
        
        # Adjust scores based on keyword matching
        for ranked_context in ranked:
            context = ranked_context.context_unit
            
            # Check content keywords
            content_words = set(context.content.lower().split())
            keyword_overlap = len(task_words & content_words) / max(len(task_words), 1)
            
            # Check tag matches
            tag_matches = sum(1 for tag in context.tags if tag.lower() in task_lower)
            tag_score = tag_matches * 0.2
            
            # Combine scores
            semantic_score = ranked_context.relevance_score * (1 - keyword_weight)
            keyword_score = (keyword_overlap + tag_score) * keyword_weight
            
            ranked_context.relevance_score = semantic_score + keyword_score
        
        # Re-sort and return top N
        ranked.sort(key=lambda x: x.relevance_score, reverse=True)
        return ranked[:max_results]


# Global instance
relevance_engine = RelevanceEngine()
