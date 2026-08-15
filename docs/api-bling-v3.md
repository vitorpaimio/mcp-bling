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

## 4. Endpoints usados neste MCP

| Módulo | Endpoints |
|---|---|
| Produtos | `GET/POST /produtos` · `GET/PUT/PATCH/DELETE /produtos/{id}` · `PATCH /produtos/{id}/situacoes` |
| Estoques | `GET /estoques/saldos` (filtro `idsProdutos[]`) · `GET /estoques/saldos/{idDeposito}` · `POST /estoques` (movimentação) |
| Depósitos | `GET /depositos` |
| Pedidos de venda | `GET/POST /pedidos/vendas` · `GET/PUT/DELETE /pedidos/vendas/{id}` · `PATCH .../{id}/situacoes/{idSituacao}` · `POST .../{id}/lancar-estoque` · `.../estornar-estoque` |
| Situações | `GET /situacoes/modulos` · `GET /situacoes/modulos/{idModulo}` |
| Contatos | `GET/POST /contatos` · `GET/PUT/DELETE /contatos/{id}` · `GET /contatos/tipos` |

### Payloads de criação (campos principais)

- **`POST /estoques`**: `{produto: {id}, deposito: {id}, operacao: "E"|"S"|"B", quantidade, preco?, custo?, observacoes?}`
  (E = entrada, S = saída, B = balanço)
- **`POST /pedidos/vendas`**: `{contato: {id}, data?, itens: [{descricao, quantidade, valor, produto?: {id}, codigo?, unidade?}], parcelas?, ...}`
- **`POST /produtos`**: `{nome, tipo: "P"|"S", situacao: "A"|"I", formato: "S"|"V"|"E", codigo?, preco?, unidade?, ...}`
- **`POST /contatos`**: `{nome, tipo: "F"|"J", situacao?: "A", numeroDocumento?, celular?, email?, endereco?, ...}`

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
