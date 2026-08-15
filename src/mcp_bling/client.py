"""Cliente HTTP da API v3 do Bling.

Responsabilidades:
- Bearer token com renovação automática (access 6 h / refresh 30 dias, rotativo);
- throttle de ~3 req/s e retry com backoff em 429 (limites são por conta Bling);
- tradução dos erros da API em mensagens acionáveis para o modelo.
"""

import threading
import time

import httpx
from dotenv import load_dotenv

from .tokens import load_tokens, save_tokens

BASE_URL = "https://api.bling.com.br/Api/v3"
TOKEN_URL = f"{BASE_URL}/oauth/token"
MIN_INTERVAL = 0.35  # segundos entre requisições (limite da conta: 3 req/s)
MAX_429_RETRIES = 3

SEM_TOKENS = (
    "Nenhum token encontrado. O usuário precisa executar `uv run mcp-bling-auth` "
    "no diretório do projeto para autorizar o acesso ao Bling."
)
REAUTORIZAR = (
    "Não foi possível renovar o token. Isso acontece quando o refresh token expira "
    "(30 dias) ou quando os escopos do aplicativo foram alterados no Bling, o que revoga "
    "as instalações. O usuário precisa executar `uv run mcp-bling-auth` novamente."
)


class BlingError(Exception):
    """Erro de negócio/autenticação já formatado para o modelo."""


class BlingClient:
    def __init__(self):
        load_dotenv()
        self._http = httpx.Client(base_url=BASE_URL, timeout=30)
        self._throttle_lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._last_request = 0.0
        self._tokens = load_tokens()

    # -- autenticação ------------------------------------------------------

    def _require_tokens(self) -> dict:
        if self._tokens is None:
            self._tokens = load_tokens()
        if self._tokens is None:
            raise BlingError(SEM_TOKENS)
        return self._tokens

    def _refresh(self, token_recusado: str | None = None) -> None:
        from .auth import basic_auth_header

        with self._refresh_lock:
            # Outro processo (ou thread) pode ter renovado enquanto esperávamos o lock; como o
            # refresh token rotaciona, reaproveitar o do disco evita invalidar a sessão dele.
            # Só aproveitamos se o token em disco for realmente OUTRO: um 401 em token que ainda
            # parece válido (o Bling revoga na hora quando os escopos mudam) precisa renovar de
            # fato, senão o cliente ficaria repetindo o mesmo token recusado para sempre.
            do_disco = load_tokens()
            if (
                do_disco
                and do_disco.get("expires_at", 0) > time.time()
                and do_disco.get("access_token") != token_recusado
            ):
                self._tokens = do_disco
                return

            tokens = do_disco or self._require_tokens()
            resposta = httpx.post(
                TOKEN_URL,
                headers={
                    "Authorization": basic_auth_header(),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": tokens["refresh_token"],
                },
                timeout=30,
            )
            if resposta.status_code != 200:
                raise BlingError(REAUTORIZAR)
            save_tokens(resposta.json())
            self._tokens = load_tokens()

    def _access_token(self) -> str:
        tokens = self._require_tokens()
        if time.time() >= tokens.get("expires_at", 0):
            self._refresh()
            tokens = self._tokens
        return tokens["access_token"]

    # -- requisições -------------------------------------------------------

    def _throttle(self) -> None:
        with self._throttle_lock:
            espera = self._last_request + MIN_INTERVAL - time.monotonic()
            if espera > 0:
                time.sleep(espera)
            self._last_request = time.monotonic()

    def request(self, method: str, path: str, *, params: dict | None = None,
                json: dict | None = None) -> dict:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        ja_renovou = False

        for tentativa in range(MAX_429_RETRIES + 1):
            self._throttle()
            token = self._access_token()
            resposta = self._http.request(
                method,
                path,
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {token}"},
            )
            if resposta.status_code == 401 and not ja_renovou:
                ja_renovou = True
                self._refresh(token_recusado=token)
                continue
            if resposta.status_code == 429 and tentativa < MAX_429_RETRIES:
                time.sleep(2**tentativa)  # 1s, 2s, 4s
                continue
            break

        if resposta.status_code >= 400:
            raise BlingError(self._formatar_erro(resposta, method, path))
        if resposta.status_code == 204 or not resposta.content:
            return {}
        return resposta.json()

    @staticmethod
    def _formatar_erro(resposta: httpx.Response, method: str, path: str) -> str:
        try:
            erro = resposta.json().get("error", {})
            detalhe = erro.get("description") or erro.get("message") or resposta.text
            tipo = erro.get("type", "")
        except ValueError:
            detalhe, tipo = resposta.text[:500], ""

        prefixo = f"Bling API {resposta.status_code} em {method} {path}"
        if resposta.status_code == 403:
            return (
                f"{prefixo}: acesso negado ({detalhe}). O aplicativo cadastrado no Bling não tem "
                "o escopo deste recurso. O usuário precisa habilitá-lo na Central de Extensões e, "
                "como alterar escopos revoga as instalações, rodar `uv run mcp-bling-auth` depois."
            )
        if resposta.status_code == 429:
            return (
                f"{prefixo}: limite de requisições da conta excedido mesmo após as tentativas "
                "automáticas. O limite (3 req/s, 120 mil/dia) vale para a conta Bling inteira, "
                "incluindo outras integrações. Aguarde e tente de novo."
            )
        if resposta.status_code == 404:
            return f"{prefixo}: recurso não encontrado. Confira se o ID informado existe."
        return f"{prefixo} [{tipo}]: {detalhe}"


_client: BlingClient | None = None


def get_client() -> BlingClient:
    global _client
    if _client is None:
        _client = BlingClient()
    return _client
