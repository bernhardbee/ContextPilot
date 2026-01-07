"""
Tests for prompt logging functionality.
"""
import pytest
from datetime import datetime
from prompt_logger import PromptLogger, PromptLogEntry
from models import ContextUnit, RankedContextUnit, GeneratedPrompt, ContextType


class TestPromptLogger:
    """Tests for the PromptLogger class."""
    
    def test_initialization(self):
        """Test that logger initializes correctly."""
        logger = PromptLogger(max_logs=100)
        assert logger._max_logs == 100
        assert len(logger._logs) == 0
        assert logger._log_counter == 0
    
    def test_log_prompt_generation(self):
        """Test logging a prompt generation."""
        logger = PromptLogger()
        
        # Create test data
        context = ContextUnit(
            type=ContextType.PREFERENCE,
            content="Test preference"
        )
        ranked = RankedContextUnit(
            context_unit=context,
            relevance_score=0.9
        )
        generated = GeneratedPrompt(
            original_task="Test task",
            relevant_context=[ranked],
            generated_prompt="Test generated prompt"
        )
        
        log_id = logger.log_prompt_generation(
            task="Test task",
            ranked_contexts=[ranked],
            generated=generated,
            prompt_type="full",
            max_contexts_requested=5
        )
        
        assert log_id == "prompt-000001"
        assert len(logger._logs) == 1
        assert logger._log_counter == 1
    
    def test_log_multiple_generations(self):
        """Test logging multiple prompt generations."""
        logger = PromptLogger()
        
        context1 = ContextUnit(type=ContextType.PREFERENCE, content="Preference 1")
        context2 = ContextUnit(type=ContextType.GOAL, content="Goal 1")
        
        for i in range(3):
            ranked = RankedContextUnit(
                context_unit=context1 if i % 2 == 0 else context2,
                relevance_score=0.9
            )
            generated = GeneratedPrompt(
                original_task=f"Task {i}",
                relevant_context=[ranked],
                generated_prompt=f"Generated prompt {i}"
            )
            
            logger.log_prompt_generation(
                task=f"Task {i}",
                ranked_contexts=[ranked],
                generated=generated,
                prompt_type="full" if i % 2 == 0 else "compact",
                max_contexts_requested=5
            )
        
        assert len(logger._logs) == 3
        assert logger._log_counter == 3
    
    def test_max_logs_limit(self):
        """Test that max_logs limit is enforced."""
        logger = PromptLogger(max_logs=5)
        
        context = ContextUnit(type=ContextType.PREFERENCE, content="Test")
        ranked = RankedContextUnit(context_unit=context, relevance_score=0.9)
        
        # Add 10 logs
        for i in range(10):
            generated = GeneratedPrompt(
                original_task=f"Task {i}",
                relevant_context=[ranked],
                generated_prompt=f"Prompt {i}"
            )
            logger.log_prompt_generation(
                task=f"Task {i}",
                ranked_contexts=[ranked],
                generated=generated,
                prompt_type="full",
                max_contexts_requested=5
            )
        
        # Should only keep last 5
        assert len(logger._logs) == 5
        assert logger._logs[0].original_task == "Task 5"
        assert logger._logs[-1].original_task == "Task 9"
    
    def test_get_logs(self):
        """Test retrieving logs."""
        logger = PromptLogger()
        
        context = ContextUnit(type=ContextType.PREFERENCE, content="Test")
        ranked = RankedContextUnit(context_unit=context, relevance_score=0.9)
        
        # Add 5 logs
        for i in range(5):
            generated = GeneratedPrompt(
                original_task=f"Task {i}",
                relevant_context=[ranked],
                generated_prompt=f"Prompt {i}"
            )
            logger.log_prompt_generation(
                task=f"Task {i}",
                ranked_contexts=[ranked],
                generated=generated,
                prompt_type="full" if i < 3 else "compact",
                max_contexts_requested=5
            )
        
        # Get all logs
        all_logs = logger.get_logs()
        assert len(all_logs) == 5
        
        # Most recent first
        assert all_logs[0].original_task == "Task 4"
        assert all_logs[-1].original_task == "Task 0"
    
    def test_get_logs_with_limit(self):
        """Test retrieving logs with limit."""
        logger = PromptLogger()
        
        context = ContextUnit(type=ContextType.PREFERENCE, content="Test")
        ranked = RankedContextUnit(context_unit=context, relevance_score=0.9)
        
        for i in range(10):
            generated = GeneratedPrompt(
                original_task=f"Task {i}",
                relevant_context=[ranked],
                generated_prompt=f"Prompt {i}"
            )
            logger.log_prompt_generation(
                task=f"Task {i}",
                ranked_contexts=[ranked],
                generated=generated,
                prompt_type="full",
                max_contexts_requested=5
            )
        
        logs = logger.get_logs(limit=3)
        assert len(logs) == 3
        assert logs[0].original_task == "Task 9"
    
    def test_get_logs_with_offset(self):
        """Test retrieving logs with offset."""
        logger = PromptLogger()
        
        context = ContextUnit(type=ContextType.PREFERENCE, content="Test")
        ranked = RankedContextUnit(context_unit=context, relevance_score=0.9)
        
        for i in range(10):
            generated = GeneratedPrompt(
                original_task=f"Task {i}",
                relevant_context=[ranked],
                generated_prompt=f"Prompt {i}"
            )
            logger.log_prompt_generation(
                task=f"Task {i}",
                ranked_contexts=[ranked],
                generated=generated,
                prompt_type="full",
                max_contexts_requested=5
            )
        
        logs = logger.get_logs(limit=3, offset=2)
        assert len(logs) == 3
        assert logs[0].original_task == "Task 7"
    
    def test_get_logs_by_type(self):
        """Test filtering logs by prompt type."""
        logger = PromptLogger()
        
        context = ContextUnit(type=ContextType.PREFERENCE, content="Test")
        ranked = RankedContextUnit(context_unit=context, relevance_score=0.9)
        
        for i in range(10):
            generated = GeneratedPrompt(
                original_task=f"Task {i}",
                relevant_context=[ranked],
                generated_prompt=f"Prompt {i}"
            )
            logger.log_prompt_generation(
                task=f"Task {i}",
                ranked_contexts=[ranked],
                generated=generated,
                prompt_type="full" if i < 6 else "compact",
                max_contexts_requested=5
            )
        
        full_logs = logger.get_logs(prompt_type="full")
        compact_logs = logger.get_logs(prompt_type="compact")
        
        assert len(full_logs) == 6
        assert len(compact_logs) == 4
    
    def test_get_log_by_id(self):
        """Test retrieving a specific log by ID."""
        logger = PromptLogger()
        
        context = ContextUnit(type=ContextType.PREFERENCE, content="Test")
        ranked = RankedContextUnit(context_unit=context, relevance_score=0.9)
        generated = GeneratedPrompt(
            original_task="Test task",
            relevant_context=[ranked],
            generated_prompt="Test prompt"
        )
        
        log_id = logger.log_prompt_generation(
            task="Test task",
            ranked_contexts=[ranked],
            generated=generated,
            prompt_type="full",
            max_contexts_requested=5
        )
        
        log = logger.get_log_by_id(log_id)
        assert log is not None
        assert log.log_id == log_id
        assert log.original_task == "Test task"
        
        # Test non-existent ID
        missing_log = logger.get_log_by_id("prompt-999999")
        assert missing_log is None
    
    def test_get_stats_empty(self):
        """Test stats with no logs."""
        logger = PromptLogger()
        stats = logger.get_stats()
        
        assert stats["total_logs"] == 0
        assert stats["logs_by_type"] == {}
        assert stats["avg_contexts_used"] == 0
        assert stats["avg_prompt_length"] == 0
    
    def test_get_stats_with_logs(self):
        """Test stats with multiple logs."""
        logger = PromptLogger()
        
        context = ContextUnit(type=ContextType.PREFERENCE, content="Test")
        ranked = RankedContextUnit(context_unit=context, relevance_score=0.9)
        
        for i in range(5):
            generated = GeneratedPrompt(
                original_task=f"Task {i}",
                relevant_context=[ranked] * (i + 1),  # Varying context counts
                generated_prompt="X" * (100 * (i + 1))  # Varying lengths
            )
            logger.log_prompt_generation(
                task=f"Task {i}",
                ranked_contexts=[ranked] * (i + 1),
                generated=generated,
                prompt_type="full" if i < 3 else "compact",
                max_contexts_requested=5
            )
        
        stats = logger.get_stats()
        
        assert stats["total_logs"] == 5
        assert stats["logs_by_type"]["full"] == 3
        assert stats["logs_by_type"]["compact"] == 2
        assert stats["avg_contexts_used"] == 3.0  # (1+2+3+4+5)/5
        assert stats["avg_prompt_length"] == 300.0  # (100+200+300+400+500)/5
    
    def test_clear_logs(self):
        """Test clearing all logs."""
        logger = PromptLogger()
        
        context = ContextUnit(type=ContextType.PREFERENCE, content="Test")
        ranked = RankedContextUnit(context_unit=context, relevance_score=0.9)
        
        for i in range(5):
            generated = GeneratedPrompt(
                original_task=f"Task {i}",
                relevant_context=[ranked],
                generated_prompt=f"Prompt {i}"
            )
            logger.log_prompt_generation(
                task=f"Task {i}",
                ranked_contexts=[ranked],
                generated=generated,
                prompt_type="full",
                max_contexts_requested=5
            )
        
        assert len(logger._logs) == 5
        
        count = logger.clear_logs()
        
        assert count == 5
        assert len(logger._logs) == 0
    
    def test_log_entry_to_dict(self):
        """Test converting log entry to dictionary."""
        context = ContextUnit(type=ContextType.PREFERENCE, content="Test")
        ranked = RankedContextUnit(context_unit=context, relevance_score=0.9)
        
        entry = PromptLogEntry(
            log_id="prompt-000001",
            timestamp=datetime.utcnow(),
            original_task="Test task",
            num_contexts_used=1,
            context_ids=[context.id],
            context_types={"preference": 1},
            generated_prompt="Generated prompt",
            prompt_type="full",
            prompt_length=16,
            max_contexts_requested=5
        )
        
        data = entry.to_dict()
        
        assert data["log_id"] == "prompt-000001"
        assert data["original_task"] == "Test task"
        assert data["num_contexts_used"] == 1
        assert data["prompt_type"] == "full"
        assert isinstance(data["timestamp"], str)
    
    def test_context_types_aggregation(self):
        """Test that context types are properly aggregated."""
        logger = PromptLogger()
        
        contexts = [
            ContextUnit(type=ContextType.PREFERENCE, content="Pref 1"),
            ContextUnit(type=ContextType.PREFERENCE, content="Pref 2"),
            ContextUnit(type=ContextType.GOAL, content="Goal 1"),
            ContextUnit(type=ContextType.FACT, content="Fact 1"),
        ]
        
        ranked = [
            RankedContextUnit(context_unit=c, relevance_score=0.9)
            for c in contexts
        ]
        
        generated = GeneratedPrompt(
            original_task="Test",
            relevant_context=ranked,
            generated_prompt="Test prompt"
        )
        
        log_id = logger.log_prompt_generation(
            task="Test",
            ranked_contexts=ranked,
            generated=generated,
            prompt_type="full",
            max_contexts_requested=10
        )
        
        log = logger.get_log_by_id(log_id)
        
        assert log.context_types["preference"] == 2
        assert log.context_types["goal"] == 1
        assert log.context_types["fact"] == 1
