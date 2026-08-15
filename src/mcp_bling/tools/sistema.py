"""Módulos de apoio: situações, campos customizados, contratos, produção, empresa e
notificações."""

from ..client import get_client
from . import resumos
from ._modulo import Acao, Modulo


def _situacoes_de_vendas() -> dict:
    """Atalho para o caminho mais pedido: as situações de pedido de venda e seus IDs.

    Situação no Bling é entidade com ID próprio por módulo, então sem este atalho o
    modelo precisaria listar os módulos, achar o de vendas e só então listar as situações.
    """
    client = get_client()
    modulos = client.request("GET", "/situacoes/modulos").get("data", [])
    modulo_vendas = next(
        (m for m in modulos if "venda" in (m.get("descricao") or m.get("nome") or "").lower()),
        None,
    )
    if modulo_vendas is None:
        return {"modulos_disponiveis": modulos}
    situacoes = client.request(
        "GET", f"/situacoes/modulos/{modulo_vendas['id']}"
    ).get("data", [])
    return {
        "modulo": modulo_vendas,
        "situacoes": [
            {"id": s.get("id"), "nome": s.get("nome"), "cor": s.get("cor")} for s in situacoes
        ],
    }


SITUACOES = Modulo(
    nome="situacoes",
    recurso="/situacoes",
    descricao="Situações dos módulos do Bling (vendas, compras, produção, ...). Cada "
              "situação é uma entidade com ID próprio dentro de um módulo.",
    acoes=(
        Acao("vendas", "GET", executar_custom=_situacoes_de_vendas,
             ajuda="Atalho: acha o módulo de vendas e devolve as situações com seus IDs — "
                   "é o que `pedidos_venda`, ação alterar_situacao, precisa."),
        Acao("modulos", "GET", "modulos", ajuda="Módulos que têm situações."),
        Acao("do_modulo", "GET", "modulos/{id}", ajuda="Situações do módulo `id`."),
        Acao("acoes_do_modulo", "GET", "modulos/{id}/acoes"),
        Acao("transicoes_do_modulo", "GET", "modulos/{id}/transicoes"),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST", corpo="{nome, idHerdado?, cor?, idModulo}"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
    ),
)

SITUACOES_TRANSICOES = Modulo(
    nome="situacoes_transicoes",
    recurso="/situacoes/transicoes",
    descricao="Transições entre situações (as automações de mudança de status).",
    acoes=(
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST", corpo="{situacaoOrigem: {id}, situacaoDestino: {id}, acoes?}"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
    ),
)

CAMPOS_CUSTOMIZADOS = Modulo(
    nome="campos_customizados",
    recurso="/campos-customizados",
    descricao="Campos customizados dos cadastros (produtos, contatos, pedidos, ...).",
    chave="campos",
    acoes=(
        Acao("modulos", "GET", "modulos", ajuda="Módulos que aceitam campos customizados."),
        Acao("tipos", "GET", "tipos", ajuda="Tipos de campo disponíveis."),
        Acao("do_modulo", "GET", "modulos/{id}", paginado=True,
             resumo=resumos.campos("id", "nome", "tipo", "situacao")),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST",
             corpo="{nome, tipo, idModulo, obrigatorio?, situacao?, opcoes?}"),
        Acao("atualizar", "PATCH", "{id}", corpo="mesmos campos de `criar`"),
        Acao("alterar_situacao", "PATCH", "{id}/situacoes", corpo="{situacao}"),
    ),
)

CONTRATOS = Modulo(
    nome="contratos",
    recurso="/contratos",
    descricao="Contratos de recorrência (assinaturas e cobranças periódicas).",
    chave="contratos",
    acoes=(
        Acao(
            "listar", "GET", paginado=True,
            resumo=resumos.campos("id", "descricao", "situacao", "contato", "valor"),
            filtros=(
                "situacao", "idContato", "idContatoCobranca", "dataCriacaoInicio",
                "dataCriacaoFinal", "dataBaseInicio", "dataBaseFinal",
            ),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST",
             corpo="{contato: {id}, descricao, valor, dataBase?, periodicidade?, ...}"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
    ),
)

ORDENS_PRODUCAO = Modulo(
    nome="ordens_producao",
    recurso="/ordens-producao",
    descricao="Ordens de produção (montagem de produtos com estrutura).",
    chave="ordens",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, filtros=("idsSituacoes",),
            resumo=resumos.campos("id", "numero", "situacao", "dataPrevista", "produto"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST",
             corpo="{produto: {id}, quantidade, dataPrevista?, deposito?: {id}, "
                   "observacoes?}"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
        Acao("alterar_situacao", "PATCH", "{id}/situacoes", corpo="{situacao}"),
        Acao("gerar_sob_demanda", "POST", "gerar-sob-demanda",
             ajuda="Gera as ordens necessárias para atender à demanda em aberto."),
    ),
)

EMPRESAS = Modulo(
    nome="empresas",
    recurso="/empresas",
    descricao="Dados da empresa conectada.",
    acoes=(
        Acao("dados_basicos", "GET", "me/dados-basicos",
             ajuda="Razão social, CNPJ, endereço e plano da conta autenticada."),
    ),
)

NOTIFICACOES = Modulo(
    nome="notificacoes",
    recurso="/notificacoes",
    descricao="Notificações da conta Bling.",
    chave="notificacoes",
    acoes=(
        Acao("listar", "GET", filtros=("periodo",),
             resumo=resumos.campos("id", "titulo", "descricao", "data", "lida")),
        Acao("confirmar_leitura", "POST", "{id}/confirmar-leitura"),
    ),
)

MODULOS = (
    SITUACOES,
    SITUACOES_TRANSICOES,
    CAMPOS_CUSTOMIZADOS,
    CONTRATOS,
    ORDENS_PRODUCAO,
    EMPRESAS,
    NOTIFICACOES,
)
