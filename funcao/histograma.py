from math import ceil

import matplotlib.pyplot as plt
import pandas as pd


COLUNAS_HISTOGRAMA = [
    "idade",
    "valor_mensal",
    "nps",
    "dias_ativos_ult_mes",
    "horas_assistidas_total",
]


def gerar_histogramas(
    df_clientes: pd.DataFrame,
    colunas: list[str] | None = None,
) -> None:
    """Gera histogramas para as colunas numericas escolhidas."""
    # Usei as colunas principais quando nenhuma lista for informada
    colunas_analisadas = colunas or COLUNAS_HISTOGRAMA

    # Organizei os histogramas em uma grade com duas colunas
    quantidade_colunas_grafico = 2
    quantidade_linhas = ceil(len(colunas_analisadas) / quantidade_colunas_grafico)
    figura, eixos = plt.subplots(
        quantidade_linhas,
        quantidade_colunas_grafico,
        figsize=(14, 4 * quantidade_linhas),
        squeeze=False,
    )
    eixos = eixos.flatten()

    for coluna, eixo in zip(colunas_analisadas, eixos):
        eixo.hist(
            df_clientes[coluna].dropna(),
            bins=20,
            color="steelblue",
            edgecolor="black",
            alpha=0.8,
        )
        eixo.set_title(f"Histograma de {coluna.replace('_', ' ').title()}")
        eixo.set_xlabel(coluna.replace("_", " ").title())
        eixo.set_ylabel("Frequencia")
        eixo.grid(axis="y", linestyle="--", alpha=0.4)

    # Escondi os espacos da grade que nao receberam nenhum grafico
    for eixo in eixos[len(colunas_analisadas) :]:
        eixo.set_visible(False)

    figura.suptitle("Distribuicao das colunas numericas", fontsize=16)
    figura.tight_layout(rect=(0, 0, 1, 0.97))
