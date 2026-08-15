"""Armazenamento local dos tokens OAuth do Bling.

Os tokens ficam fora do repositório (em ~/.config/mcp-bling/) justamente para que
um fork publicado no GitHub nunca corra o risco de versionar credenciais.
"""

import json
import os
import tempfile
import time
from pathlib import Path


def tokens_path() -> Path:
    """Caminho do arquivo de tokens. Configurável por BLING_TOKENS_PATH."""
    override = os.environ.get("BLING_TOKENS_PATH")
    if override:
        return Path(override).expanduser()
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "mcp-bling" / "tokens.json"


def save_tokens(payload: dict) -> None:
    """Salva a resposta do /oauth/token, anotando o instante de expiração.

    A escrita é atômica: se o processo morrer no meio, o arquivo antigo continua
    íntegro em vez de virar um JSON truncado.
    """
    data = {
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
        # margem de 60 s para nunca usar um token no limite da validade
        "expires_at": time.time() + payload.get("expires_in", 21600) - 60,
    }
    destino = tokens_path()
    destino.parent.mkdir(parents=True, exist_ok=True)

    fd, temporario = tempfile.mkstemp(dir=destino.parent, prefix=".tokens-", suffix=".tmp")
    try:
        os.write(fd, json.dumps(data, indent=2).encode())
        os.close(fd)
        os.chmod(temporario, 0o600)
        os.replace(temporario, destino)
    except BaseException:
        os.unlink(temporario)
        raise


def load_tokens() -> dict | None:
    caminho = tokens_path()
    if not caminho.exists():
        return None
    try:
        return json.loads(caminho.read_text())
    except json.JSONDecodeError:
        return None
