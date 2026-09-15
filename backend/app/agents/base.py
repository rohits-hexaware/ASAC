"""Base agent utilities."""

from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

from pydantic import BaseModel

from app.ai.service import ai_service
from app.config import settings

logger = logging.getLogger(__name__)


T = TypeVar("T", bound=BaseModel)


async def run_agent(
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    schema: type[T],
    schema_hint: str,
    fallback_fn: Callable[[], T],
    max_tokens: int | None = None,
) -> tuple[T, str]:
    """Execute agent with AI + validation, falling back to template."""
    logger.info("[DEBUG] Agent starting execution: '%s'", agent_name)
    print(f"[DEBUG] Agent starting execution: '{agent_name}'", flush=True)
    ai_error: Exception | None = None
    try:
        data, provider = await ai_service.complete_json(
            system_prompt, user_prompt, schema_hint, max_tokens=max_tokens
        )
        if data and provider != "template":
            try:
                return schema.model_validate(data), provider
            except Exception as val_err:
                logger.warning("Pydantic validation failed for %s, constructing model: %s", agent_name, val_err)
                return schema.model_construct(**data), provider
    except Exception as e:
        ai_error = e
        logger.warning("Agent %s AI call failed: %s", agent_name, e)

    if settings.template_fallback:
        result = fallback_fn()
        return result, "template"
    else:
        raise RuntimeError(f"Agent {agent_name} failed: {ai_error}") from ai_error

