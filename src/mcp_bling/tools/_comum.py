"""Validações compartilhadas pelas tools."""

from datetime import date

from ..client import BlingError


def validar_intervalo(data_inicial: str | None, data_final: str | None) -> None:
    """A API do Bling responde 400 para filtros de data com mais de 1 ano de intervalo;
    validar aqui economiza a requisição e devolve um erro que o modelo entende."""
    if not (data_inicial and data_final):
        return
    try:
        inicio, fim = date.fromisoformat(data_inicial), date.fromisoformat(data_final)
    except (TypeError, ValueError) as exc:
        raise BlingError(
            f"data inválida ({exc}). O Bling espera o formato AAAA-MM-DD."
        ) from exc
    if (fim - inicio).days > 365:
        raise BlingError(
            "A API do Bling rejeita filtros de data com intervalo maior que 1 ano. "
            "Divida a consulta em períodos menores."
        )
