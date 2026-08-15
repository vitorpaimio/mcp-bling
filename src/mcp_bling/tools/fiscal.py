"""Módulos fiscais: NF-e, NFC-e, NFS-e e naturezas de operação.

Criar uma nota **não** a transmite: emitir é a ação `enviar`.
"""

from . import resumos
from ._modulo import Acao, Modulo

LANCAMENTOS = (
    Acao("lancar_contas", "POST", "{id}/lancar-contas",
         ajuda="Gera as contas a receber da nota."),
    Acao("estornar_contas", "POST", "{id}/estornar-contas"),
    Acao("lancar_estoque", "POST", "{id}/lancar-estoque"),
    Acao("lancar_estoque_no_deposito", "POST", "{id}/lancar-estoque/{id2}",
         ajuda="`id_secundario` é o depósito."),
    Acao("estornar_estoque", "POST", "{id}/estornar-estoque"),
)

NFE = Modulo(
    nome="nfe",
    recurso="/nfe",
    descricao="Notas fiscais eletrônicas (NF-e) de produto.",
    chave="notas",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, resumo=resumos.nota_fiscal,
            ajuda="situacao: 1 pendente, 2 cancelada, 3 aguardando recibo, 4 rejeitada, "
                  "5 autorizada, 6 emitida DANFE, 7 registrada, 8 aguardando protocolo, "
                  "9 denegada, 10 consulta situação, 11 bloqueada. tipo: 0 entrada, 1 saída.",
            filtros=("situacao", "tipo", "numeroLoja", "dataEmissaoInicial", "dataEmissaoFinal"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao(
            "criar", "POST",
            ajuda="Cria a nota em rascunho; para emitir, use `enviar` depois.",
            corpo="{tipo, numero?, dataOperacao?, contato: {...}, naturezaOperacao: {id}, "
                  "itens: [{codigo, descricao, unidade, quantidade, valor}], parcelas?, "
                  "transporte?, observacoes?}",
        ),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
        Acao("enviar", "POST", "{id}/enviar",
             ajuda="Transmite a nota para a SEFAZ. Ação irreversível: confirme antes."),
        *LANCAMENTOS,
    ),
)

NFCE = Modulo(
    nome="nfce",
    recurso="/nfce",
    descricao="Notas fiscais de consumidor eletrônicas (NFC-e).",
    chave="notas",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, resumo=resumos.nota_fiscal,
            filtros=("situacao", "dataEmissaoInicial", "dataEmissaoFinal"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST", corpo="mesma estrutura da NF-e (contato, itens, parcelas, ...)"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
        Acao("enviar", "POST", "{id}/enviar",
             ajuda="Transmite a nota para a SEFAZ. Ação irreversível: confirme antes."),
        *LANCAMENTOS,
    ),
)

NFSE = Modulo(
    nome="nfse",
    recurso="/nfse",
    descricao="Notas fiscais de serviço eletrônicas (NFS-e) e suas configurações.",
    chave="notas",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, resumo=resumos.nota_fiscal,
            filtros=("situacao", "dataEmissaoInicial", "dataEmissaoFinal"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST",
             corpo="{contato: {...}, servicos: [{descricao, valor, ...}], data?, "
                   "observacoes?, ...}"),
        Acao("enviar", "POST", "{id}/enviar",
             ajuda="Transmite a nota para a prefeitura. Ação irreversível: confirme antes."),
        Acao("cancelar", "POST", "{id}/cancelar", corpo="{motivo}"),
        Acao("configuracoes", "GET", "configuracoes",
             ajuda="Configurações de emissão de NFS-e da empresa."),
        Acao("atualizar_configuracoes", "PUT", "configuracoes",
             corpo="os campos devolvidos por `configuracoes`"),
    ),
)

NATUREZAS_OPERACOES = Modulo(
    nome="naturezas_operacoes",
    recurso="/naturezas-operacoes",
    descricao="Naturezas de operação (CFOP e regras fiscais) usadas nas notas.",
    chave="naturezas",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, filtros=("situacao", "descricao"),
            resumo=resumos.campos("id", "descricao", "situacao", "padrao"),
        ),
        Acao(
            "obter_tributacao", "POST", "{id}/obter-tributacao",
            ajuda="Calcula a tributação de um produto sob esta natureza de operação.",
            corpo="{produto: {id}, uf?, tipoPessoa?, consumidorFinal?, ...}",
        ),
    ),
)

MODULOS = (NFE, NFCE, NFSE, NATUREZAS_OPERACOES)
