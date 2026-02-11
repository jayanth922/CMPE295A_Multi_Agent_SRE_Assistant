#!/usr/bin/env python3
"""
Centralized LLM utilities with improved error handling.

This module provides a single point for LLM creation with proper error handling
for authentication, access, and configuration issues.
"""

import logging
from typing import Any, Dict

from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from .constants import SREConstants

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    """Exception raised when LLM provider creation fails."""

    pass


class LLMAuthenticationError(LLMProviderError):
    """Exception raised when LLM authentication fails."""

    pass


class LLMAccessError(LLMProviderError):
    """Exception raised when LLM access is denied."""

    pass


def create_llm_with_error_handling(provider: str = "groq", **kwargs):
    """Create LLM instance with proper error handling and helpful error messages.

    Args:
        provider: LLM provider (only "groq" is supported)
        **kwargs: Additional configuration overrides

    Returns:
        LLM instance

    Raises:
        LLMProviderError: For general provider errors
        LLMAuthenticationError: For authentication failures
        LLMAccessError: For access/permission failures
        ValueError: For unsupported providers
    """
    if provider == "groq":
        logger.info(f"Creating LLM with provider: {provider}")
    elif provider == "ollama":
        logger.info(f"Creating LLM with provider: {provider}")
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. Supported: 'groq', 'ollama'."
        )

    try:
        config = SREConstants.get_model_config(provider, **kwargs)
        
        if provider == "groq":
            logger.info(f"Creating Groq LLM - Model: {config['model_id']}")
            return _create_groq_llm(config)
        elif provider == "ollama":
            logger.info(f"Creating Ollama LLM - Model: {config['model_id']} at {config['base_url']}")
            return _create_ollama_llm(config)

    except Exception as e:
        error_msg = _get_helpful_error_message(provider, e)
        logger.error(f"Failed to create LLM: {error_msg}")

        # Classify the error type for better handling
        if _is_auth_error(e):
            raise LLMAuthenticationError(error_msg) from e
        elif _is_access_error(e):
            raise LLMAccessError(error_msg) from e
        else:
            raise LLMProviderError(error_msg) from e


def _create_ollama_llm(config: Dict[str, Any]):
    """Create Ollama LLM instance."""
    return ChatOllama(
        model=config["model_id"],
        base_url=config.get("base_url", "http://localhost:11434"),
        temperature=config["temperature"],
        # Explicitly set context window to 32k to avoid truncation of logs/diffs
        num_ctx=32768, 
    )


def _create_groq_llm(config: Dict[str, Any]):
    """Create Groq LLM instance."""
    return ChatGroq(
        model=config["model_id"],
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
    )


def _is_auth_error(error: Exception) -> bool:
    """Check if error is authentication-related."""
    error_str = str(error).lower()
    auth_keywords = [
        "authentication",
        "unauthorized",
        "invalid credentials",
        "api key",
        "access key",
        "token",
        "permission denied",
        "403",
        "401",
    ]
    return any(keyword in error_str for keyword in auth_keywords)


def _is_access_error(error: Exception) -> bool:
    """Check if error is access/permission-related."""
    error_str = str(error).lower()
    access_keywords = [
        "access denied",
        "forbidden",
        "not authorized",
        "insufficient permissions",
        "quota exceeded",
        "rate limit",
        "service unavailable",
        "region not supported",
    ]
    return any(keyword in error_str for keyword in access_keywords)


def _get_helpful_error_message(provider: str, error: Exception) -> str:
    """Generate helpful error message based on provider and error type."""
    base_error = str(error)

    if _is_auth_error(error):
        return (
            f"Groq authentication failed: {base_error}\n"
            "Solutions:\n"
            "  1. Set GROQ_API_KEY environment variable\n"
            "  2. Check if your API key is valid and active\n"
            "  3. Try: export GROQ_API_KEY='your-key-here'"
        )
    elif _is_access_error(error):
        return (
            f"Groq access error: {base_error}\n"
            "Solutions:\n"
            "  1. Verify model name exists for your account\n"
            "  2. Check rate limits / quotas in Groq console\n"
            "  3. Try a lighter model (e.g., llama-3.1-8b-instant)"
        )
    else:
        return (
            "  2. Verify model name and parameters\n"
            "  3. Try again"
        )
    
    if provider == "ollama":
        if "connection refused" in base_error.lower():
            return (
                f"Ollama connection failed: {base_error}\n"
                "Solutions:\n"
                "  1. Ensure Ollama container is running (docker-compose up -d ollama)\n"
                "  2. Check OLLAMA_BASE_URL (http://ollama:11434 from inside docker)\n"
            )
        elif "not found" in base_error.lower():
             return (
                f"Ollama model not found: {base_error}\n"
                "Solutions:\n"
                "  1. Run scripts/init_ollama.sh to pull the model\n"
            )

    return (
        f"{provider} provider error: {base_error}\n"
        "Solutions:\n"
        "  1. Check service status and your network\n"
        "  2. Verify model name and parameters\n"
        "  3. Try again"
    )


def validate_provider_access(provider: str = "groq", **kwargs) -> bool:
    """Validate if the specified provider is accessible.

    Args:
        provider: LLM provider to validate (only "groq" is supported)
        **kwargs: Additional configuration

    Returns:
        True if provider is accessible, False otherwise
    """
    if provider not in ["groq", "ollama"]:
        logger.warning(f"Unsupported provider: {provider}. Supported: 'groq', 'ollama'.")
        return False

    try:
        llm = create_llm_with_error_handling(provider, **kwargs)
        # Try a simple test call to validate access
        # Note: This is a minimal validation - actual usage may still fail
        logger.info(f"Provider {provider} validation successful")
        return True
    except Exception as e:
        logger.warning(f"Provider {provider} validation failed: {e}")
        return False


def get_recommended_provider() -> str:
    """Get recommended provider based on availability.

    Returns:
        Recommended provider name (always "groq")
    """
    # Prefer Ollama for local execution if available
    if validate_provider_access("ollama"):
        logger.info("Recommended provider: ollama")
        return "ollama"

    if validate_provider_access("groq"):
        logger.info("Recommended provider: groq")
        return "groq"

    logger.warning("No providers accessible. Defaulting to ollama.")
    return "ollama"
