"""Resumos das listagens.

A API devolve o registro inteiro em toda listagem; despejar isso no contexto do modelo
custa caro e ajuda pouco. Cada listagem resume os campos que servem para decidir o
próximo passo — o registro completo sai na ação `obter`.
"""

from collections.abc import Callable

SITUACOES_RECEBER = {
    1: "em aberto",
    2: "recebido",
    3: "parcialmente recebido",
    4: "devolvido",
    5: "cancelado",
    6: "devolvido parcial",
    7: "confirmado",
}
SITUACOES_PAGAR = {**SITUACOES_RECEBER, 2: "pago", 3: "parcialmente pago"}


def campos(*nomes: str) -> Callable[[dict], dict]:
    """Resumo genérico: só as chaves informadas, na ordem informada."""
    return lambda registro: {nome: registro.get(nome) for nome in nomes}


def produto(p: dict) -> dict:
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


def pedido(p: dict) -> dict:
    contato = p.get("contato") or {}
    return {
        "id": p.get("id"),
        "numero": p.get("numero"),
        "data": p.get("data"),
        "total": p.get("total"),
        "contato": {"id": contato.get("id"), "nome": contato.get("nome")},
        "situacao": p.get("situacao"),
        "numeroLoja": p.get("numeroLoja"),
    }


def contato(c: dict) -> dict:
    return {
        "id": c.get("id"),
        "nome": c.get("nome"),
        "tipo": c.get("tipo"),
        "numeroDocumento": c.get("numeroDocumento"),
        "situacao": c.get("situacao"),
        "telefone": c.get("telefone"),
        "celular": c.get("celular"),
    }


def conta(situacoes: dict[int, str]) -> Callable[[dict], dict]:
    """Resumo de conta a receber/pagar. A API devolve a situação como número; o nome
    evita que o modelo tenha que decorar a tabela."""

    def resumir(c: dict) -> dict:
        contato_ = c.get("contato") or {}
        return {
            "id": c.get("id"),
            "situacao": c.get("situacao"),
            "situacaoNome": situacoes.get(c.get("situacao")),
            "vencimento": c.get("vencimento"),
            "valor": c.get("valor"),
            "dataEmissao": c.get("dataEmissao"),
            "numeroDocumento": c.get("numeroDocumento"),
            "historico": c.get("historico"),
            "contato": {"id": contato_.get("id"), "nome": contato_.get("nome")},
        }

    return resumir


def nota_fiscal(n: dict) -> dict:
    contato_ = n.get("contato") or {}
    return {
        "id": n.get("id"),
        "numero": n.get("numero"),
        "serie": n.get("serie"),
        "tipo": n.get("tipo"),
        "situacao": n.get("situacao"),
        "dataEmissao": n.get("dataEmissao"),
        "valorNota": n.get("valorNota"),
        "chaveAcesso": n.get("chaveAcesso"),
        "contato": {"id": contato_.get("id"), "nome": contato_.get("nome")},
    }
