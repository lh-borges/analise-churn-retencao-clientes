<<<<<<< HEAD
# Auditoria da base de clientes

## Sobre o exercício

Este projeto parte do enunciado [Módulo 01 — Projeto Exercício](../../Modulo_01_Projeto_Exercício.pdf), cujo desafio é investigar o cancelamento de clientes de uma plataforma de conteúdo por assinatura. O objetivo final é recomendar uma única iniciativa de retenção, definir o público prioritário e indicar como o resultado deverá ser medido.

Esta primeira versão do projeto concentra-se na **auditoria e preparação da base**. Ela verifica a estrutura dos dados, tipos, ausências, duplicidades, categorias inconsistentes, relações entre datas, valores numéricos suspeitos e distribuições. Nenhuma alteração é gravada no CSV original.

## Decisão de negócio

O problema investigado é o cancelamento de assinaturas. A análise deverá apoiar a escolha da primeira iniciativa de retenção a ser testada, identificando um público com oportunidade relevante e indicadores adequados para acompanhar o teste.

A coluna `churn` foi interpretada como um indicador de situação: `1` representa cliente cancelado e `0` representa cliente ativo na data de extração. Essa interpretação é coerente com `data_cancelamento`, mas ainda deve ser confirmada com o responsável pela base. Os dados representam um retrato extraído em **31/01/2024**, com assinaturas iniciadas entre **11/02/2019 e 30/01/2024**. A base possui 5.025 registros e 5.000 clientes únicos.

Três hipóteses iniciais para as próximas etapas são:

1. Clientes de ciclo mensal apresentam maior proporção de cancelamento do que clientes de ciclo anual. A hipótese será contrariada se a proporção do ciclo anual for igual ou superior, considerando o tamanho dos grupos.
2. Clientes cancelados apresentam NPS e engajamento menores. A hipótese será contrariada se as distribuições de NPS, dias ativos e horas assistidas forem semelhantes ou melhores entre cancelados.
3. Clientes com maior tempo desde o último acesso apresentam mais cancelamentos. A hipótese será contrariada se a associação não aparecer entre clientes com tempos de acompanhamento comparáveis. Essa variável exige cautela porque pode refletir o próprio cancelamento.

Para avaliar uma iniciativa real ainda seriam necessários custos de campanha, margem por cliente, histórico de cobrança, datas dos contatos, exposição a campanhas anteriores, reclamações, eventos de uso com data e resultados de um teste controlado.

## Fontes de dados

- `data/clientes_base.csv`: base principal usada nesta auditoria.
- `data/funil_eventos.csv`: base opcional, ainda não usada no fluxo atual.
- `Modulo_01_Projeto_Exercício.pdf`: enunciado do projeto.

O arquivo original `clientes_base.csv` é somente lido. Normalizações e colunas calculadas existem apenas no DataFrame em memória.

## Estrutura do projeto

```text
Modulo - Auditar_Contagoole/
├── init.py
├── README.md
├── data/
│   ├── clientes_base.csv
│   └── funil_eventos.csv
├── analise_bivariada.py
└── funcao/
    ├── extracao_normalizacao.py
    ├── geracao_colunas.py
    ├── filtros.py
    ├── estatistica_descritiva.py
    ├── estatistica_bivariada.py
    ├── distribuicoes.py
    ├── histograma.py
    ├── receita.py
    └── relatorio_html.py
```

- `init.py`: chama cada etapa da auditoria, imprime as tabelas e abre os gráficos.

Cada arquivo de `funcao/` contém uma classe. Os métodos com `_` na frente são de uso interno da classe.

| Arquivo | Classe | Uso |
|---|---|---|
| `extracao_normalizacao.py` | `ExtracaoNormalizacao(caminho_csv)` | `carregar()`: lê o CSV, converte datas e normaliza `plano`. |
| `geracao_colunas.py` | `GeracaoColunas()` | `adicionar_diferencas_data(df)`: cria as diferenças entre datas, em dias. |
| `filtros.py` | `Filtros(idade_minima, idade_maxima, valor_mensal_maximo)` | `aplicar(df, nomes)`: aplica os filtros pelo nome e resume quantos registros cada um removeu; `disponiveis` lista os nomes. |
| `estatistica_descritiva.py` | `EstatisticaDescritiva(df)` | Tabelas descritivas, sanity checks, datas inválidas, contagens categóricas, boxplots e gráficos de barras. |
| `histograma.py` | `Histograma(colunas, limites, bins)` | `gerar(df)`: histogramas com curva de densidade e limites por coluna. |
| `receita.py` | `Receita(df)` | Calcula meses de assinatura e receita acumulada; `estatisticas()` e `resumo_por_grupo(coluna)`. |
| `relatorio_html.py` | `RelatorioHtml(titulo)` | Monta um HTML sem framework: `adicionar_secao()`, `adicionar_tabela()`, `adicionar_lista()`, `adicionar_figura()` e `salvar(caminho)`. |
| `estatistica_bivariada.py` | `EstatisticaBivariada(df)` | Pearson, Spearman, regressão linear, teste t de Welch, ponto-bisserial, qui-quadrado, V de Cramér, taxas por faixa ou categoria e os gráficos de cada um. |
| `distribuicoes.py` | `Distribuicoes` | P-valores das distribuições t e qui-quadrado, implementados sem o scipy. |

`analise_bivariada.py` usa essas classes para cruzar região x assinaturas, idade x cancelamento, receita acumulada x tempo de assinatura e ciclo x cancelamento, e gera `saida/analise_bivariada.html`:

```powershell
python ".\Modulo - Auditar_Contagoole\analise_bivariada.py"
```

Os métodos não imprimem nem chamam `plt.show()`: retornam tabelas, DataFrames ou figuras para que qualquer script os reutilize. O fluxo de `init.py` é:

```text
init.py
  → ExtracaoNormalizacao(caminho).carregar()
  → GeracaoColunas().adicionar_diferencas_data()
  → EstatisticaDescritiva(df): tabelas e verificações da base completa
  → Filtros().aplicar() → Receita(df_ativos): estatísticas dos ativos
  → gráficos
  → RelatorioHtml.salvar() → saida/relatorio_clientes.html
```

## Como executar

Requisitos:

- Python 3.10 ou superior.
- pandas.
- matplotlib.

Instalação das bibliotecas:

```powershell
pip install pandas matplotlib
```

Execução a partir da pasta `Exercícios`:

```powershell
python ".\Modulo - Auditar_Contagoole\init.py"
```

O programa gera o relatório `saida/relatorio_clientes.html` e o abre no navegador. O arquivo é único e independente: as tabelas, o estilo e os três gráficos (boxplots das diferenças de datas, barras das categorias e histogramas das variáveis numéricas) ficam dentro dele, sem framework nem arquivos externos.

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

Também foram criadas, somente em memória, quatro colunas em dias:

- `dias_assinatura_cancelamento`;
- `dias_assinatura_ultimo_acesso`;
- `dias_ultimo_acesso_extracao`;
- `dias_assinatura_extracao`.

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

As duplicidades **não foram removidas**, pois não existe regra de precedência. Entre os 25 IDs duplicados foram observados conflitos em `plano` (15 IDs), `valor_mensal` (8), `regiao` (2), `canal_aquisicao` (18) e `motivo_cancelamento` (3). A decisão correta depende de uma chave temporal ou regra de negócio que não está disponível.

### Ausências

| Coluna | Nulos | Interpretação inicial |
|---|---:|---|
| `data_cancelamento` | 3.509 | Coerente com os 3.509 registros marcados como ativos. |
| `motivo_cancelamento` | 3.509 | Coerente com a ausência de cancelamento nos ativos. |
| `data_ultimo_acesso` | 50 | Requer confirmação; pode representar falta de rastreamento ou ausência de acesso. |
| Demais colunas | 0 | Sem nulos formais. |

Ausência formal e qualidade são conceitos diferentes: `regiao` não possui nulos, mas contém `?` em 170 registros.

### Categorias e normalização

A coluna `plano` possuía oito grafias equivalentes. Foram removidas diferenças de espaços, caixa e acentuação, resultando em:

| Plano normalizado | Registros |
|---|---:|
| Basico | 2.062 |
| Padrao | 1.965 |
| Premium | 998 |

Essa transformação ocorre apenas no DataFrame. Outras inconsistências foram identificadas, mas preservadas nesta etapa:

- `canal_aquisicao`: `Organico`/`orgânico`, `Indicacao`/`indicação`, `Google`/`google` e `IG`/`Instagram`/`instagram`;
- `motivo_cancelamento`: `Preço`/`preco`/`PREÇO` e `Problema técnico`/`problema tecnico`;
- `regiao`: 170 registros com `?`.

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

A inconsistência cronológica encontrada pertence ao `cliente_id` **3426**: assinatura em 18/08/2023 e último acesso em 02/07/2023, diferença de **−47 dias**. O registro foi sinalizado, mas não corrigido.

### Diferenças entre datas

| Diferença em dias | Contagem | Média | Mediana | Mínimo | Máximo | Outliers pelo boxplot |
|---|---:|---:|---:|---:|---:|---:|
| Assinatura até cancelamento | 1.516 | 220,41 | 182,5 | 11 | 1.067 | 53 |
| Assinatura até último acesso | 4.975 | 372,19 | 307 | −47 | 1.809 | 148 |
| Último acesso até extração | 4.975 | 40,45 | 20 | 0 | 469 | 630 |
| Assinatura até extração | 5.025 | 412,43 | 349 | 1 | 1.815 | 148 |

Os outliers foram identificados pela regra de 1,5 vezes a amplitude interquartil. Um outlier não é automaticamente um erro; ele indica apenas que o valor merece investigação.

### Valores numéricos suspeitos

- `idade` varia de **−2 a 300 anos**: existem 3 valores negativos, 9 abaixo de 18 e 4 acima de 100.
- `valor_mensal` possui os valores 19,9; 34,9; 55,9; 1990; 3490 e 5590. Há 603 registros acima de 100, sugerindo possível problema de escala ou separador decimal.
- `nps` varia de 0 a 10, dentro da faixa esperada.
- `dias_ativos_ult_mes` varia de 0 a 28.
- `horas_assistidas_total` varia de 0 a 900.

Idades e valores mensais suspeitos foram **preservados**. Corrigi-los sem uma regra confirmada poderia introduzir erros e distorcer os indicadores financeiros.

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
| Duplicidades de cliente | 25 IDs | Preservadas | Evita remoção arbitrária; indicadores ainda podem sofrer influência. |
| Região `?` | 170 registros | Preservada e sinalizada | Mantém rastreabilidade da ausência disfarçada. |
| Canais e motivos equivalentes | Diversos registros | Identificados, ainda não normalizados | Pareto e segmentações não devem ser concluídos antes do tratamento. |
| Idades e mensalidades suspeitas | 13 idades extremas pelos cortes usados; 603 mensalidades acima de 100 | Preservadas e sinalizadas | Evita correção sem evidência da unidade correta. |
| Data cronologicamente incoerente | 1 registro | Preservada e listada | Impede que o problema passe despercebido. |

## Visualizações implementadas

- Gráficos de barras de `plano`, `ciclo`, `regiao` e `canal_aquisicao`.
- Boxplots das quatro diferenças entre datas.
- Histogramas de `idade`, `valor_mensal`, `nps`, `dias_ativos_ult_mes` e `horas_assistidas_total`.

Essas visualizações mostram distribuição, dispersão e valores extremos. Elas ainda não demonstram causalidade nem respondem sozinhas qual ação de retenção funcionará.

## Limitações e próximas etapas

A auditoria é uma etapa preparatória. Antes da recomendação executiva solicitada no enunciado, ainda é necessário:

1. Definir uma regra para consolidar os 25 clientes duplicados.
2. Confirmar e tratar a escala de `valor_mensal` e os limites válidos de `idade`.
3. Normalizar `canal_aquisicao`, `motivo_cancelamento` e o marcador `?` de `regiao`.
4. Calcular a proporção de cancelados por plano, ciclo e canal com contagens e denominadores.
5. Comparar NPS e engajamento por situação de churn.
6. Construir o Pareto dos motivos de cancelamento.
7. Criar o RFM adaptado somente para clientes ativos.
8. Escolher uma iniciativa e um público, simular cenários e propor um teste com grupo de controle.

Até que essas etapas sejam concluídas, os resultados permitem descrever e auditar a base, mas não sustentam uma recomendação causal de retenção.
=======
# analise-churn-retencao-clientes
>>>>>>> 47b5c182503ef85c27869a56c9c890f28ac66385
