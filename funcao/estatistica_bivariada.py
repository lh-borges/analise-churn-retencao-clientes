from math import sqrt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from .distribuicoes import Distribuicoes
from .histograma import Histograma


class EstatisticaBivariada:
    """Mede a relacao entre duas colunas de uma base de clientes.

    Cada metodo devolve uma tabela com as colunas medida, valor e leitura,
    para mostrar o resultado e o que ele significa.
    """

    NIVEL_SIGNIFICANCIA = 0.05

    COR_ATIVO = "steelblue"
    COR_CANCELADO = "darkorange"

    def __init__(self, df_clientes: pd.DataFrame) -> None:
        """Guarda a base que sera analisada."""
        self.df_clientes = df_clientes

    # ------------------------------------------------------------------
    # Numerica x numerica
    # ------------------------------------------------------------------

    def correlacao(self, coluna_x: str, coluna_y: str) -> pd.DataFrame:
        """Correlacao de Pearson (linear) e de Spearman (por postos)."""
        dados = self.df_clientes[[coluna_x, coluna_y]].dropna()
        n = len(dados)

        pearson = dados[coluna_x].corr(dados[coluna_y], method="pearson")

        # Spearman e o Pearson calculado sobre os postos (ranks) dos valores.
        # Calculei assim porque o method="spearman" do pandas exige o scipy
        spearman = dados[coluna_x].rank().corr(dados[coluna_y].rank())

        return self._resultado(
            [
                ("n", n, "Pares de valores usados"),
                ("pearson_r", pearson, self._ler_correlacao(pearson)),
                (
                    "pearson_p_valor",
                    self._p_valor_correlacao(pearson, n),
                    self._ler_p_valor(self._p_valor_correlacao(pearson, n)),
                ),
                ("spearman_rho", spearman, self._ler_correlacao(spearman)),
                (
                    "spearman_p_valor",
                    self._p_valor_correlacao(spearman, n),
                    self._ler_p_valor(self._p_valor_correlacao(spearman, n)),
                ),
            ]
        )

    def regressao_linear(self, coluna_x: str, coluna_y: str) -> pd.DataFrame:
        """Regressao linear simples y = intercepto + inclinacao * x."""
        dados = self.df_clientes[[coluna_x, coluna_y]].dropna()
        x = dados[coluna_x].to_numpy(dtype=float)
        y = dados[coluna_y].to_numpy(dtype=float)
        n = len(dados)

        inclinacao, intercepto = np.polyfit(x, y, 1)
        residuos = y - (intercepto + inclinacao * x)

        # R2: quanto da variacao de y a reta consegue explicar
        r2 = 1 - (residuos**2).sum() / ((y - y.mean()) ** 2).sum()

        # Teste t da inclinacao: ela e diferente de zero?
        erro_padrao = sqrt((residuos**2).sum() / (n - 2) / ((x - x.mean()) ** 2).sum())
        p_valor = Distribuicoes.p_valor_t(inclinacao / erro_padrao, n - 2)

        return self._resultado(
            [
                ("n", n, "Pares de valores usados"),
                (
                    "inclinacao",
                    inclinacao,
                    f"Cada 1 de {coluna_x} muda {coluna_y} em {inclinacao:,.2f}",
                ),
                ("intercepto", intercepto, f"{coluna_y} estimado quando {coluna_x} = 0"),
                ("r2", r2, f"A reta explica {r2:.1%} da variacao de {coluna_y}"),
                ("erro_padrao_inclinacao", erro_padrao, "Incerteza da inclinacao"),
                ("p_valor_inclinacao", p_valor, self._ler_p_valor(p_valor)),
            ]
        )

    def media_por_valor(self, coluna_x: str, coluna_y: str) -> pd.DataFrame:
        """Media, mediana e quantidade de coluna_y para cada valor de coluna_x."""
        return self.df_clientes.groupby(coluna_x)[coluna_y].agg(
            clientes="count",
            media="mean",
            mediana="median",
        )

    def grafico_dispersao_regressao(
        self,
        coluna_x: str,
        coluna_y: str,
        coluna_grupo: str | None = None,
    ) -> Figure:
        """Dispersao com a reta de regressao e a media de y para cada x."""
        dados = self.df_clientes[[coluna_x, coluna_y]].dropna()
        figura, (eixo_dispersao, eixo_media) = plt.subplots(1, 2, figsize=(16, 6))

        # Pontos: separei por grupo quando informado (ex.: plano)
        if coluna_grupo:
            for grupo, df_grupo in self.df_clientes.groupby(coluna_grupo):
                eixo_dispersao.scatter(
                    df_grupo[coluna_x], df_grupo[coluna_y], s=10, alpha=0.5, label=grupo
                )
        else:
            eixo_dispersao.scatter(
                dados[coluna_x], dados[coluna_y], s=10, alpha=0.5, color=self.COR_ATIVO
            )

        # Reta da regressao com todos os pontos
        inclinacao, intercepto = np.polyfit(dados[coluna_x], dados[coluna_y], 1)
        eixo_x = np.linspace(dados[coluna_x].min(), dados[coluna_x].max(), 100)
        eixo_dispersao.plot(
            eixo_x,
            intercepto + inclinacao * eixo_x,
            color="black",
            linewidth=2,
            label=f"y = {intercepto:,.1f} + {inclinacao:,.1f}x",
        )
        eixo_dispersao.set_title(f"{self._titulo(coluna_y)} x {self._titulo(coluna_x)}")
        eixo_dispersao.set_xlabel(self._titulo(coluna_x))
        eixo_dispersao.set_ylabel(self._titulo(coluna_y))
        eixo_dispersao.legend()
        eixo_dispersao.grid(linestyle="--", alpha=0.4)

        # Media de y em cada valor de x
        medias = self.media_por_valor(coluna_x, coluna_y)
        eixo_media.plot(medias.index, medias["media"], marker="o", color=self.COR_ATIVO)
        eixo_media.set_title(f"Media de {self._titulo(coluna_y)} por {self._titulo(coluna_x)}")
        eixo_media.set_xlabel(self._titulo(coluna_x))
        eixo_media.set_ylabel(f"Media de {self._titulo(coluna_y)}")
        eixo_media.grid(linestyle="--", alpha=0.4)

        figura.tight_layout()
        return figura

    # ------------------------------------------------------------------
    # Numerica x grupo binario (ex.: idade x churn)
    # ------------------------------------------------------------------

    def comparar_grupos(self, coluna_numerica: str, coluna_grupo: str) -> pd.DataFrame:
        """Estatistica descritiva da coluna numerica em cada grupo."""
        return (
            self.df_clientes.groupby(coluna_grupo)[coluna_numerica]
            .describe()
            .rename(
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

    def teste_diferenca_medias(
        self,
        coluna_numerica: str,
        coluna_grupo: str,
    ) -> pd.DataFrame:
        """Teste t de Welch e correlacao ponto-bisserial entre numerica e grupo 0/1."""
        dados = self.df_clientes[[coluna_numerica, coluna_grupo]].dropna()
        grupo_0 = dados.loc[dados[coluna_grupo] == 0, coluna_numerica]
        grupo_1 = dados.loc[dados[coluna_grupo] == 1, coluna_numerica]

        # Welch: compara as medias sem supor variancias iguais
        variancia_0 = grupo_0.var() / len(grupo_0)
        variancia_1 = grupo_1.var() / len(grupo_1)
        estatistica_t = (grupo_1.mean() - grupo_0.mean()) / sqrt(variancia_0 + variancia_1)
        graus_liberdade = (variancia_0 + variancia_1) ** 2 / (
            variancia_0**2 / (len(grupo_0) - 1) + variancia_1**2 / (len(grupo_1) - 1)
        )
        p_valor_t = Distribuicoes.p_valor_t(estatistica_t, graus_liberdade)

        # Ponto-bisserial: e o Pearson entre a numerica e o grupo 0/1
        r = dados[coluna_numerica].corr(dados[coluna_grupo])
        p_valor_r = self._p_valor_correlacao(r, len(dados))

        return self._resultado(
            [
                (f"media_{coluna_grupo}_0", grupo_0.mean(), f"{len(grupo_0)} clientes"),
                (f"media_{coluna_grupo}_1", grupo_1.mean(), f"{len(grupo_1)} clientes"),
                (
                    "diferenca_medias",
                    grupo_1.mean() - grupo_0.mean(),
                    "Media do grupo 1 menos a do grupo 0",
                ),
                ("t_welch", estatistica_t, f"{graus_liberdade:,.0f} graus de liberdade"),
                ("p_valor_t", p_valor_t, self._ler_p_valor(p_valor_t)),
                ("r_ponto_bisserial", r, self._ler_correlacao(r)),
                ("p_valor_r", p_valor_r, self._ler_p_valor(p_valor_r)),
            ]
        )

    def resumo_numericas_por_alvo(
        self,
        colunas_numericas: list[str],
        coluna_alvo: str,
    ) -> pd.DataFrame:
        """Compara varias colunas numericas entre os grupos 0 e 1 do alvo.

        Para cada coluna: medias e medianas dos dois grupos, d de Cohen
        (tamanho da diferenca em desvios padrao), correlacao ponto-bisserial,
        p-valor do teste t de Welch e AUC (quanto a coluna separa os grupos).
        """
        linhas = []
        for coluna in colunas_numericas:
            dados = self.df_clientes[[coluna, coluna_alvo]].dropna()
            grupo_0 = dados.loc[dados[coluna_alvo] == 0, coluna]
            grupo_1 = dados.loc[dados[coluna_alvo] == 1, coluna]

            teste = EstatisticaBivariada(dados).teste_diferenca_medias(coluna, coluna_alvo)
            auc = self._auc(dados[coluna], dados[coluna_alvo])

            # d de Cohen: diferenca das medias dividida pelo desvio padrao combinado
            desvio_combinado = sqrt(
                ((len(grupo_0) - 1) * grupo_0.var() + (len(grupo_1) - 1) * grupo_1.var())
                / (len(dados) - 2)
            )

            linhas.append(
                {
                    "variavel": coluna,
                    "n": len(dados),
                    "media_0": grupo_0.mean(),
                    "media_1": grupo_1.mean(),
                    "mediana_0": grupo_0.median(),
                    "mediana_1": grupo_1.median(),
                    "d_cohen": (grupo_1.mean() - grupo_0.mean()) / desvio_combinado,
                    "r_ponto_bisserial": teste.loc["r_ponto_bisserial", "valor"],
                    "p_valor_t": teste.loc["p_valor_t", "valor"],
                    "auc": auc,
                    "leitura": self._ler_auc(auc),
                }
            )

        tabela = pd.DataFrame(linhas).set_index("variavel")

        # Ordenei da variavel que mais separa os grupos para a que menos separa
        separacao = (tabela["auc"] - 0.5).abs()
        return tabela.loc[separacao.sort_values(ascending=False).index]

    def resumo_categoricas_por_alvo(
        self,
        colunas_categoricas: list[str],
        coluna_alvo: str,
        valores_ignorados: dict[str, list[str]] | None = None,
    ) -> pd.DataFrame:
        """Compara a taxa do alvo entre as categorias de varias colunas."""
        valores_ignorados = valores_ignorados or {}

        linhas = []
        for coluna in colunas_categoricas:
            # Deixei de fora os valores que nao identificam uma categoria real
            dados = self.df_clientes[
                ~self.df_clientes[coluna].isin(valores_ignorados.get(coluna, []))
            ]
            bivariada = EstatisticaBivariada(dados)
            taxas = bivariada.taxa_por_categoria(coluna, coluna_alvo)["taxa"]
            teste = bivariada.qui_quadrado(coluna, coluna_alvo)

            linhas.append(
                {
                    "variavel": coluna,
                    "n": len(dados),
                    "categorias": len(taxas),
                    "menor_taxa": f"{taxas.idxmin()} ({taxas.min():.1%})",
                    "maior_taxa": f"{taxas.idxmax()} ({taxas.max():.1%})",
                    "qui_quadrado": teste.loc["qui_quadrado", "valor"],
                    "p_valor": teste.loc["p_valor", "valor"],
                    "v_cramer": teste.loc["v_cramer", "valor"],
                    "leitura": teste.loc["v_cramer", "leitura"],
                }
            )

        return pd.DataFrame(linhas).set_index("variavel").sort_values(
            "v_cramer", ascending=False
        )

    def taxa_por_faixa(
        self,
        coluna_numerica: str,
        coluna_alvo: str,
        limites_faixas: list[float],
    ) -> pd.DataFrame:
        """Quantidade e taxa do alvo (ex.: cancelamento) em cada faixa da numerica."""
        faixas = pd.cut(
            self.df_clientes[coluna_numerica],
            bins=limites_faixas,
            right=False,
        )
        tabela = self.df_clientes.groupby(faixas, observed=False)[coluna_alvo].agg(
            clientes="count",
            casos="sum",
            taxa="mean",
        )
        tabela.index = tabela.index.astype(str)
        tabela.index.name = f"faixa_{coluna_numerica}"

        return tabela

    def grafico_histograma_por_grupo(
        self,
        coluna_numerica: str,
        coluna_grupo: str,
        rotulos_grupos: dict[int, str] | None = None,
    ) -> Figure:
        """Histogramas sobrepostos da numerica nos grupos 0 e 1, com KDE e mediana.

        Cada histograma mostra o % do proprio grupo, para que grupos de
        tamanhos diferentes (ex.: 3.500 ativos e 380 cancelados) possam ser
        comparados no mesmo grafico.
        """
        if rotulos_grupos is None:
            rotulos_grupos = {0: "Ativos", 1: "Cancelados"}

        dados = self.df_clientes[[coluna_numerica, coluna_grupo]].dropna()
        bins = self._bins_histograma(dados[coluna_numerica])
        largura_bin = bins[1] - bins[0]

        figura, eixo = plt.subplots(figsize=(14, 6))
        cores = {0: self.COR_ATIVO, 1: self.COR_CANCELADO}

        for grupo in (0, 1):
            valores = dados.loc[dados[coluna_grupo] == grupo, coluna_numerica]
            rotulo = f"{rotulos_grupos[grupo]} ({coluna_grupo} = {grupo}, n={len(valores)})"

            # Pesos de 100/n fazem as barras de cada grupo somarem 100%
            eixo.hist(
                valores,
                bins=bins,
                weights=np.full(len(valores), 100 / len(valores)),
                color=cores[grupo],
                alpha=0.45,
                edgecolor=cores[grupo],
                label=rotulo,
            )

            # Curva de densidade na mesma escala das barras. Em variaveis com
            # poucos valores (ex.: NPS de 0 a 10) a curva engana, entao pulei
            if valores.nunique() > 15:
                eixo_x, densidade = Histograma.calcular_curva_densidade(valores)
                eixo.plot(eixo_x, densidade * largura_bin * 100, color=cores[grupo], linewidth=2)

            eixo.axvline(
                valores.median(),
                color=cores[grupo],
                linestyle="--",
                linewidth=2,
                label=f"Mediana {rotulos_grupos[grupo].lower()}: {valores.median():,.1f}",
            )

        eixo.set_title(
            f"Histograma de {self._titulo(coluna_numerica)}: "
            f"{rotulos_grupos[0].lower()} x {rotulos_grupos[1].lower()}"
        )
        eixo.set_xlabel(self._titulo(coluna_numerica))
        eixo.set_ylabel("% dos clientes do grupo")
        eixo.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}%"))
        eixo.legend()
        eixo.grid(axis="y", linestyle="--", alpha=0.4)

        figura.tight_layout()
        return figura

    @staticmethod
    def _bins_histograma(valores: pd.Series) -> np.ndarray:
        """Limites das barras: uma por valor inteiro quando a escala e curta."""
        minimo, maximo = valores.min(), valores.max()

        # Variaveis inteiras com ate 60 valores (NPS, dias, meses): uma barra
        # centrada em cada inteiro, para nao juntar valores diferentes
        if (valores % 1 == 0).all() and maximo - minimo <= 60:
            return np.arange(minimo, maximo + 2) - 0.5

        return np.histogram_bin_edges(valores, bins=30)

    # ------------------------------------------------------------------
    # Categorica x categorica (ex.: regiao x churn, ciclo x churn)
    # ------------------------------------------------------------------

    def tabela_contingencia(self, coluna_linha: str, coluna_coluna: str) -> pd.DataFrame:
        """Contagem cruzada das duas colunas, com os totais."""
        return pd.crosstab(
            self.df_clientes[coluna_linha],
            self.df_clientes[coluna_coluna],
            margins=True,
            margins_name="total",
        )

    def taxa_por_categoria(self, coluna_categoria: str, coluna_alvo: str) -> pd.DataFrame:
        """Clientes, participacao e taxa do alvo (ex.: cancelamento) por categoria."""
        tabela = self.df_clientes.groupby(coluna_categoria)[coluna_alvo].agg(
            clientes="count",
            casos="sum",
            taxa="mean",
        )
        tabela.insert(1, "participacao", tabela["clientes"] / tabela["clientes"].sum())

        return tabela.sort_values("clientes", ascending=False)

    def qui_quadrado(self, coluna_linha: str, coluna_coluna: str) -> pd.DataFrame:
        """Teste qui-quadrado de independencia e V de Cramer."""
        observado = pd.crosstab(
            self.df_clientes[coluna_linha], self.df_clientes[coluna_coluna]
        ).to_numpy(dtype=float)
        n = observado.sum()

        # Frequencia esperada se as duas colunas fossem independentes
        esperado = observado.sum(axis=1, keepdims=True) * observado.sum(axis=0) / n
        estatistica = ((observado - esperado) ** 2 / esperado).sum()
        graus_liberdade = (observado.shape[0] - 1) * (observado.shape[1] - 1)
        p_valor = Distribuicoes.p_valor_qui_quadrado(estatistica, graus_liberdade)

        # V de Cramer: forca da associacao, de 0 (nenhuma) a 1 (total)
        v_cramer = sqrt(estatistica / (n * (min(observado.shape) - 1)))

        return self._resultado(
            [
                ("n", n, "Clientes usados"),
                ("qui_quadrado", estatistica, f"{graus_liberdade} graus de liberdade"),
                ("p_valor", p_valor, self._ler_p_valor(p_valor)),
                ("v_cramer", v_cramer, self._ler_v_cramer(v_cramer)),
                (
                    "menor_frequencia_esperada",
                    esperado.min(),
                    "Teste confiavel" if esperado.min() >= 5 else "Abaixo de 5: use com cautela",
                ),
            ]
        )

    def grafico_contagem_e_taxa(self, coluna_categoria: str, coluna_alvo: str) -> Figure:
        """Barras empilhadas de ativos/cancelados e a taxa do alvo por categoria."""
        tabela = self.taxa_por_categoria(coluna_categoria, coluna_alvo)
        figura, (eixo_contagem, eixo_taxa) = plt.subplots(1, 2, figsize=(16, 6))

        # Contagem: ativos embaixo e cancelados em cima
        ativos = tabela["clientes"] - tabela["casos"]
        eixo_contagem.bar(
            tabela.index, ativos, color=self.COR_ATIVO, edgecolor="black",
            label=f"{coluna_alvo} = 0",
        )
        eixo_contagem.bar(
            tabela.index, tabela["casos"], bottom=ativos, color=self.COR_CANCELADO,
            edgecolor="black", label=f"{coluna_alvo} = 1",
        )
        eixo_contagem.set_title(f"Clientes por {self._titulo(coluna_categoria)}")
        eixo_contagem.set_ylabel("Clientes")
        eixo_contagem.legend()
        eixo_contagem.grid(axis="y", linestyle="--", alpha=0.4)

        # Taxa: mesma escala para todas as categorias, com a taxa geral de referencia
        barras = eixo_taxa.bar(
            tabela.index, tabela["taxa"], color=self.COR_CANCELADO, edgecolor="black"
        )
        self._rotular_barras(eixo_taxa, barras, [f"{t:.1%}" for t in tabela["taxa"]])
        eixo_taxa.axhline(
            self.df_clientes[coluna_alvo].mean(),
            color="black",
            linestyle="--",
            label="Taxa geral",
        )
        eixo_taxa.set_title(f"Taxa de {coluna_alvo} por {self._titulo(coluna_categoria)}")
        eixo_taxa.set_ylabel(f"Taxa de {coluna_alvo}")
        eixo_taxa.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
        eixo_taxa.legend()
        eixo_taxa.grid(axis="y", linestyle="--", alpha=0.4)

        for eixo in (eixo_contagem, eixo_taxa):
            eixo.tick_params(axis="x", rotation=30)

        figura.tight_layout()
        return figura

    # ------------------------------------------------------------------
    # Apoio
    # ------------------------------------------------------------------

    def e_significativo(self, p_valor: float) -> bool:
        """Indica se o p-valor fica abaixo do nivel de significancia."""
        return p_valor < self.NIVEL_SIGNIFICANCIA

    @staticmethod
    def _p_valor_correlacao(r: float, n: int) -> float:
        """P-valor do teste t para saber se a correlacao e diferente de zero."""
        if abs(r) >= 1:
            return 0.0
        estatistica_t = r * sqrt((n - 2) / (1 - r**2))
        return Distribuicoes.p_valor_t(estatistica_t, n - 2)

    def _ler_p_valor(self, p_valor: float) -> str:
        """Traduz o p-valor em texto usando o nivel de significancia."""
        if self.e_significativo(p_valor):
            return f"Significativo (p < {self.NIVEL_SIGNIFICANCIA})"
        return f"Nao significativo (p >= {self.NIVEL_SIGNIFICANCIA})"

    @staticmethod
    def _ler_correlacao(r: float) -> str:
        """Classifica a forca e o sentido de uma correlacao."""
        forca = abs(r)
        if forca < 0.1:
            return "Desprezivel"
        if forca < 0.3:
            intensidade = "Fraca"
        elif forca < 0.5:
            intensidade = "Moderada"
        elif forca < 0.7:
            intensidade = "Forte"
        else:
            intensidade = "Muito forte"
        sentido = "positiva" if r > 0 else "negativa"
        return f"{intensidade} {sentido}"

    @staticmethod
    def _rotular_barras(eixo, barras, rotulos: list[str]) -> None:
        """Escreve o rotulo dentro das barras altas e acima das barras baixas."""
        altura_maxima = max(barra.get_height() for barra in barras) or 1

        for barra, rotulo in zip(barras, rotulos):
            altura = barra.get_height()
            centro_x = barra.get_x() + barra.get_width() / 2

            # Barra alta: rotulo branco no meio. Barra baixa: rotulo escuro em cima
            if altura >= 0.25 * altura_maxima:
                eixo.text(
                    centro_x, altura / 2, rotulo, ha="center", va="center",
                    color="white", fontsize=9, fontweight="bold",
                )
            else:
                eixo.text(
                    centro_x, altura + 0.01 * altura_maxima, rotulo, ha="center",
                    va="bottom", color="black", fontsize=9, fontweight="bold",
                )

    @staticmethod
    def _auc(valores: pd.Series, alvo: pd.Series) -> float:
        """Area sob a curva ROC, calculada pelos postos (igual ao Mann-Whitney).

        E a chance de um cliente do grupo 1 ter valor maior que um do grupo 0.
        0.5 = a coluna nao separa os grupos; perto de 0 ou de 1 = separa muito.
        """
        postos = valores.rank()
        n_1 = int(alvo.sum())
        n_0 = len(alvo) - n_1
        soma_postos_1 = postos[alvo == 1].sum()

        return (soma_postos_1 - n_1 * (n_1 + 1) / 2) / (n_1 * n_0)

    @staticmethod
    def _ler_auc(auc: float) -> str:
        """Classifica o quanto a coluna separa os grupos e em qual sentido."""
        # Uso a distancia ate 0.5: AUC de 0.2 separa tanto quanto 0.8
        separacao = max(auc, 1 - auc)
        if separacao < 0.6:
            return "Nao separa os grupos"
        if separacao < 0.7:
            intensidade = "Separa pouco"
        elif separacao < 0.8:
            intensidade = "Separa moderadamente"
        elif separacao < 0.9:
            intensidade = "Separa bem"
        else:
            intensidade = "Separa muito"
        sentido = "valores maiores" if auc > 0.5 else "valores menores"
        return f"{intensidade}: grupo 1 tem {sentido}"

    @staticmethod
    def _ler_v_cramer(v: float) -> str:
        """Classifica a forca da associacao medida pelo V de Cramer."""
        if v < 0.1:
            return "Associacao desprezivel"
        if v < 0.3:
            return "Associacao fraca"
        if v < 0.5:
            return "Associacao moderada"
        return "Associacao forte"

    @staticmethod
    def _resultado(linhas: list[tuple[str, float, str]]) -> pd.DataFrame:
        """Monta a tabela padrao de resultado: medida, valor e leitura."""
        return pd.DataFrame(linhas, columns=["medida", "valor", "leitura"]).set_index(
            "medida"
        )

    @staticmethod
    def _titulo(coluna: str) -> str:
        """Transforma o nome da coluna em um titulo legivel."""
        return coluna.replace("_", " ").title()
