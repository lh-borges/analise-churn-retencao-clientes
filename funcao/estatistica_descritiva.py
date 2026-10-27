import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from .extracao_normalizacao import ExtracaoNormalizacao
from .geracao_colunas import GeracaoColunas


COLUNAS_DATA = ExtracaoNormalizacao.COLUNAS_DATA
COLUNAS_DIFERENCA_DATA = GeracaoColunas.COLUNAS_DIFERENCA_DATA


class EstatisticaDescritiva:
    """Gera tabelas, verificacoes e graficos descritivos de uma base de clientes."""

    COLUNAS_CATEGORICAS = ["plano", "ciclo", "regiao", "canal_aquisicao"]

    # Valores que nao representam uma categoria real em cada coluna
    VALORES_IGNORADOS_CATEGORICAS = {"regiao": ["?"]}

    def __init__(self, df_clientes: pd.DataFrame) -> None:
        """Guarda a base que sera analisada."""
        self.df_clientes = df_clientes

    @staticmethod
    def descrever(df_clientes: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
        """Retorna a estatistica descritiva das colunas com os nomes em portugues."""
        return (
            df_clientes[colunas]
            .describe()
            .T.rename(
                columns={
                    "count": "contagem",
                    "mean": "media",
                    "std": "desvio_padrao",
                    "min": "minimo",
                    "25%": "quartil_25",
                    "50%": "mediana",
                    "75%": "quartil_75",
                    "max": "maximo",
                }
            )
        )

    @property
    def colunas_numericas(self) -> list[str]:
        """Retorna as colunas numericas da base."""
        return self.df_clientes.select_dtypes(include="number").columns.tolist()

    def estatisticas_numericas(self) -> pd.DataFrame:
        """Retorna as estatisticas descritivas e os nulos das colunas numericas."""
        estatisticas = self.descrever(self.df_clientes, self.colunas_numericas)
        estatisticas.insert(
            1,
            "nulos",
            self.df_clientes[self.colunas_numericas].isna().sum(),
        )

        return estatisticas

    def sanity_check_datas(self) -> pd.DataFrame:
        """Resume nulos, intervalos e valores negativos das diferencas de datas."""
        diferencas = self.df_clientes[COLUNAS_DIFERENCA_DATA]

        # Fiz uma verificacao rapida para encontrar diferencas de datas incoerentes
        return pd.DataFrame(
            {
                "nao_nulos": diferencas.count(),
                "nulos": diferencas.isna().sum(),
                "minimo_dias": diferencas.min(),
                "maximo_dias": diferencas.max(),
                "valores_negativos": diferencas.lt(0).sum(),
            }
        )

    def estatisticas_diferencas_data(self) -> pd.DataFrame:
        """Gera a tabela descritiva com as informacoes usadas nos boxplots."""
        # Comecei pelas estatisticas descritivas das diferencas entre datas
        estatisticas = self.descrever(self.df_clientes, COLUNAS_DIFERENCA_DATA)

        # Calculei a amplitude interquartil e os limites usados no boxplot
        estatisticas["amplitude_interquartil"] = (
            estatisticas["quartil_75"] - estatisticas["quartil_25"]
        )
        estatisticas["limite_inferior_boxplot"] = (
            estatisticas["quartil_25"] - 1.5 * estatisticas["amplitude_interquartil"]
        )
        estatisticas["limite_superior_boxplot"] = (
            estatisticas["quartil_75"] + 1.5 * estatisticas["amplitude_interquartil"]
        )

        # Calculei os bigodes e contei os outliers de cada coluna
        for coluna in COLUNAS_DIFERENCA_DATA:
            valores = self.df_clientes[coluna].dropna()
            limite_inferior = estatisticas.loc[coluna, "limite_inferior_boxplot"]
            limite_superior = estatisticas.loc[coluna, "limite_superior_boxplot"]
            valores_sem_outliers = valores.between(limite_inferior, limite_superior)

            estatisticas.loc[coluna, "bigode_inferior"] = valores[
                valores_sem_outliers
            ].min()
            estatisticas.loc[coluna, "bigode_superior"] = valores[
                valores_sem_outliers
            ].max()
            estatisticas.loc[coluna, "quantidade_outliers"] = (
                ~valores_sem_outliers
            ).sum()

        return estatisticas

    def datas_invalidas(self) -> pd.DataFrame:
        """Retorna os registros com alguma diferenca de datas negativa."""
        # Separei os registros negativos para mostrar as inconsistencias encontradas
        mascara = self.df_clientes[COLUNAS_DIFERENCA_DATA].lt(0).any(axis=1)
        return self.df_clientes.loc[
            mascara,
            ["cliente_id", *COLUNAS_DATA, *COLUNAS_DIFERENCA_DATA],
        ]

    def contagens_categoricas(
        self,
        colunas: list[str] | None = None,
        valores_ignorados: dict[str, list[str]] | None = None,
    ) -> dict[str, pd.Series]:
        """Retorna a contagem de cada valor das colunas categoricas."""
        colunas_analisadas = colunas or self.COLUNAS_CATEGORICAS
        if valores_ignorados is None:
            valores_ignorados = self.VALORES_IGNORADOS_CATEGORICAS

        contagens = {}
        for coluna in colunas_analisadas:
            # Deixei de fora os valores que nao identificam uma categoria real
            valores = self.df_clientes[coluna]
            valores = valores[~valores.isin(valores_ignorados.get(coluna, []))]
            contagens[coluna] = valores.value_counts(dropna=False)

        return contagens

    def boxplots_datas(self) -> Figure:
        """Gera os boxplots das diferencas entre datas."""
        # Criei um boxplot para cada diferenca de data
        figura, eixos = plt.subplots(2, 2, figsize=(16, 10))

        for coluna, eixo in zip(COLUNAS_DIFERENCA_DATA, eixos.flatten()):
            eixo.boxplot(
                self.df_clientes[coluna].dropna(),
                orientation="horizontal",
                patch_artist=True,
                boxprops={"facecolor": "lightblue", "edgecolor": "black"},
                medianprops={"color": "red", "linewidth": 2},
            )
            eixo.set_title(self._titulo(coluna))
            eixo.set_xlabel("Dias")
            eixo.set_yticks([])
            eixo.grid(axis="x", linestyle="--", alpha=0.4)

        figura.suptitle("Boxplots das diferencas entre datas", fontsize=16)
        figura.tight_layout(rect=(0, 0, 1, 0.96))

        return figura

    def graficos_categoricos(
        self,
        contagens: dict[str, pd.Series] | None = None,
    ) -> Figure:
        """Gera um grafico de barras para cada contagem categorica."""
        if contagens is None:
            contagens = self.contagens_categoricas()

        figura, eixos = plt.subplots(2, 2, figsize=(16, 10))
        eixos = eixos.flatten()

        for (coluna, contagem), eixo in zip(contagens.items(), eixos):
            contagem.plot(
                kind="bar",
                ax=eixo,
                color="steelblue",
                edgecolor="black",
            )
            eixo.set_title(f"Contagem por {self._titulo(coluna)}")
            eixo.set_xlabel(self._titulo(coluna))
            eixo.set_ylabel("Quantidade")
            eixo.tick_params(axis="x", rotation=45)

        # Escondi os espacos da grade que nao receberam nenhum grafico
        for eixo in eixos[len(contagens) :]:
            eixo.set_visible(False)

        figura.tight_layout()

        return figura

    @staticmethod
    def _titulo(coluna: str) -> str:
        """Transforma o nome da coluna em um titulo legivel."""
        return coluna.replace("_", " ").title()
