"""Auditoria da base de clientes.

Fluxo do script:
    1. Carrega o CSV e prepara a base (datas, planos e diferencas entre datas)
    2. Gera a estatistica descritiva da base completa
    3. Filtra os clientes ativos e calcula meses de assinatura e receita
    4. Gera os graficos (boxplots, barras e histogramas)
    5. Salva tudo em um relatorio HTML e abre no navegador

Cada etapa usa uma classe da pasta funcao/. As classes so calculam e
devolvem os resultados; quem junta tudo no relatorio e este arquivo.
"""

import webbrowser
from io import StringIO
from pathlib import Path

# Classes do projeto, uma por arquivo dentro de funcao/
from funcao.estatistica_descritiva import EstatisticaDescritiva
from funcao.extracao_normalizacao import ExtracaoNormalizacao
from funcao.filtros import Filtros
from funcao.geracao_colunas import GeracaoColunas
from funcao.histograma import Histograma
from funcao.receita import Receita
from funcao.relatorio_html import RelatorioHtml


# Este bloco so roda quando o arquivo e executado diretamente
# (python init.py). Se outro arquivo importar o init.py, nada aqui e executado.
if __name__ == "__main__":
    # Montei os caminhos a partir da pasta deste arquivo, assim o script
    # funciona independente da pasta de onde ele for executado
    pasta_projeto = Path(__file__).resolve().parent
    caminho_csv = pasta_projeto / "data" / "clientes_base.csv"
    caminho_relatorio = pasta_projeto / "saida" / "relatorio_clientes.html"

    # O relatorio comeca vazio; cada etapa abaixo acrescenta secoes nele
    relatorio = RelatorioHtml("Auditoria da base de clientes")

    # =========================================================================
    # 1. CARREGAMENTO E PREPARACAO DA BASE
    # =========================================================================

    # Le o CSV, converte as 4 colunas de data para datetime e padroniza o
    # plano (ex.: "BASICO", "básico" e "Basico" viram "Basico")
    df_clientes = ExtracaoNormalizacao(caminho_csv).carregar()

    # Acrescenta 4 colunas com a diferenca em dias entre as datas
    # (ex.: dias_assinatura_extracao = data_extracao - data_assinatura)
    df_clientes = GeracaoColunas().adicionar_diferencas_data(df_clientes)

    # Filtros() usa os limites padrao: idade de 0 a 100 e valor mensal ate 100.
    # Para mudar, passe no construtor, ex.: Filtros(idade_minima=18).
    # Os nomes validos de filtro estao em filtros.disponiveis
    filtros = Filtros()

    # Diferenca de datas negativa nao faz sentido (ex.: ultimo acesso 47 dias
    # ANTES da assinatura). Guardei esses registros para mostrar no relatorio
    # e depois tirei eles da base; todas as etapas seguintes ja usam a base limpa
    datas_fora_de_ordem = EstatisticaDescritiva(df_clientes).datas_invalidas()
    df_clientes, resumo_datas = filtros.aplicar(
        df_clientes,
        ["diferencas_data_validas"],
    )

    # Estrutura da base: tipo de cada coluna, quantidade de linhas e de nulos.
    # O df.info() escreve direto no terminal, entao capturei o texto dele
    # em um buffer para conseguir colocar no relatorio
    informacoes = StringIO()
    df_clientes.info(buf=informacoes)

    relatorio.adicionar_secao(
        "Estrutura da base",
        f"Base carregada de {caminho_csv.name}, ja com datas convertidas, "
        "planos padronizados e as diferencas entre datas calculadas. Registros "
        "com diferenca de datas negativa foram removidos antes da analise.",
    )
    relatorio.adicionar_tabela(
        "Tipos das colunas",
        df_clientes.dtypes.astype(str).rename("tipo"),
    )
    relatorio.adicionar_texto_fixo("Informacoes do DataFrame", informacoes.getvalue())

    # =========================================================================
    # 2. ESTATISTICA DESCRITIVA DA BASE COMPLETA
    # =========================================================================

    # Criei o objeto uma vez com a base; todos os metodos abaixo usam ela
    estatistica = EstatisticaDescritiva(df_clientes)

    # Contagem, media, desvio padrao, quartis, minimo, maximo e nulos de cada
    # coluna numerica. Aqui entram todos os registros com datas em ordem
    relatorio.adicionar_secao(
        "Estatistica descritiva da base completa",
        f"{len(df_clientes)} registros: a base inteira, menos os que tinham "
        "diferenca de datas negativa.",
    )
    relatorio.adicionar_tabela(
        "Estatisticas das colunas numericas",
        estatistica.estatisticas_numericas(),
    )

    # Registros que o filtro diferencas_data_validas tirou da base
    relatorio.adicionar_secao(
        "Diferencas entre datas",
        "Valores negativos indicam datas fora de ordem, como um ultimo acesso "
        "anterior a assinatura. Esses registros foram removidos da base.",
    )
    if datas_fora_de_ordem.empty:
        relatorio.adicionar_texto("Nenhuma diferenca de datas negativa encontrada.")
    else:
        relatorio.adicionar_tabela(
            f"Registros removidos por datas fora de ordem ({len(datas_fora_de_ordem)})",
            datas_fora_de_ordem,
            mostrar_indice=False,
        )

    # Verificacao das diferencas entre datas depois do filtro: a coluna
    # valores_negativos deve estar zerada
    relatorio.adicionar_tabela("Sanity check", estatistica.sanity_check_datas())

    # Estatisticas das diferencas entre datas com os limites do boxplot
    # (amplitude interquartil, bigodes e quantidade de outliers)
    relatorio.adicionar_tabela(
        "Estatistica descritiva e limites do boxplot",
        estatistica.estatisticas_diferencas_data(),
    )

    # Conta quantos clientes ha em cada valor de plano, ciclo, regiao e canal.
    # A regiao "?" fica de fora porque nao identifica nenhuma regiao.
    # Guardei o resultado para reaproveitar no grafico de barras
    contagens_categoricas = estatistica.contagens_categoricas()

    relatorio.adicionar_secao(
        "Colunas categoricas",
        'Quantidade de clientes em cada valor. A regiao "?" foi deixada de fora.',
    )
    for coluna, contagem in contagens_categoricas.items():
        relatorio.adicionar_tabela(
            f"{coluna} ({len(contagem)} valores unicos)",
            contagem.rename("quantidade"),
        )

    # =========================================================================
    # 3. CLIENTES ATIVOS: FILTROS, MESES DE ASSINATURA E RECEITA
    # =========================================================================

    # Reaproveitei o mesmo objeto filtros criado na etapa 1.
    # Os filtros sao aplicados na ordem da lista, um depois do outro.
    # Devolve a base filtrada e uma tabela com quantos registros cada filtro
    # removeu
    df_ativos, resumo_filtros = filtros.aplicar(
        df_clientes,
        [
            "clientes_ativos",  # churn = 0
            "idade_valida",  # idade entre 0 e 100 anos
            "valor_mensal_valido",  # valor mensal ate 100 (tira erro de escala)
            "regiao_informada",  # regiao diferente de "?"
        ],
    )

    # Ao criar o objeto, a Receita ja calcula duas colunas novas:
    #   meses_assinatura  = meses completos entre a assinatura e a extracao
    #   receita_acumulada = meses_assinatura x valor_mensal
    receita_ativos = Receita(df_ativos)

    relatorio.adicionar_secao(
        "Clientes ativos",
        f"A base tem {len(df_clientes)} registros. Os filtros abaixo foram "
        "aplicados em sequencia. meses_assinatura conta os meses completos entre "
        "a assinatura e a extracao; receita_acumulada = meses_assinatura x "
        "valor_mensal.",
    )

    # Quantos registros sobraram depois de cada filtro
    relatorio.adicionar_tabela(
        "Registros removidos por filtro",
        resumo_filtros,
        mostrar_indice=False,
    )

    # Estatistica descritiva de meses_assinatura e receita_acumulada,
    # com a soma total no final da tabela
    relatorio.adicionar_tabela(
        "Estatistica descritiva dos clientes ativos",
        receita_ativos.estatisticas(),
    )

    # Mesmas medidas separadas por plano. Para agrupar por outra coluna,
    # troque "plano" por "regiao", "ciclo", "canal_aquisicao" etc.
    relatorio.adicionar_tabela(
        "Resumo por plano",
        receita_ativos.resumo_por_grupo("plano"),
    )

    # =========================================================================
    # 4. GRAFICOS
    # =========================================================================

    # Cada metodo monta a figura e o relatorio converte em imagem PNG
    # dentro do proprio HTML, sem criar arquivos de imagem separados
    relatorio.adicionar_secao("Graficos")
    relatorio.adicionar_figura(
        "Boxplots das diferencas entre datas",
        estatistica.boxplots_datas(),
    )
    relatorio.adicionar_figura(
        "Contagem das colunas categoricas",
        estatistica.graficos_categoricos(contagens_categoricas),
    )
    relatorio.adicionar_figura(
        "Histogramas com curva de densidade (KDE)",
        Histograma().gerar(df_clientes),
    )

    # =========================================================================
    # 5. SALVAR E ABRIR O RELATORIO
    # =========================================================================

    # Grava o arquivo (cria a pasta saida/ se ela nao existir) e abre no
    # navegador padrao
    caminho_salvo = relatorio.salvar(caminho_relatorio)
    print(f"Relatorio salvo em: {caminho_salvo}")
    webbrowser.open(caminho_salvo.as_uri())
