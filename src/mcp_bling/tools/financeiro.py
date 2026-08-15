"""Módulos financeiros: contas a receber e a pagar, borderôs e cadastros de apoio."""

from datetime import date

from . import resumos
from ._modulo import Acao, Modulo

CAMPOS_CONTA = (
    "{contato: {id}, vencimento, valor, dataEmissao?, numeroDocumento?, competencia?, "
    "historico?, categoria?: {id}, portador?: {id}, formaPagamento?: {id}, "
    "ocorrencia?: {tipo 1 única|2 parcelada|3 mensal|4 bimestral|5 trimestral|"
    "6 semestral|7 anual|8 quinzenal|9 semanal, diaVencimento?, numeroParcelas?}}"
)
CAMPOS_BAIXA = (
    "{data (padrão: hoje), usarDataVencimento?, portador: {id}, categoria: {id}, "
    "historico?, juros?, desconto?, acrescimo?, valorRecebido? (omita para baixa integral)}"
)
SITUACOES = (
    "situacoes aceita lista de números: 1 em aberto, 2 recebido/pago, "
    "3 parcialmente recebido/pago, 4 devolvido, 5 cancelado, 6 devolvido parcial, "
    "7 confirmado."
)


def _baixa(dados: dict) -> dict:
    """A data da baixa é obrigatória na API; hoje é o padrão sensato."""
    dados.setdefault("data", date.today().isoformat())
    dados.setdefault("usarDataVencimento", False)
    return dados


CONTAS_RECEBER = Modulo(
    nome="contas_receber",
    recurso="/contas/receber",
    descricao="Contas a receber: consulta, criação e baixa (recebimento).",
    chave="contas",
    acoes=(
        Acao(
            "listar", "GET", paginado=True,
            resumo=resumos.conta(resumos.SITUACOES_RECEBER), somar="valor",
            ajuda=f"Soma os valores da página em valor_total_da_pagina. {SITUACOES} "
                  'tipoFiltroData diz a que as datas se referem: "E" emissão, '
                  '"V" vencimento, "R" recebimento (padrão da API: emissão). '
                  "Datas em AAAA-MM-DD, intervalo máximo de 1 ano.",
            filtros=(
                "situacoes", "tipoFiltroData", "dataInicial", "dataFinal", "idContato",
                "idsCategorias", "idPortador", "idVendedor", "idFormaPagamento",
                "boletoGerado",
            ),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("boletos", "GET", "boletos", filtros=("idOrigem", "situacoes"),
             ajuda="Boletos emitidos para as contas."),
        Acao("criar", "POST", corpo=CAMPOS_CONTA),
        Acao("atualizar", "PUT", "{id}", corpo=CAMPOS_CONTA),
        Acao(
            "baixar", "POST", "{id}/baixar", corpo=CAMPOS_BAIXA,
            corpo_opcional=True, preparar=_baixa,
            ajuda="Liquida a conta e devolve o borderô gerado. O Bling costuma exigir "
                  "portador e categoria (IDs em `contas_contabeis` e "
                  "`categorias_financeiras`).",
        ),
    ),
)

CONTAS_PAGAR = Modulo(
    nome="contas_pagar",
    recurso="/contas/pagar",
    descricao="Contas a pagar: consulta, criação e baixa (pagamento).",
    chave="contas",
    acoes=(
        Acao(
            "listar", "GET", paginado=True,
            resumo=resumos.conta(resumos.SITUACOES_PAGAR), somar="valor",
            ajuda=f"Soma os valores da página em valor_total_da_pagina. {SITUACOES} "
                  "Aqui não existe tipoFiltroData: cada tipo de data tem seu par de "
                  "filtros. Datas em AAAA-MM-DD, intervalo máximo de 1 ano.",
            filtros=(
                "situacao", "idContato", "dataEmissaoInicial", "dataEmissaoFinal",
                "dataVencimentoInicial", "dataVencimentoFinal", "dataPagamentoInicial",
                "dataPagamentoFinal",
            ),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST", corpo=CAMPOS_CONTA.replace("contato: {id}", "contato: {id} (fornecedor)")),
        Acao("atualizar", "PUT", "{id}", corpo=CAMPOS_CONTA),
        Acao(
            "baixar", "POST", "{id}/baixar", corpo=CAMPOS_BAIXA,
            corpo_opcional=True, preparar=_baixa,
            ajuda="Liquida a conta e devolve o borderô gerado. O campo do valor chama-se "
                  "valorRecebido também aqui. O Bling costuma exigir portador e categoria.",
        ),
    ),
)

CATEGORIAS_FINANCEIRAS = Modulo(
    nome="categorias_financeiras",
    recurso="/categorias/receitas-despesas",
    descricao="Categorias de receitas e despesas — os IDs usados ao criar e baixar contas.",
    chave="categorias",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, filtros=("tipo", "situacao"),
            resumo=resumos.campos("id", "descricao", "tipo", "idCategoriaPai"),
            ajuda="tipo: 0 todas (padrão), 1 despesa, 2 receita, 3 receita e despesa. "
                  "situacao: 0 todas (padrão), 1 ativas, 2 inativas.",
        ),
        Acao("obter", "GET", "{id}"),
    ),
)

CONTAS_CONTABEIS = Modulo(
    nome="contas_contabeis",
    recurso="/contas-contabeis",
    descricao="Contas contábeis, que no financeiro são os portadores (caixa, bancos, "
              "cartões) — quem recebe ou paga na baixa de uma conta.",
    chave="portadores",
    acoes=(
        Acao(
            "listar", "GET", paginado=True,
            resumo=resumos.campos("id", "descricao"),
            filtros=(
                "situacoes", "ocultarInvisiveis", "ocultarContasIntegracaoPagamento",
                "ocultarTipoContaBancaria",
            ),
        ),
        Acao("obter", "GET", "{id}"),
    ),
)

FORMAS_PAGAMENTO = Modulo(
    nome="formas_pagamento",
    recurso="/formas-pagamentos",
    descricao="Formas de pagamento usadas em contas, pedidos e notas.",
    chave="formas_pagamento",
    acoes=(
        Acao(
            "listar", "GET", paginado=True,
            filtros=("descricao", "tiposPagamentos", "situacao"),
            resumo=resumos.campos(
                "id", "descricao", "tipoPagamento", "finalidade", "situacao", "padrao"
            ),
            ajuda="tipoPagamento segue a tabela fiscal (1 dinheiro, 3 cartão de crédito, "
                  "15 boleto, 17 pix dinâmico, 20 pix estático, 99 outros); "
                  "finalidade: 1 pagamentos, 2 recebimentos, 3 ambos.",
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST", corpo="{descricao, tipoPagamento, situacao?, finalidade?, "
                                    "condicao?, destino?, taxas?}"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
    ),
)

BORDEROS = Modulo(
    nome="borderos",
    recurso="/borderos",
    descricao="Borderôs: o lançamento em caixa/banco gerado pela baixa de contas.",
    acoes=(
        Acao("obter", "GET", "{id}",
             ajuda="O ID vem na resposta da baixa em `contas_receber`/`contas_pagar`."),
    ),
)

MODULOS = (
    CONTAS_RECEBER,
    CONTAS_PAGAR,
    CATEGORIAS_FINANCEIRAS,
    CONTAS_CONTABEIS,
    FORMAS_PAGAMENTO,
    BORDEROS,
)
