from math import ceil

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class Quintis:
    """Divide colunas numericas em grupos de mesmo tamanho (quintis, por padrao).

    Valores iguais sempre ficam no mesmo grupo. Por isso, quando ha muitos
    empates, os grupos saem com tamanhos diferentes ou em quantidade menor
    que a pedida (ex.: valor_mensal tem so 3 precos e nao forma 5 grupos).
    """

    COR = "darkorange"

    def __init__(self, quantidade: int = 5) -> None:
        """Guarda em quantos grupos as colunas serao divididas."""
        self.quantidade = quantidade

    def cortes(self, df_clientes: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
        """Mostra os pontos de corte e se a coluna consegue formar os grupos."""
        linhas = []
        for coluna in colunas:
            valores = df_clientes[coluna].dropna()
            grupos = self._dividir(valores)
            tamanhos = grupos.value_counts()

            linhas.append(
                {
                    "variavel": coluna,
                    "n": len(valores),
                    "nulos": int(df_clientes[coluna].isna().sum()),
                    "valores_distintos": valores.nunique(),
                    "pontos_de_corte": ", ".join(
                        f"{corte:g}"
                        for corte in valores.quantile(
                            [i / self.quantidade for i in range(1, self.quantidade)]
                        )
                    ),
                    "grupos_formados": len(tamanhos),
                    "menor_grupo": tamanhos.min(),
                    "maior_grupo": tamanhos.max(),
                    "leitura": self._ler_grupos(len(tamanhos), tamanhos),
                }
            )

        return pd.DataFrame(linhas).set_index("variavel")

    def pontuar(self, valores: pd.Series, maior_e_melhor: bool = True) -> pd.Series:
        """Nota de 1 a N pelo grupo do valor (N = maior nota). Nulos ficam nulos.

        Com maior_e_melhor=False, os menores valores recebem as maiores notas
        (ex.: recencia, em que menos dias desde o ultimo acesso e melhor).
        """
        notas = self._dividir(valores)
        if not maior_e_melhor:
            notas = notas.max() + 1 - notas
        return notas

    def taxa_por_quintil(
        self,
        df_clientes: pd.DataFrame,
        coluna: str,
        coluna_alvo: str,
    ) -> pd.DataFrame:
        """Quantidade, faixa de valores e taxa do alvo em cada grupo da coluna."""
        dados = df_clientes[[coluna, coluna_alvo]].dropna()
        dados = dados.assign(grupo=self._dividir(dados[coluna]))

        tabela = dados.groupby("grupo").agg(
            minimo=(coluna, "min"),
            maximo=(coluna, "max"),
            clientes=(coluna_alvo, "count"),
            casos=(coluna_alvo, "sum"),
            taxa=(coluna_alvo, "mean"),
        )
        tabela.index = [f"Q{grupo}" for grupo in tabela.index]
        tabela.index.name = f"quintil_{coluna}"

        return tabela

    def grafico_taxa_por_quintil(
        self,
        df_clientes: pd.DataFrame,
        colunas: list[str],
        coluna_alvo: str,
    ) -> Figure:
        """Um grafico de barras com a taxa do alvo por quintil de cada coluna."""
        quantidade_colunas_grafico = 2
        quantidade_linhas = ceil(len(colunas) / quantidade_colunas_grafico)
        figura, eixos = plt.subplots(
            quantidade_linhas,
            quantidade_colunas_grafico,
            figsize=(16, 4.5 * quantidade_linhas),
            squeeze=False,
        )
        eixos = eixos.flatten()
        taxa_geral = df_clientes[coluna_alvo].mean()

        for coluna, eixo in zip(colunas, eixos):
            tabela = self.taxa_por_quintil(df_clientes, coluna, coluna_alvo)

            # Rotulo de cada barra: o quintil e a faixa de valores que ele cobre,
            # com ate 3 algarismos para nao sobrepor os rotulos vizinhos
            rotulos = [
                f"{quintil}\n{linha['minimo']:.3g} a {linha['maximo']:.3g}"
                for quintil, linha in tabela.iterrows()
            ]
            barras = eixo.bar(rotulos, tabela["taxa"], color=self.COR, edgecolor="black")
            eixo.bar_label(barras, labels=[f"{t:.1%}" for t in tabela["taxa"]], fontsize=9)
            eixo.axhline(taxa_geral, color="black", linestyle="--", label="Taxa geral")

            eixo.set_title(f"Taxa de {coluna_alvo} por quintil de {coluna}")
            eixo.set_ylabel(f"Taxa de {coluna_alvo}")
            eixo.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
            eixo.set_ylim(0, max(tabela["taxa"].max(), taxa_geral) * 1.2 or 0.1)
            eixo.legend()
            eixo.grid(axis="y", linestyle="--", alpha=0.4)

        # Escondi os espacos da grade que nao receberam nenhum grafico
        for eixo in eixos[len(colunas) :]:
            eixo.set_visible(False)

        figura.tight_layout()
        return figura

    def _dividir(self, valores: pd.Series) -> pd.Series:
        """Numero do grupo (1 = menores valores) de cada valor."""
        # duplicates="drop" junta cortes repetidos quando ha muitos empates,
        # o que forma menos grupos em vez de dar erro
        grupos = pd.qcut(valores, self.quantidade, labels=False, duplicates="drop")
        return grupos + 1

    def _ler_grupos(self, grupos_formados: int, tamanhos: pd.Series) -> str:
        """Explica se a divisao em grupos funcionou para a coluna."""
        if grupos_formados < self.quantidade:
            return (
                f"Empates demais: so {grupos_formados} grupos; "
                "precisa de outra regra de pontuacao"
            )
        if tamanhos.max() > 1.5 * tamanhos.min():
            return "Grupos de tamanhos desiguais por causa de empates"
        return "Grupos equilibrados"
