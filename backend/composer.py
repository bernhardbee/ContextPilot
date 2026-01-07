"""
Prompt composer that combines task with relevant context.
"""
from typing import List
from datetime import datetime
from models import RankedContextUnit, GeneratedPrompt


class PromptComposer:
    """Composes optimized prompts by combining task with relevant context."""
    
    def compose(
        self,
        task: str,
        relevant_contexts: List[RankedContextUnit]
    ) -> GeneratedPrompt:
        """
        Compose a prompt by combining the task with relevant context.
        
        Args:
            task: The user's task description
            relevant_contexts: Ranked list of relevant context units
            
        Returns:
            GeneratedPrompt with the composed prompt
        """
        if not relevant_contexts:
            return GeneratedPrompt(
                original_task=task,
                relevant_context=[],
                generated_prompt=task
            )
        
        # Build the contextualized prompt
        prompt_parts = ["# Context\n"]
        
        # Group contexts by type
        contexts_by_type = {}
        for ranked in relevant_contexts:
            ctx_type = ranked.context_unit.type.value
            if ctx_type not in contexts_by_type:
                contexts_by_type[ctx_type] = []
            contexts_by_type[ctx_type].append(ranked)
        
        # Add contexts organized by type
        for ctx_type in ["preference", "goal", "decision", "fact"]:
            if ctx_type in contexts_by_type:
                prompt_parts.append(f"\n## {ctx_type.capitalize()}s")
                for ranked in contexts_by_type[ctx_type]:
                    context = ranked.context_unit
                    confidence_indicator = "✓" if context.confidence >= 0.8 else "~"
                    prompt_parts.append(f"- [{confidence_indicator}] {context.content}")
                    if context.tags:
                        prompt_parts.append(f"  (Tags: {', '.join(context.tags)})")
        
        # Add the task
        prompt_parts.append(f"\n# Task\n\n{task}")
        
        # Add instructions for the LLM
        prompt_parts.append("\n# Instructions\n")
        prompt_parts.append("Please complete the task above, taking into account the provided context.")
        prompt_parts.append("Align your response with the stated preferences, goals, and decisions.")
        
        generated_prompt = "\n".join(prompt_parts)
        
        return GeneratedPrompt(
            original_task=task,
            relevant_context=relevant_contexts,
            generated_prompt=generated_prompt
        )
    
    def compose_compact(
        self,
        task: str,
        relevant_contexts: List[RankedContextUnit]
    ) -> GeneratedPrompt:
        """
        Compose a more compact prompt format.
        
        Args:
            task: The user's task description
            relevant_contexts: Ranked list of relevant context units
            
        Returns:
            GeneratedPrompt with the composed prompt
        """
        if not relevant_contexts:
            return GeneratedPrompt(
                original_task=task,
                relevant_context=[],
                generated_prompt=task
            )
        
        # Build compact context
        context_items = []
        for ranked in relevant_contexts:
            context = ranked.context_unit
            context_items.append(context.content)
        
        # Build the prompt
        prompt = f"""Given the following context about the user:

{chr(10).join(f"• {item}" for item in context_items)}

Task: {task}
"""
        
        return GeneratedPrompt(
            original_task=task,
            relevant_context=relevant_contexts,
            generated_prompt=prompt
        )


# Global instance
prompt_composer = PromptComposer()
