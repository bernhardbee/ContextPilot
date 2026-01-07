"""
Prompt logging system for traceability and auditing.
Tracks all AI prompt generations with full context.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from models import RankedContextUnit, GeneratedPrompt
from logger import logger
import json


@dataclass
class PromptLogEntry:
    """A single prompt generation log entry."""
    log_id: str
    timestamp: datetime
    original_task: str
    num_contexts_used: int
    context_ids: List[str]
    context_types: Dict[str, int]  # Count by type
    generated_prompt: str
    prompt_type: str  # "full" or "compact"
    prompt_length: int
    max_contexts_requested: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "original_task": self.original_task,
            "num_contexts_used": self.num_contexts_used,
            "context_ids": self.context_ids,
            "context_types": self.context_types,
            "generated_prompt": self.generated_prompt,
            "prompt_type": self.prompt_type,
            "prompt_length": self.prompt_length,
            "max_contexts_requested": self.max_contexts_requested
        }


class PromptLogger:
    """
    Logger for tracking all prompt generations.
    Provides audit trail and traceability for AI operations.
    """
    
    def __init__(self, max_logs: int = 10000):
        """
        Initialize the prompt logger.
        
        Args:
            max_logs: Maximum number of logs to retain in memory
        """
        self._logs: List[PromptLogEntry] = []
        self._max_logs = max_logs
        self._log_counter = 0
        logger.info(f"PromptLogger initialized with max_logs={max_logs}")
    
    def log_prompt_generation(
        self,
        task: str,
        ranked_contexts: List[RankedContextUnit],
        generated: GeneratedPrompt,
        prompt_type: str,
        max_contexts_requested: int
    ) -> str:
        """
        Log a prompt generation event.
        
        Args:
            task: The original task/query
            ranked_contexts: Contexts that were used
            generated: The generated prompt result
            prompt_type: Type of prompt ("full" or "compact")
            max_contexts_requested: How many contexts were requested
            
        Returns:
            The log ID for this entry
        """
        self._log_counter += 1
        log_id = f"prompt-{self._log_counter:06d}"
        
        # Extract context information
        context_ids = [rc.context_unit.id for rc in ranked_contexts]
        context_types = {}
        for rc in ranked_contexts:
            ctx_type = rc.context_unit.type.value
            context_types[ctx_type] = context_types.get(ctx_type, 0) + 1
        
        # Create log entry
        entry = PromptLogEntry(
            log_id=log_id,
            timestamp=datetime.utcnow(),
            original_task=task,
            num_contexts_used=len(ranked_contexts),
            context_ids=context_ids,
            context_types=context_types,
            generated_prompt=generated.generated_prompt,
            prompt_type=prompt_type,
            prompt_length=len(generated.generated_prompt),
            max_contexts_requested=max_contexts_requested
        )
        
        # Add to logs
        self._logs.append(entry)
        
        # Trim if needed
        if len(self._logs) > self._max_logs:
            removed = self._logs.pop(0)
            logger.debug(f"Removed oldest log entry: {removed.log_id}")
        
        logger.info(
            f"Logged prompt generation: {log_id} - "
            f"task_length={len(task)}, contexts={len(ranked_contexts)}, "
            f"type={prompt_type}, prompt_length={len(generated.generated_prompt)}"
        )
        
        return log_id
    
    def get_logs(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        prompt_type: Optional[str] = None
    ) -> List[PromptLogEntry]:
        """
        Retrieve prompt generation logs.
        
        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            prompt_type: Filter by prompt type ("full" or "compact")
            
        Returns:
            List of log entries, most recent first
        """
        # Filter by type if specified
        logs = self._logs
        if prompt_type:
            logs = [log for log in logs if log.prompt_type == prompt_type]
        
        # Sort by timestamp descending (most recent first)
        logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)
        
        # Apply offset and limit
        logs = logs[offset:]
        if limit:
            logs = logs[:limit]
        
        return logs
    
    def get_log_by_id(self, log_id: str) -> Optional[PromptLogEntry]:
        """
        Get a specific log entry by ID.
        
        Args:
            log_id: The log ID to retrieve
            
        Returns:
            The log entry if found, None otherwise
        """
        for log in self._logs:
            if log.log_id == log_id:
                return log
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about prompt generation logs.
        
        Returns:
            Dictionary with statistics
        """
        if not self._logs:
            return {
                "total_logs": 0,
                "logs_by_type": {},
                "avg_contexts_used": 0,
                "avg_prompt_length": 0,
                "oldest_log": None,
                "newest_log": None
            }
        
        logs_by_type = {}
        total_contexts = 0
        total_prompt_length = 0
        
        for log in self._logs:
            logs_by_type[log.prompt_type] = logs_by_type.get(log.prompt_type, 0) + 1
            total_contexts += log.num_contexts_used
            total_prompt_length += log.prompt_length
        
        sorted_logs = sorted(self._logs, key=lambda x: x.timestamp)
        
        return {
            "total_logs": len(self._logs),
            "logs_by_type": logs_by_type,
            "avg_contexts_used": total_contexts / len(self._logs),
            "avg_prompt_length": total_prompt_length / len(self._logs),
            "oldest_log": sorted_logs[0].timestamp.isoformat() if sorted_logs else None,
            "newest_log": sorted_logs[-1].timestamp.isoformat() if sorted_logs else None
        }
    
    def export_logs(self, filepath: str) -> None:
        """
        Export all logs to a JSON file.
        
        Args:
            filepath: Path to write the JSON file
        """
        logs_data = [log.to_dict() for log in self._logs]
        with open(filepath, 'w') as f:
            json.dump(logs_data, f, indent=2)
        logger.info(f"Exported {len(logs_data)} logs to {filepath}")
    
    def clear_logs(self) -> int:
        """
        Clear all logs (use with caution).
        
        Returns:
            Number of logs that were cleared
        """
        count = len(self._logs)
        self._logs.clear()
        logger.warning(f"Cleared {count} prompt generation logs")
        return count


# Global instance
prompt_logger = PromptLogger()
