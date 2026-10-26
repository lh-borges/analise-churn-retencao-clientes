from pathlib import Path

import pandas as pd


COLUNAS_DATA = [
    "data_assinatura",
    "data_cancelamento",
    "data_ultimo_acesso",
    "data_extracao",
]


def extrair_clientes(caminho_csv: str | Path) -> pd.DataFrame:
    """Carrega o arquivo CSV em um DataFrame."""
    # Carreguei a base usando o caminho recebido pela funcao
    return pd.read_csv(caminho_csv)


def normalizar_clientes(df_clientes: pd.DataFrame) -> pd.DataFrame:
    """Converte as datas e padroniza os nomes dos planos."""
    # Fiz uma copia para nao alterar o DataFrame recebido pela funcao
    df_normalizado = df_clientes.copy()

    # Converti as colunas de data. Valores invalidos passam a ser NaT
    df_normalizado[COLUNAS_DATA] = df_normalizado[COLUNAS_DATA].apply(
        pd.to_datetime,
        errors="coerce",
    )

    # Juntei os planos iguais que estavam escritos com caixa ou acento diferentes
    df_normalizado["plano"] = (
        df_normalizado["plano"]
        .str.strip()
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

    return df_normalizado


def extrair_e_normalizar_clientes(caminho_csv: str | Path) -> pd.DataFrame:
    """Executa a extracao e passa o resultado para a normalizacao."""
    # Primeiro extraio os dados e depois envio o resultado para a normalizacao
    df_clientes = extrair_clientes(caminho_csv)
    return normalizar_clientes(df_clientes)
