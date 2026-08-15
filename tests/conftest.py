import time

import httpx
import pytest

from mcp_bling import client as client_mod


@pytest.fixture(autouse=True)
def tokens_isolados(tmp_path, monkeypatch):
    """Isola os tokens em um diretório temporário para os testes nunca tocarem
    nos tokens reais do usuário em ~/.config/mcp-bling/."""
    monkeypatch.setenv("BLING_TOKENS_PATH", str(tmp_path / "tokens.json"))
    monkeypatch.setenv("BLING_CLIENT_ID", "id-de-teste")
    monkeypatch.setenv("BLING_CLIENT_SECRET", "segredo-de-teste")
    client_mod._client = None
    yield
    client_mod._client = None


@pytest.fixture
def tokens_validos():
    from mcp_bling.tokens import save_tokens

    save_tokens({"access_token": "token-valido", "refresh_token": "refresh-1", "expires_in": 21600})


@pytest.fixture
def cliente_com():
    """Fábrica de BlingClient cujo tráfego HTTP é atendido por um handler, não pela rede."""

    def fabricar(handler) -> client_mod.BlingClient:
        c = client_mod.BlingClient()
        c._http = httpx.Client(
            base_url=client_mod.BASE_URL, transport=httpx.MockTransport(handler)
        )
        c._throttle = lambda: None  # dispensa a espera de 0,35 s entre chamadas
        return c

    return fabricar


@pytest.fixture
def resposta_json():
    def fabricar(dados: dict, status: int = 200) -> httpx.Response:
        return httpx.Response(status, json=dados)

    return fabricar
