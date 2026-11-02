"""
Step 4: talk to the language model.

Both providers get the same two inputs:
  system -> standing instructions (how to behave, how to cite)
  user   -> the question plus the retrieved document chunks
and return plain text. The rest of the code does not care which one is used,
so switching provider is a one-line change in .env (LLM_PROVIDER).

Privacy note for the client: with Ollama, the model runs on your own machine
and no document text leaves it. The Claude API does not train on API data by
default, but the text is sent to Anthropic's servers.
"""

import requests

import config


def generate(system: str, user: str) -> str:
    if config.LLM_PROVIDER == "ollama":
        return _ollama(system, user)
    if config.LLM_PROVIDER == "anthropic":
        return _anthropic(system, user)
    raise ValueError(f"Unknown LLM_PROVIDER: {config.LLM_PROVIDER!r} (use 'ollama' or 'anthropic')")


def _ollama(system: str, user: str) -> str:
    response = requests.post(
        f"{config.OLLAMA_URL}/api/chat",
        json={
            "model": config.OLLAMA_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "options": {"temperature": 0},  # 0 = no creativity, stick to the facts
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def _anthropic(system: str, user: str) -> str:
    import anthropic  # imported here so Ollama users don't need the package configured

    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("Set ANTHROPIC_API_KEY in your .env file to use the Claude API.")
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in message.content if block.type == "text").strip()
