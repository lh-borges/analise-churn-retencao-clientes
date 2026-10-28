import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class Pareto:
    """Ordena categorias por frequencia e calcula o percentual acumulado."""

    COR_BARRAS = "steelblue"
    COR_ACUMULADO = "darkorange"

    def __init__(self, linha_referencia: float = 0.8) -> None:
        """Guarda a linha de referencia do grafico (80%, por padrao)."""
        self.linha_referencia = linha_referencia

    def tabela(self, valores: pd.Series) -> pd.DataFrame:
        """Contagem, participacao e participacao acumulada de cada categoria.

        Valores ausentes ficam fora do calculo; use ausentes() para conta-los.
        """
        contagem = valores.dropna().value_counts()
        tabela = contagem.rename("quantidade").to_frame()
        tabela["participacao"] = tabela["quantidade"] / tabela["quantidade"].sum()
        tabela["participacao_acumulada"] = tabela["participacao"].cumsum()
        tabela.index.name = valores.name
        return tabela

    @staticmethod
    def ausentes(valores: pd.Series) -> pd.DataFrame:
        """Quantos registros tem a categoria informada e quantos nao tem."""
        return pd.DataFrame(
            {
                "registros": [valores.notna().sum(), valores.isna().sum()],
                "participacao": [valores.notna().mean(), valores.isna().mean()],
            },
            index=pd.Index(["informado", "ausente"], name=valores.name),
        )

    def categorias_ate_referencia(self, tabela: pd.DataFrame) -> list[str]:
        """Categorias necessarias para chegar a linha de referencia (ex.: 80%)."""
        antes_da_referencia = tabela["participacao_acumulada"].shift(fill_value=0) < self.linha_referencia
        return tabela.index[antes_da_referencia].tolist()

    def grafico(self, tabela: pd.DataFrame, titulo: str) -> Figure:
        """Barras com a quantidade e linha com o percentual acumulado."""
        figura, eixo_barras = plt.subplots(figsize=(14, 6))

        barras = eixo_barras.bar(
            tabela.index, tabela["quantidade"], color=self.COR_BARRAS, edgecolor="black"
        )
        eixo_barras.bar_label(
            barras,
            labels=[f"{q}\n({p:.1%})" for q, p in zip(tabela["quantidade"], tabela["participacao"])],
            fontsize=9,
        )
        eixo_barras.set_ylabel("Quantidade")
        eixo_barras.set_ylim(0, tabela["quantidade"].max() * 1.2)
        eixo_barras.tick_params(axis="x", rotation=20)

        # Segundo eixo para o percentual acumulado, de 0% a 100%
        eixo_acumulado = eixo_barras.twinx()
        eixo_acumulado.plot(
            tabela.index,
            tabela["participacao_acumulada"],
            color=self.COR_ACUMULADO,
            marker="o",
            linewidth=2,
            label="% acumulado",
        )
        for x, y in zip(tabela.index, tabela["participacao_acumulada"]):
            # Fundo branco para o rotulo nao se misturar com as barras
            eixo_acumulado.annotate(
                f"{y:.0%}", (x, y), textcoords="offset points", xytext=(0, 10),
                ha="center", fontsize=9, color=self.COR_ACUMULADO, fontweight="bold",
                bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none"},
            )
        eixo_acumulado.axhline(
            self.linha_referencia,
            color="black",
            linestyle="--",
            label=f"Referencia de {self.linha_referencia:.0%}",
        )
        eixo_acumulado.set_ylim(0, 1.1)
        eixo_acumulado.set_ylabel("% acumulado")
        eixo_acumulado.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
        eixo_acumulado.legend(loc="center right")

        eixo_barras.set_title(titulo)
        eixo_barras.grid(axis="y", linestyle="--", alpha=0.4)

        figura.tight_layout()
        return figura
