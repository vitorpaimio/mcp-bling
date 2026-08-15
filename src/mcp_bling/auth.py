"""Fluxo OAuth 2.0 (authorization code) do Bling.

Uso: `uv run mcp-bling-auth`. Abre o navegador na tela de autorização do Bling,
recebe o callback em http://localhost:8730/callback e salva os tokens em
~/.config/mcp-bling/tokens.json.

Atenção: o `code` retornado pelo Bling expira em 1 minuto e é de uso único —
a troca por tokens acontece imediatamente no callback.
"""

import base64
import os
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from dotenv import load_dotenv

from .tokens import TOKENS_PATH, save_tokens

AUTHORIZE_URL = "https://bling.com.br/Api/v3/oauth/authorize"
TOKEN_URL = "https://api.bling.com.br/Api/v3/oauth/token"
CALLBACK_PORT = 8730


def basic_auth_header() -> str:
    client_id = os.environ.get("BLING_CLIENT_ID", "")
    client_secret = os.environ.get("BLING_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise SystemExit(
            "Defina BLING_CLIENT_ID e BLING_CLIENT_SECRET no ambiente ou no arquivo .env "
            "(veja .env.example)."
        )
    raw = f"{client_id}:{client_secret}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def exchange_code(code: str) -> dict:
    response = httpx.post(
        TOKEN_URL,
        headers={
            "Authorization": basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "authorization_code", "code": code},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    load_dotenv()
    state = secrets.token_urlsafe(16)
    result: dict = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != "/callback":
                self.send_error(404)
                return
            params = parse_qs(parsed.query)
            if params.get("state", [""])[0] != state:
                result["error"] = "state divergente (possível CSRF) — fluxo abortado."
                self._respond("Erro: state divergente. Feche esta aba e tente novamente.")
                return
            if "error" in params:
                result["error"] = params["error"][0]
                self._respond(f"Autorização negada: {result['error']}")
                return
            try:
                # o code expira em 1 minuto: trocar imediatamente
                result["tokens"] = exchange_code(params["code"][0])
                self._respond("Autorizado com sucesso! Pode fechar esta aba.")
            except httpx.HTTPStatusError as exc:
                result["error"] = f"falha na troca do code: {exc.response.text}"
                self._respond("Falha ao trocar o code por tokens. Veja o terminal.")

        def _respond(self, message: str):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h2>Bling MCP</h2><p>{message}</p>".encode())

        def log_message(self, *args):
            pass

    auth_url = AUTHORIZE_URL + "?" + urlencode(
        {
            "response_type": "code",
            "client_id": os.environ.get("BLING_CLIENT_ID", ""),
            "state": state,
        }
    )
    basic_auth_header()  # valida credenciais antes de abrir o navegador

    server = HTTPServer(("localhost", CALLBACK_PORT), CallbackHandler)
    print(f"Aguardando autorização em http://localhost:{CALLBACK_PORT}/callback ...")
    print(f"Se o navegador não abrir, acesse:\n\n  {auth_url}\n")
    threading.Timer(1.0, webbrowser.open, args=(auth_url,)).start()

    while not result:
        server.handle_request()
    server.server_close()

    if "error" in result:
        print(f"Erro: {result['error']}", file=sys.stderr)
        raise SystemExit(1)

    save_tokens(result["tokens"])
    print(f"Tokens salvos em {TOKENS_PATH}")
    print("Access token válido por 6 h; renovação automática pelo servidor MCP (refresh de 30 dias).")


if __name__ == "__main__":
    main()
