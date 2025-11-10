"""
Custom PyRIT target implementation for OpenAI's Atlas browser.
This module provides the interface between PyRIT and the Atlas API.
"""
import asyncio
import time
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from pyrit.models import PromptRequestResponse, PromptRequestPiece
from pyrit.prompt_target import PromptTarget

from config import Config


class AtlasTarget(PromptTarget):
    """
    Custom PyRIT target for interacting with OpenAI's Atlas browser.
    
    This class implements the PromptTarget interface to enable PyRIT
    to send adversarial prompts to Atlas and receive responses.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the Atlas target.
        
        Args:
            model: The model to use (defaults to Config.ATLAS_MODEL)
            max_tokens: Maximum tokens in response (defaults to Config.ATLAS_MAX_TOKENS)
            temperature: Sampling temperature (defaults to Config.ATLAS_TEMPERATURE)
            timeout: Request timeout in seconds (defaults to Config.TIMEOUT_SECONDS)
        """
        super().__init__()
        
        self.model = model or Config.ATLAS_MODEL
        self.max_tokens = max_tokens or Config.ATLAS_MAX_TOKENS
        self.temperature = temperature or Config.ATLAS_TEMPERATURE
        self.timeout = timeout or Config.TIMEOUT_SECONDS
        
        # Initialize async OpenAI client
        self.client = AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_API_BASE,
            timeout=self.timeout,
        )
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 60.0 / Config.REQUESTS_PER_MINUTE
        
        # Conversation history for multi-turn attacks
        self.conversation_history: List[Dict[str, str]] = []
    
    async def send_prompt_async(
        self,
        prompt_request: PromptRequestResponse
    ) -> PromptRequestResponse:
        """
        Send a prompt to Atlas and return the response.
        
        Args:
            prompt_request: The prompt request containing the adversarial input
            
        Returns:
            PromptRequestResponse containing the model's response
        """
        # Apply rate limiting
        await self._rate_limit()
        
        # Extract the prompt text
        prompt_text = prompt_request.request_pieces[0].converted_value
        
        # Build messages for the API call
        messages = self._build_messages(prompt_text)
        
        try:
            # Send request to Atlas
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": prompt_text})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Create response piece
            response_piece = PromptRequestPiece(
                role="assistant",
                original_value=response_text,
                converted_value=response_text,
                original_value_data_type="text",
                converted_value_data_type="text",
                prompt_target_identifier=self.get_identifier(),
            )
            
            # Update the prompt request with the response
            prompt_request.request_pieces.append(response_piece)
            
            return prompt_request
            
        except Exception as e:
            # Handle errors gracefully
            error_text = f"Error communicating with Atlas: {str(e)}"
            
            error_piece = PromptRequestPiece(
                role="assistant",
                original_value=error_text,
                converted_value=error_text,
                original_value_data_type="text",
                converted_value_data_type="text",
                prompt_target_identifier=self.get_identifier(),
            )
            
            prompt_request.request_pieces.append(error_piece)
            
            return prompt_request
    
    def _build_messages(self, prompt_text: str) -> List[Dict[str, str]]:
        """
        Build the messages list for the API call.
        
        Args:
            prompt_text: The current prompt to send
            
        Returns:
            List of message dictionaries
        """
        if Config.ENABLE_MULTI_TURN and len(self.conversation_history) > 0:
            # Include conversation history for multi-turn attacks
            messages = self.conversation_history.copy()
            messages.append({"role": "user", "content": prompt_text})
            
            # Limit conversation history to prevent token overflow
            max_history_turns = Config.MAX_CONVERSATION_TURNS * 2  # user + assistant pairs
            if len(messages) > max_history_turns:
                messages = messages[-max_history_turns:]
        else:
            # Single turn - just the current prompt
            messages = [{"role": "user", "content": prompt_text}]
        
        return messages
    
    async def _rate_limit(self) -> None:
        """Implement rate limiting to respect API quotas."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self._last_request_time = time.time()
    
    def reset_conversation(self) -> None:
        """Reset the conversation history for a new test."""
        self.conversation_history = []
    
    def get_identifier(self) -> Dict[str, str]:
        """Get identifier for this target."""
        return {
            "id": f"atlas_{self.model}",
            "model": self.model,
            "type": "atlas_browser"
        }
    
    def get_conversation_length(self) -> int:
        """Get the number of turns in the current conversation."""
        return len(self.conversation_history) // 2

