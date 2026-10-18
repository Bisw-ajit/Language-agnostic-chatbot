import pytest
from unittest.mock import MagicMock, patch
from backend.rag.llm_provider import GroqProvider, LLMGenerationResult, get_llm_provider
from backend.config import Settings


def test_groq_provider_initialization():
    p = GroqProvider(api_key="gsk_test123", model_name="qwen/qwen3.8-27b")
    assert p.api_key == "gsk_test123"
    assert p.model_name == "qwen/qwen3.8-27b"
    assert p.timeout_seconds == 30.0


def test_groq_provider_missing_api_key():
    p = GroqProvider(api_key="")
    result = p.generate(prompt="Hello", system_prompt="Test")
    assert result.status == "LLM_AUTH_ERROR"
    assert "not configured" in result.error_message


def test_groq_provider_successful_generation():
    p = GroqProvider(api_key="gsk_valid_key")
    
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a factual response about Odisha schemes."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    p._client = mock_client
    p._initialized = True

    result = p.generate(
        prompt="Tell me about KALIA scheme",
        system_prompt="You are a government assistant"
    )

    assert result.status == "LLM_SUCCESS"
    assert "Odisha schemes" in result.text
    assert result.model == "qwen/qwen3.8-27b"
    assert result.error_message is None

    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "qwen/qwen3.8-27b"
    assert len(call_kwargs["messages"]) == 2
    assert call_kwargs["messages"][0]["role"] == "system"
    assert call_kwargs["messages"][1]["role"] == "user"


def test_groq_provider_rate_limit_handling():
    GroqProvider._rate_limit_until = 0.0
    p = GroqProvider(api_key="gsk_valid_key")
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("429 rate_limit_exceeded: TPM limit reached")
    
    p._client = mock_client
    p._initialized = True

    result = p.generate(prompt="Test prompt")
    assert result.status == "LLM_RATE_LIMIT"
    assert "rate_limit" in result.error_message.lower() or "429" in result.error_message.lower()


def test_groq_provider_timeout_handling():
    GroqProvider._rate_limit_until = 0.0
    p = GroqProvider(api_key="gsk_valid_key")
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("Request timed out")
    
    p._client = mock_client
    p._initialized = True

    result = p.generate(prompt="Test prompt")
    assert result.status == "LLM_TIMEOUT"


def test_get_llm_provider_factory_groq():
    test_settings = Settings(
        llm_provider="groq",
        groq_api_key="gsk_factory_test",
        groq_model="qwen/qwen3.8-27b"
    )
    with patch("backend.rag.llm_provider.get_settings", return_value=test_settings):
        provider = get_llm_provider()
        assert isinstance(provider, GroqProvider)
        assert provider.model_name == "qwen/qwen3.8-27b"
