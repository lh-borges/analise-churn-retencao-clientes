from pathlib import Path

from funcao.estatistica_descritiva import executar_analise_descritiva
from funcao.geracao_colunas import preparar_base_clientes


def executar() -> None:
    """Prepara a base e inicia a analise descritiva."""
    # Defini o caminho do arquivo que vou analisar
    caminho_csv = Path(__file__).resolve().parent / "data" / "clientes_base.csv"

    # Preparei a base e passei o resultado para a estatistica descritiva
    df_clientes_base = preparar_base_clientes(caminho_csv)
    executar_analise_descritiva(df_clientes_base)


if __name__ == "__main__":
    executar()
