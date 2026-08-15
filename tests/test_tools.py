import asyncio
import json

import httpx
import pytest

from mcp_bling import client as client_mod
from mcp_bling.client import BlingError
from mcp_bling.server import mcp
from mcp_bling.tools.pedidos import _validar_intervalo

TOOLS_ESPERADAS = {
    "listar_produtos", "obter_produto", "criar_produto", "atualizar_produto",
    "obter_saldos_estoque", "listar_depositos", "criar_movimentacao_estoque",
    "listar_pedidos_venda", "obter_pedido_venda", "criar_pedido_venda",
    "alterar_situacao_pedido", "listar_situacoes_vendas", "lancar_estoque_pedido",
    "listar_contatos", "obter_contato", "criar_contato", "atualizar_contato",
}


@pytest.fixture
def chamar_tool(cliente_com):
    """Executa uma tool do servidor MCP com o HTTP do Bling mockado.

    Injeta pelo singleton do módulo em vez de monkeypatchar `get_client`: as tools
    importam a função direto (`from ..client import get_client`), então substituir o
    atributo do módulo não alcançaria a referência que elas já resolveram.
    """

    def executar(nome: str, args: dict, handler) -> str:
        client_mod._client = cliente_com(handler)
        resultado = asyncio.run(mcp.call_tool(nome, args))
        return resultado.content[0].text

    return executar


def test_todas_as_tools_registradas():
    tools = asyncio.run(mcp.list_tools())
    assert {t.name for t in tools} == TOOLS_ESPERADAS


def test_toda_tool_tem_descricao():
    """A descrição é o que o modelo lê para decidir quando usar a tool."""
    for tool in asyncio.run(mcp.list_tools()):
        assert tool.description and len(tool.description) > 30, tool.name


def test_intervalo_de_ate_um_ano_e_aceito():
    _validar_intervalo("2026-01-01", "2026-12-31")


def test_intervalo_maior_que_um_ano_e_recusado_antes_da_chamada():
    """A API devolveria 400; validar localmente economiza uma requisição."""
    with pytest.raises(BlingError, match="1 ano"):
        _validar_intervalo("2024-01-01", "2026-01-01")


def test_intervalo_parcial_nao_valida():
    _validar_intervalo("2026-01-01", None)
    _validar_intervalo(None, None)


def test_listar_produtos_resume_a_resposta(tokens_validos, chamar_tool, resposta_json):
    bruto = {
        "data": [
            {
                "id": 1, "nome": "Sacola", "codigo": "SKU1", "preco": 10.0,
                "tipo": "P", "situacao": "A", "formato": "S",
                "estoque": {"saldoVirtualTotal": 7},
                "descricaoCurta": "campo longo que nao deve aparecer no resumo",
            }
        ]
    }
    texto = chamar_tool("listar_produtos", {}, lambda req: resposta_json(bruto))
    assert '"saldoVirtualTotal": 7' in texto and '"quantidade": 1' in texto
    assert "campo longo" not in texto


def test_criar_movimentacao_monta_corpo_aninhado(tokens_validos, chamar_tool, resposta_json):
    corpos = []

    def handler(req):
        corpos.append(json.loads(req.content))
        return resposta_json({"data": {"id": 99}})

    chamar_tool(
        "criar_movimentacao_estoque",
        {"id_produto": 5, "id_deposito": 7, "operacao": "E", "quantidade": 3},
        handler,
    )
    assert corpos[0] == {
        "produto": {"id": 5},
        "deposito": {"id": 7},
        "operacao": "E",
        "quantidade": 3,
    }


def test_atualizar_produto_mescla_antes_do_put(tokens_validos, chamar_tool, resposta_json):
    """O PUT do Bling substitui o recurso inteiro, então a tool precisa buscar,
    mesclar e reenviar tudo — senão os campos omitidos seriam apagados."""
    chamadas = []

    def handler(req):
        chamadas.append((req.method, json.loads(req.content) if req.content else None))
        if req.method == "GET":
            return resposta_json(
                {"data": {"id": 1, "nome": "Antigo", "preco": 10, "unidade": "UN"}}
            )
        return resposta_json({"data": {"id": 1}})

    chamar_tool("atualizar_produto", {"id_produto": 1, "dados": {"preco": 99}}, handler)
    metodo, corpo = chamadas[1]
    assert metodo == "PUT"
    assert corpo["preco"] == 99  # alterado
    assert corpo["nome"] == "Antigo" and corpo["unidade"] == "UN"  # preservados
    assert "id" not in corpo


def test_listar_situacoes_encontra_o_modulo_de_vendas(tokens_validos, chamar_tool, resposta_json):
    def handler(req):
        if req.url.path.endswith("/situacoes/modulos"):
            return resposta_json(
                {
                    "data": [
                        {"id": 575904, "nome": "PedidosCompra", "descricao": "Pedidos de Compra"},
                        {"id": 98310, "nome": "Vendas", "descricao": "Pedidos de Venda"},
                    ]
                }
            )
        # precisa consultar o módulo de vendas, não o de compras
        assert "98310" in str(req.url)
        return resposta_json({"data": [{"id": 9, "nome": "Atendido", "cor": "#3FB57A"}]})

    assert "Atendido" in chamar_tool("listar_situacoes_vendas", {}, handler)


def test_alterar_situacao_confirma_sem_corpo(tokens_validos, chamar_tool):
    """O PATCH de situação responde sem corpo; a tool devolve uma confirmação explícita."""
    texto = chamar_tool(
        "alterar_situacao_pedido",
        {"id_pedido": 42, "id_situacao": 9},
        lambda req: httpx.Response(204),
    )
    assert '"ok": true' in texto.lower() and '"id_pedido": 42' in texto
