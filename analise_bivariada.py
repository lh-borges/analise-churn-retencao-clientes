"""Analise bivariada da base de clientes.

Quatro relacoes entre duas variaveis:
    1. Numero de assinaturas x regiao   (contagem, taxa de cancelamento e qui-quadrado)
    2. Idade x cancelamento             (teste t de Welch, ponto-bisserial e faixas)
    3. Receita acumulada x tempo        (Pearson, Spearman e regressao linear)
    4. Ciclo x cancelamento             (tabela cruzada, qui-quadrado e V de Cramer)

O resultado vai para saida/analise_bivariada.html, que abre no navegador.
"""

import webbrowser
from pathlib import Path

import pandas as pd

# Classes do projeto, uma por arquivo dentro de funcao/
from funcao.estatistica_bivariada import EstatisticaBivariada
from funcao.extracao_normalizacao import ExtracaoNormalizacao
from funcao.filtros import Filtros
from funcao.geracao_colunas import GeracaoColunas
from funcao.receita import Receita
from funcao.relatorio_html import RelatorioHtml


# Faixas de idade usadas na taxa de cancelamento. O ultimo limite e 101
# porque as faixas fecham a esquerda: [65, 101) inclui os 100 anos
FAIXAS_IDADE = [0, 18, 25, 35, 45, 55, 65, 101]


# Este bloco so roda quando o arquivo e executado diretamente
# (python analise_bivariada.py)
if __name__ == "__main__":
    pasta_projeto = Path(__file__).resolve().parent
    caminho_csv = pasta_projeto / "data" / "clientes_base.csv"
    caminho_relatorio = pasta_projeto / "saida" / "analise_bivariada.html"

    # =========================================================================
    # PREPARACAO DA BASE (mesma do init.py)
    # =========================================================================

    # Le o CSV, converte as datas, padroniza o plano e cria as diferencas
    # entre datas. Depois tira os registros com datas fora de ordem
    df_clientes = ExtracaoNormalizacao(caminho_csv).carregar()
    df_clientes = GeracaoColunas().adicionar_diferencas_data(df_clientes)

    filtros = Filtros()
    df_clientes, _ = filtros.aplicar(df_clientes, ["diferencas_data_validas"])

    # Cada analise abaixo aplica so os filtros que fazem sentido para ela,
    # assim nenhuma perde registros por causa de uma coluna que nao usa

    # =========================================================================
    # 1. NUMERO DE ASSINATURAS x REGIAO
    # =========================================================================

    # Tirei a regiao "?", que nao identifica nenhuma regiao
    df_regiao, filtros_regiao = filtros.aplicar(df_clientes, ["regiao_informada"])
    bivariada_regiao = EstatisticaBivariada(df_regiao)

    # Clientes por regiao, participacao no total e taxa de cancelamento
    taxa_regiao = bivariada_regiao.taxa_por_categoria("regiao", "churn")

    # Qui-quadrado: a taxa de cancelamento depende da regiao?
    teste_regiao = bivariada_regiao.qui_quadrado("regiao", "churn")

    # =========================================================================
    # 2. IDADE x CANCELAMENTO
    # =========================================================================

    # Mantive so as idades entre 0 e 100 anos
    df_idade, filtros_idade = filtros.aplicar(df_clientes, ["idade_valida"])
    bivariada_idade = EstatisticaBivariada(df_idade)

    # Idade de quem cancelou (churn = 1) e de quem continua ativo (churn = 0)
    idade_por_churn = bivariada_idade.comparar_grupos("idade", "churn")

    # Teste t de Welch: a idade media dos dois grupos e diferente?
    # Ponto-bisserial: correlacao de Pearson entre a idade e o churn (0/1)
    teste_idade = bivariada_idade.teste_diferenca_medias("idade", "churn")

    # Taxa de cancelamento em cada faixa de idade (pega relacoes nao lineares)
    taxa_faixa_idade = bivariada_idade.taxa_por_faixa("idade", "churn", FAIXAS_IDADE)

    # =========================================================================
    # 3. RECEITA ACUMULADA x TEMPO DE ASSINATURA
    # =========================================================================

    # Mesmos filtros do init.py. Usei so os ativos porque a receita e calculada
    # ate a data de extracao, o que so vale para quem nao cancelou
    df_receita, filtros_receita = filtros.aplicar(
        df_clientes,
        ["clientes_ativos", "idade_valida", "valor_mensal_valido", "regiao_informada"],
    )

    # A Receita cria meses_assinatura e receita_acumulada (meses x valor_mensal)
    df_receita = Receita(df_receita).df_clientes
    bivariada_receita = EstatisticaBivariada(df_receita)

    # Pearson mede relacao linear; Spearman mede se uma sobe quando a outra sobe
    correlacao_receita = bivariada_receita.correlacao("meses_assinatura", "receita_acumulada")

    # Regressao: quanto a receita acumulada sobe a cada mes de assinatura
    regressao_receita = bivariada_receita.regressao_linear(
        "meses_assinatura", "receita_acumulada"
    )

    # Media da receita acumulada em cada mes de assinatura
    media_receita_por_mes = bivariada_receita.media_por_valor(
        "meses_assinatura", "receita_acumulada"
    )

    # Mesma regressao separada por plano. Como receita = meses x valor_mensal,
    # dentro de um plano a inclinacao deve ser o proprio valor mensal
    linhas_plano = []
    for plano, df_plano in df_receita.groupby("plano"):
        regressao_plano = EstatisticaBivariada(df_plano).regressao_linear(
            "meses_assinatura", "receita_acumulada"
        )["valor"]
        linhas_plano.append(
            {
                "plano": plano,
                "clientes": len(df_plano),
                "valor_mensal": df_plano["valor_mensal"].iloc[0],
                "inclinacao": regressao_plano["inclinacao"],
                "intercepto": regressao_plano["intercepto"],
                "r2": regressao_plano["r2"],
            }
        )
    regressao_por_plano = pd.DataFrame(linhas_plano).set_index("plano")

    # =========================================================================
    # 4. CICLO x CANCELAMENTO
    # =========================================================================

    # Ciclo nao tem valores invalidos, entao usei a base inteira
    bivariada_ciclo = EstatisticaBivariada(df_clientes)

    # Tabela cruzada: quantos clientes de cada ciclo cancelaram ou nao
    contingencia_ciclo = bivariada_ciclo.tabela_contingencia("ciclo", "churn")
    taxa_ciclo = bivariada_ciclo.taxa_por_categoria("ciclo", "churn")

    # Qui-quadrado: o cancelamento depende do ciclo?
    teste_ciclo = bivariada_ciclo.qui_quadrado("ciclo", "churn")

    # =========================================================================
    # CONCLUSOES (montadas a partir dos resultados acima)
    # =========================================================================

    def ler(tabela: pd.DataFrame, medida: str) -> float:
        """Pega o valor de uma medida na tabela de resultado."""
        return tabela.loc[medida, "valor"]

    def significancia(analise: EstatisticaBivariada, p_valor: float) -> str:
        """Texto curto dizendo se o p-valor e significativo."""
        if analise.e_significativo(p_valor):
            return f"diferenca estatisticamente significativa (p = {p_valor:.4f})"
        return f"sem diferenca estatisticamente significativa (p = {p_valor:.4f})"

    conclusoes = [
        f"Regiao: o Sudeste concentra {taxa_regiao.loc['Sudeste', 'participacao']:.1%} "
        f"das assinaturas. A taxa de cancelamento vai de {taxa_regiao['taxa'].min():.1%} "
        f"a {taxa_regiao['taxa'].max():.1%} entre as regioes, "
        f"{significancia(bivariada_regiao, ler(teste_regiao, 'p_valor'))}; "
        f"V de Cramer = {ler(teste_regiao, 'v_cramer'):.3f}.",
        f"Idade: a idade media e {ler(teste_idade, 'media_churn_0'):.1f} anos nos ativos "
        f"e {ler(teste_idade, 'media_churn_1'):.1f} nos cancelados, "
        f"{significancia(bivariada_idade, ler(teste_idade, 'p_valor_t'))}; "
        f"correlacao ponto-bisserial r = {ler(teste_idade, 'r_ponto_bisserial'):.3f}.",
        f"Receita x tempo: correlacao de Pearson r = {ler(correlacao_receita, 'pearson_r'):.3f}. "
        f"Cada mes de assinatura soma em media R$ {ler(regressao_receita, 'inclinacao'):.2f} "
        f"a receita acumulada (R2 = {ler(regressao_receita, 'r2'):.1%}). A relacao e forte "
        "por construcao, ja que receita = meses x valor mensal; o que espalha os pontos "
        "e o plano (R2 perto de 100% dentro de cada plano).",
        f"Ciclo: a taxa de cancelamento e {taxa_ciclo.loc['Anual', 'taxa']:.2%} no anual "
        f"e {taxa_ciclo.loc['Mensal', 'taxa']:.2%} no mensal, "
        f"{significancia(bivariada_ciclo, ler(teste_ciclo, 'p_valor'))}; "
        f"V de Cramer = {ler(teste_ciclo, 'v_cramer'):.3f}.",
    ]

    # =========================================================================
    # RELATORIO HTML
    # =========================================================================

    relatorio = RelatorioHtml("Analise bivariada da base de clientes")

    relatorio.adicionar_secao(
        "Principais conclusoes",
        f"Nivel de significancia de {EstatisticaBivariada.NIVEL_SIGNIFICANCIA:.0%}. "
        "Correlacao e associacao nao indicam causa.",
    )
    relatorio.adicionar_lista(conclusoes)

    # --- 1. Regiao ---
    relatorio.adicionar_secao(
        "1. Numero de assinaturas x regiao",
        "Quantos clientes ha em cada regiao e se a taxa de cancelamento muda entre "
        "elas. O qui-quadrado testa se regiao e cancelamento sao independentes; o "
        "V de Cramer mede a forca da associacao (0 = nenhuma, 1 = total).",
    )
    relatorio.adicionar_tabela("Filtros aplicados", filtros_regiao, mostrar_indice=False)
    relatorio.adicionar_tabela("Assinaturas e cancelamento por regiao", taxa_regiao, casas_decimais=3)
    relatorio.adicionar_tabela("Teste qui-quadrado", teste_regiao, casas_decimais=4)
    relatorio.adicionar_figura(
        "Assinaturas e taxa de cancelamento por regiao",
        bivariada_regiao.grafico_contagem_e_taxa("regiao", "churn"),
    )

    # --- 2. Idade ---
    relatorio.adicionar_secao(
        "2. Idade x cancelamento",
        "Compara a idade de quem cancelou com a de quem continua ativo. O teste t de "
        "Welch verifica se as medias sao diferentes; a correlacao ponto-bisserial e o "
        "Pearson entre a idade e o churn (0/1). As faixas mostram relacoes que nao "
        "seguem uma linha reta.",
    )
    relatorio.adicionar_tabela("Filtros aplicados", filtros_idade, mostrar_indice=False)
    relatorio.adicionar_tabela("Idade por situacao (churn)", idade_por_churn)
    relatorio.adicionar_tabela("Teste t de Welch e ponto-bisserial", teste_idade, casas_decimais=4)
    relatorio.adicionar_tabela(
        "Taxa de cancelamento por faixa de idade", taxa_faixa_idade, casas_decimais=3
    )
    relatorio.adicionar_texto(
        "Faixas com poucos clientes (como menores de 18 e acima de 65) tem taxas "
        "instaveis e nao devem ser usadas sozinhas para conclusoes."
    )
    relatorio.adicionar_figura(
        "Idade por situacao e taxa de cancelamento por faixa",
        bivariada_idade.grafico_numerica_por_grupo("idade", "churn", FAIXAS_IDADE),
    )

    # --- 3. Receita x tempo ---
    relatorio.adicionar_secao(
        "3. Receita acumulada x tempo de assinatura",
        "Somente clientes ativos, com os mesmos filtros do relatorio principal. "
        "meses_assinatura conta os meses completos ate a extracao e "
        "receita_acumulada = meses_assinatura x valor_mensal.",
    )
    relatorio.adicionar_tabela("Filtros aplicados", filtros_receita, mostrar_indice=False)
    relatorio.adicionar_tabela("Correlacao", correlacao_receita, casas_decimais=4)
    relatorio.adicionar_tabela("Regressao linear", regressao_receita, casas_decimais=4)
    relatorio.adicionar_tabela(
        "Regressao por plano (a inclinacao deve ser o valor mensal)",
        regressao_por_plano,
        casas_decimais=4,
    )
    relatorio.adicionar_figura(
        "Receita acumulada x meses de assinatura",
        bivariada_receita.grafico_dispersao_regressao(
            "meses_assinatura", "receita_acumulada", coluna_grupo="plano"
        ),
    )
    relatorio.adicionar_texto(
        "No grafico da direita a media oscila depois de uns 40 meses porque cada "
        "mes tem poucos clientes, e a media passa a depender de qual plano eles tem. "
        "A coluna clientes da tabela abaixo mostra isso."
    )
    relatorio.adicionar_tabela(
        "Media da receita acumulada por mes de assinatura", media_receita_por_mes
    )

    # --- 4. Ciclo ---
    relatorio.adicionar_secao(
        "4. Ciclo x cancelamento",
        "Contagem de clientes por ciclo (mensal ou anual) e situacao. O qui-quadrado "
        "testa se o cancelamento depende do ciclo.",
    )
    relatorio.adicionar_tabela("Tabela cruzada ciclo x churn", contingencia_ciclo)
    relatorio.adicionar_tabela("Cancelamento por ciclo", taxa_ciclo, casas_decimais=4)
    relatorio.adicionar_tabela("Teste qui-quadrado", teste_ciclo, casas_decimais=4)
    relatorio.adicionar_figura(
        "Clientes e taxa de cancelamento por ciclo",
        bivariada_ciclo.grafico_contagem_e_taxa("ciclo", "churn"),
    )

    # --- Limitacoes ---
    relatorio.adicionar_secao("Limitacoes")
    relatorio.adicionar_lista(
        [
            "Os 25 cliente_id duplicados ainda estao na base e podem contar o mesmo "
            "cliente duas vezes.",
            "canal_aquisicao e motivo_cancelamento ainda nao foram normalizados.",
            "A base e um retrato de uma data (31/01/2024): clientes com tempos de "
            "assinatura diferentes tiveram chances diferentes de cancelar.",
            "Os p-valores foram calculados com as distribuicoes t e qui-quadrado "
            "implementadas em funcao/distribuicoes.py, sem o scipy.",
        ]
    )

    # Grava o arquivo e abre no navegador padrao
    caminho_salvo = relatorio.salvar(caminho_relatorio)
    print(f"Relatorio salvo em: {caminho_salvo}")
    webbrowser.open(caminho_salvo.as_uri())
