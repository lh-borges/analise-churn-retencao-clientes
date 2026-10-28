from pathlib import Path

import pandas as pd


class ExtracaoNormalizacao:
    """Carrega o CSV de clientes e padroniza datas, planos, canais e motivos."""

    COLUNAS_DATA = [
        "data_assinatura",
        "data_cancelamento",
        "data_ultimo_acesso",
        "data_extracao",
    ]

    # Para cada coluna de texto: grafia em minusculas e sem acento -> nome padrao
    NOMES_PADRAO = {
        "plano": {
            "basico": "Basico",
            "padrao": "Padrao",
            "premium": "Premium",
        },
        "canal_aquisicao": {
            "organico": "Organico",
            "indicacao": "Indicacao",
            "google": "Google",
            "instagram": "Instagram",
            "ig": "Instagram",
        },
        "motivo_cancelamento": {
            "preco": "Preco",
            "pouco conteudo novo": "Pouco conteudo novo",
            "problema tecnico": "Problema tecnico",
            "falta de tempo": "Falta de tempo",
            "concorrente": "Concorrente",
            "outro": "Outro",
        },
    }

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
        """Converte as datas e padroniza plano, canal e motivo de cancelamento."""
        # Fiz uma copia para nao alterar o DataFrame recebido
        df_normalizado = df_clientes.copy()
        df_normalizado = self._converter_datas(df_normalizado)

        # Padronizei as colunas de texto que tinham grafias equivalentes
        for coluna, nomes_padrao in self.NOMES_PADRAO.items():
            df_normalizado[coluna] = self._padronizar_texto(
                df_normalizado[coluna], nomes_padrao
            )

        return df_normalizado

    def _converter_datas(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Converte as colunas de data. Valores invalidos passam a ser NaT."""
        df_clientes[self.COLUNAS_DATA] = df_clientes[self.COLUNAS_DATA].apply(
            pd.to_datetime,
            errors="coerce",
        )
        return df_clientes

    @staticmethod
    def _padronizar_texto(valores: pd.Series, nomes_padrao: dict[str, str]) -> pd.Series:
        """Junta textos iguais escritos com caixa, acento ou abreviacao diferentes.

        Primeiro deixa o texto em minusculas e sem acento (ex.: "Padrão" e
        "PADRAO" viram "padrao"); depois troca pelo nome padrao do dicionario.
        """
        return (
            valores.str.strip()
            .str.lower()
            .str.normalize("NFKD")
            .str.encode("ascii", errors="ignore")
            .str.decode("utf-8")
            .replace(nomes_padrao)
        )
