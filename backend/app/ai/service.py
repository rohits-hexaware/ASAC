"""AI service abstraction with Azure OpenAI, OpenAI, Ollama, and template fallback."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, List

import httpx
from openai import AsyncAzureOpenAI, AsyncOpenAI

from app.config import settings

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

logger = logging.getLogger(__name__)

_local_embedder = HashingVectorizer(n_features=384, alternate_sign=False)


class AIService:
    """Unified AI client with fallback chain."""

    def __init__(self) -> None:
        self.last_provider: str = "none"

    def _get_azure_client(self) -> AsyncAzureOpenAI | None:
        if settings.azure_openai_api_key and settings.azure_openai_endpoint:
            return AsyncAzureOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
            )
        return None

    def _get_openai_client(self) -> AsyncOpenAI | None:
        if settings.openai_api_key:
            return AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        return None

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_hint: str | None = None,
        max_tokens: int | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Return parsed JSON dict and provider name used."""
        prompt = user_prompt
        if schema_hint:
            prompt = f"{user_prompt}\n\nRespond with valid JSON matching this structure:\n{schema_hint}"

        target_max_tokens = max_tokens or settings.max_tokens

        # 1. Try Azure OpenAI
        azure_client = self._get_azure_client()
        if azure_client:
            try:
                resp = await azure_client.chat.completions.create(
                    model=settings.azure_openai_deployment,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=target_max_tokens,
                    timeout=settings.agent_timeout,
                )
                content = resp.choices[0].message.content or "{}"
                self.last_provider = "azure_openai"
                return json.loads(content), "azure_openai"
            except Exception as e:
                logger.warning("Azure OpenAI failed: %s", e)

        # 2. Try Standard OpenAI / Groq with retry on 429 & 400 truncation
        openai_client = self._get_openai_client()
        if openai_client:
            token_budget = target_max_tokens
            current_prompt = prompt
            for attempt in range(2):
                try:
                    logger.info("Calling OpenAI model '%s' with max_tokens=%d", settings.openai_model, token_budget)
                    resp = await openai_client.chat.completions.create(
                        model=settings.openai_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": current_prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.3,
                        max_tokens=token_budget,
                        timeout=settings.agent_timeout,
                    )
                    content = resp.choices[0].message.content or "{}"
                    self.last_provider = "openai"
                    return json.loads(content), "openai"
                except Exception as e:
                    err_str = str(e)
                    is_rate_limit = "429" in err_str or "rate_limit" in err_str.lower()
                    is_json_truncation = "json_validate_failed" in err_str or "max completion tokens" in err_str or "400" in err_str

                    if attempt == 0 and (is_rate_limit or is_json_truncation):
                        if is_rate_limit:
                            token_budget = max(400, token_budget - 250)
                            logger.warning("OpenAI rate limit (429) hit. Retrying in 2.5s with max_tokens=%d: %s", token_budget, e)
                            await asyncio.sleep(2.5)
                        else:
                            # JSON was truncated before completion: enforce extreme brevity on retry
                            current_prompt = (
                                f"{prompt}\n\n"
                                "CRITICAL CONSTRAINT: The output MUST be ultra-compact to avoid truncation. "
                                "Limit all JSON array lists to a maximum of 3 items each and keep all string descriptions under 15 words."
                            )
                            logger.warning("JSON truncation (400) hit. Retrying with ultra-compact prompt constraint: %s", e)
                            await asyncio.sleep(1.0)
                    else:
                        logger.warning("OpenAI failed: %s", e)
                        break

        # 3. Try Ollama
        try:
            result = await self._call_ollama(system_prompt, prompt)
            self.last_provider = "ollama"
            return result, "ollama"
        except Exception as e:
            logger.warning("Ollama failed: %s", e)

        # 4. Fallback or Raise based on settings.template_fallback
        if settings.template_fallback:
            self.last_provider = "template"
            return {}, "template"
        else:
            raise RuntimeError("All AI providers failed and template_fallback is disabled.")

    async def complete_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> tuple[str, str]:
        """Return plain text response."""
        target_max_tokens = max_tokens or settings.max_tokens

        # 1. Try Azure OpenAI
        azure_client = self._get_azure_client()
        if azure_client:
            try:
                resp = await azure_client.chat.completions.create(
                    model=settings.azure_openai_deployment,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.5,
                    max_tokens=target_max_tokens,
                    timeout=settings.agent_timeout,
                )
                text = resp.choices[0].message.content or ""
                self.last_provider = "azure_openai"
                return text, "azure_openai"
            except Exception as e:
                logger.warning("Azure OpenAI text failed: %s", e)

        # 2. Try Standard OpenAI / Groq
        openai_client = self._get_openai_client()
        if openai_client:
            token_budget = target_max_tokens
            for attempt in range(2):
                try:
                    resp = await openai_client.chat.completions.create(
                        model=settings.openai_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.5,
                        max_tokens=token_budget,
                        timeout=settings.agent_timeout,
                    )
                    text = resp.choices[0].message.content or ""
                    self.last_provider = "openai"
                    return text, "openai"
                except Exception as e:
                    err_str = str(e)
                    is_rate_limit = "429" in err_str or "rate_limit" in err_str.lower() or "limit" in err_str.lower()
                    if is_rate_limit and attempt == 0:
                        token_budget = max(400, token_budget - 200)
                        logger.warning("OpenAI rate limit hit for text. Retrying in 2.5s with max_tokens=%d: %s", token_budget, e)
                        await asyncio.sleep(2.5)
                    else:
                        logger.warning("OpenAI text failed: %s", e)
                        break

        # 3. Try Ollama
        try:
            text = await self._call_ollama_text(system_prompt, user_prompt)
            self.last_provider = "ollama"
            return text, "ollama"
        except Exception as e:
            logger.warning("Ollama text failed: %s", e)

        if settings.template_fallback:
            self.last_provider = "template"
            return (
                "Operating in fallback mode without AI connectivity. "
                "Please review the structured analysis findings above.",
                "template",
            )
        else:
            raise RuntimeError("All AI providers failed and template_fallback is disabled.")

    async def get_embedding(self, text: str) -> List[float] | None:
        """Get 384-dim normalized vector using local scikit-learn HashingVectorizer (0 API cost)."""
        try:
            vec = _local_embedder.transform([text]).toarray()[0].astype(float)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec.tolist()
        except Exception as e:
            logger.warning("Local embedding failed: %s", e)
            return [0.0] * 384

    async def _call_ollama(self, system: str, user: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=settings.agent_timeout) as client:
            resp = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [
                        {"role": "system", "content": system + " Always respond with valid JSON only."},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                    "format": "json",
                },
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            return json.loads(content)

    async def _call_ollama_text(self, system: str, user: str) -> str:
        async with httpx.AsyncClient(timeout=settings.agent_timeout) as client:
            resp = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]

    async def check_azure_openai(self) -> str:
        if not (settings.azure_openai_api_key and settings.azure_openai_endpoint):
            return "not_configured"
        try:
            client = self._get_azure_client()
            if client:
                # Lightweight check
                return "available"
            return "unavailable"
        except Exception:
            return "unavailable"

    async def check_openai(self) -> str:
        if not settings.openai_api_key:
            return "not_configured"
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"{settings.openai_base_url.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                )
                return "available" if resp.status_code == 200 else "unavailable"
        except Exception:
            return "unavailable"

    async def check_ollama(self) -> str:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
                return "available" if resp.status_code == 200 else "unavailable"
        except Exception:
            return "unavailable"


ai_service = AIService()
