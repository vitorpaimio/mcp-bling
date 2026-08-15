import asyncio
import json
from datetime import date

import httpx
import pytest

from mcp_bling import client as client_mod
from mcp_bling.client import BlingError
from mcp_bling.server import MODULOS, mcp
from mcp_bling.tools._comum import validar_intervalo

TOOLS_ESPERADAS = {
    # catálogo
    "produtos", "produtos_variacoes", "produtos_estruturas", "produtos_fornecedores",
    "produtos_lojas", "categorias_produtos", "grupos_produtos", "estoques", "depositos",
    # comercial
    "pedidos_venda", "pedidos_compra", "propostas_comerciais", "contatos", "vendedores",
    "canais_venda", "categorias_lojas",
    # financeiro
    "contas_receber", "contas_pagar", "categorias_financeiras", "contas_contabeis",
    "formas_pagamento", "borderos",
    # fiscal
    "nfe", "nfce", "nfse", "naturezas_operacoes",
    # logística
    "logisticas", "logisticas_servicos", "logisticas_etiquetas", "logisticas_objetos",
    "logisticas_remessas",
    # apoio
    "situacoes", "situacoes_transicoes", "campos_customizados", "contratos",
    "ordens_producao", "empresas", "notificacoes",
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


# -- registro e declaração dos módulos ------------------------------------


def test_todas_as_tools_registradas():
    tools = asyncio.run(mcp.list_tools())
    assert {t.name for t in tools} == TOOLS_ESPERADAS


def test_toda_tool_descreve_suas_acoes():
    """A descrição é o que o modelo lê para escolher a ação e os parâmetros."""
    for tool in asyncio.run(mcp.list_tools()):
        assert "Ações (parâmetro `acao`)" in tool.description, tool.name
        assert len(tool.description) > 80, tool.name


def test_nenhuma_acao_exclui_registros():
    """Não existem ações de exclusão, de propósito: apagar só pela interface do Bling."""
    for modulo in MODULOS:
        for acao in modulo.acoes:
            assert acao.metodo != "DELETE", f"{modulo.nome}.{acao.nome}"


def test_acoes_sao_coerentes():
    nomes = [m.nome for m in MODULOS]
    assert len(nomes) == len(set(nomes))
    for modulo in MODULOS:
        assert modulo.recurso.startswith("/")
        for acao in modulo.acoes:
            assert acao.metodo in {"GET", "POST", "PUT", "PATCH"}
            assert not acao.caminho.startswith("/"), f"{modulo.nome}.{acao.nome}"
            # `mesclar` refaz um PUT em cima do registro atual: precisa do id no caminho
            assert not acao.mesclar or "{id}" in acao.caminho


# -- erros de uso, respondidos antes de gastar requisição ------------------


def _nunca_chamado(req):
    raise AssertionError(f"não deveria chamar a API: {req.url}")


def test_acao_inexistente_lista_as_disponiveis(tokens_validos, chamar_tool):
    with pytest.raises(Exception, match="listar, obter, criar"):
        chamar_tool("produtos", {"acao": "deletar"}, _nunca_chamado)


def test_filtro_inexistente_lista_os_aceitos(tokens_validos, chamar_tool):
    with pytest.raises(Exception, match="Filtros aceitos"):
        chamar_tool(
            "produtos", {"acao": "listar", "filtros": {"nomeDoProduto": "x"}}, _nunca_chamado
        )


def test_acao_que_exige_id_avisa(tokens_validos, chamar_tool):
    with pytest.raises(Exception, match="exige o parâmetro `id`"):
        chamar_tool("produtos", {"acao": "obter"}, _nunca_chamado)


def test_acao_que_exige_corpo_avisa(tokens_validos, chamar_tool):
    with pytest.raises(Exception, match="exige `dados`"):
        chamar_tool("produtos", {"acao": "criar"}, _nunca_chamado)


def test_intervalo_maior_que_um_ano_e_recusado_antes_da_chamada(tokens_validos, chamar_tool):
    """A API devolveria 400; validar localmente economiza uma requisição."""
    with pytest.raises(Exception, match="1 ano"):
        chamar_tool(
            "pedidos_venda",
            {"acao": "listar", "filtros": {"dataInicial": "2024-01-01",
                                           "dataFinal": "2026-01-01"}},
            _nunca_chamado,
        )


def test_intervalo_de_ate_um_ano_e_aceito():
    validar_intervalo("2026-01-01", "2026-12-31")


def test_intervalo_parcial_nao_valida():
    validar_intervalo("2026-01-01", None)
    validar_intervalo(None, None)


def test_data_malformada_vira_erro_explicado():
    with pytest.raises(BlingError, match="AAAA-MM-DD"):
        validar_intervalo("01/01/2026", "31/12/2026")


# -- montagem das requisições ---------------------------------------------


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
    texto = chamar_tool("produtos", {"acao": "listar"}, lambda req: resposta_json(bruto))
    assert '"saldoVirtualTotal": 7' in texto and '"quantidade": 1' in texto
    assert "campo longo" not in texto


def test_filtro_de_lista_vai_com_sufixo_de_array(tokens_validos, chamar_tool, resposta_json):
    urls = []

    def handler(req):
        urls.append(str(req.url))
        return resposta_json({"data": []})

    chamar_tool(
        "pedidos_venda", {"acao": "listar", "filtros": {"idsSituacoes": [9, 12]}}, handler
    )
    assert "idsSituacoes%5B%5D=9" in urls[0] and "idsSituacoes%5B%5D=12" in urls[0]


def test_criar_movimentacao_envia_o_corpo_informado(tokens_validos, chamar_tool, resposta_json):
    corpos = []

    def handler(req):
        assert req.url.path.endswith("/estoques")
        corpos.append(json.loads(req.content))
        return resposta_json({"data": {"id": 99}})

    dados = {
        "produto": {"id": 5}, "deposito": {"id": 7}, "operacao": "E", "quantidade": 3,
    }
    chamar_tool("estoques", {"acao": "criar_movimentacao", "dados": dados}, handler)
    assert corpos[0] == dados


def test_atualizar_produto_mescla_antes_do_put(tokens_validos, chamar_tool, resposta_json):
    """O PUT do Bling substitui o recurso inteiro, então a ação `atualizar` precisa
    buscar, mesclar e reenviar tudo — senão os campos omitidos seriam apagados."""
    chamadas = []

    def handler(req):
        chamadas.append((req.method, json.loads(req.content) if req.content else None))
        if req.method == "GET":
            return resposta_json(
                {"data": {"id": 1, "nome": "Antigo", "preco": 10, "unidade": "UN"}}
            )
        return resposta_json({"data": {"id": 1}})

    chamar_tool("produtos", {"acao": "atualizar", "id": 1, "dados": {"preco": 99}}, handler)
    metodo, corpo = chamadas[1]
    assert metodo == "PUT"
    assert corpo["preco"] == 99  # alterado
    assert corpo["nome"] == "Antigo" and corpo["unidade"] == "UN"  # preservados
    assert "id" not in corpo


def test_alterar_situacao_de_pedido_usa_os_dois_ids(tokens_validos, chamar_tool):
    """O PATCH de situação leva o ID do pedido e o da situação no caminho, e não tem corpo."""
    caminhos = []

    def handler(req):
        caminhos.append(req.url.path)
        return httpx.Response(204)

    chamar_tool(
        "pedidos_venda",
        {"acao": "alterar_situacao", "id": 42, "id_secundario": 9},
        handler,
    )
    assert caminhos[0].endswith("/pedidos/vendas/42/situacoes/9")


def test_acao_que_exige_id_secundario_avisa(tokens_validos, chamar_tool):
    with pytest.raises(Exception, match="id_secundario"):
        chamar_tool("pedidos_venda", {"acao": "alterar_situacao", "id": 42}, _nunca_chamado)


def test_situacoes_de_vendas_encontra_o_modulo(tokens_validos, chamar_tool, resposta_json):
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

    assert "Atendido" in chamar_tool("situacoes", {"acao": "vendas"}, handler)


# -- financeiro -----------------------------------------------------------


def test_listar_contas_receber_resume_traduz_situacao_e_soma(
    tokens_validos, chamar_tool, resposta_json
):
    urls = []

    def handler(req):
        urls.append(str(req.url))
        return resposta_json(
            {
                "data": [
                    {"id": 1, "situacao": 1, "vencimento": "2026-09-10", "valor": 100.5,
                     "contato": {"id": 7, "nome": "Cliente", "numeroDocumento": "000"}},
                    {"id": 2, "situacao": 2, "vencimento": "2026-09-11", "valor": 49.5,
                     "contato": {"id": 8, "nome": "Outro"}},
                ]
            }
        )

    texto = chamar_tool(
        "contas_receber",
        {"acao": "listar", "filtros": {"situacoes": [1], "tipoFiltroData": "V",
                                       "dataInicial": "2026-09-01",
                                       "dataFinal": "2026-09-30"}},
        handler,
    )
    assert '"valor_total_da_pagina": 150.0' in texto
    assert '"situacaoNome": "em aberto"' in texto and '"situacaoNome": "recebido"' in texto
    assert '"000"' not in texto  # do contato só saem id e nome
    assert "situacoes%5B%5D=1" in urls[0] and "tipoFiltroData=V" in urls[0]


def test_contas_pagar_tem_filtros_de_data_proprios(tokens_validos, chamar_tool, resposta_json):
    """Contas a pagar não aceita `tipoFiltroData`: cada tipo tem seu par de parâmetros."""
    urls = []

    def handler(req):
        urls.append(str(req.url))
        return resposta_json({"data": []})

    chamar_tool(
        "contas_pagar",
        {"acao": "listar", "filtros": {"dataPagamentoInicial": "2026-09-01",
                                       "dataPagamentoFinal": "2026-09-30"}},
        handler,
    )
    assert "dataPagamentoInicial=2026-09-01" in urls[0]
    with pytest.raises(Exception, match="Filtros aceitos"):
        chamar_tool(
            "contas_pagar", {"acao": "listar", "filtros": {"tipoFiltroData": "V"}},
            _nunca_chamado,
        )


def test_baixar_conta_usa_a_data_de_hoje_por_padrao(
    tokens_validos, chamar_tool, resposta_json
):
    corpos = []

    def handler(req):
        assert req.url.path.endswith("/contas/receber/42/baixar")
        corpos.append(json.loads(req.content))
        return resposta_json({"bordero": {"id": 5}})

    chamar_tool(
        "contas_receber",
        {"acao": "baixar", "id": 42, "dados": {"portador": {"id": 3},
                                               "categoria": {"id": 9}}},
        handler,
    )
    assert corpos[0] == {
        "portador": {"id": 3},
        "categoria": {"id": 9},
        "data": date.today().isoformat(),
        "usarDataVencimento": False,
    }
