from pathlib import Path

import pandas as pd

from .extracao_normalizacao import extrair_e_normalizar_clientes


COLUNAS_DIFERENCA_DATA = [
    "dias_assinatura_cancelamento",
    "dias_assinatura_ultimo_acesso",
    "dias_ultimo_acesso_extracao",
    "dias_assinatura_extracao",
]


def gerar_colunas_diferenca_data(df_clientes: pd.DataFrame) -> pd.DataFrame:
    """Cria as colunas com as diferencas entre as datas, em dias."""
    # Fiz uma copia para manter o DataFrame de entrada sem alteracoes
    df_com_diferencas = df_clientes.copy()

    # Calculei cada intervalo usando as datas que ja foram normalizadas
    df_com_diferencas["dias_assinatura_cancelamento"] = (
        df_com_diferencas["data_cancelamento"]
        - df_com_diferencas["data_assinatura"]
    ).dt.days
    df_com_diferencas["dias_assinatura_ultimo_acesso"] = (
        df_com_diferencas["data_ultimo_acesso"]
        - df_com_diferencas["data_assinatura"]
    ).dt.days
    df_com_diferencas["dias_ultimo_acesso_extracao"] = (
        df_com_diferencas["data_extracao"]
        - df_com_diferencas["data_ultimo_acesso"]
    ).dt.days
    df_com_diferencas["dias_assinatura_extracao"] = (
        df_com_diferencas["data_extracao"]
        - df_com_diferencas["data_assinatura"]
    ).dt.days

    return df_com_diferencas


def preparar_base_clientes(caminho_csv: str | Path) -> pd.DataFrame:
    """Extrai, normaliza e acrescenta as colunas calculadas."""
    # Consumi a funcao do primeiro arquivo e usei o resultado nesta etapa
    df_normalizado = extrair_e_normalizar_clientes(caminho_csv)
    return gerar_colunas_diferenca_data(df_normalizado)
