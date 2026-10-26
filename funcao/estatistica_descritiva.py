import matplotlib.pyplot as plt
import pandas as pd

from .extracao_normalizacao import COLUNAS_DATA
from .geracao_colunas import COLUNAS_DIFERENCA_DATA
from .histograma import gerar_histogramas


def gerar_estatisticas_numericas(
    df_clientes: pd.DataFrame,
) -> tuple[list[str], pd.DataFrame]:
    """Retorna as colunas numericas e suas estatisticas descritivas."""
    # Identifiquei automaticamente as colunas numericas do DataFrame
    colunas_numericas = df_clientes.select_dtypes(include="number").columns.tolist()

    # Montei a tabela com as estatisticas e a quantidade de nulos
    estatisticas = (
        df_clientes[colunas_numericas]
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
    estatisticas.insert(1, "nulos", df_clientes[colunas_numericas].isna().sum())

    return colunas_numericas, estatisticas


def gerar_sanity_check_datas(df_clientes: pd.DataFrame) -> pd.DataFrame:
    """Resume nulos, intervalos e valores negativos das diferencas de datas."""
    # Fiz uma verificacao rapida para encontrar diferencas de datas incoerentes
    return pd.DataFrame(
        {
            "nao_nulos": df_clientes[COLUNAS_DIFERENCA_DATA].count(),
            "nulos": df_clientes[COLUNAS_DIFERENCA_DATA].isna().sum(),
            "minimo_dias": df_clientes[COLUNAS_DIFERENCA_DATA].min(),
            "maximo_dias": df_clientes[COLUNAS_DIFERENCA_DATA].max(),
            "valores_negativos": df_clientes[COLUNAS_DIFERENCA_DATA]
            .lt(0)
            .sum(),
        }
    )


def gerar_estatisticas_diferencas_data(
    df_clientes: pd.DataFrame,
) -> pd.DataFrame:
    """Gera a tabela descritiva com as informacoes usadas nos boxplots."""
    # Comecei pelas estatisticas descritivas das diferencas entre datas
    estatisticas = (
        df_clientes[COLUNAS_DIFERENCA_DATA]
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
        valores = df_clientes[coluna].dropna()
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


def gerar_boxplots_datas(df_clientes: pd.DataFrame) -> None:
    """Gera os boxplots das diferencas entre datas."""
    # Criei um boxplot para cada diferenca de data
    figura, eixos = plt.subplots(2, 2, figsize=(16, 10))

    for coluna, eixo in zip(COLUNAS_DIFERENCA_DATA, eixos.flatten()):
        eixo.boxplot(
            df_clientes[coluna].dropna(),
            orientation="horizontal",
            patch_artist=True,
            boxprops={"facecolor": "lightblue", "edgecolor": "black"},
            medianprops={"color": "red", "linewidth": 2},
        )
        eixo.set_title(coluna.replace("_", " ").title())
        eixo.set_xlabel("Dias")
        eixo.set_yticks([])
        eixo.grid(axis="x", linestyle="--", alpha=0.4)

    figura.suptitle("Boxplots das diferencas entre datas", fontsize=16)
    figura.tight_layout(rect=(0, 0, 1, 0.96))


def analisar_colunas_categoricas(df_clientes: pd.DataFrame) -> None:
    """Mostra as contagens e gera os graficos das colunas categoricas."""
    # Escolhi as colunas categoricas solicitadas para fazer a analise
    colunas_categoricas = ["plano", "ciclo", "regiao", "canal_aquisicao"]
    figura, eixos = plt.subplots(2, 2, figsize=(16, 10))

    for coluna, eixo in zip(colunas_categoricas, eixos.flatten()):
        valores_unicos = df_clientes[coluna].unique()
        contagem = df_clientes[coluna].value_counts(dropna=False)

        print(f"\nColuna: {coluna}")
        print(f"Valores unicos: {valores_unicos}")
        print(
            "Quantidade de valores unicos: "
            f"{df_clientes[coluna].nunique(dropna=False)}"
        )
        print("Contagem de cada valor:")
        print(contagem)

        contagem.plot(
            kind="bar",
            ax=eixo,
            color="steelblue",
            edgecolor="black",
        )
        eixo.set_title(f"Contagem por {coluna.replace('_', ' ').title()}")
        eixo.set_xlabel(coluna.replace("_", " ").title())
        eixo.set_ylabel("Quantidade")
        eixo.tick_params(axis="x", rotation=45)

    figura.tight_layout()


def executar_analise_descritiva(df_clientes: pd.DataFrame) -> None:
    """Executa as estatisticas, verificacoes e graficos da base preparada."""
    print("CLIENTES")
    print("Tipos das colunas:")
    print(df_clientes.dtypes)

    print("\nInformacoes do DataFrame:")
    df_clientes.info()

    # Consumi a funcao das estatisticas numericas e mostrei os resultados
    colunas_numericas, estatisticas_numericas = gerar_estatisticas_numericas(
        df_clientes
    )
    print("\nCOLUNAS NUMERICAS")
    print(colunas_numericas)
    print("\nESTATISTICAS DAS COLUNAS NUMERICAS")
    print(estatisticas_numericas.round(2).to_string())

    sanity_check_datas = gerar_sanity_check_datas(df_clientes)
    print("\nSANITY CHECK DAS DIFERENCAS ENTRE DATAS")
    print(sanity_check_datas)

    estatisticas_datas = gerar_estatisticas_diferencas_data(df_clientes)
    print("\nESTATISTICA DESCRITIVA DAS DIFERENCAS ENTRE DATAS")
    print(estatisticas_datas.round(2).to_string())

    # Separei os registros negativos para mostrar as inconsistencias encontradas
    mascara_datas_invalidas = df_clientes[COLUNAS_DIFERENCA_DATA].lt(0).any(axis=1)
    datas_invalidas = df_clientes.loc[
        mascara_datas_invalidas,
        ["cliente_id", *COLUNAS_DATA, *COLUNAS_DIFERENCA_DATA],
    ]

    print("\nRegistros com diferencas de datas negativas:")
    if datas_invalidas.empty:
        print("Nenhuma inconsistencia encontrada.")
    else:
        print(datas_invalidas.to_string(index=False))

    gerar_boxplots_datas(df_clientes)
    analisar_colunas_categoricas(df_clientes)
    gerar_histogramas(df_clientes)
    plt.show()
