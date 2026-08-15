"""Fábrica das tools: um módulo do Bling = uma tool com o parâmetro `acao`.

A API v3 tem cerca de 150 endpoints. Uma tool por endpoint deixaria a lista impraticável
para o modelo, então cada módulo é declarado como dados (as ações abaixo) e vira uma única
tool. A descrição da tool é gerada a partir da declaração, de modo que o modelo sempre
enxerga método, caminho, filtros aceitos e campos do corpo de cada ação.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from ..client import BlingError, get_client
from ._comum import validar_intervalo


@dataclass(frozen=True)
class Acao:
    """Um endpoint do módulo, exposto como um valor possível de `acao`."""

    nome: str
    metodo: str
    caminho: str = ""  # sufixo do recurso; {id} e {id2} são preenchidos pelos parâmetros
    ajuda: str = ""
    filtros: tuple[str, ...] = ()
    paginado: bool = False
    corpo: str = ""  # descrição dos campos aceitos em `dados`; vazio = não envia corpo
    corpo_opcional: bool = False
    mesclar: bool = False  # busca o registro, mescla `dados` e reenvia (PUT substitui tudo)
    resumo: Callable[[dict], dict] | None = None
    somar: str = ""  # campo numérico totalizado na listagem (ex.: "valor")
    preparar: Callable[[dict], dict] | None = None  # completa `dados` antes de enviar
    executar_custom: Callable[[], dict] | None = None  # atalho que faz mais de uma chamada


@dataclass(frozen=True)
class Modulo:
    """Um módulo da API, que vira uma tool."""

    nome: str  # nome da tool
    recurso: str  # caminho base, ex.: "/produtos"
    descricao: str
    acoes: tuple[Acao, ...] = field(default_factory=tuple)
    chave: str = "itens"  # nome da lista devolvida pelas listagens resumidas


def _achar_acao(modulo: Modulo, nome: str) -> Acao:
    for acao in modulo.acoes:
        if acao.nome == nome:
            return acao
    disponiveis = ", ".join(a.nome for a in modulo.acoes)
    raise BlingError(
        f'ação "{nome}" não existe em `{modulo.nome}`. Ações disponíveis: {disponiveis}.'
    )


def _caminho(modulo: Modulo, acao: Acao, id: int | None, id2: int | None) -> str:
    if not acao.caminho:
        return modulo.recurso
    if "{id}" in acao.caminho and id is None:
        raise BlingError(f'a ação "{acao.nome}" de `{modulo.nome}` exige o parâmetro `id`.')
    if "{id2}" in acao.caminho and id2 is None:
        raise BlingError(
            f'a ação "{acao.nome}" de `{modulo.nome}` exige também `id_secundario` '
            f"(caminho {modulo.recurso}/{acao.caminho})."
        )
    return f"{modulo.recurso}/{acao.caminho.format(id=id, id2=id2)}"


def _validar_datas(filtros: dict) -> None:
    """Filtros de data no Bling vêm em pares Inicial/Final (ou Inicio/Final) e aceitam
    no máximo 1 ano de intervalo."""
    for chave, valor in filtros.items():
        if chave.endswith("Inicial") or chave.endswith("Inicio"):
            final = chave.replace("Inicial", "Final").replace("Inicio", "Final")
            validar_intervalo(valor, filtros.get(final))


def _params(modulo: Modulo, acao: Acao, pagina: int, limite: int, filtros: dict | None) -> dict:
    filtros = filtros or {}
    desconhecidos = [c for c in filtros if c not in acao.filtros]
    if desconhecidos:
        aceitos = ", ".join(acao.filtros) or "nenhum"
        raise BlingError(
            f'filtro(s) {", ".join(desconhecidos)} não existem na ação "{acao.nome}" de '
            f"`{modulo.nome}`. Filtros aceitos: {aceitos}."
        )
    _validar_datas(filtros)

    params: dict = {}
    if acao.paginado:
        params["pagina"], params["limite"] = pagina, limite
    for chave, valor in filtros.items():
        # listas viajam com sufixo [] na querystring (idsProdutos[]=1&idsProdutos[]=2)
        params[f"{chave}[]" if isinstance(valor, list) else chave] = valor
    return params


def _resumir(modulo: Modulo, acao: Acao, resposta: dict, pagina: int) -> dict:
    itens = [acao.resumo(item) for item in resposta.get("data", [])]
    envelope: dict = {"pagina": pagina, "quantidade": len(itens)}
    if acao.somar:
        total = sum(
            i[acao.somar] for i in itens if isinstance(i.get(acao.somar), (int, float))
        )
        envelope["valor_total_da_pagina"] = round(total, 2)
    envelope[modulo.chave] = itens
    return envelope


def executar(
    modulo: Modulo,
    acao_nome: str,
    id: int | None = None,
    id_secundario: int | None = None,
    pagina: int = 1,
    limite: int = 100,
    filtros: dict | None = None,
    dados: dict | None = None,
) -> dict:
    acao = _achar_acao(modulo, acao_nome)
    if acao.executar_custom:
        return acao.executar_custom()
    caminho = _caminho(modulo, acao, id, id_secundario)
    client = get_client()

    if acao.mesclar:
        if not dados:
            raise BlingError(
                f'a ação "{acao.nome}" de `{modulo.nome}` exige `dados` com os campos a '
                f"alterar. Campos: {acao.corpo}"
            )
        atual = client.request("GET", caminho).get("data", {})
        atual.pop("id", None)
        atual.update(dados)
        return client.request(acao.metodo, caminho, json=atual)

    if acao.corpo and not acao.corpo_opcional and not dados:
        raise BlingError(
            f'a ação "{acao.nome}" de `{modulo.nome}` exige `dados`. Campos: {acao.corpo}'
        )
    if acao.preparar:
        dados = acao.preparar(dados or {})

    resposta = client.request(
        acao.metodo,
        caminho,
        params=_params(modulo, acao, pagina, limite, filtros) or None,
        json=dados or None,
    )
    return _resumir(modulo, acao, resposta, pagina) if acao.resumo else resposta


def descrever(modulo: Modulo) -> str:
    """Monta a descrição que o modelo lê para escolher a ação e os parâmetros."""
    linhas = [modulo.descricao, "", "Ações (parâmetro `acao`):"]
    for acao in modulo.acoes:
        alvo = modulo.recurso + (f"/{acao.caminho}" if acao.caminho else "")
        partes = [f"• {acao.nome} [{acao.metodo} {alvo}]" if not acao.executar_custom
                  else f"• {acao.nome}"]
        if acao.ajuda:
            partes.append(acao.ajuda)
        if acao.paginado:
            partes.append("Paginado (pagina, limite; máx. 100).")
        if acao.filtros:
            partes.append(f'Filtros: {", ".join(acao.filtros)}.')
        if acao.mesclar:
            partes.append(
                f"Busca o registro, mescla `dados` e reenvia — o PUT do Bling substitui o "
                f"recurso inteiro. Campos: {acao.corpo}"
            )
        elif acao.corpo:
            opcional = " (opcional)" if acao.corpo_opcional else ""
            partes.append(f"dados{opcional}: {acao.corpo}")
        linhas.append(" ".join(partes))
    return "\n".join(linhas)


def registrar(mcp, *modulos: Modulo) -> None:
    for modulo in modulos:
        _registrar_um(mcp, modulo)


def _registrar_um(mcp, modulo: Modulo) -> None:
    def ferramenta(
        acao: str,
        id: int | None = None,
        id_secundario: int | None = None,
        pagina: int = 1,
        limite: int = 100,
        filtros: dict | None = None,
        dados: dict | None = None,
    ) -> dict:
        return executar(modulo, acao, id, id_secundario, pagina, limite, filtros, dados)

    mcp.tool(name=modulo.nome, description=descrever(modulo))(ferramenta)
