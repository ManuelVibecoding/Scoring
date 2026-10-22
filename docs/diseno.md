# Diseño

Objetivo: que la app se vea como un producto hecho por un estudio de diseño, no como una
plantilla generada por IA. Sobria, editorial y centrada en el dato.

## Dirección visual

**Elegida: C · Suizo minimal** (2026-10-22). Grilla estricta, números grandes como
protagonistas, blanco y negro con un único rojo de señal. Archivo como única familia
tipográfica, con cifras tabulares. La escala del mapa va de gris claro a negro; el rojo
se reserva para alertas y para el punto seleccionado.

Se dejan A y B como referencia de lo que se descartó:

| | A · Cartografía editorial | B · Plano nocturno | **C · Suizo minimal (elegida)** |
|---|---|---|---|
| Referencia | Mapas del Financial Times, atlas impresos, swisstopo | Instrumentos, terminales de datos | Carteles suizos, Müller-Brockmann |
| Fondo | Papel cálido `#F3EFE6` | Casi negro `#0F1514` | Blanco `#FFFFFF` |
| Tinta | `#1D1C1A` | `#E7E3D8` | `#111111` |
| Acento único | Ladrillo `#A8432A` | Ámbar `#D9A441` | Rojo señal `#E2231A` |
| Títulos y veredicto | Newsreader (serif) | IBM Plex Sans | Archivo |
| Texto | IBM Plex Sans | IBM Plex Sans | Archivo |
| Números | IBM Plex Mono, cifras tabulares | IBM Plex Mono | Archivo, cifras tabulares |

## Principios (valen para cualquier dirección)

1. **El dato es el protagonista.** El puntaje y las cifras son grandes; la interfaz se
   retira. Nada compite con el mapa.
2. **Un solo color de acento**, usado solo para lo que importa (una debilidad, la selección).
   El resto es tinta y neutros.
3. **Escala de color del mapa perceptual y secuencial** (de claro a oscuro, sin arcoíris),
   legible para daltónicos.
4. **Líneas finas en vez de tarjetas.** Separar con filetes de 1 px y espacio en blanco,
   no con cajas con sombra.
5. **Tipografía con jerarquía clara:** etiquetas pequeñas en versalitas o mono, cifras
   tabulares para que los números se alineen.
6. **Mapa base propio:** estilo desaturado y coherente con la paleta (MapLibre con
   estilo personalizado), nunca el mapa OSM por defecto.
7. **Microcopia en español chileno, sobria:** "Muy bien conectada, barrio consolidado", no
   "¡Excelente ubicación! 🎉".

## Lo que está prohibido (señales de "hecho por IA")

- Degradados morado-azul, fondos con mallas o "glassmorphism".
- Emojis como íconos, destellos ✨, signos de exclamación en la interfaz.
- Todo dentro de tarjetas redondeadas con sombra; cuadrículas de tarjetas iguales.
- Inter + gris pizarra por defecto, botones "pill" con degradado.
- Badges y chips por todas partes, íconos del mismo tamaño en cada línea.
- Hero centrado con título gigante y subtítulo gris.
- Animaciones que rebotan; el movimiento debe ser breve y funcional.

## Herramientas

- Skills de diseño sugeridas para instalar: `frontend-design` (Anthropic) y
  `Website Design` (UXKIN, basada en sistemas de diseño de sitios reales).
- El sistema de diseño se implementa como tokens CSS (colores, tipografía, espaciado) en
  `frontend/src/styles/tokens.css`; ningún componente usa colores sueltos.
- La ficha exportable usa exactamente los mismos tokens que la app.
