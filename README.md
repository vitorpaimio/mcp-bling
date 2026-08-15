# mcp-bling

Servidor MCP local (stdio) em Python para a **API v3 do Bling**, cobrindo **produtos,
estoque, pedidos de venda e contatos**. Referência de estudo da API em
[`docs/api-bling-v3.md`](docs/api-bling-v3.md).

> O Bling também oferece um MCP oficial remoto (`https://mcp.bling.com.br/mcp`).
> Este projeto é a alternativa local, com controle total das ferramentas.

## Pré-requisitos

1. Conta Bling ativa.
2. Aplicativo criado na **Central de Extensões → Área do Integrador** com:
   - **URL de redirecionamento**: `http://localhost:8730/callback`
   - **Escopos**: produtos, estoques, depósitos, pedidos de venda, situações, contatos
3. [uv](https://docs.astral.sh/uv/) instalado.

## Setup

```bash
cp .env.example .env   # preencha BLING_CLIENT_ID e BLING_CLIENT_SECRET
uv sync
uv run mcp-bling-auth  # abre o navegador para autorizar; salva os tokens
```

Os tokens ficam em `~/.config/mcp-bling/tokens.json` (permissão 600). O access token
dura 6 h e é renovado automaticamente pelo servidor; o refresh token dura 30 dias —
expirando, basta rodar `mcp-bling-auth` de novo.

## Registrar no Claude Code

```bash
claude mcp add bling -- uv run --directory /Users/paim/mcp-bling mcp-bling
```

Ou teste interativamente com o MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run mcp-bling
```

## Ferramentas

| Módulo | Tools |
|---|---|
| Produtos/estoque | `listar_produtos`, `obter_produto`, `criar_produto`, `atualizar_produto`, `obter_saldos_estoque`, `listar_depositos`, `criar_movimentacao_estoque` |
| Pedidos de venda | `listar_pedidos_venda`, `obter_pedido_venda`, `criar_pedido_venda`, `alterar_situacao_pedido`, `listar_situacoes_vendas`, `lancar_estoque_pedido` |
| Contatos | `listar_contatos`, `obter_contato`, `criar_contato`, `atualizar_contato` |

## Escopos: erro 403

Se uma tool retornar **403 — "The request requires higher privileges than provided by
the access token"**, o aplicativo cadastrado no Bling não tem o escopo daquele recurso.
Habilite o escopo correspondente no cadastro do app e **rode `uv run mcp-bling-auth`
novamente** — alterar escopos revoga todas as instalações, invalidando os tokens atuais.

Mapa de escopo por tool:

| Escopo no app | Tools afetadas |
|---|---|
| Produtos | `listar_produtos`, `obter_produto`, `criar_produto`, `atualizar_produto` |
| Estoques | `obter_saldos_estoque`, `criar_movimentacao_estoque` |
| Depósitos | `listar_depositos` |
| Pedidos de venda | `listar_pedidos_venda`, `obter_pedido_venda`, `criar_pedido_venda`, `lancar_estoque_pedido` |
| Situações | `listar_situacoes_vendas`, `alterar_situacao_pedido` |
| Contatos | `listar_contatos`, `obter_contato`, `criar_contato`, `atualizar_contato` |

Decisões de design:

- Listagens retornam JSON **resumido** + paginação (`pagina`, `limite` ≤ 100).
- **Sem tools de DELETE** (segurança).
- Throttle de ~3 req/s e retry com backoff em 429 (limites são **por conta Bling**).
- Filtros de data validados localmente (a API rejeita intervalos > 1 ano).
- `atualizar_*` faz GET + merge + PUT, porque o PUT da API substitui o recurso inteiro.
