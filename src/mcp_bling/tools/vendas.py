"""Módulos comerciais: pedidos de venda e compra, propostas, contatos e vendedores."""

from . import resumos
from ._modulo import Acao, Modulo

PEDIDOS_VENDA = Modulo(
    nome="pedidos_venda",
    recurso="/pedidos/vendas",
    descricao="Pedidos de venda: consulta, criação, situação e os lançamentos derivados "
              "(estoque, contas, NF-e).",
    chave="pedidos",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, resumo=resumos.pedido,
            ajuda="Datas em AAAA-MM-DD, intervalo máximo de 1 ano. idsSituacoes aceita "
                  "lista; os IDs saem de `situacoes` (ação vendas).",
            filtros=(
                "idContato", "idsSituacoes", "dataInicial", "dataFinal",
                "dataAlteracaoInicial", "dataAlteracaoFinal", "dataPrevistaInicial",
                "dataPrevistaFinal", "numero", "idLoja", "idVendedor",
                "idControleCaixa", "numerosLojas",
            ),
        ),
        Acao("obter", "GET", "{id}", ajuda="Pedido completo: itens, parcelas, transporte."),
        Acao(
            "criar", "POST",
            corpo="{contato: {id}, itens: [{descricao, quantidade, valor, produto?: {id}, "
                  "codigo?, unidade?}], data?, numero?, parcelas?, transporte?, "
                  "vendedor?: {id}, observacoes?}",
        ),
        Acao(
            "atualizar", "PUT", "{id}",
            ajuda="O PUT substitui o pedido inteiro: reenvie também os itens.",
            corpo="mesmos campos de `criar`",
        ),
        Acao(
            "alterar_situacao", "PATCH", "{id}/situacoes/{id2}",
            ajuda="`id_secundario` é o ID da situação (descubra com `situacoes`, ação vendas).",
        ),
        Acao("lancar_estoque", "POST", "{id}/lancar-estoque",
             ajuda="Baixa o estoque dos itens no depósito padrão."),
        Acao("lancar_estoque_no_deposito", "POST", "{id}/lancar-estoque/{id2}",
             ajuda="`id_secundario` é o depósito."),
        Acao("estornar_estoque", "POST", "{id}/estornar-estoque"),
        Acao("lancar_contas", "POST", "{id}/lancar-contas",
             ajuda="Gera as contas a receber das parcelas do pedido."),
        Acao("estornar_contas", "POST", "{id}/estornar-contas"),
        Acao("gerar_nfe", "POST", "{id}/gerar-nfe",
             ajuda="Cria a NF-e a partir do pedido — não transmite (use `nfe`, ação enviar)."),
        Acao("gerar_nfce", "POST", "{id}/gerar-nfce"),
    ),
)

PEDIDOS_COMPRA = Modulo(
    nome="pedidos_compra",
    recurso="/pedidos/compras",
    descricao="Pedidos de compra a fornecedores e seus lançamentos (estoque e contas a pagar).",
    chave="pedidos",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, resumo=resumos.pedido,
            filtros=("idFornecedor", "idSituacao", "valorSituacao", "dataInicial", "dataFinal"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao(
            "criar", "POST",
            corpo="{fornecedor: {id}, itens: [{descricao, quantidade, valor, produto?: {id}}], "
                  "data?, numero?, observacoes?, parcelas?}",
        ),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
        Acao("alterar_situacao", "PATCH", "{id}/situacoes", corpo="{situacao}"),
        Acao("lancar_estoque", "POST", "{id}/lancar-estoque",
             ajuda="Dá entrada no estoque dos itens comprados."),
        Acao("estornar_estoque", "POST", "{id}/estornar-estoque"),
        Acao("lancar_contas", "POST", "{id}/lancar-contas",
             ajuda="Gera as contas a pagar do pedido."),
        Acao("estornar_contas", "POST", "{id}/estornar-contas"),
    ),
)

PROPOSTAS_COMERCIAIS = Modulo(
    nome="propostas_comerciais",
    recurso="/propostas-comerciais",
    descricao="Propostas comerciais (orçamentos) enviadas a clientes.",
    chave="propostas",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, resumo=resumos.pedido,
            filtros=("situacao", "idContato", "dataInicial", "dataFinal"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao(
            "criar", "POST",
            corpo="{contato: {id}, itens: [{descricao, quantidade, valor}], data?, "
                  "validade?, observacoes?}",
        ),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
        Acao("alterar_situacao", "PATCH", "{id}/situacoes", corpo="{situacao}"),
    ),
)

CONTATOS = Modulo(
    nome="contatos",
    recurso="/contatos",
    descricao="Contatos: clientes, fornecedores, transportadoras e demais cadastros.",
    chave="contatos",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, resumo=resumos.contato,
            ajuda="A busca textual é `pesquisa` (nome, e-mail ou documento), não `nome`.",
            filtros=(
                "pesquisa", "criterio", "numeroDocumento", "idTipoContato", "idVendedor",
                "uf", "telefone", "idsContatos", "dataInclusaoInicial", "dataInclusaoFinal",
                "dataAlteracaoInicial", "dataAlteracaoFinal",
            ),
        ),
        Acao("obter", "GET", "{id}", ajuda="Cadastro completo: endereço, e-mail, IE, ..."),
        Acao("tipos_do_contato", "GET", "{id}/tipos",
             ajuda="Papéis do contato (cliente, fornecedor, ...)."),
        Acao("tipos_cadastrados", "GET", "tipos", ajuda="Todos os tipos de contato do Bling."),
        Acao("consumidor_final", "GET", "consumidor-final",
             ajuda="O contato genérico usado em vendas sem identificação."),
        Acao(
            "criar", "POST",
            corpo='{nome, tipo "F" física|"J" jurídica, situacao? "A", numeroDocumento? '
                  "(só dígitos), email?, celular?, telefone?, endereco?, ie?, rg?}",
        ),
        Acao(
            "atualizar", "PUT", "{id}", mesclar=True,
            corpo='os campos a alterar, ex.: {"celular": "11999998888"}',
        ),
        Acao("alterar_situacao", "PUT", "{id}/situacoes", corpo='{situacao: "A"|"I"|"E"}'),
        Acao("alterar_situacao_varios", "POST", "situacoes",
             corpo='{idsContatos: [1, 2], situacao: "A"|"I"}'),
    ),
)

VENDEDORES = Modulo(
    nome="vendedores",
    recurso="/vendedores",
    descricao="Vendedores cadastrados (cada um vinculado a um contato).",
    chave="vendedores",
    acoes=(
        Acao(
            "listar", "GET", paginado=True,
            resumo=resumos.campos("id", "contato", "situacao", "loja"),
            filtros=(
                "nomeContato", "situacaoContato", "idContato", "idLoja",
                "dataAlteracaoInicial", "dataAlteracaoFinal",
            ),
        ),
        Acao("obter", "GET", "{id}"),
    ),
)

CANAIS_VENDA = Modulo(
    nome="canais_venda",
    recurso="/canais-venda",
    descricao="Canais de venda (lojas, marketplaces e integrações).",
    chave="canais",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, filtros=("tipos", "situacao", "agrupador"),
            resumo=resumos.campos("id", "descricao", "tipo", "situacao"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("tipos", "GET", "tipos", filtros=("agrupador",),
             ajuda="Tipos de canal disponíveis para cadastro."),
    ),
)

CATEGORIAS_LOJAS = Modulo(
    nome="categorias_lojas",
    recurso="/categorias/lojas",
    descricao="De-para entre as categorias do Bling e as categorias de cada loja/canal.",
    chave="categorias",
    acoes=(
        Acao(
            "listar", "GET", paginado=True,
            filtros=("idLoja", "idCategoriaProduto", "idCategoriaProdutoPai"),
            resumo=resumos.campos("id", "descricao", "loja", "categoriaProduto"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST", corpo="{descricao, loja: {id}, categoriaProduto: {id}}"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
    ),
)

MODULOS = (
    PEDIDOS_VENDA,
    PEDIDOS_COMPRA,
    PROPOSTAS_COMERCIAIS,
    CONTATOS,
    VENDEDORES,
    CANAIS_VENDA,
    CATEGORIAS_LOJAS,
)
