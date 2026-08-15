"""Cliente HTTP da API v3 do Bling.

Responsabilidades:
- Bearer token com renovação automática (access 6 h / refresh 30 dias, com rotação);
- throttle de ~3 req/s e retry com backoff em 429 (limites por conta Bling);
- tradução dos erros da API em mensagens acionáveis para o LLM.
"""

import threading
import time

import httpx
from dotenv import load_dotenv

from .tokens import load_tokens, save_tokens

BASE_URL = "https://api.bling.com.br/Api/v3"
TOKEN_URL = f"{BASE_URL}/oauth/token"
MIN_INTERVAL = 0.35  # segundos entre requisições (limite: 3 req/s por conta)
MAX_429_RETRIES = 3


class BlingError(Exception):
    """Erro de negócio/autenticação já formatado para o LLM."""


class BlingClient:
    def __init__(self):
        load_dotenv()
        self._http = httpx.Client(base_url=BASE_URL, timeout=30)
        self._lock = threading.Lock()
        self._last_request = 0.0
        self._tokens = load_tokens()

    # -- autenticação ------------------------------------------------------

    def _require_tokens(self) -> dict:
        if self._tokens is None:
            self._tokens = load_tokens()
        if self._tokens is None:
            raise BlingError(
                "Nenhum token encontrado. Peça ao usuário para executar `uv run mcp-bling-auth` "
                "no diretório do projeto para autorizar o acesso ao Bling."
            )
        return self._tokens

    def _refresh(self) -> None:
        from .auth import basic_auth_header

        tokens = self._require_tokens()
        response = httpx.post(
            TOKEN_URL,
            headers={
                "Authorization": basic_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]},
            timeout=30,
        )
        if response.status_code != 200:
            raise BlingError(
                "Falha ao renovar o token (o refresh token dura 30 dias). Peça ao usuário para "
                "executar `uv run mcp-bling-auth` novamente para reautorizar o acesso."
            )
        payload = response.json()
        save_tokens(payload)  # o refresh token rotaciona a cada renovação
        self._tokens = load_tokens()

    def _access_token(self) -> str:
        tokens = self._require_tokens()
        if time.time() >= tokens.get("expires_at", 0):
            self._refresh()
            tokens = self._tokens
        return tokens["access_token"]

    # -- requisições -------------------------------------------------------

    def _throttle(self) -> None:
        with self._lock:
            wait = self._last_request + MIN_INTERVAL - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()

    def request(self, method: str, path: str, *, params: dict | None = None,
                json: dict | None = None) -> dict:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        refreshed = False
        for attempt in range(MAX_429_RETRIES + 1):
            self._throttle()
            response = self._http.request(
                method,
                path,
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {self._access_token()}"},
            )
            if response.status_code == 401 and not refreshed:
                refreshed = True
                self._refresh()
                continue
            if response.status_code == 429 and attempt < MAX_429_RETRIES:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
                continue
            break

        if response.status_code >= 400:
            raise BlingError(self._format_error(response, method, path))
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()

    @staticmethod
    def _format_error(response: httpx.Response, method: str, path: str) -> str:
        try:
            error = response.json().get("error", {})
            detail = error.get("description") or error.get("message") or response.text
            error_type = error.get("type", "")
        except ValueError:
            detail, error_type = response.text[:500], ""

        prefix = f"Bling API {response.status_code} em {method} {path}"
        if response.status_code == 403:
            return (
                f"{prefix}: acesso negado ({detail}). O aplicativo registrado no Bling "
                "provavelmente não tem o escopo deste recurso — o usuário precisa habilitá-lo "
                "na Central de Extensões (atenção: alterar escopos revoga as instalações)."
            )
        if response.status_code == 429:
            return f"{prefix}: limite de requisições da conta excedido mesmo após retries. Aguarde e tente de novo."
        return f"{prefix} [{error_type}]: {detail}"


_client: BlingClient | None = None


def get_client() -> BlingClient:
    global _client
    if _client is None:
        _client = BlingClient()
    return _client
