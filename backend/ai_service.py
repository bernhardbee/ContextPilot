"""
AI service integration for OpenAI and Anthropic.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import openai
from anthropic import Anthropic

from config import settings
from logger import logger
from models import GeneratedPrompt
from db_models import ConversationDB, MessageDB
from database import get_db_session


class AIService:
    """
    Unified AI service for multiple providers.
    """
    
    def __init__(self):
        """Initialize AI service with configured providers."""
        self.openai_client = None
        self.anthropic_client = None
        
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.openai_client = openai
            logger.info("OpenAI client initialized")
        
        if settings.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
            logger.info("Anthropic client initialized")
    
    async def generate_response(
        self,
        task: str,
        generated_prompt: GeneratedPrompt,
        context_ids: List[str],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, ConversationDB]:
        """
        Generate AI response using the specified provider.
        
        Args:
            task: User's original task
            generated_prompt: The contextualized prompt
            context_ids: List of context IDs used
            provider: AI provider ("openai" or "anthropic")
            model: Model to use
            temperature: Temperature parameter
            max_tokens: Max tokens in response
            
        Returns:
            Tuple of (response_text, conversation_record)
        """
        provider = provider or settings.default_ai_provider
        model = model or settings.default_ai_model
        temperature = temperature if temperature is not None else settings.ai_temperature
        max_tokens = max_tokens or settings.ai_max_tokens
        
        if provider == "openai":
            return await self._generate_openai(
                task, generated_prompt, context_ids, model, temperature, max_tokens
            )
        elif provider == "anthropic":
            return await self._generate_anthropic(
                task, generated_prompt, context_ids, model, temperature, max_tokens
            )
        else:
            raise ValueError(f"Unknown AI provider: {provider}")
    
    async def _generate_openai(
        self,
        task: str,
        generated_prompt: GeneratedPrompt,
        context_ids: List[str],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Tuple[str, ConversationDB]:
        """Generate response using OpenAI API."""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            # Create conversation record
            conversation = self._create_conversation(
                task=task,
                prompt_type="full" if "compact" not in generated_prompt.generated_prompt.lower() else "compact",
                context_ids=context_ids,
                provider="openai",
                model=model
            )
            
            # Prepare messages
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant with access to personalized context."},
                {"role": "user", "content": generated_prompt.generated_prompt}
            ]
            
            # Call OpenAI API
            response = self.openai_client.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract response
            assistant_message = response.choices[0].message['content']
            finish_reason = response.choices[0].finish_reason
            tokens_used = response.usage.total_tokens
            
            # Save messages
            self._save_messages(
                conversation.id,
                messages=[
                    {"role": "system", "content": messages[0]["content"]},
                    {"role": "user", "content": messages[1]["content"]},
                    {"role": "assistant", "content": assistant_message, "tokens": tokens_used, "finish_reason": finish_reason}
                ]
            )
            
            logger.info(f"OpenAI response generated: {model}, {tokens_used} tokens")
            return assistant_message, conversation
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _generate_anthropic(
        self,
        task: str,
        generated_prompt: GeneratedPrompt,
        context_ids: List[str],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Tuple[str, ConversationDB]:
        """Generate response using Anthropic API."""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        try:
            # Create conversation record
            conversation = self._create_conversation(
                task=task,
                prompt_type="full" if "compact" not in generated_prompt.generated_prompt.lower() else "compact",
                context_ids=context_ids,
                provider="anthropic",
                model=model
            )
            
            # Call Anthropic API
            response = self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": generated_prompt.generated_prompt}
                ]
            )
            
            # Extract response
            assistant_message = response.content[0].text
            finish_reason = response.stop_reason
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            # Save messages
            self._save_messages(
                conversation.id,
                messages=[
                    {"role": "user", "content": generated_prompt.prompt},
                    {"role": "assistant", "content": assistant_message, "tokens": tokens_used, "finish_reason": finish_reason}
                ]
            )
            
            logger.info(f"Anthropic response generated: {model}, {tokens_used} tokens")
            return assistant_message, conversation
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _create_conversation(
        self,
        task: str,
        prompt_type: str,
        context_ids: List[str],
        provider: str,
        model: str
    ) -> ConversationDB:
        """Create a conversation record in the database."""
        with get_db_session() as db:
            conversation = ConversationDB(
                task=task,
                prompt_type=prompt_type,
                provider=provider,
                model=model,
                context_ids=context_ids
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return conversation
    
    def _save_messages(self, conversation_id: str, messages: List[Dict]):
        """Save messages to the database."""
        with get_db_session() as db:
            for msg in messages:
                db_message = MessageDB(
                    conversation_id=conversation_id,
                    role=msg["role"],
                    content=msg["content"],
                    tokens=msg.get("tokens"),
                    finish_reason=msg.get("finish_reason")
                )
                db.add(db_message)
            db.commit()
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get a conversation with all its messages."""
        with get_db_session() as db:
            conversation = db.query(ConversationDB).filter(
                ConversationDB.id == conversation_id
            ).first()
            
            if not conversation:
                return None
            
            return {
                "id": conversation.id,
                "task": conversation.task,
                "prompt_type": conversation.prompt_type,
                "provider": conversation.provider,
                "model": conversation.model,
                "context_ids": conversation.context_ids,
                "created_at": conversation.created_at.isoformat(),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "tokens": msg.tokens,
                        "finish_reason": msg.finish_reason,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in conversation.messages
                ]
            }
    
    def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List recent conversations."""
        with get_db_session() as db:
            conversations = db.query(ConversationDB)\
                .order_by(ConversationDB.created_at.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            return [
                {
                    "id": conv.id,
                    "task": conv.task,
                    "prompt_type": conv.prompt_type,
                    "provider": conv.provider,
                    "model": conv.model,
                    "created_at": conv.created_at.isoformat(),
                    "message_count": len(conv.messages)
                }
                for conv in conversations
            ]


# Global AI service instance
ai_service = AIService()
