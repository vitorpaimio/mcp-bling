"""Fluxo OAuth 2.0 (authorization code) do Bling.

Uso: `uv run mcp-bling-auth`. Abre o navegador na tela de autorização do Bling,
recebe o callback em http://localhost:8730/callback e salva os tokens.

Atenção: o `code` retornado pelo Bling expira em 1 minuto e é de uso único —
por isso a troca por tokens acontece imediatamente dentro do callback.
"""

import base64
import errno
import os
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from dotenv import load_dotenv

from .tokens import save_tokens, tokens_path

AUTHORIZE_URL = "https://bling.com.br/Api/v3/oauth/authorize"
TOKEN_URL = "https://api.bling.com.br/Api/v3/oauth/token"
PORTA_PADRAO = 8730


def callback_port() -> int:
    """Porta do servidor de callback. Configurável por BLING_CALLBACK_PORT.

    Se você mudar a porta, atualize também a URL de redirecionamento cadastrada
    no aplicativo do Bling — os dois valores precisam ser idênticos.
    """
    return int(os.environ.get("BLING_CALLBACK_PORT", PORTA_PADRAO))


def redirect_uri() -> str:
    return f"http://localhost:{callback_port()}/callback"


def basic_auth_header() -> str:
    client_id = os.environ.get("BLING_CLIENT_ID", "").strip()
    client_secret = os.environ.get("BLING_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise SystemExit(
            "BLING_CLIENT_ID e/ou BLING_CLIENT_SECRET não definidos.\n\n"
            "1. Crie um aplicativo no Bling: Central de Extensões -> Área do Integrador\n"
            f"2. Cadastre a URL de redirecionamento: {redirect_uri()}\n"
            "3. Copie `.env.example` para `.env` e preencha as duas credenciais.\n\n"
            "Veja o README para o passo a passo completo."
        )
    return "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()


def exchange_code(code: str) -> dict:
    resposta = httpx.post(
        TOKEN_URL,
        headers={
            "Authorization": basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "authorization_code", "code": code},
        timeout=30,
    )
    resposta.raise_for_status()
    return resposta.json()


def _pagina(titulo: str, mensagem: str) -> bytes:
    return (
        "<!doctype html><meta charset='utf-8'>"
        "<div style=\"font-family:system-ui;max-width:32rem;margin:4rem auto;text-align:center\">"
        f"<h2>{titulo}</h2><p>{mensagem}</p></div>"
    ).encode()


def main() -> None:
    load_dotenv()
    basic_auth_header()  # valida credenciais antes de abrir o navegador
    porta = callback_port()
    state = secrets.token_urlsafe(16)
    resultado: dict = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            partes = urlparse(self.path)
            if partes.path != "/callback":
                self.send_error(404)
                return
            params = parse_qs(partes.query)

            if params.get("state", [""])[0] != state:
                resultado["erro"] = "state divergente (possível CSRF) — fluxo abortado."
                self._responder("Erro de segurança", "State divergente. Tente novamente.")
                return
            if "error" in params:
                descricao = params.get("error_description", [params["error"][0]])[0]
                resultado["erro"] = f"autorização negada pelo Bling: {descricao}"
                self._responder("Autorização negada", descricao)
                return
            if "code" not in params:
                resultado["erro"] = "o Bling não retornou o parâmetro `code`."
                self._responder("Resposta inesperada", "Nenhum código recebido.")
                return

            try:
                # o code expira em 1 minuto e é de uso único: trocar agora
                resultado["tokens"] = exchange_code(params["code"][0])
                self._responder("Autorizado!", "Pode fechar esta aba e voltar ao terminal.")
            except httpx.HTTPStatusError as exc:
                resultado["erro"] = (
                    f"falha ao trocar o code por tokens (HTTP {exc.response.status_code}): "
                    f"{exc.response.text[:300]}"
                )
                self._responder("Falha na troca de tokens", "Veja o erro no terminal.")

        def _responder(self, titulo: str, mensagem: str):
            corpo = _pagina(titulo, mensagem)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def log_message(self, *args):
            pass  # silencia o log padrão do http.server

    url = AUTHORIZE_URL + "?" + urlencode(
        {
            "response_type": "code",
            "client_id": os.environ["BLING_CLIENT_ID"].strip(),
            "state": state,
        }
    )

    try:
        servidor = HTTPServer(("localhost", porta), CallbackHandler)
    except OSError as exc:
        if exc.errno in (errno.EADDRINUSE, errno.EACCES):
            raise SystemExit(
                f"A porta {porta} já está em uso. Feche o processo que a ocupa ou defina outra "
                "porta em BLING_CALLBACK_PORT — lembrando de atualizar a URL de redirecionamento "
                "no cadastro do aplicativo no Bling para o mesmo valor."
            ) from exc
        raise

    print(f"Aguardando autorização em {redirect_uri()} ...", flush=True)
    print(f"Se o navegador não abrir, acesse:\n\n  {url}\n", flush=True)
    threading.Timer(1.0, webbrowser.open, args=(url,)).start()

    while not resultado:
        servidor.handle_request()
    servidor.server_close()

    if "erro" in resultado:
        print(f"Erro: {resultado['erro']}", file=sys.stderr, flush=True)
        raise SystemExit(1)

    save_tokens(resultado["tokens"])
    print(f"Tokens salvos em {tokens_path()}", flush=True)
    print(
        "Access token válido por 6 h, renovado automaticamente pelo servidor. "
        "O refresh token dura 30 dias — depois disso, rode este comando de novo.",
        flush=True,
    )


if __name__ == "__main__":
    main()
