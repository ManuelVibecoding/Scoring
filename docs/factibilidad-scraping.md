# Prueba de factibilidad del scraping

Fecha: 2026-10-22. Peticiones HTTP simples (Python, sin navegador), ritmo de 1 petición
cada 2 segundos, búsqueda de prueba: arriendo de departamentos en Ñuñoa.

## Resultado

| | Toc Toc | Portal Inmobiliario |
|---|---|---|
| Responde a HTTP simple | Sí (200, ~4,5 s) | Sí (200, ~1 s) |
| Captcha o bloqueo | No | No |
| Formato de los datos | JSON embebido (`__NEXT_DATA__`) | JSON embebido en la página (tarjetas `polycard`) |
| Avisos por página | **260** | ~48 |
| Total en Ñuñoa (arriendo depto.) | 835 | 1.425 |
| **Coordenadas por aviso** | **Sí** (`latitud`, `longitud`) | **No** en la búsqueda; solo en la ficha de cada aviso |
| Precio | UF y CLP (`precios`) | CLP (`prc`) |
| m², dormitorios, baños | Sí | Por confirmar en la tarjeta |
| Fecha / antigüedad | `horasPublicado` | Por confirmar |
| robots.txt | Permite las páginas de comuna; prohíbe `/search`, `/resultados/`, `/Propiedades/VistaMapa` | Permite las páginas de comuna; prohíbe varios filtros (`_TOTAL*AREA_`, `_FilterId_`, etc.) |

Ejemplo de aviso de Toc Toc (campos útiles): título, comuna, tipo de propiedad y operación,
precio en UF y CLP, superficie, dormitorios, baños, horas publicado, latitud, longitud,
URL de la ficha, identificador.

## Conclusiones

1. **Toc Toc es la fuente principal.** Trae coordenadas exactas y 260 avisos por página:
   una comuna completa como Ñuñoa son ~4 páginas, unos **20 segundos**. Cumple de sobra la
   meta de menos de 1 minuto por clic.
2. **Portal Inmobiliario es complementario.** Tiene más avisos, pero sin coordenadas en la
   búsqueda. Sirve para precio mediano de la comuna (sin ubicar cada aviso) o, más adelante,
   para abrir solo las fichas cercanas al punto.
3. **Estrategia concreta para el clic:** se scrapea la comuna del punto (y las vecinas si
   el punto está cerca del límite), se guardan todos los avisos con fecha en DuckDB y se
   filtran los que están a menos de ~800 m. La comuna queda en caché 7 días.
4. Se respetan las rutas prohibidas por `robots.txt` y un ritmo de una petición cada
   1–2 segundos.

## Riesgos

- Los portales pueden cambiar su estructura: cada scraper es un adaptador aislado con
  pruebas sobre páginas guardadas, para detectar el cambio y arreglarlo en un solo lugar.
- Puede aparecer un bloqueo si se aumenta el ritmo: no se evade; se usa el otro portal o
  el precio de referencia.
