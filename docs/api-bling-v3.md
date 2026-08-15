# Referência de estudo — API v3 do Bling

Consolidado a partir da documentação oficial (https://developer.bling.com.br) em 14/08/2026.
Páginas-fonte: `/bling-api`, `/aplicativos`, `/limites`, `/webhooks`, `/referencia`,
`/erros-comuns`, `/perguntas-frequentes`, `/boas-praticas`, `/migracao-jwt`, `/mcp-server`.

## 1. Autenticação (OAuth 2.0, authorization code)

**Registro do app**: Central de Extensões → Área do Integrador → "Criar aplicativo".
Define `redirect_uri` e os **escopos** (permissões por recurso). O `client_id` e
`client_secret` aparecem após o cadastro.

> ⚠️ Alterar os escopos de um app **revoga todos os usuários instalados**.

**Fluxo**:

1. Redirecionar o usuário para:
   `https://bling.com.br/Api/v3/oauth/authorize?response_type=code&client_id=...&state=...`
2. O Bling redireciona para a `redirect_uri` cadastrada com `code` e `state`.
   - `code` **expira em 1 minuto** e é de **uso único** — reutilizar um code revoga o acesso do usuário.
   - Validar `state` (anti-CSRF).
3. Trocar o code por tokens:
   `POST https://api.bling.com.br/Api/v3/oauth/token`
   - Headers: `Content-Type: application/x-www-form-urlencoded`, `Authorization: Basic base64(client_id:client_secret)`
   - Body: `grant_type=authorization_code&code=...`
4. Resposta:

```json
{
  "access_token": "...",
  "expires_in": 21600,
  "token_type": "Bearer",
  "scope": "98309 318257570",
  "refresh_token": "..."
}
```

**Durações**: `access_token` = 6 h (21600 s); `refresh_token` = 30 dias.
Renovação: mesmo endpoint com `grant_type=refresh_token&refresh_token=...`
(o refresh token **rotaciona** — salvar o novo a cada renovação).
Revogação: `POST /oauth/revoke`.

**JWT (2026)**: enviar header `enable-jwt: 1` no `/oauth/token` passa a emitir JWTs
(1.500–3.000 caracteres). Tokens opacos ainda funcionam; data de corte "em definição".

## 2. Estrutura da API

- **Base URL**: `https://api.bling.com.br/Api/v3/`
- REST, JSON. Headers: `Authorization: Bearer <token>`, `Content-Type: application/json`.
- **Paginação**: query params `pagina` e `limite` (máximo 100 por página).
- **Erros**: `{"error": {"type", "message", "description"}}`
  - 400 `VALIDATION_ERROR` / `MISSING_REQUIRED_FIELD_ERROR`
  - 401 `UNAUTHORIZED` (token expirado/inválido)
  - 403 `FORBIDDEN` (token sem o escopo do recurso)
  - 404 `RESOURCE_NOT_FOUND`
  - 429 `TOO_MANY_REQUESTS`
- Datas no formato `AAAA-MM-DD`; filtros de data aceitam intervalo **máximo de 1 ano** (senão HTTP 400).

## 3. Rate limits (por conta, não por app)

- **3 requisições/segundo** e **120.000 requisições/dia**.
- Bloqueios de IP automáticos: 300 erros em 10 s → 10 min; 600 req em 10 s → 10 min;
  **20 chamadas a `/oauth/token` em 60 s → 60 min**.

## 4. Endpoints cobertos por este MCP

A cobertura é a API inteira, menos `DELETE` (decisão do projeto), `/usuarios/*`
(recuperação e redefinição de senha) e `/homologacao/*` (certificação de aplicativos).
Cada módulo abaixo vira uma tool com parâmetro `acao`.

| Módulo | Recurso base | Endpoints além de listar/obter/criar/atualizar |
|---|---|---|
| Produtos | `/produtos` | `PATCH /{id}/situacoes` · `POST /situacoes` (em lote) |
| Variações | `/produtos/variacoes` | `PATCH /{id}/atributos` · `POST /atributos/gerar-combinacoes` |
| Estruturas | `/produtos/estruturas` | `POST /{id}` (componente) · `PATCH /{id}/componentes/{idComponente}` |
| Fornecedores / Lojas do produto | `/produtos/fornecedores` · `/produtos/lojas` | — |
| Categorias / Grupos | `/categorias/produtos` · `/grupos-produtos` | — |
| Estoques | `/estoques` | `GET /saldos` e `GET /saldos/{idDeposito}` (filtros `idsProdutos[]`, `codigos[]`) |
| Depósitos | `/depositos` | — |
| Pedidos de venda | `/pedidos/vendas` | `PATCH /{id}/situacoes/{idSituacao}` · `POST /{id}/lancar-estoque[/{idDeposito}]` · `estornar-estoque` · `lancar-contas` · `estornar-contas` · `gerar-nfe` · `gerar-nfce` |
| Pedidos de compra | `/pedidos/compras` | `PATCH /{id}/situacoes` · `lancar-estoque` · `estornar-estoque` · `lancar-contas` · `estornar-contas` |
| Propostas comerciais | `/propostas-comerciais` | `PATCH /{id}/situacoes` |
| Contatos | `/contatos` | `GET /{id}/tipos` · `GET /tipos` · `GET /consumidor-final` · `PUT /{id}/situacoes` · `POST /situacoes` |
| Vendedores / Canais de venda | `/vendedores` · `/canais-venda` | `GET /canais-venda/tipos` |
| Categorias de lojas | `/categorias/lojas` | — |
| Contas a receber | `/contas/receber` | `POST /{id}/baixar` · `GET /boletos` |
| Contas a pagar | `/contas/pagar` | `POST /{id}/baixar` |
| Financeiro (apoio) | `/categorias/receitas-despesas` · `/contas-contabeis` (portadores) · `/formas-pagamentos` · `/borderos/{id}` | — |
| NF-e / NFC-e | `/nfe` · `/nfce` | `POST /{id}/enviar` · `lancar-contas` · `estornar-contas` · `lancar-estoque[/{idDeposito}]` · `estornar-estoque` |
| NFS-e | `/nfse` | `POST /{id}/enviar` · `POST /{id}/cancelar` · `GET/PUT /configuracoes` |
| Naturezas de operação | `/naturezas-operacoes` | `POST /{id}/obter-tributacao` |
| Logística | `/logisticas` · `/logisticas/servicos` · `/logisticas/objetos` · `/logisticas/remessas` | `GET /logisticas/{id}/remessas` · `GET /logisticas/etiquetas` (`formato`, `idsVendas[]`) · `PATCH /logisticas/servicos/{id}/situacoes` |
| Ordens de produção | `/ordens-producao` | `PATCH /{id}/situacoes` · `POST /gerar-sob-demanda` |
| Situações | `/situacoes` | `GET /modulos` · `GET /modulos/{id}` · `/modulos/{id}/acoes` · `/modulos/{id}/transicoes` · `/situacoes/transicoes` |
| Campos customizados | `/campos-customizados` | `GET /modulos` · `GET /tipos` · `GET /modulos/{id}` · `PATCH /{id}/situacoes` |
| Contratos | `/contratos` | — |
| Empresa / Notificações | `/empresas/me/dados-basicos` · `/notificacoes` | `POST /notificacoes/{id}/confirmar-leitura` |

### Payloads de criação (campos principais)

- **`POST /estoques`**: `{produto: {id}, deposito: {id}, operacao: "E"|"S"|"B", quantidade, preco?, custo?, observacoes?}`
  (E = entrada, S = saída, B = balanço)
- **`POST /pedidos/vendas`**: `{contato: {id}, data?, itens: [{descricao, quantidade, valor, produto?: {id}, codigo?, unidade?}], parcelas?, ...}`
- **`POST /produtos`**: `{nome, tipo: "P"|"S", situacao: "A"|"I", formato: "S"|"V"|"E", codigo?, preco?, unidade?, ...}`
- **`POST /contatos`**: `{nome, tipo: "F"|"J", situacao?: "A", numeroDocumento?, celular?, email?, endereco?, ...}`
- **`POST /contas/receber`** (e `/contas/pagar`): `{contato: {id}, vencimento, valor, dataEmissao?, numeroDocumento?,
  competencia?, historico?, categoria?: {id}, portador?: {id}, formaPagamento?: {id}, ocorrencia?: {tipo, ...}}`
  (`ocorrencia.tipo`: 1 única, 2 parcelada, 3 mensal, 4 bimestral, 5 trimestral, 6 semestral, 7 anual, 8 quinzenal, 9 semanal)
- **`POST /contas/{receber|pagar}/{id}/baixar`**: `{data, usarDataVencimento, portador: {id}, categoria: {id},
  historico, juros?, desconto?, acrescimo?, valorRecebido?}` → responde `{bordero: {id}}`
  (`valorRecebido` é o nome do campo também na baixa de contas a pagar)

### Situações e filtros do financeiro

- Situação de conta (receber e pagar): `1` em aberto, `2` recebido/pago, `3` parcialmente recebido/pago,
  `4` devolvido, `5` cancelado, `6` devolvido parcial, `7` confirmado.
- **Contas a receber** filtra data com `tipoFiltroData` (`E` emissão, `V` vencimento, `R` recebimento)
  + `dataInicial`/`dataFinal`. **Contas a pagar não aceita `tipoFiltroData`**: usa
  `dataEmissaoInicial/Final`, `dataVencimentoInicial/Final` e `dataPagamentoInicial/Final`.
- Categorias: `tipo` `0` todas, `1` despesa, `2` receita, `3` ambas; `situacao` `0` todas, `1` ativas, `2` inativas.
- Parâmetros de lista vão com sufixo `[]` (`situacoes[]`, `idsCategorias[]`), como em `idsProdutos[]`.

### Divergências entre a documentação e a biblioteca comunitária

O levantamento dos endpoints cruzou a documentação oficial com `bling-erp-api-js`. Dois pontos
em que este projeto seguiu a documentação, e não a biblioteca:

- A biblioteca envia **PATCH** tanto no seu `update` quanto no `replace`; a documentação
  usa `PUT` para substituição. Aqui: `PUT` para atualizar recurso, `PATCH` só para as
  rotas `/situacoes`.
- Em `logisticas/servicos`, a biblioteca monta a troca de situação como
  `/logisticas/{id}/situacoes`; aqui usamos `/logisticas/servicos/{id}/situacoes`, que é o
  caminho coerente com o recurso.

Além disso, a busca textual de `GET /contatos` é o parâmetro **`pesquisa`** (com `criterio`),
não `nome` — engano fácil de cometer vindo de `/produtos`, onde `nome` existe.

## 5. Pegadinhas importantes

- **Situações de pedido são entidades com ID próprio por módulo.** Para mudar a situação:
  descobrir o módulo em `GET /situacoes/modulos`, listar as situações em
  `GET /situacoes/modulos/{idModulo}` e então `PATCH /pedidos/vendas/{id}/situacoes/{idSituacao}`.
- `PUT` substitui o recurso inteiro — para atualização parcial, buscar o recurso, mesclar e reenviar.
- Rate limit é **por conta Bling**: outras integrações na mesma conta compartilham os 3 req/s.
- `POST /nfe` cria mas **não transmite** a nota (transmitir = `POST /nfe/{id}/enviar`); ações de
  lançar estoque/contas de um pedido são endpoints explícitos separados.
- Webhooks existem (order, product, stock, invoice, ...), assinados com HMAC-SHA256
  (`X-Bling-Signature-256`, chave = client_secret); responder 2xx em ≤ 5 s.
- A v2 da API foi descontinuada em 01/08/2024; não usar exemplos antigos com `apikey`.

## 6. Ecossistema

- **Não há SDK oficial.** Referência comunitária mais madura: `bling-erp-api` (npm/TS, v5+ é só v3) —
  https://github.com/AlexandreBellas/bling-erp-api-js (bom para conferir schemas de payloads).
- **MCP oficial remoto do Bling**: `https://mcp.bling.com.br/mcp` (OAuth 2.1 + PKCE),
  documentado em https://developer.bling.com.br/mcp-server — alternativa hospedada a este projeto.
