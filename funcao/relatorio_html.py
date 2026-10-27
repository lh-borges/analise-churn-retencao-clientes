import base64
import html
from datetime import datetime
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


class RelatorioHtml:
    """Monta um relatorio HTML simples, sem framework, com tabelas e graficos."""

    ESTILO = """
        :root {
            --fundo: #f6f7f9;
            --cartao: #ffffff;
            --texto: #1f2933;
            --texto-suave: #5f6b7a;
            --borda: #dde2e8;
            --destaque: #2f6db5;
            --linha-par: #f3f6fa;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --fundo: #14181d;
                --cartao: #1d232a;
                --texto: #e6e9ed;
                --texto-suave: #a0aab5;
                --borda: #313a44;
                --destaque: #6fa8ec;
                --linha-par: #232a32;
            }
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            background: var(--fundo);
            color: var(--texto);
            font-family: "Segoe UI", Roboto, Arial, sans-serif;
            line-height: 1.5;
        }
        main { max-width: 1100px; margin: 0 auto; padding: 32px 16px 64px; }
        header { margin-bottom: 24px; }
        h1 { margin: 0 0 4px; font-size: 28px; }
        h2 {
            margin: 40px 0 12px;
            padding-bottom: 6px;
            border-bottom: 2px solid var(--destaque);
            font-size: 22px;
        }
        h3 { margin: 24px 0 8px; font-size: 17px; }
        p, li { color: var(--texto-suave); }
        .bloco ul { margin: 0; padding-left: 20px; }
        .bloco li { color: var(--texto); margin: 4px 0; }
        .gerado { margin: 0; font-size: 14px; color: var(--texto-suave); }
        nav {
            background: var(--cartao);
            border: 1px solid var(--borda);
            border-radius: 8px;
            padding: 12px 20px;
        }
        nav ol { margin: 0; padding-left: 20px; }
        nav a { color: var(--destaque); text-decoration: none; }
        nav a:hover { text-decoration: underline; }
        .bloco {
            background: var(--cartao);
            border: 1px solid var(--borda);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            overflow-x: auto;
        }
        table { border-collapse: collapse; font-size: 14px; white-space: nowrap; }
        th, td { padding: 6px 12px; border-bottom: 1px solid var(--borda); }
        th { text-align: left; background: var(--linha-par); }
        td { text-align: right; font-variant-numeric: tabular-nums; }
        tbody tr:nth-child(even) { background: var(--linha-par); }
        pre { margin: 0; font-size: 13px; }
        img { display: block; max-width: 100%; height: auto; margin: 0 auto; }
    """

    def __init__(self, titulo: str) -> None:
        """Guarda o titulo e comeca o relatorio sem nenhuma secao."""
        self.titulo = titulo
        self._secoes: list[str] = []
        self._indice: list[tuple[str, str]] = []

    def adicionar_secao(self, titulo: str, descricao: str = "") -> None:
        """Abre uma nova secao, que tambem aparece no indice do relatorio."""
        ancora = f"secao-{len(self._indice) + 1}"
        self._indice.append((ancora, titulo))
        self._secoes.append(f'<h2 id="{ancora}">{html.escape(titulo)}</h2>')
        if descricao:
            self.adicionar_texto(descricao)

    def adicionar_texto(self, texto: str) -> None:
        """Adiciona um paragrafo de texto."""
        self._secoes.append(f"<p>{html.escape(texto)}</p>")

    def adicionar_lista(self, itens: list[str]) -> None:
        """Adiciona uma lista de itens (ex.: principais conclusoes)."""
        itens_html = "\n".join(f"<li>{html.escape(item)}</li>" for item in itens)
        self._secoes.append(f'<div class="bloco"><ul>{itens_html}</ul></div>')

    def adicionar_tabela(
        self,
        titulo: str,
        tabela: pd.DataFrame | pd.Series,
        mostrar_indice: bool = True,
        casas_decimais: int = 2,
    ) -> None:
        """Adiciona uma tabela do pandas com um subtitulo."""
        if isinstance(tabela, pd.Series):
            tabela = tabela.to_frame()

        # Transformei o indice com nome em coluna para o cabecalho ficar
        # em uma linha so (ex.: "plano" no resumo por plano)
        if mostrar_indice and tabela.index.name:
            tabela = tabela.reset_index()
            mostrar_indice = False

        tabela_html = tabela.to_html(
            index=mostrar_indice,
            border=0,
            na_rep="-",
            float_format=lambda valor: self._formatar_numero(valor, casas_decimais),
        )
        self._adicionar_bloco(titulo, tabela_html)

    def adicionar_texto_fixo(self, titulo: str, texto: str) -> None:
        """Adiciona um texto que mantem o espacamento original (ex.: df.info())."""
        self._adicionar_bloco(titulo, f"<pre>{html.escape(texto)}</pre>")

    def adicionar_figura(self, titulo: str, figura: Figure) -> None:
        """Adiciona um grafico do matplotlib como imagem dentro do HTML."""
        imagem = self._figura_para_base64(figura)
        self._adicionar_bloco(
            titulo,
            f'<img src="data:image/png;base64,{imagem}" alt="{html.escape(titulo)}">',
        )

    def salvar(self, caminho: str | Path) -> Path:
        """Grava o relatorio em um arquivo HTML e devolve o caminho."""
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(self._montar_html(), encoding="utf-8")

        return caminho

    def _adicionar_bloco(self, titulo: str, conteudo: str) -> None:
        """Coloca o conteudo dentro de um cartao com subtitulo."""
        self._secoes.append(
            f"<h3>{html.escape(titulo)}</h3>\n<div class=\"bloco\">{conteudo}</div>"
        )

    @staticmethod
    def _formatar_numero(valor: float, casas_decimais: int) -> str:
        """Formata numeros inteiros sem casas e os muito pequenos em notacao cientifica."""
        if float(valor).is_integer():
            return f"{valor:,.0f}"
        # Sem isso, p-valores muito pequenos apareceriam como 0.00
        if abs(valor) < 0.001:
            return f"{valor:.2e}"
        return f"{valor:,.{casas_decimais}f}"

    @staticmethod
    def _figura_para_base64(figura: Figure) -> str:
        """Converte a figura em PNG e devolve o texto em base64."""
        # Salvei a imagem na memoria em vez de criar um arquivo separado
        buffer = BytesIO()
        figura.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
        plt.close(figura)

        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def _montar_html(self) -> str:
        """Junta o cabecalho, o indice e as secoes em um documento HTML."""
        itens_indice = "\n".join(
            f'<li><a href="#{ancora}">{html.escape(titulo)}</a></li>'
            for ancora, titulo in self._indice
        )
        gerado_em = datetime.now().strftime("%d/%m/%Y %H:%M")
        conteudo = "\n".join(self._secoes)

        return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(self.titulo)}</title>
<style>{self.ESTILO}</style>
</head>
<body>
<main>
<header>
<h1>{html.escape(self.titulo)}</h1>
<p class="gerado">Gerado em {gerado_em}</p>
</header>
<nav>
<ol>
{itens_indice}
</ol>
</nav>
{conteudo}
</main>
</body>
</html>
"""
