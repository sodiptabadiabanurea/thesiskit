"""LLM integration for ThesisKit agents."""

from abc import ABC, abstractmethod
from typing import Optional, Any
import os


class LLMClient(ABC):
    """Base class for LLM clients."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> dict:
        """Generate JSON from prompt."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI-compatible client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy init httpx client."""
        if self._client is None:
            import httpx
            self._client = httpx.Client(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
            )
        return self._client
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Generate text from prompt."""
        client = self._get_client()
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> dict:
        """Generate JSON from prompt."""
        import json
        
        text = self.generate(
            prompt=prompt,
            system=system,
            temperature=0.3,  # Lower temp for structured output
        )
        
        # Extract JSON from response
        try:
            # Try direct parse
            return json.loads(text)
        except json.JSONDecodeError:
            # Try extracting from markdown code block
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                return json.loads(text[start:end].strip())
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                return json.loads(text[start:end].strip())
            raise
    
    def close(self):
        """Close client."""
        if self._client:
            self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class GLMClient(OpenAIClient):
    """GLM (Zhipu AI) client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-5",
    ):
        super().__init__(
            api_key=api_key,
            base_url="https://api.z.ai/api/coding/paas/v4",
            model=model,
        )


def get_client(
    provider: str = "openai",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMClient:
    """Factory function to get LLM client."""
    if provider == "openai" or provider == "openai-compatible":
        return OpenAIClient(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
            model=model or "gpt-4o",
        )
    elif provider == "glm":
        return GLMClient(api_key=api_key, model=model or "glm-5")
    else:
        raise ValueError(f"Unknown provider: {provider}")
