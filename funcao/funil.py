from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class Funil:
    """Le a base de eventos do funil, limpa as etapas e mede as conversoes.

    A base tem so cliente_id e etapa, sem data do evento: da para contar
    clientes por etapa e checar a ordem da jornada, mas nao o tempo entre etapas.
    """

    # Ordem esperada da jornada
    ETAPAS = [
        "visitou_site",
        "criou_conta",
        "assistiu_1a_aula",
        "assinou_plano",
        "renovou",
    ]

    def __init__(self, caminho_csv: str | Path) -> None:
        """Guarda o caminho do arquivo de eventos."""
        self.caminho_csv = Path(caminho_csv)

    def carregar(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Devolve os eventos limpos e um resumo do que a limpeza mudou."""
        eventos_brutos = pd.read_csv(self.caminho_csv)

        # Padronizei a etapa: "Assinou_Plano" e "assinou plano" viram "assinou_plano"
        eventos = eventos_brutos.assign(
            etapa=eventos_brutos["etapa"].str.strip().str.lower().str.replace(" ", "_")
        )
        etapas_desconhecidas = sorted(set(eventos["etapa"]) - set(self.ETAPAS))
        eventos_sem_duplicatas = eventos.drop_duplicates()

        resumo = pd.DataFrame(
            [
                ("linhas_no_arquivo", len(eventos_brutos)),
                ("grafias_de_etapa_no_arquivo", eventos_brutos["etapa"].nunique()),
                ("etapas_apos_padronizar", eventos["etapa"].nunique()),
                ("etapas_fora_da_ordem_esperada", ", ".join(etapas_desconhecidas) or "nenhuma"),
                ("linhas_duplicadas_removidas", len(eventos) - len(eventos_sem_duplicatas)),
                ("linhas_apos_limpeza", len(eventos_sem_duplicatas)),
                ("clientes_unicos", eventos_sem_duplicatas["cliente_id"].nunique()),
            ],
            columns=["medida", "valor"],
        ).set_index("medida")

        return eventos_sem_duplicatas, resumo

    def presenca(self, eventos: pd.DataFrame) -> pd.DataFrame:
        """Uma linha por cliente e uma coluna por etapa: 1 se passou pela etapa."""
        return (
            pd.crosstab(eventos["cliente_id"], eventos["etapa"])
            .clip(upper=1)
            .reindex(columns=self.ETAPAS, fill_value=0)
        )

    def contagem(self, presenca: pd.DataFrame) -> pd.DataFrame:
        """Tabela do funil, na ordem das etapas, com 3 colunas.

        usuarios: clientes unicos que alcancaram a etapa
        conversao_etapa_anterior: % da etapa anterior que avancou ate esta
        conversao_topo: % do total inicial (primeira etapa) que chegou ate esta
        """
        usuarios = presenca.sum()
        tabela = usuarios.rename("usuarios").to_frame()
        tabela["conversao_etapa_anterior"] = usuarios / usuarios.shift()
        tabela["conversao_topo"] = usuarios / usuarios.iloc[0]
        tabela.index.name = "etapa"
        return tabela

    @staticmethod
    def gargalo(contagem: pd.DataFrame) -> pd.Series:
        """Etapa com a menor conversao em relacao a etapa anterior (maior queda)."""
        etapa = contagem["conversao_etapa_anterior"].idxmin()
        posicao = contagem.index.get_loc(etapa)
        etapa_anterior = contagem.index[posicao - 1]

        return pd.Series(
            {
                "etapa": etapa,
                "etapa_anterior": etapa_anterior,
                "usuarios_etapa_anterior": contagem.loc[etapa_anterior, "usuarios"],
                "usuarios_etapa": contagem.loc[etapa, "usuarios"],
                "usuarios_perdidos": contagem.loc[etapa_anterior, "usuarios"]
                - contagem.loc[etapa, "usuarios"],
                "conversao": contagem.loc[etapa, "conversao_etapa_anterior"],
                "queda": 1 - contagem.loc[etapa, "conversao_etapa_anterior"],
            }
        )

    def consistencia(self, presenca: pd.DataFrame) -> pd.DataFrame:
        """Jornadas encontradas e se seguem a ordem (sem pular etapas)."""
        jornadas = presenca.astype(str).agg("".join, axis=1)
        tabela = jornadas.value_counts().rename("clientes").to_frame()

        # Jornada valida: uma sequencia de 1 seguida so de 0 (ex.: 11100)
        tabela["etapa_final"] = [self._etapa_final(j) for j in tabela.index]
        tabela["segue_a_ordem"] = [self._segue_a_ordem(j) for j in tabela.index]
        tabela["participacao"] = tabela["clientes"] / tabela["clientes"].sum()
        tabela.index.name = "jornada (" + " > ".join(self.ETAPAS) + ")"
        return tabela

    def etapa_final(self, presenca: pd.DataFrame) -> pd.Series:
        """Ultima etapa que cada cliente alcancou."""
        jornadas = presenca.astype(str).agg("".join, axis=1)
        return jornadas.map(self._etapa_final).rename("etapa_final")

    def grafico(self, contagem: pd.DataFrame) -> Figure:
        """Funil em barras horizontais, com clientes e conversoes de cada etapa."""
        figura, eixo = plt.subplots(figsize=(14, 6))

        etapas = contagem.index[::-1]
        usuarios = contagem["usuarios"][::-1]

        # Barras centralizadas para dar o formato de funil; o gargalo em laranja
        gargalo = self.gargalo(contagem)["etapa"]
        cores = ["darkorange" if etapa == gargalo else "steelblue" for etapa in etapas]
        deslocamento = (usuarios.max() - usuarios) / 2
        eixo.barh(etapas, usuarios, left=deslocamento, color=cores, edgecolor="black")

        # Texto a direita de cada barra (as barras de baixo sao estreitas demais)
        for etapa, linha in contagem.iterrows():
            texto = f"{linha['usuarios']:,.0f} ({linha['conversao_topo']:.0%} do topo)"
            if pd.notna(linha["conversao_etapa_anterior"]):
                texto += f"\n{linha['conversao_etapa_anterior']:.0%} da etapa anterior"
            if etapa == gargalo:
                texto += "  <- maior gargalo"
            fim_da_barra = (usuarios.max() + linha["usuarios"]) / 2
            eixo.text(
                fim_da_barra + usuarios.max() * 0.02, etapa, texto,
                ha="left", va="center", fontsize=10,
                fontweight="bold" if etapa == gargalo else "normal",
            )

        eixo.set_xlim(0, usuarios.max() * 1.4)
        eixo.set_title("Funil: usuarios unicos por etapa")
        eixo.set_xticks([])
        eixo.spines[["top", "right", "bottom"]].set_visible(False)

        figura.tight_layout()
        return figura

    def _etapa_final(self, jornada: str) -> str:
        """Nome da ultima etapa marcada com 1 na jornada."""
        posicoes = [i for i, marcado in enumerate(jornada) if marcado == "1"]
        return self.ETAPAS[posicoes[-1]] if posicoes else "nenhuma"

    @staticmethod
    def _segue_a_ordem(jornada: str) -> bool:
        """True quando nao ha etapa marcada depois de uma etapa pulada."""
        return "01" not in jornada
