"""
Unified LLM Provider
=====================
A single LLMClient that abstracts over three backends:

  - "openrouter"  →  Any model on OpenRouter via OpenAI-compatible API
  - "local"       →  Ollama (local self-hosted models)
  - "gemini"      →  Google Gemini (optional fallback)

Switch backends by setting LLM_PROVIDER in your .env file.
No code changes required when swapping providers.
"""

from __future__ import annotations

from app.config.settings import settings


import contextvars
import json
import threading

_thread_local = threading.local()

# Global circuit breaker to prevent latency penalties during rate limits
_openrouter_cooldown_until = 0.0

# Contextvar to temporarily override LLM provider for the current thread/request context
provider_override: contextvars.ContextVar[str | None] = contextvars.ContextVar("provider_override", default=None)


class LLMClient:
    """
    Provider-agnostic LLM client.

    Usage:
        from app.llm.provider import llm
        response = llm.chat(system_prompt="You are...", user_prompt="Question?")
    """

    def get_last_model_used(self) -> str:
        """Returns the actual model name used during the last chat() call on this thread."""
        return getattr(_thread_local, "last_model_used", "unknown")

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = False,
        stream: bool = False,
        history: list[dict] = None,
    ) -> str | typing.Generator[str, None, None]:
        
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})

        override = provider_override.get()
        provider = override.lower() if override else settings.LLM_PROVIDER.lower()

        if provider == "openrouter":
            return self._call_openrouter(messages, temperature, max_tokens, json_mode, stream)
        elif provider == "gemini":
            return self._call_gemini(messages, temperature, stream)
        else:
            # Default: local Ollama
            return self._call_ollama(messages, temperature, max_tokens, json_mode, stream)

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    def _call_openrouter(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        json_mode: bool = False,
        stream: bool = False,
    ):
        """
        OpenRouter via the OpenAI-compatible API.

        Uses `openrouter/free` by default — OpenRouter's built-in free-models router
        that automatically selects and switches between available free models.
        """
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            max_retries=3,   # auto-retry on 429 / 5xx with exponential backoff
        )

        kwargs = dict(
            model=settings.OPENROUTER_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        import time
        from openai import RateLimitError
        global _openrouter_cooldown_until
        
        kwargs["model"] = settings.OPENROUTER_MODEL
        last_err = None
        
        # Circuit Breaker: If we recently hit a rate limit, skip the API calls and go straight to local
        if time.time() < _openrouter_cooldown_until:
            print("[LLM] OpenRouter is on cooldown. Fast-failing to Local Ollama.")
            return self._run_local_fallback(messages, temperature, max_tokens, json_mode, stream)
            
        for attempt in range(2):  # Try 2 times for the primary model
            try:
                response = client.chat.completions.create(**kwargs)
                _thread_local.last_model_used = settings.OPENROUTER_MODEL
                
                if stream:
                    def openrouter_generator():
                        for chunk in response:
                            if not chunk.choices:
                                continue
                            delta = chunk.choices[0].delta.content
                            if delta:
                                yield delta
                    return openrouter_generator()
                else:
                    return response.choices[0].message.content.strip()
            except RateLimitError as e:
                _openrouter_cooldown_until = time.time() + 60  # Cooldown for 60 seconds
                last_err = e
                print(f"[LLM] OpenRouter model '{settings.OPENROUTER_MODEL}' hit rate limit. (Attempt {attempt+1}/2)")
                if attempt == 0:
                    time.sleep(1)

        # If OpenRouter failed, fallback to local ollama immediately!
        print("[LLM] OpenRouter rate limit exhausted. Falling back to Local Ollama immediately.")
        return self._run_local_fallback(messages, temperature, max_tokens, json_mode, stream, last_err)
        
    def _run_local_fallback(self, messages, temperature, max_tokens, json_mode, stream, last_err=None):
        try:
            import ollama
            # Find an available local model
            models_data = ollama.list().get("models", [])
            local_models = []
            for m in models_data:
                # Handle both dict and object responses just in case
                if isinstance(m, dict):
                    local_models.append(m.get("model", m.get("name", "")))
                else:
                    local_models.append(getattr(m, "model", getattr(m, "name", "")))
                    
            if local_models:
                # Prefer settings.LLM_MODEL, otherwise use the first one
                fallback_local_model = settings.LLM_MODEL if settings.LLM_MODEL in local_models else local_models[0]
                print(f"[LLM] Using local model: {fallback_local_model}")
                client = ollama.Client(host=settings.OLLAMA_BASE_URL)
                response = client.chat(
                    model=fallback_local_model,
                    messages=messages,
                    options={
                        "temperature": temperature,
                        "num_ctx": 8192,
                        "num_predict": max_tokens,
                    },
                    format="json" if json_mode else "",
                    stream=stream,
                )
                _thread_local.last_model_used = f"Local Fallback ({fallback_local_model})"
                
                if stream:
                    def ollama_fallback_generator():
                        for chunk in response:
                            delta = chunk.get("message", {}).get("content", "")
                            if delta:
                                yield delta
                    return ollama_fallback_generator()
                else:
                    return response["message"]["content"].strip()
            else:
                print("[LLM] No local Ollama models found. Cannot fallback.")
        except Exception as ollama_err:
            print(f"[LLM] Local Ollama fallback failed: {ollama_err}")

        # If ollama fallback also fails or no models, raise the original rate limit error or generic error
        if last_err:
            raise last_err
        raise Exception("OpenRouter on cooldown and Local Ollama fallback failed.")

    def _call_gemini(
        self,
        messages: list[dict],
        temperature: float,
        stream: bool = False,
    ):
        """Google Gemini via the google-genai SDK."""
        from google import genai
        from google.genai import types
        from app.utils.rate_limiter import call_with_retry

        # Reconstruct the user prompt from the messages
        # Google genai prefers single string or specific format, we will just join them
        combined_prompt = ""
        sys_prompt = ""
        for m in messages:
            if m["role"] == "system":
                sys_prompt += m["content"] + "\n"
            else:
                combined_prompt += f"{m['role'].capitalize()}: {m['content']}\n"
                
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        if stream:
            response = call_with_retry(
                client.models.generate_content_stream,
                model=settings.LLM_MODEL,
                contents=combined_prompt.strip(),
                config=types.GenerateContentConfig(
                    system_instruction=sys_prompt.strip(),
                    temperature=temperature,
                ),
            )
            _thread_local.last_model_used = settings.LLM_MODEL
            def gemini_generator():
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            return gemini_generator()
        else:
            response = call_with_retry(
                client.models.generate_content,
                model=settings.LLM_MODEL,
                contents=combined_prompt.strip(),
                config=types.GenerateContentConfig(
                    system_instruction=sys_prompt.strip(),
                    temperature=temperature,
                ),
            )
            _thread_local.last_model_used = settings.LLM_MODEL
            return response.text.strip()

    def _call_ollama(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        json_mode: bool = False,
        stream: bool = False,
    ):
        """Local Ollama inference."""
        import ollama

        client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        response = client.chat(
            model=settings.LLM_MODEL,
            messages=messages,
            options={
                "temperature": temperature,
                "num_ctx": 8192,
                "num_predict": max_tokens,
            },
            format="json" if json_mode else "",
            stream=stream,
        )
        _thread_local.last_model_used = settings.LLM_MODEL
        
        if stream:
            def ollama_generator():
                for chunk in response:
                    delta = chunk.get("message", {}).get("content", "")
                    if delta:
                        yield delta
            return ollama_generator()
        else:
            return response["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere instead of creating clients
# ---------------------------------------------------------------------------
llm = LLMClient()
