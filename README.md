# mcp-bling

Servidor MCP para o **ERP Bling (API v3)**. Conecta o Bling ao Claude (ou a qualquer
cliente MCP) para consultar e cadastrar **produtos, estoque, pedidos de venda e contatos**
conversando em português.

Roda localmente via stdio: seus dados e credenciais não passam por nenhum servidor de
terceiros — o tráfego vai direto da sua máquina para a API do Bling.

```
"quantos pedidos entraram ontem?"
"qual o saldo de estoque da sacola boca de palhaço 40x50?"
"cadastra o cliente João Silva, CPF 123.456.789-00"
"muda o pedido 14003 para Atendido"
```

## Como usar este projeto

Este repositório é feito para ser **forkado**. Cada pessoa cria o próprio aplicativo
no Bling e usa as próprias credenciais — não existe servidor compartilhado nem chave
distribuída. Faça o fork, siga os quatro passos abaixo e está pronto.

### Pré-requisitos

- Conta ativa no Bling, com permissão de "Cadastro de aplicativos"
- [uv](https://docs.astral.sh/uv/) instalado (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Python 3.12+ (o `uv` instala sozinho se faltar)

### Passo 1 — criar o aplicativo no Bling

No Bling, vá em **Central de Extensões → Área do Integrador → Criar aplicativo** e
cadastre um aplicativo de visibilidade **privada**.

Preencha a **URL de redirecionamento** exatamente assim:

```
http://localhost:8730/callback
```

Marque os **escopos** conforme o que você pretende usar (veja a tabela em
[Escopos e o erro 403](#escopos-e-o-erro-403)). Para ter todas as ferramentas
funcionando, habilite: Produtos, Estoques, Depósitos, Pedidos de venda, Situações
e Contatos.

Ao salvar, o Bling mostra o **client_id** e o **client_secret**. Guarde os dois.

> ⚠️ Alterar os escopos depois **revoga todas as instalações** do aplicativo. Se você
> mexer nos escopos, vai precisar autorizar de novo (passo 3).

### Passo 2 — instalar

```bash
git clone https://github.com/vitorpaimio/mcp-bling.git
cd mcp-bling
uv sync
cp .env.example .env
```

Abra o `.env` e preencha `BLING_CLIENT_ID` e `BLING_CLIENT_SECRET` com o que o Bling
mostrou no passo 1.

### Passo 3 — autorizar

```bash
uv run mcp-bling-auth
```

O navegador abre na tela de autorização do Bling. Ao confirmar, os tokens são salvos
em `~/.config/mcp-bling/tokens.json` (permissão `600`, fora do repositório).

### Passo 4 — conectar ao Claude

**Claude Code:**

```bash
claude mcp add bling -- uv run --directory /caminho/para/mcp-bling mcp-bling
```

**Claude Desktop** — edite `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bling": {
      "command": "uv",
      "args": ["run", "--directory", "/caminho/para/mcp-bling", "mcp-bling"]
    }
  }
}
```

Para conferir se está tudo certo antes de plugar no Claude:

```bash
npx @modelcontextprotocol/inspector uv run mcp-bling
```

## Ferramentas

| Ferramenta | O que faz |
|---|---|
| `listar_produtos` | Lista produtos, com filtro por nome ou código (SKU) |
| `obter_produto` | Dados completos de um produto |
| `criar_produto` | Cadastra um produto |
| `atualizar_produto` | Altera campos de um produto |
| `obter_saldos_estoque` | Saldo físico e virtual, por produto e depósito |
| `listar_depositos` | Depósitos de estoque cadastrados |
| `criar_movimentacao_estoque` | Entrada, saída ou balanço de estoque |
| `listar_pedidos_venda` | Lista pedidos, com filtro por data, contato ou situação |
| `obter_pedido_venda` | Dados completos de um pedido (itens, parcelas, transporte) |
| `criar_pedido_venda` | Cria um pedido de venda |
| `alterar_situacao_pedido` | Muda a situação de um pedido |
| `listar_situacoes_vendas` | Situações disponíveis e seus IDs |
| `lancar_estoque_pedido` | Baixa o estoque dos itens de um pedido |
| `listar_contatos` | Lista clientes e fornecedores |
| `obter_contato` | Dados completos de um contato |
| `criar_contato` | Cadastra um contato |
| `atualizar_contato` | Altera campos de um contato |

Algumas decisões que valem saber:

- **Não existem ferramentas de exclusão.** Apagar produto, pedido ou contato só pela
  interface do Bling — é proposital, para o modelo não conseguir destruir dados.
- As listagens devolvem um **resumo** dos campos mais úteis, não o JSON inteiro. Para o
  registro completo, use as ferramentas `obter_*`.
- `atualizar_produto` e `atualizar_contato` fazem **busca, mesclagem e reenvio**, porque
  o `PUT` da API do Bling substitui o recurso inteiro. Sem isso, qualquer campo omitido
  seria apagado.

## Escopos e o erro 403

Se uma ferramenta responder **403 — "The request requires higher privileges than provided
by the access token"**, o aplicativo não tem o escopo daquele recurso. Habilite o escopo
no cadastro do aplicativo e **rode `uv run mcp-bling-auth` de novo** — mexer nos escopos
revoga as instalações e invalida os tokens atuais.

| Escopo no Bling | Ferramentas que dependem dele |
|---|---|
| Produtos | `listar_produtos`, `obter_produto`, `criar_produto`, `atualizar_produto` |
| Estoques | `obter_saldos_estoque`, `criar_movimentacao_estoque` |
| Depósitos | `listar_depositos` |
| Pedidos de venda | `listar_pedidos_venda`, `obter_pedido_venda`, `criar_pedido_venda`, `lancar_estoque_pedido` |
| Situações | `listar_situacoes_vendas`, `alterar_situacao_pedido` |
| Contatos | `listar_contatos`, `obter_contato`, `criar_contato`, `atualizar_contato` |

## Autenticação e limites

O Bling usa OAuth 2.0. O **access token vale 6 horas** e é renovado automaticamente pelo
servidor, sem você perceber. O **refresh token vale 30 dias** — passado esse prazo sem uso,
rode `uv run mcp-bling-auth` outra vez.

Os limites da API são de **3 requisições por segundo** e **120 mil por dia**, e valem para
a **conta Bling inteira** — não por aplicativo. Se você tem outras integrações rodando
(marketplace, ERP, automações), todas dividem o mesmo teto. O cliente já respeita o limite
por segundo e tenta de novo, com espera crescente, quando recebe 429.

## Solução de problemas

**"Nenhum token encontrado"** — falta autorizar: `uv run mcp-bling-auth`.

**"Não foi possível renovar o token"** — o refresh token passou dos 30 dias ou os escopos
do aplicativo mudaram. Autorize de novo com `uv run mcp-bling-auth`.

**403 em algumas ferramentas** — falta escopo. Veja a tabela acima.

**"A porta 8730 já está em uso"** — algum processo ocupou a porta. Libere-a, ou defina
outra em `BLING_CALLBACK_PORT` no `.env` — lembrando de cadastrar a mesma porta na URL de
redirecionamento do aplicativo no Bling, senão a autorização falha.

**O navegador não abriu** — o comando imprime a URL no terminal; abra na mão.

**429 mesmo devagar** — outra integração sua está consumindo o limite da conta.

## Segurança

O `.env` (com o client_secret) e os tokens ficam fora do controle de versão: o `.env`
está no `.gitignore` e os tokens moram em `~/.config/mcp-bling/`, nunca no repositório.
**Confira isso antes de publicar seu fork** — um `client_secret` vazado permite que
terceiros se passem pelo seu aplicativo.

Vale lembrar que este servidor dá ao modelo acesso de escrita ao seu ERP: ele pode criar
produtos, pedidos e contatos, e movimentar estoque. Não há ferramentas de exclusão, mas
convém revisar o que o modelo propõe antes de confirmar operações em uma conta de produção.

## Desenvolvimento

```bash
uv run pytest          # 28 testes, sem tocar na rede
```

Os testes mockam o HTTP e isolam os tokens em diretório temporário, então rodam sem
credenciais e sem risco de mexer na sua conta.

Estrutura:

```
src/mcp_bling/
├── server.py       # instancia o servidor MCP e registra as ferramentas
├── auth.py         # fluxo OAuth (comando mcp-bling-auth)
├── client.py       # HTTP: renovação de token, throttle, tradução de erros
├── tokens.py       # armazenamento local dos tokens
└── tools/          # as ferramentas, por módulo do Bling
```

## Referência da API

[`docs/api-bling-v3.md`](docs/api-bling-v3.md) reúne o que foi levantado da documentação
oficial durante a construção: fluxo OAuth, limites, endpoints e as armadilhas da API v3
(situações como entidades próprias, `PUT` que substitui o recurso, filtros de data
limitados a 1 ano, entre outras).

O Bling também mantém um **servidor MCP oficial hospedado** em `https://mcp.bling.com.br/mcp`,
documentado em [developer.bling.com.br/mcp-server](https://developer.bling.com.br/mcp-server).
Se você prefere não rodar nada localmente, ele é uma alternativa — este projeto existe para
quem quer controle total sobre quais ferramentas o modelo enxerga e como os dados são
resumidos.

## Licença

MIT — veja [LICENSE](LICENSE).
