import pandas as pd


class GeracaoColunas:
    """Cria as colunas calculadas a partir das datas da base."""

    # Cada coluna nova: (nome, data inicial, data final)
    DIFERENCAS_DATA = [
        ("dias_assinatura_cancelamento", "data_assinatura", "data_cancelamento"),
        ("dias_assinatura_ultimo_acesso", "data_assinatura", "data_ultimo_acesso"),
        ("dias_ultimo_acesso_extracao", "data_ultimo_acesso", "data_extracao"),
        ("dias_assinatura_extracao", "data_assinatura", "data_extracao"),
    ]
    COLUNAS_DIFERENCA_DATA = [nome for nome, _, _ in DIFERENCAS_DATA]

    def adicionar_diferencas_data(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Cria as colunas com as diferencas entre as datas, em dias."""
        # Fiz uma copia para manter o DataFrame de entrada sem alteracoes
        df_com_diferencas = df_clientes.copy()

        # Calculei cada intervalo usando as datas que ja foram normalizadas
        for nome, data_inicial, data_final in self.DIFERENCAS_DATA:
            df_com_diferencas[nome] = self._diferenca_em_dias(
                df_com_diferencas[data_inicial],
                df_com_diferencas[data_final],
            )

        return df_com_diferencas

    def _diferenca_em_dias(
        self,
        data_inicial: pd.Series,
        data_final: pd.Series,
    ) -> pd.Series:
        """Retorna quantos dias se passaram entre as duas datas."""
        return (data_final - data_inicial).dt.days
