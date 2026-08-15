"""Armazenamento local dos tokens OAuth do Bling."""

import json
import os
import time
from pathlib import Path

TOKENS_PATH = Path.home() / ".config" / "mcp-bling" / "tokens.json"


def save_tokens(payload: dict) -> None:
    """Salva a resposta do /oauth/token, anotando o instante de expiração."""
    data = {
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
        # margem de 60 s para nunca usar um token no limite da validade
        "expires_at": time.time() + payload.get("expires_in", 21600) - 60,
    }
    TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_PATH.write_text(json.dumps(data, indent=2))
    os.chmod(TOKENS_PATH, 0o600)


def load_tokens() -> dict | None:
    if not TOKENS_PATH.exists():
        return None
    return json.loads(TOKENS_PATH.read_text())
