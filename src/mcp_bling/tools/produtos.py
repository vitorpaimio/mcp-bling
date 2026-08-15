"""Tools MCP: produtos, estoque e depósitos."""

from mcp.server.mcpserver import MCPServer

from ..client import get_client


def _resumo_produto(p: dict) -> dict:
    return {
        "id": p.get("id"),
        "nome": p.get("nome"),
        "codigo": p.get("codigo"),
        "preco": p.get("preco"),
        "tipo": p.get("tipo"),
        "situacao": p.get("situacao"),
        "formato": p.get("formato"),
        "saldoVirtualTotal": (p.get("estoque") or {}).get("saldoVirtualTotal"),
    }


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    def listar_produtos(
        pagina: int = 1,
        limite: int = 100,
        nome: str | None = None,
        codigo: str | None = None,
    ) -> dict:
        """Lista produtos do Bling (resumido). Filtros opcionais por nome (busca parcial)
        e codigo (SKU exato). Máximo de 100 por página; use `pagina` para paginar."""
        data = get_client().request(
            "GET",
            "/produtos",
            params={"pagina": pagina, "limite": limite, "nome": nome, "codigo": codigo},
        )
        produtos = [_resumo_produto(p) for p in data.get("data", [])]
        return {"pagina": pagina, "quantidade": len(produtos), "produtos": produtos}

    @mcp.tool()
    def obter_produto(id_produto: int) -> dict:
        """Retorna todos os dados de um produto pelo seu ID Bling."""
        return get_client().request("GET", f"/produtos/{id_produto}")

    @mcp.tool()
    def criar_produto(
        nome: str,
        preco: float | None = None,
        codigo: str | None = None,
        tipo: str = "P",
        formato: str = "S",
        situacao: str = "A",
        unidade: str | None = None,
        dados_extras: dict | None = None,
    ) -> dict:
        """Cria um produto no Bling. tipo: "P" (produto) ou "S" (serviço); formato: "S" (simples),
        "V" (com variações) ou "E" (com composição); situacao: "A" (ativo) ou "I" (inativo).
        Campos adicionais da API (descricaoCurta, gtin, pesoBruto, dimensoes, ...) vão em
        `dados_extras` e são mesclados no corpo enviado."""
        body = {
            "nome": nome,
            "tipo": tipo,
            "formato": formato,
            "situacao": situacao,
            "preco": preco,
            "codigo": codigo,
            "unidade": unidade,
        }
        body = {k: v for k, v in body.items() if v is not None}
        body.update(dados_extras or {})
        return get_client().request("POST", "/produtos", json=body)

    @mcp.tool()
    def atualizar_produto(id_produto: int, dados: dict) -> dict:
        """Atualiza um produto: busca os dados atuais, mescla as chaves de `dados` por cima
        (ex.: {"preco": 99.9, "situacao": "I"}) e reenvia via PUT (a API substitui o recurso
        inteiro, por isso a mesclagem)."""
        atual = get_client().request("GET", f"/produtos/{id_produto}").get("data", {})
        atual.pop("id", None)
        atual.update(dados)
        return get_client().request("PUT", f"/produtos/{id_produto}", json=atual)

    @mcp.tool()
    def obter_saldos_estoque(
        ids_produtos: list[int],
        id_deposito: int | None = None,
    ) -> dict:
        """Retorna os saldos de estoque (físico e virtual) dos produtos informados,
        em todos os depósitos ou apenas no depósito indicado."""
        path = f"/estoques/saldos/{id_deposito}" if id_deposito else "/estoques/saldos"
        return get_client().request("GET", path, params={"idsProdutos[]": ids_produtos})

    @mcp.tool()
    def listar_depositos() -> dict:
        """Lista os depósitos de estoque cadastrados no Bling."""
        return get_client().request("GET", "/depositos")

    @mcp.tool()
    def criar_movimentacao_estoque(
        id_produto: int,
        id_deposito: int,
        operacao: str,
        quantidade: float,
        preco: float | None = None,
        custo: float | None = None,
        observacoes: str | None = None,
    ) -> dict:
        """Cria uma movimentação de estoque. operacao: "E" (entrada), "S" (saída) ou
        "B" (balanço — define o saldo absoluto)."""
        body = {
            "produto": {"id": id_produto},
            "deposito": {"id": id_deposito},
            "operacao": operacao,
            "quantidade": quantidade,
            "preco": preco,
            "custo": custo,
            "observacoes": observacoes,
        }
        return get_client().request(
            "POST", "/estoques", json={k: v for k, v in body.items() if v is not None}
        )
