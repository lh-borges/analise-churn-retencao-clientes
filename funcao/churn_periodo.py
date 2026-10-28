import pandas as pd


class ChurnPeriodo:
    """Prepara a base para medir o cancelamento dentro de um periodo.

    Segue a definicao de taxa de churn de um periodo: a populacao exposta sao
    os clientes ativos no inicio do periodo, e o churn e quem cancelou dentro
    dele. Clientes que assinaram durante o periodo ficam de fora, porque nao
    estiveram expostos o periodo inteiro.
    """

    COLUNA_CHURN = "churn_periodo"

    # Usei a duracao media de um mes no calendario para converter dias em meses
    DIAS_POR_MES = 365.25 / 12

    def __init__(self, inicio: str, fim: str) -> None:
        """Guarda as datas de inicio e fim do periodo (ex.: "2024-01-01")."""
        self.inicio = pd.Timestamp(inicio)
        self.fim = pd.Timestamp(fim)

    def fim_efetivo(self, df_clientes: pd.DataFrame) -> pd.Timestamp:
        """Fim do periodo limitado a data de extracao (nao ha dados depois dela)."""
        return min(self.fim, df_clientes["data_extracao"].max())

    def populacao_exposta(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Clientes ativos no inicio do periodo, com o churn e colunas de apoio."""
        # Ativo no inicio: assinou antes e nao tinha cancelado ate o inicio
        ativo_no_inicio = (df_clientes["data_assinatura"] < self.inicio) & ~(
            df_clientes["data_cancelamento"] < self.inicio
        )
        df_exposto = df_clientes[ativo_no_inicio].copy()

        # Churn do periodo: cancelou entre o inicio e o fim efetivo
        fim = self.fim_efetivo(df_clientes)
        df_exposto[self.COLUNA_CHURN] = (
            df_exposto["data_cancelamento"].between(self.inicio, fim).astype(int)
        )

        # Tempo de casa no inicio do periodo, em meses completos
        df_exposto["meses_assinatura"] = (
            (self.inicio - df_exposto["data_assinatura"]).dt.days // self.DIAS_POR_MES
        ).astype(int)

        df_exposto["horas_por_mes"] = self._horas_por_mes(df_exposto)

        return df_exposto

    def resumo(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Tamanho da populacao exposta, cancelados e taxa do periodo."""
        df_exposto = self.populacao_exposta(df_clientes)
        assinaram_no_periodo = df_clientes["data_assinatura"].between(
            self.inicio, self.fim_efetivo(df_clientes)
        )

        return pd.DataFrame(
            [
                ("inicio_periodo", self.inicio.strftime("%d/%m/%Y")),
                ("fim_efetivo", self.fim_efetivo(df_clientes).strftime("%d/%m/%Y")),
                ("ativos_no_inicio", len(df_exposto)),
                ("cancelaram_no_periodo", int(df_exposto[self.COLUNA_CHURN].sum())),
                ("taxa_churn_periodo", f"{df_exposto[self.COLUNA_CHURN].mean():.2%}"),
                ("assinaram_no_periodo_fora_da_analise", int(assinaram_no_periodo.sum())),
            ],
            columns=["medida", "valor"],
        ).set_index("medida")

    def _horas_por_mes(self, df_exposto: pd.DataFrame) -> pd.Series:
        """Horas assistidas divididas pelos meses em que o cliente esteve ativo."""
        # O cliente ficou ativo ate cancelar ou, se nao cancelou, ate a extracao
        data_final = df_exposto["data_cancelamento"].fillna(df_exposto["data_extracao"])
        meses_ativo = (data_final - df_exposto["data_assinatura"]).dt.days / self.DIAS_POR_MES

        # Considerei no minimo 1 mes para nao inflar quem assinou ha poucos dias
        return df_exposto["horas_assistidas_total"] / meses_ativo.clip(lower=1)
