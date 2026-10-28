"""Analise bivariada da base de clientes.

Relacoes entre duas variaveis:
    1. Numero de assinaturas x regiao   (contagem, taxa de cancelamento e qui-quadrado)
    2. Idade x cancelamento             (teste t de Welch, ponto-bisserial e faixas)
    3. Receita acumulada x tempo        (Pearson, Spearman e regressao linear)
    4. Ciclo x cancelamento             (tabela cruzada, qui-quadrado e V de Cramer)
    5. Churn em 2024 x perfil e uso     (idade, NPS, dias ativos, horas assistidas,
                                         tempo de casa, recencia, plano, ciclo e regiao)

O resultado vai para saida/analise_bivariada.html, que abre no navegador.
"""

import webbrowser
from pathlib import Path

import pandas as pd

# Classes do projeto, uma por arquivo dentro de funcao/
from funcao.churn_periodo import ChurnPeriodo
from funcao.estatistica_bivariada import EstatisticaBivariada
from funcao.extracao_normalizacao import ExtracaoNormalizacao
from funcao.filtros import Filtros
from funcao.geracao_colunas import GeracaoColunas
from funcao.receita import Receita
from funcao.relatorio_html import RelatorioHtml


# Faixas de idade usadas na taxa de cancelamento. O ultimo limite e 101
# porque as faixas fecham a esquerda: [65, 101) inclui os 100 anos
FAIXAS_IDADE = [0, 18, 25, 35, 45, 55, 65, 101]

# Variaveis numericas comparadas com o churn de 2024 e as faixas usadas na
# taxa de cancelamento de cada uma (faixas fechadas a esquerda)
FAIXAS_CHURN_2024 = {
    "idade": FAIXAS_IDADE,
    "nps": [0, 7, 9, 11],
    "dias_ativos_ult_mes": [0, 5, 10, 15, 20, 32],
    "horas_assistidas_total": [0, 50, 100, 200, 400, 901],
    "horas_por_mes": [0, 10, 20, 30, 40, 61],
    "meses_assinatura": [0, 3, 6, 12, 24, 61],
    "dias_ultimo_acesso_extracao": [0, 7, 14, 30, 60, 470],
}

# O que cada variavel mede e o cuidado ao interpretar
NOTAS_CHURN_2024 = {
    "idade": "Idade informada, entre 0 e 100 anos.",
    "nps": (
        "Faixas: detratores (0 a 6), neutros (7 e 8) e promotores (9 e 10). A base "
        "nao informa quando a nota foi dada; se foi depois do cancelamento, ela "
        "pode refletir a saida em vez de explica-la."
    ),
    "dias_ativos_ult_mes": (
        "Medida em janeiro/2024, o mesmo mes dos cancelamentos: quem cancelou no "
        "mes naturalmente teve menos dias ativos. Mostra a consequencia da saida e "
        "nao serve para prever o cancelamento."
    ),
    "horas_assistidas_total": (
        "Acumulada desde a assinatura, entao cresce com o tempo de casa. Compare "
        "com horas_por_mes, que separa o consumo do tempo de casa."
    ),
    "horas_por_mes": (
        "horas_assistidas_total dividida pelos meses em que o cliente esteve ativo "
        "(da assinatura ao cancelamento ou a extracao; no minimo 1 mes)."
    ),
    "meses_assinatura": "Tempo de casa em 01/01/2024, em meses completos.",
    "dias_ultimo_acesso_extracao": (
        "Dias entre o ultimo acesso e a extracao (recencia). Quem cancelou parou de "
        "acessar, entao ela tambem mostra a consequencia da saida."
    ),
}

# Variaveis medidas durante ou depois do cancelamento: ficam fora das conclusoes
VARIAVEIS_CONSEQUENCIA = ["dias_ativos_ult_mes", "dias_ultimo_acesso_extracao"]


# Este bloco so roda quando o arquivo e executado diretamente
# (python 02-analise-univarida-bivariada.py)
if __name__ == "__main__":
    pasta_projeto = Path(__file__).resolve().parent
    caminho_csv = pasta_projeto / "data" / "clientes_base.csv"
    caminho_relatorio = pasta_projeto / "saida" / "analise_bivariada.html"

    # =========================================================================
    # PREPARACAO DA BASE (mesma do 01-tratamento-dados.py)
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

    # Mesmos filtros do 01-tratamento-dados.py. Usei so os ativos porque a receita e calculada
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
    # 5. CHURN EM 2024 x PERFIL E USO
    # =========================================================================

    # A base vai ate 31/01/2024, entao 2024 tem so janeiro. Segui a definicao do
    # enunciado para a taxa de um periodo: populacao exposta = clientes ativos
    # em 01/01/2024; churn de 2024 = quem cancelou entre 01/01 e 31/01/2024.
    # Quem assinou em 2024 fica de fora (nao esteve exposto o periodo inteiro)
    periodo_2024 = ChurnPeriodo("2024-01-01", "2024-12-31")
    resumo_periodo_2024 = periodo_2024.resumo(df_clientes)

    # A populacao exposta ja vem com churn_periodo, meses_assinatura (tempo de
    # casa em 01/01/2024) e horas_por_mes. Renomeei o churn para os graficos
    # mostrarem "churn_2024"
    df_2024 = periodo_2024.populacao_exposta(df_clientes).rename(
        columns={ChurnPeriodo.COLUNA_CHURN: "churn_2024"}
    )
    df_2024, filtros_2024 = filtros.aplicar(df_2024, ["idade_valida"])
    bivariada_2024 = EstatisticaBivariada(df_2024)

    # Uma linha por variavel numerica: medias e medianas de quem ficou (0) e de
    # quem cancelou (1), d de Cohen, ponto-bisserial, teste t e AUC
    resumo_numericas_2024 = bivariada_2024.resumo_numericas_por_alvo(
        list(FAIXAS_CHURN_2024), "churn_2024"
    )
    resumo_numericas_2024["cuidado"] = [
        "Consequencia da saida" if variavel in VARIAVEIS_CONSEQUENCIA else ""
        for variavel in resumo_numericas_2024.index
    ]

    # Uma linha por variavel categorica: menor e maior taxa, qui-quadrado e V de
    # Cramer. A regiao "?" fica de fora
    resumo_categoricas_2024 = bivariada_2024.resumo_categoricas_por_alvo(
        ["plano", "ciclo", "regiao"], "churn_2024", valores_ignorados={"regiao": ["?"]}
    )

    # Taxa de cancelamento em cada faixa de cada variavel numerica
    taxas_faixa_2024 = {
        variavel: bivariada_2024.taxa_por_faixa(variavel, "churn_2024", faixas)
        for variavel, faixas in FAIXAS_CHURN_2024.items()
    }

    # Para os graficos por categoria, a regiao usa a base sem "?"
    df_2024_regiao, _ = filtros.aplicar(df_2024, ["regiao_informada"])
    bivariadas_categoricas_2024 = {
        "plano": bivariada_2024,
        "ciclo": bivariada_2024,
        "regiao": EstatisticaBivariada(df_2024_regiao),
    }

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

    # Churn de 2024: destaquei as 3 variaveis que mais separam quem cancelou,
    # sem contar as que sao consequencia da saida
    explicativas_2024 = resumo_numericas_2024.drop(index=VARIAVEIS_CONSEQUENCIA)
    destaques_2024 = "; ".join(
        f"{variavel} (mediana {linha['mediana_1']:,.1f} nos cancelados contra "
        f"{linha['mediana_0']:,.1f} nos ativos, AUC {linha['auc']:.2f})"
        for variavel, linha in explicativas_2024.head(3).iterrows()
    )
    sem_relacao_2024 = ", ".join(
        explicativas_2024[explicativas_2024["leitura"] == "Nao separa os grupos"].index
    )
    conclusoes.append(
        f"Churn em 2024 (janeiro, unico mes de 2024 na base): dos "
        f"{len(df_2024)} clientes ativos em 01/01/2024, {df_2024['churn_2024'].sum()} "
        f"cancelaram ({df_2024['churn_2024'].mean():.2%}). As variaveis que mais "
        f"separam quem cancelou sao {destaques_2024}. Nao separam os grupos: "
        f"{sem_relacao_2024 or 'nenhuma'}. Dias ativos e recencia tambem separam muito, "
        "mas sao consequencia da saida e ficaram fora desta conclusao."
    )
    conclusoes.append(
        "Churn em 2024 por categoria: "
        + "; ".join(
            f"{variavel}: maior taxa em {linha['maior_taxa']} e menor em "
            f"{linha['menor_taxa']} (p = {linha['p_valor']:.4f}, V de Cramer = "
            f"{linha['v_cramer']:.3f})"
            for variavel, linha in resumo_categoricas_2024.iterrows()
        )
        + "."
    )

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
        "Histograma de idade: ativos x cancelados (% de cada grupo)",
        bivariada_idade.grafico_histograma_por_grupo("idade", "churn"),
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

    # --- 5. Churn em 2024 ---
    relatorio.adicionar_secao(
        "5. Churn em 2024 x perfil e uso",
        "A base vai ate 31/01/2024, entao 2024 tem apenas janeiro. A populacao "
        "exposta sao os clientes ativos em 01/01/2024 e o churn de 2024 e quem "
        "cancelou entre 01/01 e 31/01/2024. Essa e uma taxa de um mes, diferente da "
        "proporcao de cancelados do arquivo inteiro usada nas secoes 1 a 4.",
    )
    relatorio.adicionar_tabela("Populacao exposta em 2024", resumo_periodo_2024)
    relatorio.adicionar_tabela("Filtros aplicados", filtros_2024, mostrar_indice=False)
    relatorio.adicionar_texto(
        "Como ler o resumo: _0 sao os clientes que continuaram ativos e _1 os que "
        "cancelaram. d de Cohen e a diferenca das medias em desvios padrao (0,2 "
        "pequena, 0,5 media, 0,8 grande). AUC e a chance de um cliente que cancelou "
        "ter valor maior que um que ficou: 0,5 = a variavel nao separa os grupos; "
        "perto de 0 = quem cancela tem valores menores; perto de 1 = valores maiores. "
        "As variaveis estao ordenadas da que mais separa para a que menos separa."
    )
    relatorio.adicionar_tabela(
        "Resumo das variaveis numericas x churn de 2024",
        resumo_numericas_2024,
        casas_decimais=3,
    )
    relatorio.adicionar_tabela(
        "Resumo das variaveis categoricas x churn de 2024",
        resumo_categoricas_2024,
        casas_decimais=4,
    )

    # Uma secao por variavel numerica, na ordem do resumo: primeiro o
    # histograma de ativos x cancelados, depois a taxa por faixa
    for variavel in resumo_numericas_2024.index:
        relatorio.adicionar_secao(f"5. Churn em 2024 x {variavel}", NOTAS_CHURN_2024[variavel])
        relatorio.adicionar_figura(
            f"Histograma de {variavel}: ativos x cancelados (% de cada grupo)",
            bivariada_2024.grafico_histograma_por_grupo(variavel, "churn_2024"),
        )
        relatorio.adicionar_tabela(
            f"Taxa de cancelamento por faixa de {variavel}",
            taxas_faixa_2024[variavel],
            casas_decimais=3,
        )

    relatorio.adicionar_secao(
        "5. Churn em 2024 x plano, ciclo e regiao",
        'Taxa de cancelamento em janeiro/2024 por categoria. A regiao "?" fica de fora.',
    )
    for variavel, bivariada in bivariadas_categoricas_2024.items():
        relatorio.adicionar_tabela(
            f"Cancelamento por {variavel}",
            bivariada.taxa_por_categoria(variavel, "churn_2024"),
            casas_decimais=4,
        )
        relatorio.adicionar_figura(
            f"Clientes e taxa de cancelamento por {variavel}",
            bivariada.grafico_contagem_e_taxa(variavel, "churn_2024"),
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
            "Churn em 2024: a base so tem janeiro de 2024. NPS, dias ativos, horas "
            "e recencia sao medidos na extracao, sem data propria; parte deles pode "
            "refletir a saida em vez de explica-la. A analise e bivariada: cada "
            "variavel e vista sozinha, sem controlar as outras (ex.: clientes novos "
            "tambem assistiram menos horas no total).",
        ]
    )

    # Grava o arquivo e abre no navegador padrao
    caminho_salvo = relatorio.salvar(caminho_relatorio)
    print(f"Relatorio salvo em: {caminho_salvo}")
    webbrowser.open(caminho_salvo.as_uri())
