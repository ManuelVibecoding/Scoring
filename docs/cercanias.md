# Cercanías por hexágono (Fase 2)

Generado con `uv run score cercanias` (~80 segundos). Resultado en
`data/processed/hexagonos.parquet` y el catálogo de lugares en
`data/processed/puntos_interes.parquet`.

## Cómo se calcula

1. **Grilla:** hexágonos H3 de resolución 9 (lado ~174 m, ~0,1 km²) donde el Censo 2024
   registra manzanas. Son **9.666 hexágonos** en las 52 comunas. Cada uno guarda su
   población, hogares, viviendas y comuna.
2. **Redes de calles** desde OpenStreetMap:
   - **A pie:** 1,6 millones de nodos. Excluye autopistas y vías exclusivas de buses.
   - **En auto:** 1,1 millones de nodos. Respeta sentidos de tránsito, con velocidades
     medias supuestas por tipo de vía (ver abajo).
3. **Distancias por la red, no en línea recta:** por cada categoría se corre un solo
   Dijkstra desde todos sus lugares a la vez. Así se obtiene, para cada esquina de la RM,
   cuánto falta al más cercano y cuál es.
4. **Conteos del barrio:** lugares a menos de 800 m en línea recta.
5. **Oferta de buses:** recorridos distintos y buses por hora (punta mañana, 7–9 h, día
   hábil) en el paradero más servido a menos de 400 m.

## Columnas

| Columna | Qué es |
|---|---|
| `h3`, `lat`, `lon`, `cut` | Hexágono, su centro y su comuna |
| `personas`, `hogares`, `viviendas`, `manzanas` | Censo 2024 dentro del hexágono |
| `min_<categoría>` | Minutos al más cercano (vacío si es más de 120 min) |
| `cerca_<categoría>` | Nombre de ese lugar |
| `n800_<categoría>` | Cantidad a menos de 800 m |
| `recorridos_400m`, `buses_hora_max_400m` | Oferta de buses alrededor |

**A pie** (4,8 km/h): metro, tren, paradero, supermercado, farmacia, banco, cajero,
colegio, jardín, CESFAM, feria, mall, gimnasio, plaza (≥ 1.000 m²), parque (≥ 2 ha).

**En auto:** urgencia, hospital o clínica, acceso a autopista (desde la casa hacia el
lugar); bomberos y policía (desde el cuartel hacia la casa, que es lo que importa en una
emergencia).

**Conteos a 800 m:** colegios, jardines, supermercados, farmacias, paraderos y comercio
de barrio (restaurantes, cafés, ferias, gimnasios).

## Medianas para la población de la RM

| Medida | Minutos |
|---|---:|
| Paradero de bus (a pie) | 2,7 |
| Plaza (a pie) | 3,5 |
| Jardín infantil (a pie) | 4,8 |
| Colegio (a pie) | 5,2 |
| Farmacia (a pie) | 9,1 |
| Supermercado (a pie) | 10,3 |
| Parque (a pie) | 11,0 |
| CESFAM (a pie) | 13,1 |
| Metro (a pie) | 20,3 |
| Urgencia (auto) | 3,4 |
| Bomberos (auto) | 3,7 |
| Acceso a autopista (auto) | 4,4 |

## Validación con lugares conocidos

| Lugar | Metro más cercano | Otros |
|---|---|---|
| Plaza Ñuñoa | Chile España, 2,9 min | 15 recorridos de bus a 400 m |
| Tobalaba | Tobalaba, 3,8 min | Acceso a Kennedy en 1,6 min |
| Plaza de Armas | Plaza de Armas, 1,7 min | 34 recorridos de bus a 400 m |
| Plaza de Puente Alto | Plaza de Puente Alto, 4,7 min | |
| La Dehesa | Los Dominicos, 91 min a pie | Acceso a Costanera Norte en 1,7 min |
| La Pintana centro | Santa Rosa, 59 min a pie | SAPU San Rafael en 2,9 min |
| Melipilla centro | Sin Metro accesible | Acceso a Ruta 78 en 4,6 min |

## Supuestos y limitaciones

- **Velocidades en auto:** son promedios supuestos en hora punta (autopista 70 km/h,
  avenida principal 35, calle residencial 22…), no mediciones de congestión. Los tiempos
  en auto sirven para comparar lugares, no como tiempo real de viaje.
- **Cobertura de OpenStreetMap:** supermercados, farmacias, bancos, bomberos y policía
  vienen de OSM y su cobertura es buena en el Gran Santiago, pero menor en comunas rurales.
  "Supermercado" incluye minimercados etiquetados así en OSM.
- **Hexágonos solo donde hay manzanas:** un punto fuera de la grilla (cerro, parque
  industrial) se resuelve con el hexágono más cercano.
- **Buses rurales:** no están en el GTFS de la DTPM; en comunas rurales "paradero" queda vacío.
- **Calidad de colegios:** aún no se pondera por SIMCE (pendiente).
- **Población por hexágono:** usa la cartografía por manzana, que excluye los datos que el
  INE reserva (suma 7,06 millones en vez de 7,40). Sirve como peso relativo, no como conteo
  exacto.
