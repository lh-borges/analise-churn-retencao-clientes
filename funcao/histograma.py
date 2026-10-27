from math import ceil

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


COLUNAS_HISTOGRAMA = [
    "idade",
    "valor_mensal",
    "nps",
    "dias_ativos_ult_mes",
    "horas_assistidas_total",
]


def calcular_curva_densidade(
    valores: pd.Series,
    pontos: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """Calcula a curva de densidade (KDE gaussiana) dos valores."""
    dados = valores.to_numpy(dtype=float)

    # Usei a regra de Scott para definir a largura da curva
    largura = dados.std(ddof=1) * len(dados) ** (-1 / 5)
    eixo_x = np.linspace(dados.min(), dados.max(), pontos)

    # Somei uma curva normal centrada em cada valor e tirei a media
    distancias = (eixo_x[:, None] - dados[None, :]) / largura
    densidade = np.exp(-0.5 * distancias**2).mean(axis=1) / (
        largura * np.sqrt(2 * np.pi)
    )

    return eixo_x, densidade


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
        valores = df_clientes[coluna].dropna()

        # Mantive apenas idades entre 0 e 100 anos no histograma
        if coluna == "idade":
            valores = valores[valores.between(0, 100)]

        # Mantive apenas valores mensais de ate 100 no histograma
        if coluna == "valor_mensal":
            valores = valores[valores <= 100]

        _, limites_bins, _ = eixo.hist(
            valores,
            bins=20,
            color="steelblue",
            edgecolor="black",
            alpha=0.8,
        )

        # Ajustei a densidade para a escala de frequencia do histograma
        if valores.nunique() > 1:
            eixo_x, densidade = calcular_curva_densidade(valores)
            largura_bin = limites_bins[1] - limites_bins[0]
            eixo.plot(
                eixo_x,
                densidade * len(valores) * largura_bin,
                color="darkorange",
                linewidth=2,
                label="Densidade (KDE)",
            )
            eixo.legend()
        eixo.set_title(f"Histograma de {coluna.replace('_', ' ').title()}")
        eixo.set_xlabel(coluna.replace("_", " ").title())
        eixo.set_ylabel("Frequencia")
        eixo.grid(axis="y", linestyle="--", alpha=0.4)

    # Escondi os espacos da grade que nao receberam nenhum grafico
    for eixo in eixos[len(colunas_analisadas) :]:
        eixo.set_visible(False)

    figura.suptitle("Distribuicao das colunas numericas", fontsize=16)
    figura.tight_layout(rect=(0, 0, 1, 0.97))
