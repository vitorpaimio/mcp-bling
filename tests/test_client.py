import httpx
import pytest

from mcp_bling import client as client_mod
from mcp_bling.client import BlingError
from mcp_bling.tokens import load_tokens, save_tokens


def test_sem_tokens_orienta_a_autorizar():
    c = client_mod.BlingClient()
    with pytest.raises(BlingError, match="mcp-bling-auth"):
        c.request("GET", "/produtos")


def test_envia_bearer_token(tokens_validos, cliente_com, resposta_json):
    vistos = []

    def handler(req):
        vistos.append(req.headers["Authorization"])
        return resposta_json({"data": []})

    cliente_com(handler).request("GET", "/produtos")
    assert vistos == ["Bearer token-valido"]


def test_remove_parametros_nulos(tokens_validos, cliente_com, resposta_json):
    vistos = []

    def handler(req):
        vistos.append(str(req.url))
        return resposta_json({"data": []})

    cliente_com(handler).request("GET", "/produtos", params={"pagina": 1, "nome": None})
    assert "pagina=1" in vistos[0]
    assert "nome" not in vistos[0]


def test_renova_token_expirado_antes_de_chamar(monkeypatch, cliente_com, resposta_json):
    save_tokens({"access_token": "velho", "refresh_token": "refresh-1", "expires_in": 0})

    def post_falso(url, **kwargs):
        assert kwargs["data"]["grant_type"] == "refresh_token"
        assert kwargs["data"]["refresh_token"] == "refresh-1"
        return resposta_json(
            {"access_token": "novo", "refresh_token": "refresh-2", "expires_in": 21600}
        )

    monkeypatch.setattr(client_mod.httpx, "post", post_falso)

    usados = []

    def handler(req):
        usados.append(req.headers["Authorization"])
        return resposta_json({"data": []})

    cliente_com(handler).request("GET", "/produtos")
    assert usados == ["Bearer novo"]
    # o refresh token rotaciona: o novo precisa ter sido persistido
    assert load_tokens()["refresh_token"] == "refresh-2"


def test_401_dispara_refresh_e_repete(tokens_validos, monkeypatch, cliente_com, resposta_json):
    monkeypatch.setattr(
        client_mod.httpx,
        "post",
        lambda url, **kw: resposta_json(
            {"access_token": "novo", "refresh_token": "r2", "expires_in": 21600}
        ),
    )
    respostas = [
        httpx.Response(401, json={"error": {"type": "invalid_token"}}),
        resposta_json({"data": [{"id": 1}]}),
    ]
    c = cliente_com(lambda req: respostas.pop(0))
    assert c.request("GET", "/produtos")["data"] == [{"id": 1}]
    assert respostas == []


def test_refresh_que_falha_pede_reautorizacao(tokens_validos, monkeypatch, cliente_com):
    monkeypatch.setattr(
        client_mod.httpx, "post", lambda url, **kw: httpx.Response(400, json={})
    )
    c = cliente_com(lambda req: httpx.Response(401, json={}))
    with pytest.raises(BlingError, match="mcp-bling-auth"):
        c.request("GET", "/produtos")


def test_429_tenta_de_novo_e_sucede(tokens_validos, monkeypatch, cliente_com, resposta_json):
    monkeypatch.setattr(client_mod.time, "sleep", lambda s: None)  # sem backoff real
    respostas = [
        httpx.Response(429, json={}),
        httpx.Response(429, json={}),
        resposta_json({"data": []}),
    ]
    c = cliente_com(lambda req: respostas.pop(0))
    assert c.request("GET", "/produtos") == {"data": []}
    assert respostas == []


def test_429_persistente_explica_limite_da_conta(tokens_validos, monkeypatch, cliente_com):
    monkeypatch.setattr(client_mod.time, "sleep", lambda s: None)
    c = cliente_com(lambda req: httpx.Response(429, json={}))
    with pytest.raises(BlingError, match="conta Bling inteira"):
        c.request("GET", "/produtos")


def test_403_explica_falta_de_escopo(tokens_validos, cliente_com):
    c = cliente_com(
        lambda req: httpx.Response(
            403, json={"error": {"type": "FORBIDDEN", "description": "higher privileges"}}
        )
    )
    with pytest.raises(BlingError, match="escopo"):
        c.request("GET", "/contatos")


def test_404_menciona_id_inexistente(tokens_validos, cliente_com):
    c = cliente_com(lambda req: httpx.Response(404, json={"error": {}}))
    with pytest.raises(BlingError, match="não encontrado"):
        c.request("GET", "/produtos/999")


def test_resposta_sem_corpo_vira_dicionario_vazio(tokens_validos, cliente_com):
    c = cliente_com(lambda req: httpx.Response(204))
    assert c.request("PATCH", "/pedidos/vendas/1/situacoes/9") == {}
