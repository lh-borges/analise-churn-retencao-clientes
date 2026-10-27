from pathlib import Path

import pandas as pd


class ExtracaoNormalizacao:
    """Carrega o CSV de clientes e padroniza datas e planos."""

    COLUNAS_DATA = [
        "data_assinatura",
        "data_cancelamento",
        "data_ultimo_acesso",
        "data_extracao",
    ]

    def __init__(self, caminho_csv: str | Path) -> None:
        """Guarda o caminho do arquivo que sera carregado."""
        self.caminho_csv = Path(caminho_csv)

    def carregar(self) -> pd.DataFrame:
        """Extrai o CSV e devolve a base ja normalizada."""
        # Primeiro extraio os dados e depois envio o resultado para a normalizacao
        df_clientes = self._extrair()
        return self._normalizar(df_clientes)

    def _extrair(self) -> pd.DataFrame:
        """Carrega o arquivo CSV em um DataFrame."""
        return pd.read_csv(self.caminho_csv)

    def _normalizar(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Converte as datas e padroniza os nomes dos planos."""
        # Fiz uma copia para nao alterar o DataFrame recebido
        df_normalizado = df_clientes.copy()
        df_normalizado = self._converter_datas(df_normalizado)
        df_normalizado["plano"] = self._padronizar_plano(df_normalizado["plano"])

        return df_normalizado

    def _converter_datas(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Converte as colunas de data. Valores invalidos passam a ser NaT."""
        df_clientes[self.COLUNAS_DATA] = df_clientes[self.COLUNAS_DATA].apply(
            pd.to_datetime,
            errors="coerce",
        )
        return df_clientes

    def _padronizar_plano(self, planos: pd.Series) -> pd.Series:
        """Junta os planos iguais escritos com caixa ou acento diferentes."""
        return (
            planos.str.strip()
            .str.lower()
            .str.normalize("NFKD")
            .str.encode("ascii", errors="ignore")
            .str.decode("utf-8")
            .replace(
                {
                    "basico": "Basico",
                    "padrao": "Padrao",
                    "premium": "Premium",
                }
            )
        )
