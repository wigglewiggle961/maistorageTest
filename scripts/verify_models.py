#!/usr/bin/env python3
"""Verify all required Ollama models are available and responsive.

Usage:
    python scripts/verify_models.py

Exit codes:
    0 — All models verified successfully
    1 — One or more models failed or Ollama is unreachable
"""
import sys
from pathlib import Path

# Allow importing from src/ without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import os

import ollama
from config import EMBED_MODEL, LLM_MODEL, OLLAMA_BASE_URL, VISION_MODEL

# Configure ollama client to use the configured base URL
os.environ.setdefault("OLLAMA_HOST", OLLAMA_BASE_URL)

# Build unique model set (LLM_MODEL and VISION_MODEL may be the same model)
_ALL_MODELS: dict[str, str] = {
    LLM_MODEL: "chat",        # gemma4:e4b — primary LLM with native vision
    EMBED_MODEL: "embed",     # nomic-embed-text — embeddings
    VISION_MODEL: "chat",     # gemma4:e4b — vision at ingest time (same model)
}
# Deduplicate: if LLM_MODEL == VISION_MODEL, verify it once as 'chat'
REQUIRED_MODELS: dict[str, str] = _ALL_MODELS


def check_model_pulled(model_name: str, available_names: list[str]) -> bool:
    """Check if model is pulled (handles 'model:tag' vs 'model:latest' variants)."""
    base_name = model_name.split(":")[0]
    return any(name.startswith(base_name) for name in available_names)


def verify_chat_model(model_name: str) -> tuple[bool, str]:
    """Ping a chat model with a minimal message."""
    try:
        result = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": "ping"}],
        )
        # SDK 0.4+: result is a ChatResponse object; .message is a Message object
        msg = getattr(result, "message", None) or result.get("message")
        if msg:
            return True, f"  ✓ {model_name} — chat response OK"
        return False, f"  ✗ {model_name} — empty response"
    except Exception as exc:
        return False, f"  ✗ {model_name} — {exc}"


def verify_embed_model(model_name: str) -> tuple[bool, str]:
    """Ping an embedding model with a test string."""
    try:
        result = ollama.embed(model=model_name, input="test")
        # SDK 0.4+: result is an EmbedResponse object; .embeddings is a list of lists
        embeddings = getattr(result, "embeddings", None) or result.get("embeddings", [])
        if embeddings and len(embeddings[0]) > 0:
            dims = len(embeddings[0])
            return True, f"  ✓ {model_name} — embedding OK ({dims} dims)"
        return False, f"  ✗ {model_name} — empty embedding response"
    except Exception as exc:
        return False, f"  ✗ {model_name} — {exc}"


def main() -> int:
    print(f"Ollama endpoint: {OLLAMA_BASE_URL}")
    print("Checking Ollama connection...\n")

    # Step 1: Connect and list models
    try:
        models_response = ollama.list()
        # SDK 0.4+: ListResponse object with .models list of Model objects (.model attr)
        # Fallback to dict-style for older SDK versions
        raw_models = getattr(models_response, "models", None)
        if raw_models is not None:
            available_names = [
                getattr(m, "model", None) or getattr(m, "name", None) or m.get("name", "")
                for m in raw_models
            ]
        else:
            available_names = [m["name"] for m in models_response.get("models", [])]
        print(f"  Found {len(available_names)} model(s) pulled on this machine.")
    except Exception as exc:
        print(f"  ERROR: Cannot connect to Ollama at {OLLAMA_BASE_URL}")
        print(f"  {exc}")
        print("\n  Make sure Ollama is running:")
        print("  > ollama serve")
        return 1

    # Step 2: Check each required model
    print("\nVerifying required models:")
    print("-" * 48)
    all_passed = True

    for model_name, model_type in REQUIRED_MODELS.items():
        # Check if pulled first
        if not check_model_pulled(model_name, available_names):
            print(f"  ✗ {model_name} — NOT PULLED")
            print(f"    Run: ollama pull {model_name}")
            all_passed = False
            continue

        # Run model-type-specific ping
        if model_type == "embed":
            ok, msg = verify_embed_model(model_name)
        else:
            ok, msg = verify_chat_model(model_name)

        print(msg)
        if not ok:
            all_passed = False

    # Step 3: Summary
    print("-" * 48)
    if all_passed:
        print("\nAll models verified. Environment ready.\n")
        return 0
    else:
        print("\nSome models failed. Fix the issues above and re-run.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
