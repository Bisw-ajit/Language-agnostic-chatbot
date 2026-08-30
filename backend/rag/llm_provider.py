import abc
import os
from typing import Optional
from backend.config import get_settings

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates a text completion given a prompt and optional system prompt."""
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._initialized = False
        self._model = None
        
    def _init_client(self):
        if not self._initialized:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key, transport="rest")
                self._model = genai.GenerativeModel(self.model_name)
                self._initialized = True
            except Exception as e:
                print(f"[GeminiProvider] Initialization error: {e}")
                
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._init_client()
        if not self._model:
            raise RuntimeError("Gemini model is not initialized or API key is missing.")
            
        full_content = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        try:
            response = self._model.generate_content(
                full_content,
                request_options={"timeout": 4.0}
            )
            if response and response.text:
                return response.text.strip()
            return ""
        except Exception as e:
            print(f"[GeminiProvider] Generation error: {e}")
            raise

class MockProvider(LLMProvider):
    """Offline/Mock provider for testing or fallback when API key is unavailable."""
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return "This is a verified mock response based strictly on the retrieved institutional context."

def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        return GeminiProvider(api_key=settings.gemini_api_key, model_name=settings.gemini_model)
    elif settings.llm_provider == "mock" or not settings.gemini_api_key:
        return MockProvider()
    return GeminiProvider(api_key=settings.gemini_api_key, model_name=settings.gemini_model)
