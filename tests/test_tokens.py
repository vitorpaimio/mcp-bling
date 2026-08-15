import json
import os
import time
from pathlib import Path

from mcp_bling.tokens import load_tokens, save_tokens, tokens_path


def test_salva_e_recarrega():
    save_tokens({"access_token": "abc", "refresh_token": "xyz", "expires_in": 21600})
    tokens = load_tokens()
    assert tokens["access_token"] == "abc"
    assert tokens["refresh_token"] == "xyz"


def test_expires_at_tem_margem_de_seguranca():
    """A margem de 60 s evita usar um token que expira no meio da requisição."""
    save_tokens({"access_token": "a", "refresh_token": "b", "expires_in": 21600})
    restante = load_tokens()["expires_at"] - time.time()
    assert 21500 < restante <= 21540


def test_arquivo_e_privado():
    save_tokens({"access_token": "a", "refresh_token": "b", "expires_in": 3600})
    assert oct(tokens_path().stat().st_mode)[-3:] == "600"


def test_sem_arquivo_retorna_none():
    assert load_tokens() is None


def test_json_corrompido_nao_quebra():
    caminho = tokens_path()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("{ isto nao e json")
    assert load_tokens() is None


def test_escrita_e_atomica_sem_deixar_lixo():
    save_tokens({"access_token": "a", "refresh_token": "b", "expires_in": 3600})
    save_tokens({"access_token": "c", "refresh_token": "d", "expires_in": 3600})
    assert load_tokens()["access_token"] == "c"
    temporarios = list(tokens_path().parent.glob(".tokens-*.tmp"))
    assert temporarios == []


def test_respeita_variavel_de_ambiente(monkeypatch, tmp_path):
    destino = tmp_path / "outro" / "t.json"
    monkeypatch.setenv("BLING_TOKENS_PATH", str(destino))
    save_tokens({"access_token": "a", "refresh_token": "b", "expires_in": 3600})
    assert destino.exists()
