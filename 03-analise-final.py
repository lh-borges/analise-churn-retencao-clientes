"""Analise final da base de clientes: frameworks de segmentacao e retencao.

    1. RFM adaptado aos clientes ativos   (recencia, frequencia e valor)
    2. Quintis                            (taxa de cancelamento por quintil)
    3. Analise de cohort                  (retencao por mes de assinatura)
    4. Pareto dos motivos de cancelamento
    5. Funil                              (base opcional funil_eventos.csv)

O resultado vai para saida/analise_final.html, que abre no navegador.
"""

import webbrowser
from pathlib import Path

import pandas as pd

# Classes do projeto, uma por arquivo dentro de funcao/
from funcao.churn_periodo import ChurnPeriodo
from funcao.cohort import Cohort
from funcao.estatistica_bivariada import EstatisticaBivariada
from funcao.extracao_normalizacao import ExtracaoNormalizacao
from funcao.filtros import Filtros
from funcao.funil import Funil
from funcao.geracao_colunas import GeracaoColunas
from funcao.pareto import Pareto
from funcao.quintis import Quintis
from funcao.relatorio_html import RelatorioHtml
from funcao.rfm import RFM


# Variaveis comparadas com o churn de janeiro/2024 na analise de quintis
VARIAVEIS_QUINTIS = [
    "horas_por_mes",
    "nps",
    "meses_assinatura",
    "horas_assistidas_total",
    "idade",
]

# Cohorts analisadas: 2023 e o unico ano com cancelamentos ao longo de todos os
# meses (antes de dez/2022 quase nao ha cancelamentos registrados na base)
PRIMEIRA_COHORT = "2023-01"
ULTIMA_COHORT = "2023-12"


def comentar(relatorio: RelatorioHtml, observado: str, decisao: str, limitacao: str) -> None:
    """Escreve o comentario pedido no enunciado para cada visualizacao."""
    relatorio.adicionar_lista(
        [
            f"O que foi observado: {observado}",
            f"Decisao que apoia: {decisao}",
            f"Limitacao: {limitacao}",
        ]
    )


# Este bloco so roda quando o arquivo e executado diretamente
# (python 03-analise-final.py)
if __name__ == "__main__":
    pasta_projeto = Path(__file__).resolve().parent
    caminho_clientes = pasta_projeto / "data" / "clientes_base.csv"
    caminho_funil = pasta_projeto / "data" / "funil_eventos.csv"
    caminho_relatorio = pasta_projeto / "saida" / "analise_final.html"

    # =========================================================================
    # PREPARACAO DA BASE (mesma dos outros scripts)
    # =========================================================================

    # Le o CSV, converte as datas e padroniza plano, canal e motivo de
    # cancelamento. Depois cria as diferencas entre datas e tira os registros
    # com datas fora de ordem
    df_clientes = ExtracaoNormalizacao(caminho_clientes).carregar()
    df_clientes = GeracaoColunas().adicionar_diferencas_data(df_clientes)

    filtros = Filtros()
    df_clientes, _ = filtros.aplicar(df_clientes, ["diferencas_data_validas"])

    # =========================================================================
    # 1. RFM ADAPTADO AOS CLIENTES ATIVOS
    # =========================================================================

    # O enunciado pede o RFM so dos ativos, com o valor mensal validado
    df_ativos, filtros_rfm = filtros.aplicar(
        df_clientes, ["clientes_ativos", "valor_mensal_valido"]
    )

    quintis = Quintis(5)
    rfm = RFM(quintis)

    # Pontos de corte de R, F e M: mostra que M nao forma quintis
    cortes_rfm = quintis.cortes(df_ativos, [RFM.COLUNA_R, RFM.COLUNA_F, RFM.COLUNA_M])

    # Notas R, F e M de cada cliente, o codigo RFM e o segmento
    df_rfm = rfm.calcular(df_ativos)
    regras_rfm = rfm.regras()
    resumo_rfm = rfm.resumo_segmentos(df_rfm)

    # =========================================================================
    # 2. QUINTIS x CHURN DE JANEIRO/2024
    # =========================================================================

    # Mesma populacao da analise bivariada: ativos em 01/01/2024, com churn =
    # cancelou em janeiro/2024 (unico mes de 2024 na base)
    periodo_2024 = ChurnPeriodo("2024-01-01", "2024-12-31")
    df_2024 = periodo_2024.populacao_exposta(df_clientes).rename(
        columns={ChurnPeriodo.COLUNA_CHURN: "churn_2024"}
    )
    df_2024, filtros_2024 = filtros.aplicar(df_2024, ["idade_valida"])

    cortes_2024 = quintis.cortes(df_2024, VARIAVEIS_QUINTIS)
    taxas_quintis = {
        variavel: quintis.taxa_por_quintil(df_2024, variavel, "churn_2024")
        for variavel in VARIAVEIS_QUINTIS
    }

    # =========================================================================
    # 3. ANALISE DE COHORT
    # =========================================================================

    cohort = Cohort(PRIMEIRA_COHORT, ULTIMA_COHORT, meses_max=12)

    # Cancelamentos por mes do calendario: mostra em que periodo a base tem
    # cancelamentos registrados
    cancelamentos_mes = Cohort.cancelamentos_por_mes(df_clientes)

    # Retencao de cada cohort em cada mes de vida e a media de todas
    matriz_cohort = cohort.matriz_retencao(df_clientes)
    retencao_media = cohort.retencao_media(df_clientes)
    tamanhos_cohort = cohort.tamanhos(df_clientes)

    # --- Assinaram, renovaram e se mantiveram ---
    # A base principal tem uma unica assinatura por cliente e ninguem acessa
    # depois de cancelar, entao nao registra quem voltou a assinar. O mais
    # proximo disso e a etapa "renovou" do funil, que trago para cada cliente
    funil = Funil(caminho_funil)
    eventos, limpeza_funil = funil.carregar()
    presenca_funil = funil.presenca(eventos)

    # Um registro por cliente_id para nao contar as duplicatas duas vezes
    df_renovacao = df_clientes.drop_duplicates("cliente_id").merge(
        presenca_funil[["renovou"]], left_on="cliente_id", right_index=True
    )

    # Por cohort mensal de 2023 e por ano de assinatura (todas as cohorts)
    resumo_assinaturas_2023 = cohort.resumo_assinaturas(df_renovacao)
    cohort_por_ano = Cohort("2019-01", "2024-01")
    resumo_assinaturas_ano = cohort_por_ano.resumo_assinaturas(df_renovacao, frequencia="Y")

    # Curva de retencao de quem renovou x quem nao renovou (cohorts de 2023)
    retencao_por_renovacao = {
        "Renovaram (funil)": cohort.retencao_media(df_renovacao[df_renovacao["renovou"] == 1]),
        "Nao renovaram": cohort.retencao_media(df_renovacao[df_renovacao["renovou"] == 0]),
    }

    # Evidencias de que o "renovou" do funil nao e confiavel. Na comparacao por
    # ano deixei de fora anos com menos de 20 assinantes (2024 tem so 6)
    meses_de_casa = df_renovacao["dias_assinatura_extracao"] / Cohort.DIAS_POR_MES
    renovou = df_renovacao["renovou"] == 1
    renovou_por_ano = resumo_assinaturas_ano.loc[
        resumo_assinaturas_ano["assinaram"] >= 20, "percentual_renovaram"
    ]
    evidencias_renovou = pd.DataFrame(
        [
            (
                "percentual_renovou_por_ano_de_assinatura",
                f"{renovou_por_ano.min():.1%} a {renovou_por_ano.max():.1%} "
                f"({renovou_por_ano.index[0]} a {renovou_por_ano.index[-1]})",
                "Quase igual em 2019 e em 2023; clientes antigos deveriam ter renovado mais",
            ),
            (
                "mediana_meses_de_casa_renovou_x_nao",
                f"{meses_de_casa[renovou].median():.1f} x {meses_de_casa[~renovou].median():.1f}",
                "Mesmo tempo de casa: renovar nao esta ligado a ter mais tempo de assinatura",
            ),
            (
                "renovaram_com_menos_de_1_mes_de_casa",
                f"{(renovou & (meses_de_casa < 1)).sum()}",
                "Impossivel ter renovado antes de completar o primeiro ciclo",
            ),
            (
                "cancelaram_entre_renovou_x_nao",
                f"{df_renovacao.loc[renovou, 'churn'].mean():.1%} x "
                f"{df_renovacao.loc[~renovou, 'churn'].mean():.1%}",
                "Quem renovou cancelou na mesma proporcao de quem nao renovou",
            ),
        ],
        columns=["verificacao", "resultado", "leitura"],
    ).set_index("verificacao")

    # =========================================================================
    # 4. PARETO DOS MOTIVOS DE CANCELAMENTO
    # =========================================================================

    pareto = Pareto(linha_referencia=0.8)

    # Todos os cancelados da base
    motivos = df_clientes.loc[df_clientes["churn"] == 1, "motivo_cancelamento"]
    pareto_motivos = pareto.tabela(motivos)
    ausentes_motivos = pareto.ausentes(motivos)
    motivos_ate_80 = pareto.categorias_ate_referencia(pareto_motivos)

    # So os cancelados de janeiro/2024, para ver se os motivos mudaram
    motivos_2024 = df_2024.loc[df_2024["churn_2024"] == 1, "motivo_cancelamento"]
    pareto_motivos_2024 = pareto.tabela(motivos_2024)
    comparacao_motivos = pd.DataFrame(
        {
            "participacao_todos": pareto_motivos["participacao"],
            "participacao_jan_2024": pareto_motivos_2024["participacao"],
        }
    )

    # =========================================================================
    # 5. FUNIL
    # =========================================================================

    # O funil ja foi carregado na secao de cohort (etapas padronizadas e sem
    # duplicatas). Ordem: visitou_site > criou_conta > assistiu_1a_aula >
    # assinou_plano > renovou

    # Tabela com 3 colunas: usuarios unicos em cada etapa, % da etapa anterior
    # que avancou e % do topo do funil que chegou ate a etapa
    contagem_funil = funil.contagem(presenca_funil)

    # Maior gargalo: etapa com a menor conversao em relacao a etapa anterior
    gargalo_funil = Funil.gargalo(contagem_funil)

    jornadas_funil = funil.consistencia(presenca_funil)
    jornadas_validas = jornadas_funil.loc[jornadas_funil["segue_a_ordem"], "clientes"].sum()

    # Cruzamento com a base de clientes: o churn muda com a etapa final do funil?
    # Usei um registro por cliente_id para nao contar duplicatas duas vezes
    df_funil_churn = (
        df_clientes.drop_duplicates("cliente_id")
        .merge(funil.etapa_final(presenca_funil), left_on="cliente_id", right_index=True)
    )
    bivariada_funil = EstatisticaBivariada(df_funil_churn)
    churn_por_etapa = bivariada_funil.taxa_por_categoria("etapa_final", "churn").reindex(
        Funil.ETAPAS
    )
    teste_funil = bivariada_funil.qui_quadrado("etapa_final", "churn")

    assinou_no_funil = int(contagem_funil.loc["assinou_plano", "usuarios"])

    # =========================================================================
    # CONCLUSOES (montadas a partir dos resultados acima)
    # =========================================================================

    segmento_maior = resumo_rfm["clientes"].idxmax()
    quintil_horas = taxas_quintis["horas_por_mes"]
    quintil_nps = taxas_quintis["nps"]

    conclusoes = [
        f"RFM: {len(df_rfm)} ativos em 5 segmentos. '{segmento_maior}' e o maior "
        f"({resumo_rfm.loc[segmento_maior, 'participacao']:.0%}); 'Baixo engajamento' "
        f"tem {resumo_rfm.loc['Baixo engajamento', 'clientes']} clientes "
        f"({resumo_rfm.loc['Baixo engajamento', 'participacao']:.0%}) e "
        f"{resumo_rfm.loc['Baixo engajamento', 'participacao_valor']:.0%} do valor mensal. "
        "O valor mensal medio quase nao muda entre segmentos.",
        f"Quintis: no quintil de menor consumo (ate {quintil_horas.loc['Q1', 'maximo']:.1f} "
        f"h/mes) a taxa de cancelamento de janeiro/2024 foi "
        f"{quintil_horas.loc['Q1', 'taxa']:.1%}, contra no maximo "
        f"{quintil_horas.loc[['Q2', 'Q3', 'Q4', 'Q5'], 'taxa'].max():.1%} nos demais. No NPS, "
        f"o quintil mais baixo (0 a {quintil_nps.loc['Q1', 'maximo']:.0f}) cancelou "
        f"{quintil_nps.loc['Q1', 'taxa']:.1%}; notas 9 e 10 nao cancelaram.",
        f"Cohort: nas cohorts de 2023, a retencao media cai para "
        f"{retencao_media.loc[6, 'retencao']:.0%} no 6o mes e "
        f"{retencao_media['retencao'].iloc[-1]:.0%} no {retencao_media.index[-1]}o. Os "
        "cancelamentos se concentram de set/2023 a jan/2024 em todas as cohorts, o que "
        "indica um efeito de calendario e nao so de tempo de casa.",
        f"Pareto: {len(motivos_ate_80)} dos {len(pareto_motivos)} motivos somam "
        f"{pareto_motivos.loc[motivos_ate_80[-1], 'participacao_acumulada']:.0%} das saidas "
        f"({', '.join(motivos_ate_80)}). Preco lidera com "
        f"{pareto_motivos.loc['Preco', 'participacao']:.0%}. Todos os cancelados tem motivo "
        "informado.",
        f"Funil: de {contagem_funil['usuarios'].iloc[0]:,} visitantes, "
        f"{contagem_funil.loc['assinou_plano', 'conversao_topo']:.0%} assinaram e "
        f"{contagem_funil.loc['renovou', 'conversao_topo']:.0%} renovaram. O maior gargalo "
        f"e a passagem de '{gargalo_funil['etapa_anterior']}' para "
        f"'{gargalo_funil['etapa']}': so {gargalo_funil['conversao']:.1%} avancam (queda de "
        f"{gargalo_funil['queda']:.1%}, {gargalo_funil['usuarios_perdidos']:,} usuarios). O "
        f"funil diz que {assinou_no_funil:,} assinaram, mas os 5.000 clientes da base "
        "principal sao assinantes: as duas bases nao sao coerentes entre si.",
    ]

    # =========================================================================
    # RELATORIO HTML
    # =========================================================================

    relatorio = RelatorioHtml("Analise final: RFM, quintis, cohort, Pareto e funil")

    relatorio.adicionar_secao(
        "Principais conclusoes",
        "Resumo das cinco analises. Associacao nao comprova causa.",
    )
    relatorio.adicionar_lista(conclusoes)

    # --- 1. RFM ---
    relatorio.adicionar_secao(
        "1. RFM adaptado aos clientes ativos",
        "R = dias entre o ultimo acesso e a extracao (menos dias = nota maior); "
        "F = dias ativos no ultimo mes; M = valor mensal validado (ate 100). Somente "
        "clientes ativos.",
    )
    relatorio.adicionar_tabela("Filtros aplicados", filtros_rfm, mostrar_indice=False)
    relatorio.adicionar_tabela("Quintis de R, F e M", cortes_rfm)
    relatorio.adicionar_texto(
        "Adaptacao: R e F recebem notas de 1 a 5 pelos quintis; valores iguais ficam "
        "sempre no mesmo quintil, por isso os grupos tem tamanhos diferentes. M tem so 3 "
        "precos (19,90; 34,90; 55,90) e forma apenas 2 grupos por quintil; por isso "
        "recebe notas 1, 3 e 5 conforme o preco. Os 33 ativos sem data de ultimo acesso "
        "ficam sem nota R e formam um segmento proprio."
    )
    relatorio.adicionar_tabela("Regras e acoes sugeridas por segmento", regras_rfm)
    relatorio.adicionar_tabela("Tamanho e perfil dos segmentos", resumo_rfm)
    relatorio.adicionar_figura("Notas R x F e tamanho dos segmentos", rfm.grafico(df_rfm))
    comentar(
        relatorio,
        f"'{segmento_maior}' concentra {resumo_rfm.loc[segmento_maior, 'participacao']:.0%} "
        "dos ativos. Recencia e frequencia quase nao andam juntas (o mapa de calor e "
        "espalhado), e o valor mensal medio e parecido em todos os segmentos.",
        "Direcionar a acao de reengajamento para 'Baixo engajamento' e lembretes leves "
        "para 'Atencao', sem gastar contato com 'Engajados'.",
        "Os segmentos descrevem o engajamento observado, nao o risco de cancelar: isso "
        "exigiria validar com cancelamentos futuros. F e medida em um so mes.",
    )

    # --- 2. Quintis ---
    relatorio.adicionar_secao(
        "2. Quintis x churn de janeiro/2024",
        "Cada variavel e dividida em 5 grupos de tamanho parecido (Q1 = menores "
        "valores). Populacao: ativos em 01/01/2024; churn = cancelou em janeiro/2024.",
    )
    relatorio.adicionar_tabela("Filtros aplicados", filtros_2024, mostrar_indice=False)
    relatorio.adicionar_tabela("Pontos de corte e empates", cortes_2024)
    relatorio.adicionar_figura(
        "Taxa de cancelamento por quintil",
        quintis.grafico_taxa_por_quintil(df_2024, VARIAVEIS_QUINTIS, "churn_2024"),
    )
    for variavel, tabela in taxas_quintis.items():
        relatorio.adicionar_tabela(f"Quintis de {variavel}", tabela, casas_decimais=3)
    comentar(
        relatorio,
        f"O cancelamento se concentra no Q1 de horas por mes "
        f"({quintil_horas.loc['Q1', 'taxa']:.0%}), no Q1 de NPS "
        f"({quintil_nps.loc['Q1', 'taxa']:.0%}) e nos clientes mais novos. A idade fica "
        "estavel em todos os quintis.",
        "Usar consumo por mes, NPS e tempo de casa para definir o publico prioritario.",
        "Variaveis vistas uma a uma: clientes novos tambem tendem a consumir menos. NPS "
        "nao tem data de coleta.",
    )

    # --- 3. Cohort ---
    relatorio.adicionar_secao(
        "3. Analise de cohort",
        f"Cohorts de {PRIMEIRA_COHORT} a {ULTIMA_COHORT}. A retencao no mes k e o % da "
        "cohort que ainda nao tinha cancelado k meses depois de assinar. Celulas em "
        "branco sao meses que a cohort ainda nao completou na extracao.",
    )
    relatorio.adicionar_texto(
        "Por que so 2023: a base quase nao tem cancelamentos antes de dez/2022 (tabela "
        "abaixo). Cohorts mais antigas pareceriam ter retencao perfeita no inicio, o que "
        "indica que a base guarda so clientes que estavam ativos mais recentemente."
    )
    relatorio.adicionar_tabela("Cancelamentos por mes do calendario", cancelamentos_mes)
    relatorio.adicionar_tabela("Tamanho das cohorts", tamanhos_cohort, casas_decimais=3)
    relatorio.adicionar_figura(
        "Retencao por cohort e retencao media",
        cohort.grafico(matriz_cohort, retencao_media),
    )
    relatorio.adicionar_tabela("Matriz de retencao", matriz_cohort, casas_decimais=3)
    relatorio.adicionar_tabela("Retencao media por mes de vida", retencao_media, casas_decimais=3)
    comentar(
        relatorio,
        "As primeiras cohorts de 2023 ficam com 100% de retencao por 5 a 6 meses e "
        "depois caem; as ultimas caem ja no 1o ou 2o mes. A queda aparece sempre nos "
        "mesmos meses do calendario (set/2023 a jan/2024), formando uma diagonal no mapa.",
        "Investigar o que mudou a partir de set/2023 (preco, catalogo, problema tecnico) "
        "antes de atribuir o cancelamento ao tempo de casa.",
        "A base parece nao registrar cancelamentos antigos, entao a retencao das "
        "primeiras cohorts esta superestimada. A partir do mes 9 restam poucas cohorts.",
    )

    relatorio.adicionar_secao(
        "3. Cohort: assinaram, renovaram e se mantiveram",
        "Assinaram = clientes da cohort. Renovaram = clientes com a etapa 'renovou' no "
        "funil_eventos.csv. Se mantiveram = ainda ativos na extracao (31/01/2024).",
    )
    relatorio.adicionar_texto(
        "A base principal nao registra quem voltou a assinar: cada cliente tem uma unica "
        "assinatura, os 25 IDs repetidos tem as mesmas datas e nenhum cancelado acessou "
        "depois de cancelar. Por isso a renovacao vem do funil. As verificacoes abaixo "
        "mostram que esse dado parece pouco confiavel; leia os numeros de renovacao com "
        "cautela."
    )
    relatorio.adicionar_tabela("Verificacoes do 'renovou' do funil", evidencias_renovou)
    relatorio.adicionar_tabela(
        "Por ano de assinatura (todas as cohorts)", resumo_assinaturas_ano, casas_decimais=3
    )
    relatorio.adicionar_figura(
        "Assinaram, renovaram e se mantiveram por cohort de 2023",
        cohort.grafico_assinaturas(resumo_assinaturas_2023),
    )
    relatorio.adicionar_tabela(
        "Por cohort mensal de 2023", resumo_assinaturas_2023, casas_decimais=3
    )
    relatorio.adicionar_figura(
        "Retencao media: quem renovou x quem nao renovou (cohorts de 2023)",
        Cohort.grafico_comparar_retencao(retencao_por_renovacao),
    )
    comentar(
        relatorio,
        f"Cerca de {resumo_assinaturas_2023['percentual_renovaram'].mean():.0%} de cada "
        "cohort aparece como renovado, quase o mesmo em todas as cohorts e anos. A parcela "
        "que se manteve cai das cohorts antigas para as recentes. Quem renovou se manteve "
        "na mesma proporcao de quem nao renovou, e as curvas de retencao dos dois grupos "
        "praticamente se sobrepoem.",
        "Nao usar a renovacao do funil para escolher publico ou medir retencao ate "
        "confirmar com a fonte o que a etapa 'renovou' registra.",
        "Sem datas no funil, nao se sabe quando a renovacao aconteceu; e a base nao tem "
        "historico de assinaturas por cliente para medir reassinatura de verdade.",
    )

    # --- 4. Pareto ---
    relatorio.adicionar_secao(
        "4. Pareto dos motivos de cancelamento",
        "Clientes cancelados, com os motivos padronizados (caixa e acento). Ordenado do "
        "motivo mais frequente para o menos frequente.",
    )
    relatorio.adicionar_tabela("Motivo informado x ausente", ausentes_motivos, casas_decimais=3)
    relatorio.adicionar_tabela("Pareto dos motivos (todos os cancelados)", pareto_motivos, casas_decimais=3)
    relatorio.adicionar_figura(
        "Pareto dos motivos de cancelamento",
        pareto.grafico(pareto_motivos, f"Motivos de cancelamento ({len(motivos)} cancelados)"),
    )
    relatorio.adicionar_tabela(
        "Participacao de cada motivo: todos os cancelados x janeiro/2024",
        comparacao_motivos,
        casas_decimais=3,
    )
    comentar(
        relatorio,
        f"{len(motivos_ate_80)} motivos chegam a "
        f"{pareto_motivos.loc[motivos_ate_80[-1], 'participacao_acumulada']:.0%} das saidas; "
        "a regra 80/20 nao se aplica (sao 4 de 6 motivos, nao 20%). Preco e pouco "
        "conteudo novo somam "
        f"{pareto_motivos.loc['Pouco conteudo novo', 'participacao_acumulada']:.0%}. A "
        "distribuicao em janeiro/2024 e parecida com a do total.",
        "Priorizar uma iniciativa sobre preco (desconto, plano mais barato) ou sobre "
        "conteudo novo, que juntos explicam mais da metade das saidas.",
        "O motivo e declarado pelo cliente, com opcoes fechadas; 'Outro' nao detalha a "
        "razao. Nao ha ausentes, mas nao se sabe se a escolha era obrigatoria.",
    )

    # --- 5. Funil ---
    relatorio.adicionar_secao(
        "5. Funil",
        "Base opcional funil_eventos.csv, com cliente_id e etapa. Sem data dos eventos, "
        "nao da para medir o tempo entre etapas.",
    )
    relatorio.adicionar_tabela("Limpeza da base de eventos", limpeza_funil)
    relatorio.adicionar_texto(
        "usuarios = clientes unicos que alcancaram a etapa; conversao_etapa_anterior = % "
        "da etapa anterior que avancou ate esta; conversao_topo = % do total inicial "
        "(visitou_site) que chegou ate esta etapa."
    )
    relatorio.adicionar_tabela("Usuarios e conversao por etapa", contagem_funil, casas_decimais=3)
    relatorio.adicionar_tabela(
        "Maior gargalo do funil (menor conversao em relacao a etapa anterior)",
        gargalo_funil.rename("valor").to_frame(),
        casas_decimais=3,
    )
    relatorio.adicionar_figura("Funil de conversao (gargalo em laranja)", funil.grafico(contagem_funil))
    relatorio.adicionar_tabela("Jornadas encontradas", jornadas_funil, casas_decimais=3)
    relatorio.adicionar_texto(
        f"{jornadas_validas:,} de {len(presenca_funil):,} clientes seguem a ordem da "
        "jornada sem pular etapas."
    )
    relatorio.adicionar_tabela(
        "Proporcao de cancelados (base principal) por etapa final do funil",
        churn_por_etapa,
        casas_decimais=3,
    )
    relatorio.adicionar_tabela("Teste qui-quadrado: etapa final x churn", teste_funil, casas_decimais=4)
    comentar(
        relatorio,
        f"O maior gargalo e de '{gargalo_funil['etapa_anterior']}' para "
        f"'{gargalo_funil['etapa']}': so {gargalo_funil['conversao']:.1%} avancam e "
        f"{gargalo_funil['usuarios_perdidos']:,} usuarios ficam pelo caminho. Todas as "
        "jornadas seguem a ordem. A proporcao de cancelados na base principal quase nao "
        "muda com a etapa final do funil.",
        "Se o funil for confiavel, testar acoes entre a primeira aula e a assinatura.",
        f"O funil diz que {assinou_no_funil:,} clientes assinaram, mas todos os 5.000 da "
        "base principal sao assinantes. As bases nao sao coerentes, entao o funil nao deve "
        "ser cruzado com o churn sem antes confirmar a origem dos eventos.",
    )

    # --- Limitacoes ---
    relatorio.adicionar_secao("Limitacoes")
    relatorio.adicionar_lista(
        [
            "Os 25 cliente_id duplicados ainda estao na base principal (fora do "
            "cruzamento com o funil, que usa um registro por cliente).",
            "A base parece guardar so clientes ativos recentemente: quase nao ha "
            "cancelamentos antes de dez/2022.",
            "RFM, quintis e cohort descrevem o que foi observado; risco de cancelamento "
            "exigiria validacao com dados futuros.",
            "O funil_eventos.csv nao e coerente com a base principal na etapa de assinatura.",
        ]
    )

    # Grava o arquivo e abre no navegador padrao
    caminho_salvo = relatorio.salvar(caminho_relatorio)
    print(f"Relatorio salvo em: {caminho_salvo}")
    webbrowser.open(caminho_salvo.as_uri())
