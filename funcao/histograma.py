from math import ceil

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure


class Histograma:
    """Gera histogramas com curva de densidade para as colunas numericas."""

    COLUNAS_PADRAO = [
        "idade",
        "valor_mensal",
        "nps",
        "dias_ativos_ult_mes",
        "horas_assistidas_total",
    ]

    # Limites (minimo, maximo) aplicados em cada coluna; None deixa o lado aberto
    LIMITES_PADRAO = {
        "idade": (0, 100),
        "valor_mensal": (None, 100),
    }

    def __init__(
        self,
        colunas: list[str] | None = None,
        limites: dict[str, tuple[float | None, float | None]] | None = None,
        bins: int = 20,
    ) -> None:
        """Guarda as colunas, os limites e a quantidade de barras dos graficos."""
        # Usei as colunas e os limites principais quando nada for informado
        self.colunas = colunas or self.COLUNAS_PADRAO
        self.limites = self.LIMITES_PADRAO if limites is None else limites
        self.bins = bins

    def gerar(self, df_clientes: pd.DataFrame) -> Figure:
        """Gera um histograma para cada coluna escolhida."""
        # Organizei os histogramas em uma grade com duas colunas
        quantidade_colunas_grafico = 2
        quantidade_linhas = ceil(len(self.colunas) / quantidade_colunas_grafico)
        figura, eixos = plt.subplots(
            quantidade_linhas,
            quantidade_colunas_grafico,
            figsize=(14, 4 * quantidade_linhas),
            squeeze=False,
        )
        eixos = eixos.flatten()

        for coluna, eixo in zip(self.colunas, eixos):
            valores = self._aplicar_limites(coluna, df_clientes[coluna].dropna())

            _, limites_bins, _ = eixo.hist(
                valores,
                bins=self.bins,
                color="steelblue",
                edgecolor="black",
                alpha=0.8,
            )

            # Ajustei a densidade para a escala de frequencia do histograma
            if valores.nunique() > 1:
                eixo_x, densidade = self._calcular_curva_densidade(valores)
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
        for eixo in eixos[len(self.colunas) :]:
            eixo.set_visible(False)

        figura.suptitle("Distribuicao das colunas numericas", fontsize=16)
        figura.tight_layout(rect=(0, 0, 1, 0.97))

        return figura

    def _aplicar_limites(self, coluna: str, valores: pd.Series) -> pd.Series:
        """Mantem apenas os valores dentro dos limites definidos para a coluna."""
        minimo, maximo = self.limites.get(coluna, (None, None))
        if minimo is not None:
            valores = valores[valores >= minimo]
        if maximo is not None:
            valores = valores[valores <= maximo]

        return valores

    @staticmethod
    def _calcular_curva_densidade(
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
