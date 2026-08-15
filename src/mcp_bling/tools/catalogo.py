"""Módulos de catálogo: produtos e seus complementos, estoque e depósitos."""

from . import resumos
from ._modulo import Acao, Modulo

PRODUTOS = Modulo(
    nome="produtos",
    recurso="/produtos",
    descricao="Produtos e serviços do catálogo.",
    chave="produtos",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, resumo=resumos.produto,
            ajuda="Devolve um resumo de cada produto (use `obter` para o cadastro inteiro).",
            filtros=(
                "nome", "codigo", "criterio", "tipo", "idCategoria", "idLoja",
                "idComponente", "idsProdutos", "codigos", "dataInclusaoInicial",
                "dataInclusaoFinal", "dataAlteracaoInicial", "dataAlteracaoFinal",
            ),
        ),
        Acao("obter", "GET", "{id}", ajuda="Cadastro completo do produto."),
        Acao(
            "criar", "POST",
            corpo='{nome, tipo "P" produto|"S" serviço, formato "S" simples|"V" com '
                  'variações|"E" com composição, situacao "A"|"I", codigo?, preco?, '
                  "unidade?, descricaoCurta?, gtin?, pesoBruto?, dimensoes?, ...}",
        ),
        Acao(
            "atualizar", "PUT", "{id}", mesclar=True,
            corpo='os campos a alterar, ex.: {"preco": 99.9, "situacao": "I"}',
        ),
        Acao(
            "alterar_situacao", "PATCH", "{id}/situacoes",
            corpo='{situacao: "A" ativo|"I" inativo|"E" excluído}',
        ),
        Acao(
            "alterar_situacao_varios", "POST", "situacoes",
            corpo='{idsProdutos: [1, 2], situacao: "A"|"I"}',
        ),
    ),
)

PRODUTOS_VARIACOES = Modulo(
    nome="produtos_variacoes",
    recurso="/produtos/variacoes",
    descricao="Variações de produtos (grade de atributos, ex.: cor e tamanho).",
    acoes=(
        Acao("obter", "GET", "{id}", ajuda="`id` é o do produto pai (formato V)."),
        Acao(
            "renomear_atributo", "PATCH", "{id}/atributos",
            ajuda="`id` é o do produto pai.",
            corpo="{nomeAtual, nomeNovo}",
        ),
        Acao(
            "gerar_combinacoes", "POST", "atributos/gerar-combinacoes",
            corpo='{atributos: [{nome, valores: ["P", "M"]}]}',
        ),
    ),
)

PRODUTOS_ESTRUTURAS = Modulo(
    nome="produtos_estruturas",
    recurso="/produtos/estruturas",
    descricao="Composição de produtos com estrutura (formato E): componentes e quantidades.",
    acoes=(
        Acao("obter", "GET", "{id}", ajuda="`id` é o do produto com estrutura."),
        Acao(
            "atualizar", "PUT", "{id}",
            corpo="{componentes: [{produto: {id}, quantidade}], ...}",
        ),
        Acao(
            "adicionar_componente", "POST", "{id}",
            corpo="{produto: {id}, quantidade}",
        ),
        Acao(
            "alterar_componente", "PATCH", "{id}/componentes/{id2}",
            ajuda="`id_secundario` é o do componente.",
            corpo="{quantidade}",
        ),
    ),
)

PRODUTOS_FORNECEDORES = Modulo(
    nome="produtos_fornecedores",
    recurso="/produtos/fornecedores",
    descricao="Vínculo entre produtos e fornecedores (código e preço de compra).",
    chave="vinculos",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, filtros=("idProduto", "idFornecedor"),
            resumo=resumos.campos("id", "descricao", "codigo", "precoCusto", "padrao"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao(
            "criar", "POST",
            corpo="{produto: {id}, fornecedor: {id}, descricao?, codigo?, precoCusto?, "
                  "precoCompra?, padrao?}",
        ),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
    ),
)

PRODUTOS_LOJAS = Modulo(
    nome="produtos_lojas",
    recurso="/produtos/lojas",
    descricao="Vínculo entre produtos e lojas/canais de venda (preço e código por loja).",
    chave="vinculos",
    acoes=(
        Acao(
            "listar", "GET", paginado=True,
            filtros=("idProduto", "idLoja", "idCategoriaProduto"),
            resumo=resumos.campos("id", "codigo", "preco", "precoPromocional"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao(
            "criar", "POST",
            corpo="{produto: {id}, loja: {id}, codigo?, preco?, precoPromocional?, ...}",
        ),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
    ),
)

CATEGORIAS_PRODUTOS = Modulo(
    nome="categorias_produtos",
    recurso="/categorias/produtos",
    descricao="Categorias do catálogo de produtos (árvore com categoria pai).",
    chave="categorias",
    acoes=(
        Acao(
            "listar", "GET", paginado=True,
            resumo=resumos.campos("id", "descricao", "idCategoriaPai"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST", corpo="{descricao, categoriaPai?: {id}}"),
        Acao("atualizar", "PUT", "{id}", corpo="{descricao, categoriaPai?: {id}}"),
    ),
)

GRUPOS_PRODUTOS = Modulo(
    nome="grupos_produtos",
    recurso="/grupos-produtos",
    descricao="Grupos de produtos (agrupamento próprio do Bling, distinto das categorias).",
    chave="grupos",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, filtros=("nome", "nomePai"),
            resumo=resumos.campos("id", "nome", "grupoProdutoPai"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST", corpo="{nome, grupoProdutoPai?: {id}}"),
        Acao("atualizar", "PUT", "{id}", corpo="{nome, grupoProdutoPai?: {id}}"),
    ),
)

ESTOQUES = Modulo(
    nome="estoques",
    recurso="/estoques",
    descricao="Saldos e movimentações de estoque.",
    acoes=(
        Acao(
            "saldos", "GET", "saldos", filtros=("idsProdutos", "codigos"),
            ajuda="Saldo físico e virtual em todos os depósitos. Informe idsProdutos "
                  "(lista) ou codigos (lista de SKUs).",
        ),
        Acao(
            "saldos_do_deposito", "GET", "saldos/{id}", filtros=("idsProdutos", "codigos"),
            ajuda="Mesmo que `saldos`, restrito ao depósito `id`.",
        ),
        Acao(
            "criar_movimentacao", "POST",
            corpo='{produto: {id}, deposito: {id}, operacao "E" entrada|"S" saída|'
                  '"B" balanço, quantidade, preco?, custo?, observacoes?}',
        ),
        Acao(
            "atualizar_movimentacao", "PUT", "{id}",
            corpo="mesmos campos de `criar_movimentacao`",
        ),
    ),
)

DEPOSITOS = Modulo(
    nome="depositos",
    recurso="/depositos",
    descricao="Depósitos de estoque.",
    chave="depositos",
    acoes=(
        Acao(
            "listar", "GET", paginado=True, filtros=("descricao", "situacao"),
            resumo=resumos.campos("id", "descricao", "situacao", "padrao"),
        ),
        Acao("obter", "GET", "{id}"),
        Acao("criar", "POST", corpo="{descricao, situacao?, padrao?, desconsiderarSaldo?}"),
        Acao("atualizar", "PUT", "{id}", corpo="mesmos campos de `criar`"),
    ),
)

MODULOS = (
    PRODUTOS,
    PRODUTOS_VARIACOES,
    PRODUTOS_ESTRUTURAS,
    PRODUTOS_FORNECEDORES,
    PRODUTOS_LOJAS,
    CATEGORIAS_PRODUTOS,
    GRUPOS_PRODUTOS,
    ESTOQUES,
    DEPOSITOS,
)
