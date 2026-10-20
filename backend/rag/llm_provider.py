import abc
import os
import time
import logging
from dataclasses import dataclass
from typing import Optional
from backend.config import get_settings

logger = logging.getLogger("rag.llm_provider")

@dataclass
class LLMGenerationResult:
    text: str
    status: str  # "LLM_SUCCESS" | "LLM_TIMEOUT" | "LLM_RATE_LIMIT" | "LLM_AUTH_ERROR" | "LLM_PROVIDER_ERROR" | "LLM_FALLBACK"
    model: str
    error_message: Optional[str] = None

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMGenerationResult:
        """Generates a text completion given a prompt and optional system prompt."""
        pass

class GeminiProvider(LLMProvider):
    _rate_limit_until: float = 0.0

    def __init__(self, api_key: str, model_name: str = "gemini-3.1-flash-lite", timeout_seconds: float = 35.0):
        self.api_key = api_key
        # Ensure model is valid supported string; default to gemini-3.1-flash-lite if invalid
        supported_prefixes = ("gemini-", "gemma-")
        if not any(model_name.startswith(p) for p in supported_prefixes):
            logger.warning(f"Unrecognized Gemini model '{model_name}'. Defaulting to 'gemini-3.1-flash-lite'.")
            self.model_name = "gemini-3.1-flash-lite"
        else:
            self.model_name = model_name

        self.timeout_seconds = timeout_seconds
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
                logger.error(f"[GeminiProvider] Initialization error: {e}")
                self._model = None

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMGenerationResult:
        # Check active rate limit cooldown
        now = time.time()
        if now < GeminiProvider._rate_limit_until:
            rem = int(GeminiProvider._rate_limit_until - now)
            return LLMGenerationResult(
                text="",
                status="LLM_RATE_LIMIT",
                model=self.model_name,
                error_message=f"Rate limit cooldown active for {rem}s."
            )

        self._init_client()
        if not self._model or not self.api_key:
            return LLMGenerationResult(
                text="",
                status="LLM_AUTH_ERROR",
                model=self.model_name,
                error_message="Gemini API key is not configured or client failed to initialize."
            )
            
        full_content = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        # Execute with retry for transient network failures; skip retry on quota exhaustion
        max_attempts = 2
        last_error = None
        status = "LLM_PROVIDER_ERROR"

        for attempt in range(1, max_attempts + 1):
            try:
                response = self._model.generate_content(
                    full_content,
                    request_options={"timeout": self.timeout_seconds}
                )
                if response and response.text:
                    return LLMGenerationResult(
                        text=response.text.strip(),
                        status="LLM_SUCCESS",
                        model=self.model_name,
                        error_message=None
                    )
                return LLMGenerationResult(
                    text="",
                    status="LLM_PROVIDER_ERROR",
                    model=self.model_name,
                    error_message="Empty response received from Gemini API."
                )
            except Exception as e:
                last_error = str(e)
                err_lower = last_error.lower()
                
                if "timed out" in err_lower or "timeout" in err_lower:
                    status = "LLM_TIMEOUT"
                elif "429" in err_lower or "quota" in err_lower or "resourceexhausted" in err_lower:
                    status = "LLM_RATE_LIMIT"
                    GeminiProvider._rate_limit_until = time.time() + 60.0
                    logger.warning(f"[GeminiProvider] Quota exceeded. Cooldown initiated for 60s.")
                    break  # Don't retry quota exhaustion immediately
                elif "401" in err_lower or "403" in err_lower or "api_key" in err_lower or "unregistered" in err_lower:
                    status = "LLM_AUTH_ERROR"
                    break  # Don't retry authentication failures
                else:
                    status = "LLM_PROVIDER_ERROR"

                logger.warning(f"[GeminiProvider] Attempt {attempt}/{max_attempts} failed with {status}: {last_error}")
                if attempt < max_attempts:
                    time.sleep(1.0)

        return LLMGenerationResult(
            text="",
            status=status,
            model=self.model_name,
            error_message=last_error
        )

class GroqProvider(LLMProvider):
    _rate_limit_until: float = 0.0

    def __init__(self, api_key: str, model_name: str = "qwen/qwen3.8-27b", timeout_seconds: float = 30.0):
        self.api_key = api_key
        # Default to qwen/qwen3.8-27b if not specified or empty
        if not model_name or not isinstance(model_name, str):
            self.model_name = "qwen/qwen3.8-27b"
        else:
            self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self._client = None
        self._initialized = False

    def _init_client(self):
        if not self._initialized:
            try:
                from groq import Groq
                if self.api_key:
                    self._client = Groq(api_key=self.api_key, timeout=self.timeout_seconds)
                self._initialized = True
            except Exception as e:
                logger.error(f"[GroqProvider] Client initialization error: {e}")
                self._client = None

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMGenerationResult:
        now = time.time()
        if now < GroqProvider._rate_limit_until:
            rem = int(GroqProvider._rate_limit_until - now)
            return LLMGenerationResult(
                text="",
                status="LLM_RATE_LIMIT",
                model=self.model_name,
                error_message=f"Groq rate limit cooldown active for {rem}s."
            )

        self._init_client()
        if not self.api_key or not self._client:
            return LLMGenerationResult(
                text="",
                status="LLM_AUTH_ERROR",
                model=self.model_name,
                error_message="Groq API key is not configured or client failed to initialize. Set GROQ_API_KEY in backend/.env."
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        max_attempts = 2
        last_error = None
        status = "LLM_PROVIDER_ERROR"

        for attempt in range(1, max_attempts + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.1,  # Low temperature for factual RAG anti-hallucination
                    max_tokens=1500,
                )
                if response and response.choices and len(response.choices) > 0:
                    choice = response.choices[0]
                    content = choice.message.content if choice.message else ""
                    if content:
                        return LLMGenerationResult(
                            text=content.strip(),
                            status="LLM_SUCCESS",
                            model=self.model_name,
                            error_message=None
                        )
                return LLMGenerationResult(
                    text="",
                    status="LLM_PROVIDER_ERROR",
                    model=self.model_name,
                    error_message="Empty response received from Groq API."
                )
            except Exception as e:
                last_error = str(e)
                err_lower = last_error.lower()
                if "timed out" in err_lower or "timeout" in err_lower:
                    status = "LLM_TIMEOUT"
                elif "429" in err_lower or "rate_limit_exceeded" in err_lower or "quota" in err_lower:
                    status = "LLM_RATE_LIMIT"
                    GroqProvider._rate_limit_until = time.time() + 60.0
                    logger.warning("[GroqProvider] Rate limit reached. Cooldown initiated for 60s.")
                    break
                elif "401" in err_lower or "invalid_api_key" in err_lower or "authentication" in err_lower:
                    status = "LLM_AUTH_ERROR"
                    break
                elif "model_not_found" in err_lower or "does not exist" in err_lower or "not have access" in err_lower:
                    if self.model_name != "qwen/qwen3.8-27b":
                        logger.warning(f"[GroqProvider] Model {self.model_name} unavailable. Switching to 'qwen/qwen3.8-27b'.")
                        self.model_name = "qwen/qwen3.8-27b"
                        continue
                    status = "LLM_PROVIDER_ERROR"
                    break
                else:
                    status = "LLM_PROVIDER_ERROR"

                logger.warning(f"[GroqProvider] Attempt {attempt}/{max_attempts} failed with {status}: {last_error}")
                if attempt < max_attempts:
                    time.sleep(1.0)

        return LLMGenerationResult(
            text="",
            status=status,
            model=self.model_name,
            error_message=last_error
        )

class MockProvider(LLMProvider):
    """Offline/Mock provider for testing or fallback when API key is unavailable."""
    def __init__(self, model_name: str = "mock-grounded-v1"):
        self.model_name = model_name

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMGenerationResult:
        return LLMGenerationResult(
            text="This is a verified mock response based strictly on the retrieved institutional context.",
            status="LLM_SUCCESS",
            model=self.model_name,
            error_message=None
        )

def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider_type = getattr(settings, "llm_provider", "groq").lower()

    if provider_type == "groq":
        if getattr(settings, "groq_api_key", None):
            return GroqProvider(api_key=settings.groq_api_key, model_name=settings.groq_model)
        elif getattr(settings, "gemini_api_key", None):
            logger.warning("[get_llm_provider] GROQ_API_KEY is not set. Falling back to configured Gemini provider.")
            return GeminiProvider(api_key=settings.gemini_api_key, model_name=settings.gemini_model)
        else:
            return GroqProvider(api_key="", model_name=settings.groq_model)
    elif provider_type == "gemini":
        if getattr(settings, "gemini_api_key", None):
            return GeminiProvider(api_key=settings.gemini_api_key, model_name=settings.gemini_model)
        return MockProvider()
    elif provider_type == "mock":
        return MockProvider()

    return MockProvider()
