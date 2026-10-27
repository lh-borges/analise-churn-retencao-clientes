import pandas as pd

from .estatistica_descritiva import EstatisticaDescritiva


class Receita:
    """Calcula os meses de assinatura e a receita acumulada de uma base."""

    COLUNAS_RECEITA = ["meses_assinatura", "receita_acumulada"]

    # Usei a duracao media de um mes no calendario para converter dias em meses
    DIAS_POR_MES = 365.25 / 12

    def __init__(self, df_clientes: pd.DataFrame) -> None:
        """Guarda a base ja com as colunas de meses e receita calculadas."""
        self.df_clientes = self._adicionar_colunas(df_clientes)

    def estatisticas(self) -> pd.DataFrame:
        """Gera a estatistica descritiva dos meses de assinatura e da receita."""
        estatisticas = EstatisticaDescritiva.descrever(
            self.df_clientes,
            self.COLUNAS_RECEITA,
        )
        estatisticas["soma"] = self.df_clientes[self.COLUNAS_RECEITA].sum()

        return estatisticas

    def resumo_por_grupo(self, coluna_grupo: str = "plano") -> pd.DataFrame:
        """Resume os meses de assinatura e a receita de cada grupo."""
        return self.df_clientes.groupby(coluna_grupo).agg(
            clientes=("cliente_id", "count"),
            media_meses=("meses_assinatura", "mean"),
            mediana_meses=("meses_assinatura", "median"),
            media_receita=("receita_acumulada", "mean"),
            receita_total=("receita_acumulada", "sum"),
        )

    def _adicionar_colunas(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Cria os meses de assinatura e a receita acumulada de cada cliente."""
        df_com_receita = df_clientes.copy()

        # Contei apenas os meses completos entre a assinatura e a extracao
        df_com_receita["meses_assinatura"] = (
            df_com_receita["dias_assinatura_extracao"] // self.DIAS_POR_MES
        ).astype(int)

        # Multipliquei os meses completos pelo valor pago por mes
        df_com_receita["receita_acumulada"] = (
            df_com_receita["meses_assinatura"] * df_com_receita["valor_mensal"]
        )

        return df_com_receita
