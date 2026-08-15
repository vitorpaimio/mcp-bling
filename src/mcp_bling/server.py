"""Servidor MCP (stdio) para a API v3 do Bling."""

from mcp.server.mcpserver import MCPServer

from .tools import contatos, pedidos, produtos

mcp = MCPServer(
    "bling",
    instructions=(
        "Servidor MCP para o ERP Bling (API v3). Cobre produtos, estoque, pedidos de venda "
        "e contatos. As listagens retornam dados resumidos com paginação (máx. 100/página); "
        "use as tools obter_* para o registro completo. IDs de situação de pedido são "
        "descobertos com listar_situacoes_vendas. Se as tools falharem por falta de "
        "autorização, o usuário deve rodar `uv run mcp-bling-auth` no projeto."
    ),
)

produtos.register(mcp)
pedidos.register(mcp)
contatos.register(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
