"""Tools MCP: contatos (clientes e fornecedores)."""

from mcp.server.mcpserver import MCPServer

from ..client import get_client


def _resumo_contato(c: dict) -> dict:
    return {
        "id": c.get("id"),
        "nome": c.get("nome"),
        "tipo": c.get("tipo"),
        "numeroDocumento": c.get("numeroDocumento"),
        "situacao": c.get("situacao"),
        "telefone": c.get("telefone"),
        "celular": c.get("celular"),
    }


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    def listar_contatos(
        pagina: int = 1,
        limite: int = 100,
        nome: str | None = None,
        numero_documento: str | None = None,
    ) -> dict:
        """Lista contatos do Bling (clientes/fornecedores, resumido). Filtros opcionais por
        nome (busca parcial) e numero_documento (CPF/CNPJ, apenas dígitos)."""
        data = get_client().request(
            "GET",
            "/contatos",
            params={
                "pagina": pagina,
                "limite": limite,
                "nome": nome,
                "numeroDocumento": numero_documento,
            },
        )
        contatos = [_resumo_contato(c) for c in data.get("data", [])]
        return {"pagina": pagina, "quantidade": len(contatos), "contatos": contatos}

    @mcp.tool()
    def obter_contato(id_contato: int) -> dict:
        """Retorna todos os dados de um contato pelo seu ID Bling (endereço, e-mail, ...)."""
        return get_client().request("GET", f"/contatos/{id_contato}")

    @mcp.tool()
    def criar_contato(
        nome: str,
        tipo: str = "F",
        numero_documento: str | None = None,
        email: str | None = None,
        celular: str | None = None,
        dados_extras: dict | None = None,
    ) -> dict:
        """Cria um contato. tipo: "F" (pessoa física) ou "J" (jurídica);
        numero_documento: CPF/CNPJ apenas dígitos. Campos adicionais da API
        (endereco, ie, rg, ...) vão em `dados_extras`."""
        body = {
            "nome": nome,
            "tipo": tipo,
            "situacao": "A",
            "numeroDocumento": numero_documento,
            "email": email,
            "celular": celular,
        }
        body = {k: v for k, v in body.items() if v is not None}
        body.update(dados_extras or {})
        return get_client().request("POST", "/contatos", json=body)

    @mcp.tool()
    def atualizar_contato(id_contato: int, dados: dict) -> dict:
        """Atualiza um contato: busca os dados atuais, mescla as chaves de `dados` por cima
        (ex.: {"celular": "11999998888"}) e reenvia via PUT (a API substitui o recurso
        inteiro, por isso a mesclagem)."""
        atual = get_client().request("GET", f"/contatos/{id_contato}").get("data", {})
        atual.pop("id", None)
        atual.update(dados)
        return get_client().request("PUT", f"/contatos/{id_contato}", json=atual)
