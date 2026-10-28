import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure


class Cohort:
    """Retencao por cohort de assinatura (clientes que assinaram no mesmo mes).

    A retencao no mes k e o % da cohort que ainda nao tinha cancelado k meses
    depois de assinar. So entram os meses ja observaveis na data de extracao:
    a cohort de dez/2023, por exemplo, so tem o mes 0 e o mes 1.
    """

    # Usei a duracao media de um mes no calendario para converter dias em meses
    DIAS_POR_MES = 365.25 / 12

    def __init__(self, primeira_cohort: str, ultima_cohort: str, meses_max: int = 12) -> None:
        """Guarda os meses de assinatura analisados (ex.: "2023-01" a "2023-12")."""
        self.primeira_cohort = pd.Period(primeira_cohort, freq="M")
        self.ultima_cohort = pd.Period(ultima_cohort, freq="M")
        self.meses_max = meses_max

    def matriz_retencao(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Cohorts nas linhas, meses desde a assinatura nas colunas, % retido nas celulas."""
        df_cohort = self._clientes_das_cohorts(df_clientes)
        mes_extracao = df_clientes["data_extracao"].max().to_period("M")

        linhas = {}
        for cohort, df_mes in df_cohort.groupby("cohort"):
            meses_observaveis = (mes_extracao - cohort).n
            retencao = {}
            for k in range(self.meses_max + 1):
                # Meses que a cohort ainda nao completou ficam em branco
                if k > meses_observaveis:
                    retencao[k] = np.nan
                    continue
                retencao[k] = self._ainda_ativos(df_mes, k).mean()
            linhas[str(cohort)] = retencao

        matriz = pd.DataFrame(linhas).T
        matriz.index.name = "cohort"
        matriz.columns = [f"mes_{k}" for k in matriz.columns]
        return matriz

    def tamanhos(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Clientes de cada cohort e quantos ja tinham cancelado na extracao."""
        df_cohort = self._clientes_das_cohorts(df_clientes)
        tabela = df_cohort.groupby("cohort").agg(
            clientes=("cliente_id", "count"),
            cancelados_ate_extracao=("churn", "sum"),
        )
        tabela["proporcao_cancelados"] = tabela["cancelados_ate_extracao"] / tabela["clientes"]
        tabela.index = tabela.index.astype(str)
        return tabela

    def retencao_media(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Retencao de todas as cohorts juntas em cada mes (media ponderada)."""
        df_cohort = self._clientes_das_cohorts(df_clientes)
        mes_extracao = df_clientes["data_extracao"].max().to_period("M")

        linhas = []
        for k in range(self.meses_max + 1):
            # So entram as cohorts que ja completaram k meses
            observaveis = df_cohort[(mes_extracao - df_cohort["cohort"]).apply(lambda d: d.n) >= k]
            if observaveis.empty:
                break
            linhas.append(
                {
                    "mes": k,
                    "cohorts": observaveis["cohort"].nunique(),
                    "clientes": len(observaveis),
                    "retencao": self._ainda_ativos(observaveis, k).mean(),
                }
            )

        return pd.DataFrame(linhas).set_index("mes")

    def resumo_assinaturas(
        self,
        df_clientes: pd.DataFrame,
        coluna_renovou: str = "renovou",
        frequencia: str = "M",
    ) -> pd.DataFrame:
        """Por cohort: quantos assinaram, quantos renovaram e quantos se mantiveram.

        Se manteve = ainda ativo na extracao. Tambem compara quem se manteve
        entre os que renovaram e os que nao renovaram. A frequencia agrupa as
        cohorts por mes ("M"), trimestre ("Q") ou ano ("Y").
        """
        df_cohort = self._clientes_das_cohorts(df_clientes)
        df_cohort = df_cohort.assign(
            cohort=df_cohort["data_assinatura"].dt.to_period(frequencia),
            se_manteve=1 - df_cohort["churn"],
        )

        tabela = df_cohort.groupby("cohort").agg(
            assinaram=("cliente_id", "count"),
            renovaram=(coluna_renovou, "sum"),
            se_mantiveram=("se_manteve", "sum"),
        )
        tabela["percentual_renovaram"] = tabela["renovaram"] / tabela["assinaram"]
        tabela["percentual_se_mantiveram"] = tabela["se_mantiveram"] / tabela["assinaram"]

        # Quem se manteve entre os que renovaram e entre os que nao renovaram
        mantidos = df_cohort.pivot_table(
            index="cohort", columns=coluna_renovou, values="se_manteve", aggfunc="mean"
        )
        tabela["se_mantiveram_entre_renovaram"] = mantidos.get(1)
        tabela["se_mantiveram_entre_nao_renovaram"] = mantidos.get(0)

        tabela.index = tabela.index.astype(str)
        return tabela

    def grafico_assinaturas(self, resumo: pd.DataFrame) -> Figure:
        """Assinaram, renovaram e se mantiveram por cohort, e % que se manteve."""
        figura, (eixo_contagem, eixo_percentual) = plt.subplots(1, 2, figsize=(18, 6))
        posicoes = np.arange(len(resumo))
        largura = 0.27

        # Barras agrupadas: as tres contagens lado a lado em cada cohort
        series = [
            ("assinaram", "Assinaram", "lightgray"),
            ("renovaram", "Renovaram (funil)", "darkorange"),
            ("se_mantiveram", "Se mantiveram (ativos)", "steelblue"),
        ]
        for deslocamento, (coluna, rotulo, cor) in zip((-largura, 0, largura), series):
            eixo_contagem.bar(
                posicoes + deslocamento, resumo[coluna], width=largura,
                color=cor, edgecolor="black", label=rotulo,
            )
        eixo_contagem.set_xticks(posicoes, resumo.index, rotation=45)
        eixo_contagem.set_title("Assinaram, renovaram e se mantiveram por cohort")
        eixo_contagem.set_ylabel("Clientes")
        eixo_contagem.legend()
        eixo_contagem.grid(axis="y", linestyle="--", alpha=0.4)

        # Linhas: % que se manteve entre quem renovou e quem nao renovou
        eixo_percentual.plot(
            posicoes, resumo["se_mantiveram_entre_renovaram"], marker="o",
            color="darkorange", label="Entre quem renovou",
        )
        eixo_percentual.plot(
            posicoes, resumo["se_mantiveram_entre_nao_renovaram"], marker="o",
            color="steelblue", label="Entre quem nao renovou",
        )
        eixo_percentual.set_xticks(posicoes, resumo.index, rotation=45)
        eixo_percentual.set_title("% que se manteve ativo ate a extracao")
        eixo_percentual.set_ylabel("% ainda ativos")
        eixo_percentual.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
        eixo_percentual.set_ylim(0, 1.05)
        eixo_percentual.legend()
        eixo_percentual.grid(linestyle="--", alpha=0.4)

        figura.tight_layout()
        return figura

    @staticmethod
    def grafico_comparar_retencao(medias: dict[str, pd.DataFrame]) -> Figure:
        """Curvas de retencao media de grupos diferentes no mesmo grafico."""
        figura, eixo = plt.subplots(figsize=(14, 6))
        cores = ["darkorange", "steelblue", "seagreen", "gray"]

        for (rotulo, media), cor in zip(medias.items(), cores):
            eixo.plot(
                media.index, media["retencao"], marker="o", color=cor,
                label=f"{rotulo} (n={media['clientes'].iloc[0]})",
            )

        eixo.set_title("Retencao media por mes de vida")
        eixo.set_xlabel("Meses desde a assinatura")
        eixo.set_ylabel("% ainda ativos")
        eixo.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
        eixo.set_ylim(0, 1.05)
        eixo.legend()
        eixo.grid(linestyle="--", alpha=0.4)

        figura.tight_layout()
        return figura

    @staticmethod
    def cancelamentos_por_mes(df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Quantidade de cancelamentos registrados em cada mes."""
        meses = df_clientes["data_cancelamento"].dropna().dt.to_period("M")
        tabela = meses.value_counts().sort_index().rename("cancelamentos").to_frame()
        tabela.index = tabela.index.astype(str)
        tabela.index.name = "mes"
        return tabela

    def grafico(self, matriz: pd.DataFrame, media: pd.DataFrame) -> Figure:
        """Mapa de calor da retencao por cohort e curva da retencao media."""
        figura, (eixo_mapa, eixo_curva) = plt.subplots(
            1, 2, figsize=(18, 7), gridspec_kw={"width_ratios": [3, 2]}
        )

        # Mapa de calor: cada linha e uma cohort, cada coluna um mes de vida
        valores = matriz.to_numpy(dtype=float)
        imagem = eixo_mapa.imshow(valores, cmap="RdYlGn", vmin=0.5, vmax=1, aspect="auto")
        eixo_mapa.set_xticks(range(matriz.shape[1]), range(matriz.shape[1]))
        eixo_mapa.set_yticks(range(matriz.shape[0]), matriz.index)
        for i in range(matriz.shape[0]):
            for j in range(matriz.shape[1]):
                if not np.isnan(valores[i, j]):
                    eixo_mapa.text(j, i, f"{valores[i, j]:.0%}", ha="center", va="center", fontsize=8)
        eixo_mapa.set_title("Retencao por cohort de assinatura")
        eixo_mapa.set_xlabel("Meses desde a assinatura")
        eixo_mapa.set_ylabel("Mes da assinatura (cohort)")
        figura.colorbar(imagem, ax=eixo_mapa, label="% ainda ativos", format=plt.FuncFormatter(lambda v, _: f"{v:.0%}"))

        # Curva: retencao media de todas as cohorts observaveis em cada mes
        eixo_curva.plot(media.index, media["retencao"], marker="o", color="steelblue")
        for mes, linha in media.iterrows():
            eixo_curva.annotate(
                f"{linha['retencao']:.0%}",
                (mes, linha["retencao"]),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                fontsize=8,
            )
        eixo_curva.set_title("Retencao media por mes de vida")
        eixo_curva.set_xlabel("Meses desde a assinatura")
        eixo_curva.set_ylabel("% ainda ativos")
        eixo_curva.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
        eixo_curva.set_ylim(0, 1.05)
        eixo_curva.grid(linestyle="--", alpha=0.4)

        figura.tight_layout()
        return figura

    def _clientes_das_cohorts(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Clientes que assinaram entre a primeira e a ultima cohort."""
        cohort = df_clientes["data_assinatura"].dt.to_period("M")
        dentro = cohort.between(self.primeira_cohort, self.ultima_cohort)
        return df_clientes[dentro].assign(cohort=cohort[dentro])

    def _ainda_ativos(self, df_clientes: pd.DataFrame, meses: int) -> pd.Series:
        """True para quem nao tinha cancelado `meses` meses depois de assinar."""
        limite = df_clientes["data_assinatura"] + pd.to_timedelta(
            meses * self.DIAS_POR_MES, unit="D"
        )
        return df_clientes["data_cancelamento"].isna() | (df_clientes["data_cancelamento"] > limite)
