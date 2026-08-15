"""Tools MCP: pedidos de venda e situações."""

from datetime import date

from mcp.server.mcpserver import MCPServer

from ..client import BlingError, get_client


def _resumo_pedido(p: dict) -> dict:
    return {
        "id": p.get("id"),
        "numero": p.get("numero"),
        "data": p.get("data"),
        "total": p.get("total"),
        "contato": {
            "id": (p.get("contato") or {}).get("id"),
            "nome": (p.get("contato") or {}).get("nome"),
        },
        "situacao": p.get("situacao"),
        "numeroLoja": p.get("numeroLoja"),
    }


def _validar_intervalo(data_inicial: str | None, data_final: str | None) -> None:
    if not (data_inicial and data_final):
        return
    inicio, fim = date.fromisoformat(data_inicial), date.fromisoformat(data_final)
    if (fim - inicio).days > 365:
        raise BlingError(
            "A API do Bling rejeita filtros de data com intervalo maior que 1 ano. "
            "Divida a consulta em períodos menores."
        )


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    def listar_pedidos_venda(
        pagina: int = 1,
        limite: int = 100,
        data_inicial: str | None = None,
        data_final: str | None = None,
        id_contato: int | None = None,
        id_situacao: int | None = None,
        numero: int | None = None,
    ) -> dict:
        """Lista pedidos de venda (resumido). Datas no formato AAAA-MM-DD (intervalo máximo
        de 1 ano). id_situacao pode ser descoberto com a tool listar_situacoes_vendas."""
        _validar_intervalo(data_inicial, data_final)
        data = get_client().request(
            "GET",
            "/pedidos/vendas",
            params={
                "pagina": pagina,
                "limite": limite,
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "idContato": id_contato,
                "idsSituacoes[]": id_situacao,
                "numero": numero,
            },
        )
        pedidos = [_resumo_pedido(p) for p in data.get("data", [])]
        return {"pagina": pagina, "quantidade": len(pedidos), "pedidos": pedidos}

    @mcp.tool()
    def obter_pedido_venda(id_pedido: int) -> dict:
        """Retorna todos os dados de um pedido de venda (itens, parcelas, transporte, ...)."""
        return get_client().request("GET", f"/pedidos/vendas/{id_pedido}")

    @mcp.tool()
    def criar_pedido_venda(
        id_contato: int,
        itens: list[dict],
        data: str | None = None,
        observacoes: str | None = None,
        dados_extras: dict | None = None,
    ) -> dict:
        """Cria um pedido de venda. Cada item de `itens` precisa de: descricao (str),
        quantidade (número), valor (unitário); opcionalmente produto: {"id": ...}, codigo e
        unidade. `data` no formato AAAA-MM-DD (padrão: hoje). Campos adicionais da API
        (parcelas, transporte, vendedor, ...) vão em `dados_extras`."""
        body = {
            "contato": {"id": id_contato},
            "itens": itens,
            "data": data,
            "observacoes": observacoes,
        }
        body = {k: v for k, v in body.items() if v is not None}
        body.update(dados_extras or {})
        return get_client().request("POST", "/pedidos/vendas", json=body)

    @mcp.tool()
    def alterar_situacao_pedido(id_pedido: int, id_situacao: int) -> dict:
        """Altera a situação de um pedido de venda. Use listar_situacoes_vendas para
        descobrir o id_situacao desejado (ex.: Em aberto, Atendido, Cancelado)."""
        get_client().request(
            "PATCH", f"/pedidos/vendas/{id_pedido}/situacoes/{id_situacao}"
        )
        return {"ok": True, "id_pedido": id_pedido, "id_situacao": id_situacao}

    @mcp.tool()
    def listar_situacoes_vendas() -> dict:
        """Lista as situações disponíveis para pedidos de venda (id, nome e cor de cada uma).
        Necessário antes de alterar a situação de um pedido."""
        client = get_client()
        modulos = client.request("GET", "/situacoes/modulos").get("data", [])
        modulo_vendas = next(
            (m for m in modulos if "venda" in (m.get("descricao") or m.get("nome") or "").lower()),
            None,
        )
        if modulo_vendas is None:
            return {"modulos_disponiveis": modulos}
        situacoes = client.request(
            "GET", f"/situacoes/modulos/{modulo_vendas['id']}"
        ).get("data", [])
        return {
            "modulo": modulo_vendas,
            "situacoes": [
                {"id": s.get("id"), "nome": s.get("nome"), "cor": s.get("cor")}
                for s in situacoes
            ],
        }

    @mcp.tool()
    def lancar_estoque_pedido(id_pedido: int, id_deposito: int | None = None) -> dict:
        """Lança o estoque dos itens de um pedido de venda (baixa as quantidades). Se
        id_deposito for omitido, usa o depósito padrão configurado no Bling."""
        path = f"/pedidos/vendas/{id_pedido}/lancar-estoque"
        if id_deposito:
            path += f"/{id_deposito}"
        get_client().request("POST", path)
        return {"ok": True, "id_pedido": id_pedido}
