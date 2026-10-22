"""Veredicto en palabras: una frase sobria que resume el puntaje de un lugar."""

TITULOS: dict[str, str] = {
    "A": "Excelente ubicación",
    "B": "Muy buena ubicación",
    "C": "Ubicación correcta",
    "D": "Ubicación con limitaciones",
    "E": "Ubicación débil",
}


def _lista(nombres: list[str]) -> str:
    minusculas = [n[0].lower() + n[1:] for n in nombres]
    if len(minusculas) <= 1:
        return "".join(minusculas)
    return ", ".join(minusculas[:-1]) + " y " + minusculas[-1]


def redactar(letra: str | None, fortalezas: list[str], debilidades: list[str]) -> str:
    """'Muy buena ubicación. Destaca en transporte público y servicios cercanos; lo más
    débil es la seguridad.'"""
    if letra is None:
        return "Sin datos suficientes para evaluar este punto."
    partes = [TITULOS[letra]]
    if fortalezas:
        partes.append(f"Destaca en {_lista(fortalezas)}")
    if debilidades:
        conector = "lo más débil es" if len(debilidades) == 1 else "lo más débil son"
        partes.append(f"{conector} {_lista(debilidades)}")
    if len(partes) == 1:
        return f"{partes[0]}. Sin fortalezas ni debilidades marcadas."
    if len(partes) == 3:
        return f"{partes[0]}. {partes[1]}; {partes[2]}."
    return f"{partes[0]}. {partes[1][0].upper()}{partes[1][1:]}."
