"""Servidor MCP (stdio) para a API v3 do Bling."""

from mcp.server.mcpserver import MCPServer

from .tools import catalogo, financeiro, fiscal, logistica, sistema, vendas
from .tools._modulo import registrar

mcp = MCPServer(
    "bling",
    instructions=(
        "Servidor MCP para o ERP Bling (API v3). Cada tool é um módulo do Bling e recebe "
        "um parâmetro `acao` — a descrição da tool lista as ações, os filtros e os campos "
        "de `dados` aceitos. Convenções gerais: listagens são paginadas (máx. 100 por "
        "página) e devolvem um resumo, com o registro completo na ação `obter`; datas em "
        "AAAA-MM-DD e intervalos de no máximo 1 ano; filtros de lista aceitam arrays. "
        "IDs de apoio saem de tools próprias: `situacoes` (ação vendas) para situação de "
        "pedido, `categorias_financeiras`, `contas_contabeis` (portadores) e "
        "`formas_pagamento` para o financeiro. Não há ações de exclusão, de propósito. "
        "Se as tools falharem por falta de autorização, o usuário deve rodar "
        "`uv run mcp-bling-auth` no projeto; se falharem com 403, falta habilitar o "
        "escopo do recurso no aplicativo cadastrado no Bling."
    ),
)

MODULOS = (
    *catalogo.MODULOS,
    *vendas.MODULOS,
    *financeiro.MODULOS,
    *fiscal.MODULOS,
    *logistica.MODULOS,
    *sistema.MODULOS,
)

registrar(mcp, *MODULOS)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
