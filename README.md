# Análise de cancelamento e retenção de clientes

## Sobre o exercício

Este projeto parte do enunciado [Módulo 01 — Projeto Exercício](../../Modulo_01_Projeto_Exercício.pdf), cujo desafio é investigar o cancelamento de clientes de uma plataforma de conteúdo por assinatura. O objetivo final é recomendar uma única iniciativa de retenção, definir o público prioritário e indicar como o resultado deverá ser medido.

O projeto já cobre a **auditoria e preparação da base**, a **estatística descritiva** e uma primeira **análise bivariada** do cancelamento. Os resultados são gerados por scripts Python e publicados em dois relatórios HTML. Nenhuma alteração é gravada no CSV original.

## Andamento em relação ao enunciado

| Etapa do enunciado | Situação | Onde está |
|---|---|---|
| 1. Decisão de negócio | Concluída | Seção [Decisão de negócio](#decisão-de-negócio) |
| 2. Auditoria e preparação da base | Concluída em grande parte; faltam a regra para duplicidades e a normalização de canal e motivo | `init.py`, seções [Resultado da auditoria](#resultado-da-auditoria) e [Tratamentos realizados](#tratamentos-realizados) |
| 3. Indicadores | Parcial: proporção de cancelados, proporção por região e por ciclo e valor mensal de ativos calculados; faltam plano, canal e motivos | Seção [Indicadores](#indicadores) |
| 4. Análise exploratória e hipóteses | Parcial: distribuições, região, ciclo, idade e receita analisados; faltam NPS, engajamento, canal, plano e tempo de acompanhamento | `analise_bivariada.py`, seção [Análise bivariada](#análise-bivariada) |
| 5. Frameworks (Pareto e RFM) | Não iniciada | — |
| 6. Recomendação, simulação e teste | Não iniciada | — |
| Entregáveis | README em andamento; os scripts e relatórios HTML fazem o papel do notebook por enquanto | Este arquivo e a pasta `saida/` |

## Decisão de negócio

O problema investigado é o cancelamento de assinaturas. A análise deverá apoiar a escolha da primeira iniciativa de retenção a ser testada, identificando um público com oportunidade relevante e indicadores adequados para acompanhar o teste.

A coluna `churn` foi interpretada como um indicador de situação: `1` representa cliente cancelado e `0` representa cliente ativo na data de extração. Essa interpretação é coerente com `data_cancelamento`, mas ainda deve ser confirmada com o responsável pela base. Os dados representam um retrato extraído em **31/01/2024**, com assinaturas iniciadas entre **11/02/2019 e 30/01/2024**. A base possui 5.025 registros e 5.000 clientes únicos.

Três hipóteses iniciais orientam a análise:

| # | Hipótese | O que a contrariaria | Situação |
|---|---|---|---|
| 1 | Clientes de ciclo mensal cancelam mais do que clientes de ciclo anual. | Proporção do ciclo anual igual ou superior, considerando o tamanho dos grupos. | **Contrariada.** 30,15% no mensal e 30,16% no anual; qui-quadrado p = 0,99. |
| 2 | Clientes cancelados apresentam NPS e engajamento menores. | Distribuições de NPS, dias ativos e horas assistidas semelhantes ou melhores entre cancelados. | A verificar. |
| 3 | Clientes com maior tempo desde o último acesso cancelam mais. | A associação não aparecer entre clientes com tempos de acompanhamento comparáveis. Essa variável exige cautela porque pode refletir o próprio cancelamento. | A verificar. |

Para avaliar uma iniciativa real ainda seriam necessários custos de campanha, margem por cliente, histórico de cobrança, datas dos contatos, exposição a campanhas anteriores, reclamações, eventos de uso com data e resultados de um teste controlado.

## Fontes de dados

- `data/clientes_base.csv`: base principal.
- `data/funil_eventos.csv`: base opcional, ainda não usada.
- `Modulo_01_Projeto_Exercício.pdf`: enunciado do projeto.

O arquivo original `clientes_base.csv` é somente lido. Normalizações, filtros e colunas calculadas existem apenas nos DataFrames em memória.

## Estrutura do projeto

```text
Modulo - Auditar_Contagoole/
├── README.md
├── init.py                      auditoria e estatística descritiva
├── analise_bivariada.py         relações entre pares de variáveis
├── data/
│   ├── clientes_base.csv
│   └── funil_eventos.csv
├── funcao/                      classes reutilizáveis, uma por arquivo
│   ├── extracao_normalizacao.py
│   ├── geracao_colunas.py
│   ├── filtros.py
│   ├── estatistica_descritiva.py
│   ├── estatistica_bivariada.py
│   ├── distribuicoes.py
│   ├── histograma.py
│   ├── receita.py
│   └── relatorio_html.py
└── saida/                       relatórios gerados (recriados a cada execução)
    ├── relatorio_clientes.html
    └── analise_bivariada.html
```

Os scripts da raiz (`init.py` e `analise_bivariada.py`) chamam as classes de `funcao/` passo a passo e montam os relatórios. As classes não imprimem nem abrem janelas: devolvem tabelas, DataFrames ou figuras, para que qualquer script possa reutilizá-las. Os métodos com `_` na frente são de uso interno de cada classe.

| Arquivo | Classe | Uso |
|---|---|---|
| `extracao_normalizacao.py` | `ExtracaoNormalizacao(caminho_csv)` | `carregar()`: lê o CSV, converte datas e normaliza `plano`. |
| `geracao_colunas.py` | `GeracaoColunas()` | `adicionar_diferencas_data(df)`: cria as diferenças entre datas, em dias. |
| `filtros.py` | `Filtros(idade_minima, idade_maxima, valor_mensal_maximo)` | `aplicar(df, nomes)`: aplica os filtros pelo nome e resume quantos registros cada um removeu; `disponiveis` lista os nomes. |
| `estatistica_descritiva.py` | `EstatisticaDescritiva(df)` | Tabelas descritivas, sanity checks, datas inválidas, contagens categóricas, boxplots e gráficos de barras. |
| `estatistica_bivariada.py` | `EstatisticaBivariada(df)` | Pearson, Spearman, regressão linear, teste t de Welch, ponto-bisserial, qui-quadrado, V de Cramér, taxas por faixa ou categoria e os gráficos de cada um. |
| `distribuicoes.py` | `Distribuicoes` | P-valores das distribuições t e qui-quadrado, implementados sem o scipy. |
| `histograma.py` | `Histograma(colunas, limites, bins)` | `gerar(df)`: histogramas com curva de densidade e limites por coluna. |
| `receita.py` | `Receita(df)` | Calcula meses de assinatura e receita acumulada; `estatisticas()` e `resumo_por_grupo(coluna)`. |
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
python ".\Modulo - Auditar_Contagoole\init.py"

# Análise bivariada → saida/analise_bivariada.html
python ".\Modulo - Auditar_Contagoole\analise_bivariada.py"
```

Cada script grava o seu relatório e o abre no navegador. Cada relatório é um arquivo HTML único, com as tabelas, o estilo e os gráficos embutidos, sem framework nem arquivos externos.

| Relatório | Conteúdo |
|---|---|
| `relatorio_clientes.html` | Estrutura da base, estatística descritiva, diferenças entre datas, registros removidos, contagens categóricas, análise dos clientes ativos (meses de assinatura e receita acumulada), boxplots, gráficos de barras e histogramas com curva de densidade. |
| `analise_bivariada.html` | Conclusões, assinaturas por região, idade x cancelamento, receita acumulada x tempo de assinatura, ciclo x cancelamento e limitações. |

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
| `canal_aquisicao` | Canal de aquisição | texto | canal | Possui diferenças de caixa, acento e abreviação ainda não tratadas. |
| `nps` | Nota de recomendação | inteiro | 0 a 10 | Faixa observada válida; confirmar se é a resposta individual do NPS. |
| `data_assinatura` | Início da assinatura | datetime | data | Sem ausências após conversão. |
| `data_cancelamento` | Data do cancelamento | datetime | data | Ausente nos clientes ativos; 3.509 nulos. |
| `data_ultimo_acesso` | Último acesso registrado | datetime | data | 50 valores ausentes e uma relação cronológica inválida. |
| `data_extracao` | Data de referência da base | datetime | data | Todos os registros indicam 31/01/2024. |
| `dias_ativos_ult_mes` | Dias com atividade no último mês | inteiro | dias | Varia de 0 a 28; confirmar definição do período. |
| `horas_assistidas_total` | Consumo acumulado | decimal | horas | Varia de 0 a 900. |
| `motivo_cancelamento` | Motivo declarado para a saída | texto | categoria | Preenchido apenas para cancelados; grafias equivalentes ainda não normalizadas. |
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

Outras inconsistências foram identificadas, mas ainda não tratadas:

- `canal_aquisicao`: `Organico`/`orgânico`, `Indicacao`/`indicação`, `Google`/`google` e `IG`/`Instagram`/`instagram`;
- `motivo_cancelamento`: `Preço`/`preco`/`PREÇO` e `Problema técnico`/`problema tecnico`;
- parte do arquivo tem caracteres acentuados corrompidos (por exemplo, `Padr�o`), sinal de mistura de codificação.

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
| Canais e motivos equivalentes | Diversos registros | Identificados, ainda não normalizados | Pareto e segmentação por canal dependem desse tratamento. |

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
| Proporção por plano e por canal | — | Pendente |
| Motivos de cancelamento | — | Pendente (depende da normalização dos motivos) |

| Região | Clientes | Participação | Cancelados | Proporção de cancelados |
|---|---:|---:|---:|---:|
| Sudeste | 2.057 | 42,4% | 606 | 29,5% |
| Nordeste | 963 | 19,8% | 287 | 29,8% |
| Sul | 938 | 19,3% | 277 | 29,5% |
| Centro-Oeste | 488 | 10,1% | 157 | 32,2% |
| Norte | 408 | 8,4% | 130 | 31,9% |

**Clientes ativos.** Com os filtros `clientes_ativos`, `idade_valida`, `valor_mensal_valido` e `regiao_informada`, restam 2.996 ativos. Eles têm em média **14,7 meses** de assinatura (mediana de 13) e **receita acumulada estimada de 492,51** por cliente, somando 1.475.547,50. O tempo de assinatura é praticamente igual entre os planos (mediana de 13 meses nos três).

## Análise bivariada

Gerada por `analise_bivariada.py`. Testes com nível de significância de 5%; associação não comprova causa.

| Relação | Ferramentas | Resultado |
|---|---|---|
| Assinaturas x região | Contagem, proporção por região, qui-quadrado e V de Cramér | O Sudeste concentra 42,4% das assinaturas. A proporção de cancelados não difere de forma significativa entre regiões (χ² = 2,17; p = 0,70; V = 0,02). |
| Idade x cancelamento | Teste t de Welch, correlação ponto-bisserial e proporção por faixa etária | Idade média de 36,2 anos nos ativos e 36,3 nos cancelados, sem diferença significativa (p = 0,73; r = 0,005). As faixas com proporções diferentes (menores de 18 e acima de 65) têm poucos clientes. |
| Receita acumulada x tempo de assinatura | Pearson, Spearman, regressão linear geral e por plano | Correlação muito forte (r = 0,81; Spearman 0,85). Cada mês soma em média 33,47 à receita acumulada (R² = 65%). A relação é forte **por construção**, porque a receita é meses x valor mensal: dentro de cada plano, R² = 100% e a inclinação é o próprio valor mensal. |
| Ciclo x cancelamento | Tabela cruzada, qui-quadrado e V de Cramér | Proporções praticamente idênticas (30,16% anual e 30,15% mensal; p = 0,99). Contraria a hipótese 1. |

Até aqui, nem região, nem idade, nem ciclo diferenciam quem cancela. Proporções tão parecidas entre grupos são incomuns em bases reais e podem indicar que a base é sintética. As próximas variáveis a investigar são NPS, engajamento (dias ativos e horas assistidas), plano e canal.

### Visualizações implementadas

| Visualização | Relatório |
|---|---|
| Gráficos de barras de `plano`, `ciclo`, `regiao` (sem `?`) e `canal_aquisicao` | `relatorio_clientes.html` |
| Boxplots das quatro diferenças entre datas | `relatorio_clientes.html` |
| Histogramas com curva de densidade (KDE) de `idade` (0 a 100), `valor_mensal` (até 100), `nps`, `dias_ativos_ult_mes` e `horas_assistidas_total` | `relatorio_clientes.html` |
| Clientes e proporção de cancelados por região | `analise_bivariada.html` |
| Boxplot da idade por churn e proporção de cancelados por faixa etária | `analise_bivariada.html` |
| Dispersão da receita acumulada x meses de assinatura, com reta de regressão e média por mês | `analise_bivariada.html` |
| Clientes e proporção de cancelados por ciclo | `analise_bivariada.html` |

O enunciado pede, para cada visualização, o que foi observado, qual decisão ela apoia e qual limitação impede uma conclusão mais forte. Esses comentários já existem na análise bivariada e ainda precisam ser escritos para os gráficos do relatório principal.

## Limitações e próximas etapas

Limitações atuais:

- As 25 duplicidades de `cliente_id` ainda podem contar o mesmo cliente duas vezes.
- A unidade de `valor_mensal` não foi confirmada; os 603 valores acima de 100 foram excluídos, não corrigidos.
- A base é um retrato de uma data: clientes com tempos de assinatura diferentes tiveram chances diferentes de cancelar.
- A receita acumulada é uma estimativa (meses completos x valor mensal) e vale apenas para ativos.

Próximas etapas, na ordem do enunciado:

1. Definir uma regra para consolidar os 25 clientes duplicados.
2. Normalizar `canal_aquisicao` e `motivo_cancelamento`.
3. Calcular a proporção de cancelados por plano e por canal, com contagens e denominadores.
4. Comparar NPS e engajamento por situação de churn (hipótese 2).
5. Avaliar o tempo desde o último acesso com clientes de acompanhamento comparável (hipótese 3).
6. Construir o Pareto dos motivos de cancelamento.
7. Criar o RFM adaptado somente para clientes ativos.
8. Escolher uma iniciativa e um público, simular cenários e propor um teste com grupo de controle.
9. Escrever a conclusão executiva e decidir se os scripts serão convertidos em notebook.

Até que essas etapas sejam concluídas, os resultados permitem descrever e auditar a base, mas não sustentam uma recomendação de retenção.
