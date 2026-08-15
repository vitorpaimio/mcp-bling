# mcp-bling

Servidor MCP para o **ERP Bling (API v3)**, com **cobertura completa da API**: catálogo e
estoque, vendas e compras, financeiro, notas fiscais, logística, produção e cadastros de
apoio — 38 ferramentas, 178 ações, conversando em português.

Roda localmente via stdio: seus dados e credenciais não passam por nenhum servidor de
terceiros — o tráfego vai direto da sua máquina para a API do Bling.

```
"quantos pedidos entraram ontem?"
"qual o saldo de estoque da sacola boca de palhaço 40x50?"
"cadastra o cliente João Silva, CPF 123.456.789-00"
"muda o pedido 14003 para Atendido"
"quanto tenho a receber vencendo esta semana?"
"gera a NF-e do pedido 14003"
"quais pedidos de compra ainda não chegaram?"
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

Marque os **escopos** conforme o que você pretende usar — a tabela em
[Escopos e o erro 403](#escopos-e-o-erro-403) mostra o de-para com as ferramentas.
Como o servidor cobre a API inteira, o mais simples é habilitar todos os escopos; se
preferir restringir, marque só os módulos que você vai usar e as ferramentas dos demais
responderão 403.

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

A cobertura é a API v3 inteira: **38 ferramentas, uma por módulo do Bling, somando 178
ações**. Cada ferramenta recebe um parâmetro `acao` — expor um endpoint por ferramenta
deixaria a lista impraticável para o modelo (e cara: são ~150 endpoints).

A assinatura é sempre a mesma:

```jsonc
// pedidos_venda
{
  "acao": "listar",                 // qual endpoint do módulo
  "id": null,                       // registro alvo, quando o caminho pede
  "id_secundario": null,            // segundo ID (situação, depósito, componente)
  "pagina": 1, "limite": 100,
  "filtros": {"dataInicial": "2026-08-01", "dataFinal": "2026-08-31"},
  "dados": null                     // corpo do POST/PUT/PATCH
}
```

A descrição de cada ferramenta lista as ações com método, caminho, filtros aceitos e
campos de `dados` — o modelo não precisa adivinhar, e filtro ou ação inválidos viram um
erro que já diz quais existem, sem gastar requisição.

| Ferramenta | Módulo | Ações |
|---|---|---|
| `produtos` | Produtos e serviços do catálogo | listar, obter, criar, atualizar, alterar_situacao, alterar_situacao_varios |
| `produtos_variacoes` | Grade de variações (cor, tamanho) | obter, renomear_atributo, gerar_combinacoes |
| `produtos_estruturas` | Composição de produtos (formato E) | obter, atualizar, adicionar_componente, alterar_componente |
| `produtos_fornecedores` | Vínculo produto ↔ fornecedor | listar, obter, criar, atualizar |
| `produtos_lojas` | Vínculo produto ↔ loja/canal | listar, obter, criar, atualizar |
| `categorias_produtos` | Categorias do catálogo | listar, obter, criar, atualizar |
| `grupos_produtos` | Grupos de produtos | listar, obter, criar, atualizar |
| `estoques` | Saldos e movimentações | saldos, saldos_do_deposito, criar_movimentacao, atualizar_movimentacao |
| `depositos` | Depósitos de estoque | listar, obter, criar, atualizar |
| `pedidos_venda` | Pedidos de venda e lançamentos derivados | listar, obter, criar, atualizar, alterar_situacao, lancar_estoque, lancar_estoque_no_deposito, estornar_estoque, lancar_contas, estornar_contas, gerar_nfe, gerar_nfce |
| `pedidos_compra` | Pedidos de compra a fornecedores | listar, obter, criar, atualizar, alterar_situacao, lancar_estoque, estornar_estoque, lancar_contas, estornar_contas |
| `propostas_comerciais` | Orçamentos | listar, obter, criar, atualizar, alterar_situacao |
| `contatos` | Clientes, fornecedores, transportadoras | listar, obter, tipos_do_contato, tipos_cadastrados, consumidor_final, criar, atualizar, alterar_situacao, alterar_situacao_varios |
| `vendedores` | Vendedores | listar, obter |
| `canais_venda` | Lojas, marketplaces e integrações | listar, obter, tipos |
| `categorias_lojas` | De-para de categorias por loja | listar, obter, criar, atualizar |
| `contas_receber` | Contas a receber e recebimentos | listar, obter, boletos, criar, atualizar, baixar |
| `contas_pagar` | Contas a pagar e pagamentos | listar, obter, criar, atualizar, baixar |
| `categorias_financeiras` | Categorias de receitas e despesas | listar, obter |
| `contas_contabeis` | Portadores (caixa, bancos, cartões) | listar, obter |
| `formas_pagamento` | Formas de pagamento | listar, obter, criar, atualizar |
| `borderos` | Borderôs gerados pelas baixas | obter |
| `nfe` | Notas fiscais eletrônicas | listar, obter, criar, atualizar, enviar, lancar_contas, estornar_contas, lancar_estoque, lancar_estoque_no_deposito, estornar_estoque |
| `nfce` | Notas de consumidor | listar, obter, criar, atualizar, enviar, lancar_contas, estornar_contas, lancar_estoque, lancar_estoque_no_deposito, estornar_estoque |
| `nfse` | Notas de serviço e suas configurações | listar, obter, criar, enviar, cancelar, configuracoes, atualizar_configuracoes |
| `naturezas_operacoes` | CFOP e regras fiscais | listar, obter_tributacao |
| `logisticas` | Transportadoras e integrações de envio | listar, obter, criar, atualizar, remessas |
| `logisticas_servicos` | Serviços de envio (PAC, SEDEX, ...) | listar, obter, criar, atualizar, alterar_situacao |
| `logisticas_etiquetas` | Etiquetas de envio | gerar |
| `logisticas_objetos` | Volumes de uma remessa | obter, criar, atualizar |
| `logisticas_remessas` | Remessas e rastreio | obter, criar, atualizar |
| `situacoes` | Situações por módulo do Bling | vendas, modulos, do_modulo, acoes_do_modulo, transicoes_do_modulo, obter, criar, atualizar |
| `situacoes_transicoes` | Automações de mudança de status | obter, criar, atualizar |
| `campos_customizados` | Campos customizados dos cadastros | modulos, tipos, do_modulo, obter, criar, atualizar, alterar_situacao |
| `contratos` | Contratos de recorrência | listar, obter, criar, atualizar |
| `ordens_producao` | Ordens de produção | listar, obter, criar, atualizar, alterar_situacao, gerar_sob_demanda |
| `empresas` | Dados da empresa conectada | dados_basicos |
| `notificacoes` | Notificações da conta | listar, confirmar_leitura |

Algumas decisões que valem saber:

- **Não existem ações de exclusão.** Nenhum `DELETE` é exposto: apagar produto, pedido,
  conta ou nota só pela interface do Bling — é proposital, para o modelo não conseguir
  destruir dados. Um teste garante que nenhuma ação use o verbo.
- **Ficaram de fora** dois módulos da API por decisão, não por esquecimento: `usuarios`
  (recuperar e redefinir senha) e `homologacao` (certificação de aplicativos no Bling).
- As listagens devolvem um **resumo** dos campos mais úteis, não o JSON inteiro. Para o
  registro completo, use a ação `obter`.
- A ação `atualizar` de `produtos` e `contatos` faz **busca, mesclagem e reenvio**, porque
  o `PUT` da API do Bling substitui o recurso inteiro. Sem isso, qualquer campo omitido
  seria apagado. Nos demais módulos, `atualizar` envia o corpo como veio — reenvie o
  registro inteiro.
- As listagens financeiras somam os valores da página em `valor_total_da_pagina` — a API
  não devolve totalizador e a pergunta quase sempre é "quanto".
- Baixar uma conta gera um **borderô** (o lançamento no caixa/banco). O Bling costuma
  exigir portador e categoria na baixa: os IDs saem de `contas_contabeis` e
  `categorias_financeiras`.
- `situacoes` tem a ação `vendas` como atalho: situação é uma entidade com ID próprio por
  módulo, e sem ela o modelo precisaria de duas chamadas só para descobrir o ID de
  "Atendido".
- Criar uma nota fiscal **não** a transmite. Emitir é a ação `enviar`, e é irreversível.

## Escopos e o erro 403

Se uma ferramenta responder **403 — "The request requires higher privileges than provided
by the access token"**, o aplicativo não tem o escopo daquele recurso. Habilite o escopo
no cadastro do aplicativo e **rode `uv run mcp-bling-auth` de novo** — mexer nos escopos
revoga as instalações e invalida os tokens atuais.

Como cada ferramenta é um módulo do Bling, o de-para com os escopos é quase direto:

| Escopo no Bling | Ferramentas que dependem dele |
|---|---|
| Produtos | `produtos`, `produtos_variacoes`, `produtos_estruturas`, `produtos_fornecedores`, `produtos_lojas`, `categorias_produtos`, `grupos_produtos` |
| Estoques | `estoques` |
| Depósitos | `depositos` |
| Pedidos de venda | `pedidos_venda` |
| Pedidos de compra | `pedidos_compra` |
| Propostas comerciais | `propostas_comerciais` |
| Situações | `situacoes`, `situacoes_transicoes`, e a ação `alterar_situacao` de qualquer módulo |
| Contatos | `contatos`, `vendedores` |
| Contas a receber | `contas_receber` |
| Contas a pagar | `contas_pagar` |
| Categorias (receitas e despesas) | `categorias_financeiras` |
| Contas contábeis | `contas_contabeis` |
| Formas de pagamento | `formas_pagamento` |
| Borderôs | `borderos` |
| Notas fiscais | `nfe`, `nfce`, `nfse`, `naturezas_operacoes` |
| Logística | `logisticas`, `logisticas_servicos`, `logisticas_etiquetas`, `logisticas_objetos`, `logisticas_remessas` |
| Ordens de produção | `ordens_producao` |
| Canais de venda / Lojas | `canais_venda`, `categorias_lojas` |
| Contratos | `contratos` |
| Campos customizados | `campos_customizados` |
| Empresas / Notificações | `empresas`, `notificacoes` |

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

Vale lembrar que este servidor dá ao modelo acesso de escrita ao seu ERP inteiro: ele pode
criar produtos, pedidos e contatos, movimentar estoque, baixar contas e **transmitir notas
fiscais** — a ação `enviar` de `nfe`/`nfce`/`nfse` manda a nota para a SEFAZ e não tem
volta. Não há ações de exclusão, mas convém revisar o que o modelo propõe antes de
confirmar operações em uma conta de produção. Se o seu cliente MCP permitir, vale exigir
confirmação manual nas ferramentas fiscais e financeiras.

## Desenvolvimento

```bash
uv run pytest          # 40 testes, sem tocar na rede
```

Os testes mockam o HTTP e isolam os tokens em diretório temporário, então rodam sem
credenciais e sem risco de mexer na sua conta.

Estrutura:

```
src/mcp_bling/
├── server.py       # instancia o servidor MCP e registra os módulos
├── auth.py         # fluxo OAuth (comando mcp-bling-auth)
├── client.py       # HTTP: renovação de token, throttle, tradução de erros
├── tokens.py       # armazenamento local dos tokens
└── tools/
    ├── _modulo.py  # a fábrica: Modulo/Acao viram uma tool com parâmetro `acao`
    ├── _comum.py   # validações compartilhadas (intervalo de datas)
    ├── resumos.py  # o que cada listagem devolve
    └── catalogo.py, vendas.py, financeiro.py, fiscal.py, logistica.py, sistema.py
                    # os módulos declarados como dados
```

Adicionar um endpoint é acrescentar uma `Acao` à tupla do módulo: método, caminho,
filtros aceitos e uma linha de ajuda. A descrição que o modelo lê é gerada daí, então
declaração e documentação não têm como divergir.

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
