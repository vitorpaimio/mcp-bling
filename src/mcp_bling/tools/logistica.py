"""Módulos de logística: transportadoras, serviços, etiquetas, objetos e remessas."""

from . import resumos
from ._modulo import Acao, Modulo

LOGISTICAS = Modulo(
    nome="logisticas",
    recurso="/logisticas",
    descricao="Logísticas (transportadoras e integrações de envio) cadastradas.",
    chave="logisticas",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, filtros=("tipoIntegracao", "situacao"),
            resumo=resumos.campos("id", "descricao", "tipoIntegracao", "situacao"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST", corpo="{descricao, tipoIntegracao, situacao?, ...}"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
        Acao("remessas", "GET", "{id}/remessas", ajuda="Remessas desta logística."),
    ),
)

LOGISTICAS_SERVICOS = Modulo(
    nome="logisticas_servicos",
    recurso="/logisticas/servicos",
    descricao="Serviços de cada logística (PAC, SEDEX, transportadora X, ...).",
    chave="servicos",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, filtros=("tipoIntegracao",),
            resumo=resumos.campos("id", "descricao", "codigo", "situacao"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST",
             corpo="{logistica: {id}, descricao, codigo?, aliasNome?, freteItem?, ...}"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
        Acao("alterar_situacao", "PATCH", "{id}/situacoes", corpo="{situacao}"),
    ),
)

LOGISTICAS_ETIQUETAS = Modulo(
    nome="logisticas_etiquetas",
    recurso="/logisticas/etiquetas",
    descricao="Etiquetas de envio geradas para pedidos de venda.",
    chave="etiquetas",
    acoes=(
        Acao(
            "gerar", "GET",
            ajuda="Informe idsVendas (lista de IDs de pedido) e o formato desejado.",
            filtros=("formato", "idsVendas"),
        ),
    ),
)

LOGISTICAS_OBJETOS = Modulo(
    nome="logisticas_objetos",
    recurso="/logisticas/objetos",
    descricao="Objetos (volumes) de uma remessa logística.",
    acoes=(
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST", corpo="{remessa: {id}, dimensao?, peso?, rastreamento?, ...}"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
    ),
)

LOGISTICAS_REMESSAS = Modulo(
    nome="logisticas_remessas",
    recurso="/logisticas/remessas",
    descricao="Remessas logísticas (o envio em si, com seus objetos e rastreio).",
    acoes=(
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST",
             corpo="{servico: {id}, vendas?: [{id}], objetos?: [...], remetente?, "
                   "destinatario?, ...}"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
    ),
)

MODULOS = (
    LOGISTICAS,
    LOGISTICAS_SERVICOS,
    LOGISTICAS_ETIQUETAS,
    LOGISTICAS_OBJETOS,
    LOGISTICAS_REMESSAS,
)
