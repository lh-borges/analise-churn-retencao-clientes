# Análise de cancelamento e retenção de clientes

## Sobre o exercício

Este projeto parte do enunciado [Módulo 01 — Projeto Exercício](../../Modulo_01_Projeto_Exercício.pdf), cujo desafio é investigar o cancelamento de clientes de uma plataforma de conteúdo por assinatura. O objetivo final é recomendar uma única iniciativa de retenção, definir o público prioritário e indicar como o resultado deverá ser medido.

O projeto já cobre a **auditoria e preparação da base**, a **estatística descritiva**, a **análise bivariada** do cancelamento e os **frameworks** pedidos (RFM, Pareto), além de quintis, cohort e funil. Os resultados são gerados por scripts Python e publicados em três relatórios HTML. Nenhuma alteração é gravada no CSV original.

## Andamento em relação ao enunciado

| Etapa do enunciado | Situação | Onde está |
|---|---|---|
| 1. Decisão de negócio | Concluída | Seção [Decisão de negócio](#decisão-de-negócio) |
| 2. Auditoria e preparação da base | Concluída em grande parte; falta a regra para duplicidades | `01-tratamento-dados.py`, seções [Resultado da auditoria](#resultado-da-auditoria) e [Tratamentos realizados](#tratamentos-realizados) |
| 3. Indicadores | Em grande parte: proporção de cancelados, por região, ciclo e plano, motivos e valor mensal de ativos; falta canal | Seção [Indicadores](#indicadores) |
| 4. Análise exploratória e hipóteses | Em grande parte: distribuições, região, ciclo, idade, receita e, no churn de janeiro/2024, NPS, engajamento, tempo de casa e plano; falta canal | `02-analise-univarida-bivariada.py`, seção [Análise bivariada](#análise-bivariada) |
| 5. Frameworks (Pareto e RFM) | Concluída, com quintis, cohort e funil (extensão opcional) | `03-analise-final.py`, seção [Análise final](#análise-final-rfm-quintis-cohort-pareto-e-funil) |
| 6. Recomendação, simulação e teste | Não iniciada | — |
| Entregáveis | README em andamento; os scripts e relatórios HTML fazem o papel do notebook por enquanto | Este arquivo e a pasta `saida/` |

## Principais achados

1. **Quem cancela usa pouco a plataforma.** No churn de janeiro/2024 (9,78% dos ativos em 01/01/2024), o quintil de menor consumo (até 16 h/mês) cancelou 48,6%, contra no máximo 0,1% nos demais.
2. **NPS baixo e pouco tempo de casa acompanham o cancelamento.** NPS de 0 a 5 cancelou 32,9%, e notas 9 e 10 não cancelaram. Clientes com até 5 meses de casa cancelaram 27,9%; com 21 meses ou mais, 0%.
3. **Perfil cadastral não diferencia quem cancela.** Região, idade e ciclo (mensal 30,15% e anual 30,16%) não têm associação significativa com o churn, o que contraria a hipótese 1. O plano Básico cancela um pouco mais (11,8% em jan/2024), com associação fraca.
4. **Preço e falta de conteúdo novo explicam 59% das saídas.** Com problema técnico e falta de tempo, os quatro motivos somam 87%.
5. **Os cancelamentos se concentram de set/2023 a jan/2024** em todas as cohorts, um efeito de calendário que merece investigação.
6. **O maior gargalo do funil é entre a 1ª aula e a assinatura** (39,5% de conversão), mas o funil não é coerente com a base principal.
7. **Qualidade dos dados:** 25 IDs duplicados, 170 regiões `?`, 603 mensalidades com escala provavelmente errada, idades impossíveis, uma data fora de ordem e grafias diferentes em plano, canal, motivo e etapas do funil.

Candidato a público prioritário para a iniciativa de retenção: clientes nos primeiros meses de assinatura, com baixo consumo por mês e NPS baixo. A escolha da ação e a simulação de impacto (Etapa 6) ainda estão pendentes.

## Decisão de negócio

O problema investigado é o cancelamento de assinaturas. A análise deverá apoiar a escolha da primeira iniciativa de retenção a ser testada, identificando um público com oportunidade relevante e indicadores adequados para acompanhar o teste.

A coluna `churn` foi interpretada como um indicador de situação: `1` representa cliente cancelado e `0` representa cliente ativo na data de extração. Essa interpretação é coerente com `data_cancelamento`, mas ainda deve ser confirmada com o responsável pela base. Os dados representam um retrato extraído em **31/01/2024**, com assinaturas iniciadas entre **11/02/2019 e 30/01/2024**. A base possui 5.025 registros e 5.000 clientes únicos.

Três hipóteses iniciais orientam a análise:

| # | Hipótese | O que a contrariaria | Situação |
|---|---|---|---|
| 1 | Clientes de ciclo mensal cancelam mais do que clientes de ciclo anual. | Proporção do ciclo anual igual ou superior, considerando o tamanho dos grupos. | **Contrariada.** 30,15% no mensal e 30,16% no anual; qui-quadrado p = 0,99. |
| 2 | Clientes cancelados apresentam NPS e engajamento menores. | Distribuições de NPS, dias ativos e horas assistidas semelhantes ou melhores entre cancelados. | **Sustentada no churn de janeiro/2024, com ressalvas.** NPS mediano 4 nos cancelados contra 7 nos ativos; horas por mês 5,4 contra 24,6. Não se sabe quando o NPS foi medido, e dias ativos no último mês é consequência da saída. |
| 3 | Clientes com maior tempo desde o último acesso cancelam mais. | A associação não aparecer entre clientes com tempos de acompanhamento comparáveis. Essa variável exige cautela porque pode refletir o próprio cancelamento. | **Inconclusiva.** A associação existe (40 contra 14 dias medianos em janeiro/2024), mas a recência é medida na extração e reflete a própria saída. Seria preciso o histórico de acessos antes do cancelamento. |

Para avaliar uma iniciativa real ainda seriam necessários custos de campanha, margem por cliente, histórico de cobrança, datas dos contatos, exposição a campanhas anteriores, reclamações, eventos de uso com data e resultados de um teste controlado.

## Fontes de dados

- `data/clientes_base.csv`: base principal.
- `data/funil_eventos.csv`: base opcional, com `cliente_id` e `etapa` do funil (usada em `03-analise-final.py`).
- `Modulo_01_Projeto_Exercício.pdf`: enunciado do projeto.

O arquivo original `clientes_base.csv` é somente lido. Normalizações, filtros e colunas calculadas existem apenas nos DataFrames em memória.

## Estrutura do projeto

```text
Modulo - Auditar_Contagoole/
├── README.md
├── 01-tratamento-dados.py               auditoria e estatística descritiva
├── 02-analise-univarida-bivariada.py    relações entre pares de variáveis e churn de 2024
├── 03-analise-final.py                  RFM, quintis, cohort, Pareto e funil
├── data/
│   ├── clientes_base.csv
│   └── funil_eventos.csv
├── funcao/                              classes reutilizáveis, uma por arquivo
│   ├── extracao_normalizacao.py
│   ├── geracao_colunas.py
│   ├── filtros.py
│   ├── estatistica_descritiva.py
│   ├── estatistica_bivariada.py
│   ├── churn_periodo.py
│   ├── distribuicoes.py
│   ├── histograma.py
│   ├── receita.py
│   ├── quintis.py
│   ├── rfm.py
│   ├── cohort.py
│   ├── pareto.py
│   ├── funil.py
│   └── relatorio_html.py
└── saida/                               relatórios gerados (recriados a cada execução)
    ├── relatorio_clientes.html
    ├── analise_bivariada.html
    └── analise_final.html
```

Os scripts da raiz (`01-tratamento-dados.py`, `02-analise-univarida-bivariada.py` e `03-analise-final.py`) chamam as classes de `funcao/` passo a passo e montam os relatórios. As classes não imprimem nem abrem janelas: devolvem tabelas, DataFrames ou figuras, para que qualquer script possa reutilizá-las. Os métodos com `_` na frente são de uso interno de cada classe.

| Arquivo | Classe | Uso |
|---|---|---|
| `extracao_normalizacao.py` | `ExtracaoNormalizacao(caminho_csv)` | `carregar()`: lê o CSV, converte datas e padroniza `plano`, `canal_aquisicao` e `motivo_cancelamento`. |
| `geracao_colunas.py` | `GeracaoColunas()` | `adicionar_diferencas_data(df)`: cria as diferenças entre datas, em dias. |
| `filtros.py` | `Filtros(idade_minima, idade_maxima, valor_mensal_maximo)` | `aplicar(df, nomes)`: aplica os filtros pelo nome e resume quantos registros cada um removeu; `disponiveis` lista os nomes. |
| `estatistica_descritiva.py` | `EstatisticaDescritiva(df)` | Tabelas descritivas, sanity checks, datas inválidas, contagens categóricas, boxplots e gráficos de barras. |
| `estatistica_bivariada.py` | `EstatisticaBivariada(df)` | Pearson, Spearman, regressão linear, teste t de Welch, ponto-bisserial, d de Cohen, AUC, qui-quadrado, V de Cramér, taxas por faixa ou categoria, resumos de várias variáveis contra um alvo e os gráficos de cada um. |
| `churn_periodo.py` | `ChurnPeriodo(inicio, fim)` | `populacao_exposta(df)`: clientes ativos no início do período, com o churn do período, o tempo de casa no início e as horas por mês; `resumo(df)`: tamanho da população e taxa do período. |
| `distribuicoes.py` | `Distribuicoes` | P-valores das distribuições t e qui-quadrado, implementados sem o scipy. |
| `histograma.py` | `Histograma(colunas, limites, bins)` | `gerar(df)`: histogramas com curva de densidade e limites por coluna. |
| `receita.py` | `Receita(df)` | Calcula meses de assinatura e receita acumulada; `estatisticas()` e `resumo_por_grupo(coluna)`. |
| `quintis.py` | `Quintis(quantidade)` | `cortes()`: pontos de corte e empates; `pontuar()`: nota de 1 a 5; `taxa_por_quintil()` e o gráfico correspondente. |
| `rfm.py` | `RFM(quintis)` | `calcular(df_ativos)`: notas R, F e M, código RFM e segmento; `regras()`, `resumo_segmentos()` e `grafico()`. |
| `cohort.py` | `Cohort(primeira, ultima, meses_max)` | `matriz_retencao()`, `retencao_media()`, `tamanhos()`, `cancelamentos_por_mes()`, `resumo_assinaturas()` (assinaram, renovaram e se mantiveram por mês, trimestre ou ano) e os gráficos. |
| `pareto.py` | `Pareto(linha_referencia)` | `tabela()`: quantidade, participação e acumulado; `ausentes()`, `categorias_ate_referencia()` e `grafico()`. |
| `funil.py` | `Funil(caminho_csv)` | `carregar()`: padroniza etapas e remove duplicatas; `presenca()`; `contagem()`: usuários, conversão da etapa anterior e conversão do topo; `gargalo()`: etapa com a menor conversão; `consistencia()`, `etapa_final()` e `grafico()`. |
| `relatorio_html.py` | `RelatorioHtml(titulo)` | Monta um HTML sem framework: `adicionar_secao()`, `adicionar_tabela()`, `adicionar_lista()`, `adicionar_figura()` e `salvar(caminho)`. |

## Como executar

Requisitos:

- Python 3.10 ou superior.
- pandas, numpy e matplotlib. O scipy não é necessário: os testes estatísticos foram implementados em `funcao/distribuicoes.py`.

```powershell
pip install pandas numpy matplotlib
```

Execução a partir da pasta `Exercícios`:

```powershell
# Auditoria e estatística descritiva → saida/relatorio_clientes.html
python ".\Modulo - Auditar_Contagoole\01-tratamento-dados.py"

# Análise bivariada → saida/analise_bivariada.html
python ".\Modulo - Auditar_Contagoole\02-analise-univarida-bivariada.py"

# RFM, quintis, cohort, Pareto e funil → saida/analise_final.html
python ".\Modulo - Auditar_Contagoole\03-analise-final.py"
```

Cada script grava o seu relatório e o abre no navegador. Cada relatório é um arquivo HTML único, com as tabelas, o estilo e os gráficos embutidos, sem framework nem arquivos externos.

| Relatório | Conteúdo |
|---|---|
| `relatorio_clientes.html` | Estrutura da base, estatística descritiva, diferenças entre datas, registros removidos, contagens categóricas, análise dos clientes ativos (meses de assinatura e receita acumulada), boxplots, gráficos de barras e histogramas com curva de densidade. |
| `analise_bivariada.html` | Conclusões, assinaturas por região, idade x cancelamento, receita acumulada x tempo de assinatura, ciclo x cancelamento, churn de janeiro/2024 x perfil e uso, e limitações. |
| `analise_final.html` | Conclusões, RFM dos ativos, quintis x churn de janeiro/2024, cohort de 2023, Pareto dos motivos, funil e limitações. Cada gráfico traz o que foi observado, a decisão que apoia e a limitação. |

## Dicionário da base original

Os significados abaixo foram inferidos a partir dos nomes e dos valores. Itens relacionados a dinheiro, período de referência e regras de validade precisam de confirmação com a fonte dos dados.

| Coluna | Significado | Tipo após preparação | Unidade ou domínio | Restrição ou observação |
|---|---|---:|---|---|
| `cliente_id` | Identificador do cliente | inteiro | identificador | Deveria identificar um cliente de forma única; há duplicidades. |
| `idade` | Idade informada | inteiro | anos | Deve respeitar uma faixa plausível; há valores negativos e muito altos. |
| `plano` | Plano contratado | texto | Basico, Padrao, Premium | Normalizado em memória; originalmente havia oito grafias. |
| `ciclo` | Periodicidade do contrato | texto | Mensal, Anual | Sem ausências na base. |
| `valor_mensal` | Valor associado à mensalidade | decimal | moeda não confirmada | Há possível mistura de escala: 19,9 e 1990, por exemplo. |
| `regiao` | Região do cliente | texto | regiões brasileiras | O marcador `?` aparece em 170 registros. |
| `canal_aquisicao` | Canal de aquisição | texto | Instagram, Organico, Indicacao, Google | Normalizado em memória; originalmente havia nove grafias (incluindo `IG`). |
| `nps` | Nota de recomendação | inteiro | 0 a 10 | Faixa observada válida; confirmar se é a resposta individual do NPS. |
| `data_assinatura` | Início da assinatura | datetime | data | Sem ausências após conversão. |
| `data_cancelamento` | Data do cancelamento | datetime | data | Ausente nos clientes ativos; 3.509 nulos. |
| `data_ultimo_acesso` | Último acesso registrado | datetime | data | 50 valores ausentes e uma relação cronológica inválida. |
| `data_extracao` | Data de referência da base | datetime | data | Todos os registros indicam 31/01/2024. |
| `dias_ativos_ult_mes` | Dias com atividade no último mês | inteiro | dias | Varia de 0 a 28; confirmar definição do período. |
| `horas_assistidas_total` | Consumo acumulado | decimal | horas | Varia de 0 a 900. |
| `motivo_cancelamento` | Motivo declarado para a saída | texto | Preco, Pouco conteudo novo, Problema tecnico, Falta de tempo, Concorrente, Outro | Preenchido apenas para cancelados; normalizado em memória (originalmente nove grafias). |
| `churn` | Situação de cancelamento | inteiro | 0 ou 1 | `0` interpretado como ativo e `1` como cancelado. |

Colunas criadas somente em memória:

| Coluna | Definição | Onde é usada |
|---|---|---|
| `dias_assinatura_cancelamento` | `data_cancelamento − data_assinatura`, em dias | Validação de datas e boxplots |
| `dias_assinatura_ultimo_acesso` | `data_ultimo_acesso − data_assinatura`, em dias | Validação de datas e boxplots |
| `dias_ultimo_acesso_extracao` | `data_extracao − data_ultimo_acesso`, em dias | Validação de datas e boxplots |
| `dias_assinatura_extracao` | `data_extracao − data_assinatura`, em dias | Validação de datas, boxplots e meses de assinatura |
| `meses_assinatura` | Meses completos entre a assinatura e a extração (dias ÷ 30,44, arredondado para baixo) | Análise de clientes ativos |
| `receita_acumulada` | `meses_assinatura × valor_mensal` | Análise de clientes ativos; é uma estimativa, não caixa recebido |

## Resultado da auditoria

### Dimensão e duplicidades

| Verificação | Resultado |
|---|---:|
| Linhas | 5.025 |
| Colunas originais | 16 |
| Clientes únicos | 5.000 |
| IDs que aparecem mais de uma vez | 25 |
| Linhas envolvidas em IDs duplicados | 50 |
| Linhas excedentes se fosse mantida uma por ID | 25 |
| Duplicatas integralmente idênticas | 1 |

As duplicidades **não foram removidas**, pois não existe regra de precedência. Nos 25 pares, datas, idade, NPS, engajamento e churn são iguais; os conflitos aparecem apenas em campos de texto e valor: `canal_aquisicao` (18 IDs), `plano` (15), `valor_mensal` (8), `motivo_cancelamento` (3) e `regiao` (2). Tudo indica que é o mesmo registro inserido duas vezes com problemas de digitação ou de escala. Em dois casos a duplicata permitiria recuperar a região `?`: cliente 1805 (Centro-Oeste) e cliente 5298 (Sudeste).

### Ausências

| Coluna | Nulos | Interpretação inicial |
|---|---:|---|
| `data_cancelamento` | 3.509 | Coerente com os 3.509 registros marcados como ativos. |
| `motivo_cancelamento` | 3.509 | Coerente com a ausência de cancelamento nos ativos. |
| `data_ultimo_acesso` | 50 | Requer confirmação; pode representar falta de rastreamento ou ausência de acesso. |
| Demais colunas | 0 | Sem nulos formais. |

Ausência formal e qualidade são conceitos diferentes: `regiao` não possui nulos, mas contém `?` em 170 registros. Esses registros têm perfil igual ao das demais regiões em canal, plano, ciclo, idade, NPS, engajamento e churn, então não é possível inferir a região a partir de outras colunas.

### Categorias e normalização

A coluna `plano` possuía oito grafias equivalentes. Foram removidas diferenças de espaços, caixa e acentuação, resultando em:

| Plano normalizado | Registros |
|---|---:|
| Basico | 2.062 |
| Padrao | 1.965 |
| Premium | 998 |

O mesmo tratamento (minúsculas, sem acento e um nome padrão para cada grafia) foi aplicado a outras duas colunas:

| Coluna | Grafias originais | Resultado |
|---|---|---|
| `canal_aquisicao` | `Organico`/`orgânico`, `Indicacao`/`indicação`, `Google`/`google`, `IG`/`Instagram`/`instagram` | Instagram 1.547; Organico 1.510; Indicacao 1.082; Google 886 |
| `motivo_cancelamento` | `Preço`/`preco`/`PREÇO`, `Problema técnico`/`problema tecnico` | Preco 510; Pouco conteudo novo 385; Problema tecnico 250; Falta de tempo 174; Concorrente 130; Outro 67 |

Os acentos estão gravados corretamente no arquivo (UTF-8). Em alguns terminais do Windows eles aparecem como `�`, mas isso é só exibição, não corrupção dos dados. `IG` foi tratado como abreviação de Instagram.

### Validação das datas

As quatro colunas de data foram convertidas para `datetime`. Valores inválidos seriam convertidos para `NaT`; a conversão não acrescentou novos nulos.

| Verificação cronológica | Ocorrências |
|---|---:|
| Assinatura posterior ao cancelamento | 0 |
| Último acesso posterior à extração | 0 |
| Cancelamento posterior à extração | 0 |
| `churn = 1` sem data de cancelamento | 0 |
| `churn = 0` com data de cancelamento | 0 |
| Último acesso anterior à assinatura | 1 |

A inconsistência encontrada pertence ao `cliente_id` **3426** (cancelado): assinatura em 18/08/2023 e último acesso em 02/07/2023, diferença de **−47 dias**. O registro é listado no relatório e **retirado das análises** pelo filtro `diferencas_data_validas`. Depois do filtro, nenhuma das quatro diferenças de datas tem valor negativo.

### Diferenças entre datas

Valores da base completa, antes da retirada do registro 3426:

| Diferença em dias | Contagem | Média | Mediana | Mínimo | Máximo | Outliers pelo boxplot |
|---|---:|---:|---:|---:|---:|---:|
| Assinatura até cancelamento | 1.516 | 220,41 | 182,5 | 11 | 1.067 | 53 |
| Assinatura até último acesso | 4.975 | 372,19 | 307 | −47 | 1.809 | 148 |
| Último acesso até extração | 4.975 | 40,45 | 20 | 0 | 469 | 630 |
| Assinatura até extração | 5.025 | 412,43 | 349 | 1 | 1.815 | 148 |

Os outliers foram identificados pela regra de 1,5 vezes a amplitude interquartil. Um outlier não é automaticamente um erro; ele indica apenas que o valor merece investigação.

### Valores numéricos suspeitos

- `idade` varia de **−2 a 300 anos**: existem 3 valores negativos, 9 abaixo de 18 e 4 acima de 100.
- `valor_mensal` possui os valores 19,9; 34,9; 55,9; 1990; 3490 e 5590. Há 603 registros acima de 100, todos exatamente 100 vezes um preço válido, o que sugere erro de escala ou de separador decimal.
- `nps` varia de 0 a 10, dentro da faixa esperada.
- `dias_ativos_ult_mes` varia de 0 a 28.
- `horas_assistidas_total` varia de 0 a 900.

Idades e valores mensais suspeitos foram **preservados na base** e **excluídos por filtro** das análises em que distorceriam o resultado (histogramas, clientes ativos e receita). Corrigir o `valor_mensal` dividindo por 100 parece plausível, mas não foi feito sem confirmação da fonte.

### Situação de cancelamento

| Situação | Registros | Participação bruta |
|---|---:|---:|
| Ativos (`churn = 0`) | 3.509 | 69,83% |
| Cancelados (`churn = 1`) | 1.516 | 30,17% |

Os 30,17% representam a proporção de registros cancelados neste arquivo. Esse valor **não deve ser chamado de taxa mensal de churn**, porque a base não delimita uma população exposta no início de um mês específico e contém clientes com tempos de acompanhamento diferentes.

## Tratamentos realizados

| Problema | Quantidade afetada | Decisão | Efeito |
|---|---:|---|---|
| Datas armazenadas como texto | 4 colunas | Conversão para `datetime` com `errors="coerce"` | Permite validar ordem e calcular intervalos. |
| Oito grafias de plano | 5.025 registros avaliados; 3.167 textos alterados | Normalização para Basico, Padrao e Premium | Evita fragmentação das contagens por grafia. |
| Diferenças de datas inexistentes | 4 indicadores novos | Cálculo em dias | Permite sanity check, estatísticas e boxplots. |
| Data cronologicamente incoerente | 1 registro (cliente 3426) | Listada no relatório e retirada das análises | A base analisada passa a ter 5.024 registros. |
| Duplicidades de cliente | 25 IDs | Preservadas | Evita remoção arbitrária; indicadores ainda podem sofrer influência. |
| Região `?` | 170 registros | Preservada; excluída das contagens e análises que usam região | As proporções por região consideram só regiões informadas. |
| Idades fora de 0 a 100 | 4 registros | Preservadas; excluídas dos histogramas e das análises de idade e de ativos | Evita que valores impossíveis distorçam médias e gráficos. |
| Mensalidades acima de 100 | 603 registros | Preservadas; excluídas dos histogramas e das análises de valor e receita | Evita somar valores com escala provavelmente errada. |
| Canais e motivos com grafias equivalentes | 9 grafias de canal e 9 de motivo | Normalização para 4 canais e 6 motivos (`IG` = Instagram) | Permite o Pareto dos motivos e a segmentação por canal. |
| Funil: etapa com 3 grafias e linhas repetidas | `assinou_plano` (3 grafias); 50 linhas duplicadas | Padronização das etapas e remoção das duplicatas exatas | O funil passa a ter 5 etapas e 12.836 eventos de 5.000 clientes. |

Os filtros ficam na classe `Filtros` e são aplicados por nome. Cada análise usa apenas os filtros que fazem sentido para ela, e os relatórios mostram quantos registros cada filtro removeu:

| Filtro | Regra |
|---|---|
| `diferencas_data_validas` | Nenhuma diferença de datas negativa (nulos são mantidos) |
| `clientes_ativos` / `clientes_cancelados` | `churn = 0` / `churn = 1` |
| `idade_valida` | Idade entre 0 e 100 anos, inclusive |
| `valor_mensal_valido` | `valor_mensal` até 100 |
| `regiao_informada` | Região diferente de `?` |

## Indicadores

Calculados sobre a base sem o registro com datas incoerentes (5.024 registros). As 25 duplicidades ainda estão incluídas.

| Indicador | Definição | Resultado |
|---|---|---|
| Proporção de cancelados | Registros com `churn = 1` / registros analisados | 1.515 / 5.024 = **30,16%** |
| Proporção por região | Cancelados da região / clientes da região (sem `?`) | De 29,5% a 32,2% (tabela abaixo) |
| Proporção por ciclo | Cancelados do ciclo / clientes do ciclo | Anual 30,16%; Mensal 30,15% |
| Valor mensal de ativos | Soma de `valor_mensal` dos ativos com valor até 100 | **103.823,10** em 3.099 ativos (410 ativos excluídos pelo filtro de valor). A unidade monetária ainda não foi confirmada e o valor não equivale a caixa recebido. |
| Proporção por plano | Cancelados em jan/2024 do plano / ativos do plano em 01/01/2024 | Basico 11,8%; Padrao 8,3%; Premium 8,6% (seção [Churn em 2024](#churn-em-2024-x-perfil-e-uso)) |
| Proporção por canal | — | Pendente (o canal já foi normalizado) |
| Motivos de cancelamento | Contagem e participação entre os 1.515 cancelados; nenhum sem motivo | Preco 33,6%; Pouco conteudo novo 25,4%; Problema tecnico 16,5%; Falta de tempo 11,5%; Concorrente 8,6%; Outro 4,4% (seção [Pareto](#pareto-dos-motivos-de-cancelamento)) |

| Região | Clientes | Participação | Cancelados | Proporção de cancelados |
|---|---:|---:|---:|---:|
| Sudeste | 2.057 | 42,4% | 606 | 29,5% |
| Nordeste | 963 | 19,8% | 287 | 29,8% |
| Sul | 938 | 19,3% | 277 | 29,5% |
| Centro-Oeste | 488 | 10,1% | 157 | 32,2% |
| Norte | 408 | 8,4% | 130 | 31,9% |

**Clientes ativos.** Com os filtros `clientes_ativos`, `idade_valida`, `valor_mensal_valido` e `regiao_informada`, restam 2.996 ativos. Eles têm em média **14,7 meses** de assinatura (mediana de 13) e **receita acumulada estimada de 492,51** por cliente, somando 1.475.547,50. O tempo de assinatura é praticamente igual entre os planos (mediana de 13 meses nos três).

## Análise bivariada

Gerada por `02-analise-univarida-bivariada.py`. Testes com nível de significância de 5%; associação não comprova causa.

| Relação | Ferramentas | Resultado |
|---|---|---|
| Assinaturas x região | Contagem, proporção por região, qui-quadrado e V de Cramér | O Sudeste concentra 42,4% das assinaturas. A proporção de cancelados não difere de forma significativa entre regiões (χ² = 2,17; p = 0,70; V = 0,02). |
| Idade x cancelamento | Teste t de Welch, correlação ponto-bisserial e proporção por faixa etária | Idade média de 36,2 anos nos ativos e 36,3 nos cancelados, sem diferença significativa (p = 0,73; r = 0,005). As faixas com proporções diferentes (menores de 18 e acima de 65) têm poucos clientes. |
| Receita acumulada x tempo de assinatura | Pearson, Spearman, regressão linear geral e por plano | Correlação muito forte (r = 0,81; Spearman 0,85). Cada mês soma em média 33,47 à receita acumulada (R² = 65%). A relação é forte **por construção**, porque a receita é meses x valor mensal: dentro de cada plano, R² = 100% e a inclinação é o próprio valor mensal. |
| Ciclo x cancelamento | Tabela cruzada, qui-quadrado e V de Cramér | Proporções praticamente idênticas (30,16% anual e 30,15% mensal; p = 0,99). Contraria a hipótese 1. |

Nem região, nem idade, nem ciclo diferenciam quem cancela. Proporções tão parecidas entre grupos são incomuns em bases reais e podem indicar que a base é sintética.

### Churn em 2024 x perfil e uso

A base vai até 31/01/2024, então 2024 tem apenas janeiro. Seguindo a definição de taxa de um período do enunciado, a **população exposta** são os 3.885 clientes ativos em 01/01/2024 e o **churn de 2024** são os 380 que cancelaram entre 01/01 e 31/01/2024: **9,78% no mês**. Os 6 clientes que assinaram em janeiro ficam de fora. Depois do filtro de idade, a análise usa 3.880 clientes, dos quais 379 cancelaram.

| Variável | Mediana nos ativos | Mediana nos cancelados | AUC | Leitura |
|---|---:|---:|---:|---|
| `horas_por_mes` | 24,6 | 5,4 | 0,01 | Separa muito. Quem assiste menos de 10 h/mês cancelou 91,5%; de 20 h/mês para cima, cerca de 0%. |
| `horas_assistidas_total` | 323,3 | 22,7 | 0,01 | Separa muito, mas é acumulada e cresce com o tempo de casa. |
| `nps` | 7 | 4 | 0,12 | Separa bem. Detratores (0 a 6) cancelaram 24,2%, neutros 2,6% e promotores 0%. |
| `meses_assinatura` (em 01/01/2024) | 12 | 4 | 0,16 | Separa bem. Clientes com menos de 3 meses cancelaram 37%; com 24 meses ou mais, 0%. |
| `idade` | 36 | 36 | 0,51 | Não separa. |
| `dias_ativos_ult_mes` | 14 | 3 | 0,002 | Consequência da saída: medida no mesmo mês do cancelamento. |
| `dias_ultimo_acesso_extracao` | 14 | 40 | 0,94 | Consequência da saída: recência medida na extração. |

AUC é a chance de um cliente que cancelou ter valor maior que um que ficou: 0,5 significa que a variável não separa os grupos; perto de 0 ou de 1, que separa muito. Por categoria, o plano Básico teve a maior taxa (11,8%, contra 8,3% no Padrão e 8,6% no Premium; p = 0,002), mas a associação é fraca (V de Cramér = 0,06). Ciclo (p = 0,86) e região (p = 0,45) não mostraram diferença.

O consumo por mês, o NPS e o tempo de casa são os principais candidatos para definir o público da iniciativa de retenção. Antes disso, é preciso confirmar quando o NPS foi coletado e verificar se essas variáveis continuam relevantes quando analisadas juntas, por exemplo com uma regressão logística.

### Visualizações implementadas

| Visualização | Relatório |
|---|---|
| Gráficos de barras de `plano`, `ciclo`, `regiao` (sem `?`) e `canal_aquisicao` | `relatorio_clientes.html` |
| Boxplots das quatro diferenças entre datas | `relatorio_clientes.html` |
| Histogramas com curva de densidade (KDE) de `idade` (0 a 100), `valor_mensal` (até 100), `nps`, `dias_ativos_ult_mes` e `horas_assistidas_total` | `relatorio_clientes.html` |
| Clientes e proporção de cancelados por região | `analise_bivariada.html` |
| Histograma da idade: ativos x cancelados (% de cada grupo, com KDE e mediana) | `analise_bivariada.html` |
| Dispersão da receita acumulada x meses de assinatura, com reta de regressão e média por mês | `analise_bivariada.html` |
| Clientes e proporção de cancelados por ciclo | `analise_bivariada.html` |
| Churn de 2024: histogramas de ativos x cancelados (% de cada grupo, com KDE e mediana) para idade, NPS, dias ativos, horas assistidas, horas por mês, tempo de casa e recência, acompanhados da tabela de taxa por faixa | `analise_bivariada.html` |
| Churn de 2024: clientes e taxa de cancelamento por plano, ciclo e região | `analise_bivariada.html` |
| RFM: mapa de calor das notas R x F e tamanho e valor de cada segmento | `analise_final.html` |
| Taxa de cancelamento de jan/2024 por quintil de horas por mês, NPS, tempo de casa, horas assistidas e idade | `analise_final.html` |
| Cohort: mapa de calor da retenção por mês de assinatura e curva de retenção média | `analise_final.html` |
| Cohort: assinaram, renovaram e se mantiveram por cohort de 2023, e retenção de quem renovou x quem não renovou | `analise_final.html` |
| Pareto dos motivos de cancelamento | `analise_final.html` |
| Funil de conversão por etapa | `analise_final.html` |

O enunciado pede, para cada visualização, o que foi observado, qual decisão ela apoia e qual limitação impede uma conclusão mais forte. Esses comentários existem na análise bivariada e na análise final, e ainda precisam ser escritos para os gráficos do relatório principal.

## Análise final: RFM, quintis, cohort, Pareto e funil

Gerada por `03-analise-final.py`.

### RFM adaptado aos clientes ativos

População: 3.099 ativos com `valor_mensal` validado. R = dias desde o último acesso (menos dias, nota maior), F = dias ativos no último mês e M = valor mensal.

**Adaptação:** R e F recebem notas de 1 a 5 por quintis. Valores iguais ficam sempre no mesmo quintil, então os grupos têm tamanhos diferentes (de 535 a 693 em R e de 472 a 822 em F). M tem só 3 preços e forma apenas 2 grupos por quintil; por isso recebe notas 1, 3 e 5 conforme o preço. Os segmentos seguem regras explícitas sobre R e F; M entra como perfil de valor.

| Segmento | Regra | Clientes | % dos ativos | % do valor mensal | Ação sugerida |
|---|---|---:|---:|---:|---|
| Engajados | R ≥ 4 e F ≥ 4 | 404 | 13% | 13% | Programa de indicação e oferta de upgrade |
| Regulares | R ≥ 3 e F ≥ 3 | 579 | 19% | 19% | Recomendações e avisos de lançamentos |
| Atenção | Uma nota boa e outra fraca | 1.499 | 48% | 49% | Lembretes personalizados com conteúdo novo |
| Baixo engajamento | R ≤ 2 e F ≤ 2 | 584 | 19% | 19% | Reengajamento; público candidato ao teste de retenção |
| Sem acesso registrado | Sem data de último acesso | 33 | 1% | 1% | Conferir rastreamento ou problema técnico |

Recência e frequência quase não andam juntas, e o valor mensal médio é parecido em todos os segmentos. Os segmentos descrevem engajamento observado; tratá-los como risco de churn exigiria validação com cancelamentos futuros.

### Quintis

Taxa de cancelamento de janeiro/2024 (ativos em 01/01/2024) em cada quintil:

| Variável | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---:|---:|---:|---:|---:|
| Horas por mês | 48,6% (até 16,1 h) | 0,0% | 0,1% | 0,1% | 0,0% |
| NPS | 32,9% (0 a 5) | 7,1% (6 e 7) | 1,9% (8) | 0,0% (9) | 0,0% (10) |
| Tempo de casa | 27,9% (0 a 5 meses) | 10,5% | 4,1% | 1,4% | 0,0% (21+ meses) |
| Idade | 9,3% | 10,5% | 9,4% | 10,2% | 9,5% |

O cancelamento se concentra no quintil de menor consumo, no de NPS mais baixo e nos clientes mais novos. A idade não muda a taxa.

### Cohort

Retenção das cohorts de 2023 (clientes que assinaram no mesmo mês), usando só os meses já observáveis na extração. A retenção média cai para **84% no 6º mês** e **77% no 12º**. Na matriz, as primeiras cohorts de 2023 ficam com 100% por 5 a 6 meses e as últimas caem já no 1º ou 2º mês. A queda aparece sempre nos mesmos meses do calendário (set/2023 a jan/2024), o que indica um **efeito de calendário**: algo mudou nesse período, independentemente do tempo de casa.

Só 2023 foi usado porque a base quase não tem cancelamentos antes de dez/2022 (5 em 2022, contra 1.128 em 2023 e 382 em janeiro de 2024). As cohorts antigas pareceriam ter retenção perfeita, o que sugere que a base guarda só clientes que estavam ativos recentemente.

**Assinaram, renovaram e se mantiveram.** A base principal não registra quem voltou a assinar: cada cliente tem uma única assinatura, os IDs repetidos têm as mesmas datas e nenhum cancelado acessou depois de cancelar. A renovação veio da etapa `renovou` do funil, cruzada com a cohort de cada cliente:

| Ano de assinatura | Assinaram | Renovaram (funil) | Se mantiveram (ativos) | Se mantiveram entre quem renovou | Entre quem não renovou |
|---|---:|---:|---:|---:|---:|
| 2019 | 20 | 3 (15,0%) | 20 (100%) | 100% | 100% |
| 2020 | 89 | 15 (16,9%) | 86 (96,6%) | 93,3% | 97,3% |
| 2021 | 428 | 59 (13,8%) | 397 (92,8%) | 94,9% | 92,4% |
| 2022 | 1.641 | 228 (13,9%) | 1.285 (78,3%) | 73,2% | 79,1% |
| 2023 | 2.815 | 387 (13,7%) | 1.697 (60,3%) | 58,4% | 60,6% |

O `renovou` do funil parece pouco confiável: a proporção de quem renovou é quase igual em todos os anos (13,7% a 16,9%), quem renovou tem o mesmo tempo de casa de quem não renovou, 2 clientes "renovaram" com menos de 1 mês de assinatura, e a retenção dos dois grupos é praticamente a mesma. Esse dado não deve orientar a escolha do público até a fonte confirmar o que a etapa registra.

### Pareto dos motivos de cancelamento

| Motivo | Cancelados | Participação | Acumulado |
|---|---:|---:|---:|
| Preco | 509 | 33,6% | 33,6% |
| Pouco conteudo novo | 385 | 25,4% | 59,0% |
| Problema tecnico | 250 | 16,5% | 75,5% |
| Falta de tempo | 174 | 11,5% | 87,0% |
| Concorrente | 130 | 8,6% | 95,6% |
| Outro | 67 | 4,4% | 100,0% |

Quatro dos seis motivos somam 87% das saídas; a regra 80/20 não se aplica. Preço e pouco conteúdo novo explicam 59%. Todos os 1.515 cancelados têm motivo informado, e a distribuição de janeiro/2024 é parecida com a do total.

### Funil

Usuários únicos que alcançaram cada etapa, na ordem do funil:

| Etapa | Usuários | Conversão da etapa anterior | Conversão do topo |
|---|---:|---:|---:|
| visitou_site | 5.000 | — | 100,0% |
| criou_conta | 3.377 | 67,5% | 67,5% |
| assistiu_1a_aula | 2.698 | 79,9% | 54,0% |
| **assinou_plano** | **1.066** | **39,5%** | **21,3%** |
| renovou | 695 | 65,2% | 13,9% |

**Maior gargalo: de `assistiu_1a_aula` para `assinou_plano`.** Só 39,5% de quem assistiu à primeira aula assina um plano, uma queda de 60,5% e 1.632 usuários perdidos. É a menor conversão entre etapas e também a maior perda em número de usuários. Todas as jornadas seguem a ordem, sem pular etapas. A proporção de cancelados na base principal quase não muda com a etapa final do funil.

**Incoerência entre as bases:** o funil diz que 1.066 clientes assinaram, mas todos os 5.000 clientes da base principal são assinantes. Antes de cruzar o funil com o churn, é preciso confirmar com a fonte o que os eventos representam.

## Limitações e próximas etapas

Limitações atuais:

- As 25 duplicidades de `cliente_id` ainda podem contar o mesmo cliente duas vezes.
- A unidade de `valor_mensal` não foi confirmada; os 603 valores acima de 100 foram excluídos, não corrigidos.
- A base é um retrato de uma data: clientes com tempos de assinatura diferentes tiveram chances diferentes de cancelar.
- A receita acumulada é uma estimativa (meses completos x valor mensal) e vale apenas para ativos.
- A base quase não registra cancelamentos antes de dez/2022, então parece guardar só clientes ativos recentemente.
- O `funil_eventos.csv` não é coerente com a base principal na etapa de assinatura.

Próximas etapas, na ordem do enunciado:

1. Definir uma regra para consolidar os 25 clientes duplicados.
2. Calcular a proporção de cancelados por canal, com contagens e denominadores.
3. Analisar NPS, horas por mês e tempo de casa juntos (por exemplo, com regressão logística) e confirmar quando o NPS foi coletado.
4. Investigar o que mudou a partir de set/2023, quando os cancelamentos se concentram.
5. Escolher uma iniciativa e um público, simular cenários e propor um teste com grupo de controle.
6. Escrever a conclusão executiva e decidir se os scripts serão convertidos em notebook.

Até que essas etapas sejam concluídas, os resultados permitem descrever e auditar a base, mas não sustentam uma recomendação de retenção.
