# Catálogo de fuentes de datos

Actualizado: 2026-10-22. Las fuentes **descargadas** están registradas en
`backend/src/score/pipeline/fuentes.py` y se bajan con `uv run score datos descargar`
(las pesadas con `--incluir-pesadas`). Cada carpeta de `data/raw/` tiene un
`_manifiesto.json` con URL, fecha, tamaño y sha256 de cada archivo.

**Estado:**
- **Descargada:** en `data/raw/`, con manifiesto.
- **Confirmada:** existe y se sabe cómo obtenerla, pero aún no se descarga.
- **Bloqueada:** el sitio rechaza el acceso o no publica los datos.
- **Por verificar:** fuente conocida, aún no revisada.

## Descargadas

| ID | Fuente | Qué aporta | Granularidad | Tamaño | Notas |
|---|---|---|---|---|---|
| `censo2024_cartografia_rm` | INE, Censo 2024 | Polígonos de manzanas, zonas, comunas, límite urbano; las manzanas traen 190 variables censales | Manzana | 64 MB | GeoParquet, bucket público del INE. 66.873 manzanas en la RM |
| `censo2024_manzana_entidad` | INE, Censo 2024 | Base manzana–entidad completa, con filas "contenedor comunal" | Manzana | 26 MB | Suma exacta de la RM: 7.400.741 personas |
| `minsal_establecimientos` | IDE-Minsal | 1.070 establecimientos de salud en la RM, con tipo, urgencia y nivel | Punto | 1 MB | Vigentes al 12-06-2026 |
| `dtpm_gtfs` | DTPM | Buses RED, Metro, EFE; 12.223 paraderos y 126 estaciones de Metro en la RM | Punto / línea | 13 MB | Vigente desde el 03-10-2026. No incluye buses rurales |
| `osm_chile` | Geofabrik / OSM | Calles, comercio, parques, autopistas | Punto / línea | 350 MB | Para la Fase 2 (cercanías) |
| `mineduc_directorio` | Mineduc | 3.237 establecimientos en funcionamiento en la RM, con dependencia, matrícula y coordenadas | Punto | 1 MB | Directorio 2025. Reemplaza las capas de 2021 |
| `cead_delitos` | CEAD (extracción comunitaria) | Casos policiales mensuales por comuna y 30 tipos de delito, 2010 – dic. 2025 | Comuna | 2 MB | El sitio oficial del CEAD respondía 502 al revisarlo; se usa el extracto de [bastianolea/delincuencia_chile](https://github.com/bastianolea/delincuencia_chile) |
| `mma_ruido` | Ministerio del Medio Ambiente | Mapa de ruido 2023, 35 comunas | Superficie | 220 MB | Para la Fase 2 |
| `casen_pobreza_comunal` | MDSF (BIDAT) | Pobreza por ingresos, multidimensional e inseguridad alimentaria 2024 | Comuna | <1 MB | Estimaciones SAE con Casen 2024 y Censo 2024 (publicadas en abril de 2026). Más nuevas que las de 2022 previstas |
| `icvu` | CChC + IEUT UC | Nivel ICVU 2025 (Alto, Medio alto, Medio bajo, Bajo) | Comuna (42 de la RM) | 2 MB | El informe publica niveles, no puntajes numéricos |

## Precios

| Fuente | Estado | Notas |
|---|---|---|
| Toc Toc | **Confirmada** | Scraping bajo demanda; ver [factibilidad-scraping.md](factibilidad-scraping.md) |
| Portal Inmobiliario | **Confirmada** | Complemento, sin coordenadas en la búsqueda |
| Informes públicos (CChC, GlobalProperty, Banco Central) | Por verificar | Respaldo comunal |
| SII, avalúo fiscal | Por verificar | |

## Bloqueadas o postergadas

| Fuente | Estado | Qué pasó | Alternativa |
|---|---|---|---|
| SINIM (ingresos municipales, áreas verdes por habitante) | **Bloqueada** | sinim.gov.cl y datos.sinim.gov.cl responden 403, también desde el navegador | Bajarlo a mano desde otra red, o reemplazar áreas verdes por OSM + vegetación satelital |
| SIMCE y categoría de desempeño (Agencia de Calidad) | **Postergada** | El portal público solo muestra categorías hasta 2019 y la API no lista archivos | Revisar en la Fase 2; por ahora los colegios se cuentan sin ponderar por calidad |
| Farmacias (Minsal) | **Postergada** | No hay API pública documentada | OSM (`amenity=pharmacy`) |
| CEAD oficial | **Caída** | 502 al revisarlo | Extracto comunitario (ver arriba) |

## Por verificar (Fase 2)

ENUSC, Informe Nacional de Homicidios, AIM (grupos socioeconómicos), catastro de
campamentos, Sentinel-2 (vegetación), Landsat (islas de calor), SINCA (aire),
SERNAGEOMIN / PRMS (riesgos), proyectos futuros de Metro y autopistas.
