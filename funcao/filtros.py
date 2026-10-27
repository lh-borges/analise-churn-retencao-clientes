from collections.abc import Callable

import pandas as pd

from .geracao_colunas import GeracaoColunas


FiltroClientes = Callable[[pd.DataFrame], pd.DataFrame]


class Filtros:
    """Reune os filtros da base de clientes e aplica os escolhidos pelo nome."""

    def __init__(
        self,
        idade_minima: int = 0,
        idade_maxima: int = 100,
        valor_mensal_maximo: float = 100,
    ) -> None:
        """Guarda os limites usados pelos filtros e registra os disponiveis."""
        self.idade_minima = idade_minima
        self.idade_maxima = idade_maxima
        self.valor_mensal_maximo = valor_mensal_maximo

        # Registrei os filtros pelo nome para que sejam escolhidos de fora
        self._filtros: dict[str, FiltroClientes] = {
            "clientes_ativos": self._filtrar_clientes_ativos,
            "clientes_cancelados": self._filtrar_clientes_cancelados,
            "idade_valida": self._filtrar_idade_valida,
            "valor_mensal_valido": self._filtrar_valor_mensal_valido,
            "regiao_informada": self._filtrar_regiao_informada,
            "diferencas_data_validas": self._filtrar_diferencas_data_validas,
        }

    @property
    def disponiveis(self) -> list[str]:
        """Retorna os nomes dos filtros que podem ser aplicados."""
        return list(self._filtros)

    def aplicar(
        self,
        df_clientes: pd.DataFrame,
        nomes_filtros: list[str],
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Aplica os filtros em sequencia e resume quantos registros cada um removeu."""
        filtros_invalidos = set(nomes_filtros) - set(self._filtros)
        if filtros_invalidos:
            raise ValueError(
                f"Filtros inexistentes: {sorted(filtros_invalidos)}. "
                f"Disponiveis: {self.disponiveis}"
            )

        df_filtrado = df_clientes
        resumo = []

        # Registrei a quantidade antes e depois de cada filtro
        for nome in nomes_filtros:
            quantidade_antes = len(df_filtrado)
            df_filtrado = self._filtros[nome](df_filtrado)
            resumo.append(
                {
                    "filtro": nome,
                    "removidos": quantidade_antes - len(df_filtrado),
                    "restantes": len(df_filtrado),
                }
            )

        return df_filtrado.copy(), pd.DataFrame(resumo)

    def _filtrar_clientes_ativos(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Mantem apenas os clientes ativos (churn = 0)."""
        return df_clientes[df_clientes["churn"] == 0]

    def _filtrar_clientes_cancelados(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Mantem apenas os clientes cancelados (churn = 1)."""
        return df_clientes[df_clientes["churn"] == 1]

    def _filtrar_idade_valida(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Mantem as idades dentro da faixa definida, incluindo os limites."""
        return df_clientes[
            df_clientes["idade"].between(self.idade_minima, self.idade_maxima)
        ]

    def _filtrar_valor_mensal_valido(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Remove os valores mensais acima do limite, que parecem erro de escala."""
        return df_clientes[df_clientes["valor_mensal"] <= self.valor_mensal_maximo]

    def _filtrar_regiao_informada(self, df_clientes: pd.DataFrame) -> pd.DataFrame:
        """Remove a regiao "?", que nao identifica nenhuma regiao."""
        return df_clientes[df_clientes["regiao"] != "?"]

    def _filtrar_diferencas_data_validas(
        self,
        df_clientes: pd.DataFrame,
    ) -> pd.DataFrame:
        """Remove os registros com diferenca de datas negativa (datas fora de ordem)."""
        # Usei "nao e negativo" em vez de ">= 0" para manter os nulos, que sao
        # esperados (ex.: cliente ativo nao tem data de cancelamento)
        diferencas = df_clientes[GeracaoColunas.COLUNAS_DIFERENCA_DATA]
        return df_clientes[~diferencas.lt(0).any(axis=1)]
