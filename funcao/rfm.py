import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from .quintis import Quintis


class RFM:
    """Segmenta clientes ativos por recencia, frequencia e valor (RFM adaptado).

    R = dias entre o ultimo acesso e a extracao (menor e melhor)
    F = dias ativos no ultimo mes (maior e melhor)
    M = valor mensal validado (maior e melhor)

    R e F recebem notas de 1 a 5 pelos quintis. M tem so 3 precos, que nao
    formam quintis; por isso recebe 1, 3 ou 5 conforme o preco do plano.
    """

    COLUNA_R = "dias_ultimo_acesso_extracao"
    COLUNA_F = "dias_ativos_ult_mes"
    COLUNA_M = "valor_mensal"

    # Ordem dos segmentos do mais engajado para o menos engajado
    SEGMENTOS = [
        "Engajados",
        "Regulares",
        "Atencao",
        "Baixo engajamento",
        "Sem acesso registrado",
    ]

    REGRAS = {
        "Engajados": "R >= 4 e F >= 4: acessaram ha pouco e usam muito",
        "Regulares": "R >= 3 e F >= 3, sem estar em Engajados",
        "Atencao": "Uma nota boa e outra fraca: esfriando (R <= 2) ou usando pouco (F <= 2)",
        "Baixo engajamento": "R <= 2 e F <= 2: nao acessam ha tempo e usam pouco",
        "Sem acesso registrado": "Sem data de ultimo acesso, entao sem nota R",
    }

    ACOES = {
        "Engajados": "Manter e aproveitar: programa de indicacao e oferta de upgrade de plano.",
        "Regulares": "Manter o habito: recomendacoes de conteudo e avisos de lancamentos.",
        "Atencao": "Reativar cedo: lembretes personalizados com conteudo novo do interesse do cliente.",
        "Baixo engajamento": (
            "Reengajar: contato com pesquisa de satisfacao e conteudo recomendado; "
            "publico candidato ao teste de retencao."
        ),
        "Sem acesso registrado": "Investigar: conferir rastreamento de acesso ou problema tecnico.",
    }

    def __init__(self, quintis: Quintis | None = None) -> None:
        """Guarda a divisao em quintis usada nas notas de R e F."""
        self.quintis = quintis or Quintis(5)

    def calcular(self, df_ativos: pd.DataFrame) -> pd.DataFrame:
        """Devolve a base com as notas R, F, M, o codigo RFM e o segmento."""
        df_rfm = df_ativos.copy()

        df_rfm["nota_r"] = self.quintis.pontuar(df_rfm[self.COLUNA_R], maior_e_melhor=False)
        df_rfm["nota_f"] = self.quintis.pontuar(df_rfm[self.COLUNA_F])
        df_rfm["nota_m"] = self._nota_valor(df_rfm[self.COLUNA_M])

        # Codigo com as tres notas (ex.: "543"); nota ausente aparece como "-"
        df_rfm["codigo_rfm"] = (
            df_rfm[["nota_r", "nota_f", "nota_m"]]
            .astype("Int64")
            .astype(str)
            .fillna("-")
            .agg("".join, axis=1)
        )
        df_rfm["segmento"] = df_rfm.apply(self._segmento, axis=1)

        return df_rfm

    def regras(self) -> pd.DataFrame:
        """Tabela com a regra e a acao sugerida de cada segmento."""
        return pd.DataFrame(
            {
                "regra": [self.REGRAS[s] for s in self.SEGMENTOS],
                "acao_sugerida": [self.ACOES[s] for s in self.SEGMENTOS],
            },
            index=pd.Index(self.SEGMENTOS, name="segmento"),
        )

    def resumo_segmentos(self, df_rfm: pd.DataFrame) -> pd.DataFrame:
        """Tamanho e perfil de cada segmento."""
        resumo = df_rfm.groupby("segmento").agg(
            clientes=("cliente_id", "count"),
            recencia_mediana_dias=(self.COLUNA_R, "median"),
            dias_ativos_mediana=(self.COLUNA_F, "median"),
            valor_mensal_medio=(self.COLUNA_M, "mean"),
            valor_mensal_total=(self.COLUNA_M, "sum"),
            nps_mediano=("nps", "median"),
            horas_assistidas_mediana=("horas_assistidas_total", "median"),
            percentual_premium=("plano", lambda planos: (planos == "Premium").mean()),
        )
        resumo.insert(1, "participacao", resumo["clientes"] / resumo["clientes"].sum())
        resumo.insert(
            5,
            "participacao_valor",
            resumo["valor_mensal_total"] / resumo["valor_mensal_total"].sum(),
        )

        return resumo.reindex([s for s in self.SEGMENTOS if s in resumo.index])

    def grafico(self, df_rfm: pd.DataFrame) -> Figure:
        """Mapa de calor das notas R x F e tamanho e valor de cada segmento."""
        figura, (eixo_mapa, eixo_segmentos) = plt.subplots(1, 2, figsize=(16, 6))

        # Mapa de calor: quantos clientes ha em cada combinacao de notas R e F
        contagem = pd.crosstab(df_rfm["nota_f"], df_rfm["nota_r"]).sort_index(ascending=False)
        imagem = eixo_mapa.imshow(contagem, cmap="Blues")
        eixo_mapa.set_xticks(range(len(contagem.columns)), [f"{int(r)}" for r in contagem.columns])
        eixo_mapa.set_yticks(range(len(contagem.index)), [f"{int(f)}" for f in contagem.index])
        limite_cor = contagem.to_numpy().max() * 0.6
        for i in range(contagem.shape[0]):
            for j in range(contagem.shape[1]):
                valor = contagem.iat[i, j]
                eixo_mapa.text(
                    j, i, valor, ha="center", va="center",
                    color="white" if valor > limite_cor else "black",
                )
        eixo_mapa.set_title("Clientes por nota de recencia (R) e frequencia (F)")
        eixo_mapa.set_xlabel("Nota R (5 = acessou ha menos tempo)")
        eixo_mapa.set_ylabel("Nota F (5 = mais dias ativos)")
        figura.colorbar(imagem, ax=eixo_mapa, label="Clientes")

        # Barras: clientes de cada segmento, com a participacao no valor mensal
        resumo = self.resumo_segmentos(df_rfm)
        barras = eixo_segmentos.barh(
            resumo.index[::-1], resumo["clientes"][::-1], color="steelblue", edgecolor="black"
        )
        eixo_segmentos.bar_label(
            barras,
            labels=[
                f"{n} clientes ({p:.0%}) | {v:.0%} do valor"
                for n, p, v in zip(
                    resumo["clientes"][::-1],
                    resumo["participacao"][::-1],
                    resumo["participacao_valor"][::-1],
                )
            ],
            padding=4,
            fontsize=9,
        )
        eixo_segmentos.set_xlim(0, resumo["clientes"].max() * 1.6)
        eixo_segmentos.set_title("Tamanho dos segmentos e participacao no valor mensal")
        eixo_segmentos.set_xlabel("Clientes")
        eixo_segmentos.grid(axis="x", linestyle="--", alpha=0.4)

        figura.tight_layout()
        return figura

    @staticmethod
    def _nota_valor(valores: pd.Series) -> pd.Series:
        """Nota de 1 a 5 espalhando os precos distintos de forma igual.

        Com 3 precos (19,90; 34,90; 55,90) as notas ficam 1, 3 e 5.
        """
        posicao = valores.rank(method="dense")
        quantidade_precos = posicao.max()
        if quantidade_precos == 1:
            return pd.Series(3, index=valores.index)
        return (1 + (posicao - 1) * 4 / (quantidade_precos - 1)).round().astype(int)

    @staticmethod
    def _segmento(linha: pd.Series) -> str:
        """Aplica as regras de segmento as notas R e F de um cliente."""
        nota_r, nota_f = linha["nota_r"], linha["nota_f"]
        if np.isnan(nota_r):
            return "Sem acesso registrado"
        if nota_r >= 4 and nota_f >= 4:
            return "Engajados"
        if nota_r >= 3 and nota_f >= 3:
            return "Regulares"
        if nota_r <= 2 and nota_f <= 2:
            return "Baixo engajamento"
        return "Atencao"
