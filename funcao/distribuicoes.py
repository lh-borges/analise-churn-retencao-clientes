from math import exp, lgamma, log


class Distribuicoes:
    """Calcula p-valores das distribuicoes t e qui-quadrado sem usar o scipy.

    As funcoes gama e beta incompletas seguem os algoritmos classicos do
    livro Numerical Recipes (serie e fracao continuada de Lentz).
    """

    _MAXIMO_ITERACOES = 500
    _PRECISAO = 1e-12
    _MENOR_VALOR = 1e-300

    @classmethod
    def p_valor_t(cls, estatistica_t: float, graus_liberdade: float) -> float:
        """P-valor bilateral de uma estatistica t de Student."""
        x = graus_liberdade / (graus_liberdade + estatistica_t**2)
        return cls._beta_incompleta(graus_liberdade / 2, 0.5, x)

    @classmethod
    def p_valor_qui_quadrado(cls, estatistica: float, graus_liberdade: int) -> float:
        """P-valor (cauda superior) de uma estatistica qui-quadrado."""
        return cls._gama_incompleta_superior(graus_liberdade / 2, estatistica / 2)

    @classmethod
    def _beta_incompleta(cls, a: float, b: float, x: float) -> float:
        """Funcao beta incompleta regularizada I_x(a, b)."""
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0

        fator = exp(
            lgamma(a + b) - lgamma(a) - lgamma(b) + a * log(x) + b * log(1 - x)
        )

        # A fracao continuada converge rapido de um lado; do outro uso a simetria
        if x < (a + 1) / (a + b + 2):
            return fator * cls._fracao_continuada_beta(a, b, x) / a
        return 1 - fator * cls._fracao_continuada_beta(b, a, 1 - x) / b

    @classmethod
    def _fracao_continuada_beta(cls, a: float, b: float, x: float) -> float:
        """Fracao continuada usada na beta incompleta (metodo de Lentz)."""
        soma_ab, a_mais_1, a_menos_1 = a + b, a + 1, a - 1
        c = 1.0
        d = cls._evitar_zero(1 - soma_ab * x / a_mais_1)
        d = 1 / d
        resultado = d

        for m in range(1, cls._MAXIMO_ITERACOES + 1):
            dois_m = 2 * m

            # Termo par da fracao
            termo = m * (b - m) * x / ((a_menos_1 + dois_m) * (a + dois_m))
            d = 1 / cls._evitar_zero(1 + termo * d)
            c = cls._evitar_zero(1 + termo / c)
            resultado *= d * c

            # Termo impar da fracao
            termo = -(a + m) * (soma_ab + m) * x / ((a + dois_m) * (a_mais_1 + dois_m))
            d = 1 / cls._evitar_zero(1 + termo * d)
            c = cls._evitar_zero(1 + termo / c)
            variacao = d * c
            resultado *= variacao

            if abs(variacao - 1) < cls._PRECISAO:
                break

        return resultado

    @classmethod
    def _gama_incompleta_superior(cls, a: float, x: float) -> float:
        """Funcao gama incompleta regularizada superior Q(a, x)."""
        if x <= 0:
            return 1.0

        fator = exp(-x + a * log(x) - lgamma(a))

        # Para x pequeno a serie converge melhor; para x grande, a fracao continuada
        if x < a + 1:
            termo = soma = 1 / a
            denominador = a
            for _ in range(cls._MAXIMO_ITERACOES):
                denominador += 1
                termo *= x / denominador
                soma += termo
                if abs(termo) < abs(soma) * cls._PRECISAO:
                    break
            return 1 - soma * fator

        b = x + 1 - a
        c = 1 / cls._MENOR_VALOR
        d = 1 / b
        resultado = d
        for i in range(1, cls._MAXIMO_ITERACOES + 1):
            termo = -i * (i - a)
            b += 2
            d = 1 / cls._evitar_zero(termo * d + b)
            c = cls._evitar_zero(b + termo / c)
            variacao = d * c
            resultado *= variacao
            if abs(variacao - 1) < cls._PRECISAO:
                break

        return fator * resultado

    @classmethod
    def _evitar_zero(cls, valor: float) -> float:
        """Troca valores muito proximos de zero para nao dividir por zero."""
        return cls._MENOR_VALOR if abs(valor) < cls._MENOR_VALOR else valor
