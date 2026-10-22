# Catálogo de fuentes de datos

Primera versión: 2026-10-22. Se actualiza a medida que cada fuente se descarga y revisa.

**Estado:**
- **Confirmada:** se verificó que existe, con formato y fecha conocidos.
- **Parcial:** existe, pero falta confirmar la descarga, la vigencia o la granularidad.
- **Por verificar:** fuente conocida, aún no revisada en esta fase.

## Base cartográfica

| Fuente | Qué aporta | Granularidad | Formato | Estado | Notas |
|---|---|---|---|---|---|
| Censo 2024 (INE): cartografía y base manzana–entidad | Límites de manzanas, zonas y comunas; 189 variables de personas, hogares y viviendas | Manzana | GeoParquet | **Confirmada** | Publicada en diciembre de 2025 ([INE](https://www.ine.gob.cl/sala-de-prensa/prensa/general/noticia/2025/12/04/ine-publica-base-de-datos-del-censo-de-poblaci%C3%B3n-y-vivienda-2024), [ejemplo de uso](https://github.com/bastianolea/censo_2024_mapas)) |
| OpenStreetMap (extracto Chile, Geofabrik) | Calles, red peatonal, puntos de interés, parques, autopistas y accesos | Punto / línea | PBF | Por verificar | Base de casi todas las cercanías |
| Límites comunales (BCN / IDE Chile) | Respaldo de los límites de las 52 comunas | Comuna | Shapefile | Por verificar | El Censo 2024 probablemente basta |

## Seguridad

| Fuente | Qué aporta | Granularidad | Estado | Notas |
|---|---|---|---|---|
| CEAD (Subsecretaría de Prevención del Delito) | Casos policiales por delito, tasas por 100 mil hab. | Comuna, anual / trimestral | **Parcial** | Nivel comunal confirmado; los datos de 2024 se publicaron en abril de 2025. Falta confirmar la vía de descarga y si 2025 ya está ([ChileAtiende](https://www.chileatiende.gob.cl/fichas/114579-centro-de-estudios-y-analisis-del-delito-cead)) |
| ENUSC (INE) | Victimización y percepción de inseguridad | Comuna (muestra) | Por verificar | |
| Informe Nacional de Homicidios | Homicidios por comuna | Comuna | Por verificar | |
| Comisarías, PDI | Ubicación | Punto | Por verificar | OSM como primera opción |

## Socioeconómico y calidad de vida

| Fuente | Qué aporta | Granularidad | Estado | Notas |
|---|---|---|---|---|
| Censo 2024 (INE) | Escolaridad, hacinamiento, edad, densidad, materialidad | Manzana | **Confirmada** | Permite calcular un índice tipo ISMT actualizado a 2024 |
| ISMT (Observatorio de Ciudades UC) | Índice socio-material | Manzana | **Parcial** | Basado en Censo 2017; existe paquete R `ismtchile` con la metodología ([CRAN](https://rdrr.io/cran/ismtchile/)). Propuesta: recalcularlo con el Censo 2024 |
| CASEN 2022, estimaciones SAE | Pobreza por ingresos y multidimensional | Comuna | **Confirmada** | [Resultados SAE 2022 (MDSF)](https://bid-ckan.ministeriodesarrollosocial.gob.cl:443/dataset/20ec8eff-15c2-4645-8687-90221be9e3c5/resource/5a96048a-afaf-4082-8016-af46689f4e74/download/resultados_estimaciones_sae_2022.pdf) |
| ICVU 2025 (CChC + IEUT UC) | Índice de calidad de vida urbana, 6 dimensiones | Comuna (99 comunas del país; 42 de la RM) | **Confirmada** | [Informe ICVU 2025](https://estudiosurbanos.uc.cl/wp-content/uploads/2026/07/DOCUMENTO-ICVU-2025-1.pdf). No cubre las 52 comunas: faltan las rurales |
| SINIM (SUBDERE) | Ingresos propios, presupuesto por habitante, áreas verdes | Comuna, anual | **Parcial** | Exporta a Excel desde datos.sinim.gov.cl; falta confirmar el último año disponible |
| AIM, grupos socioeconómicos | Distribución ABC1 a E | Comuna | Por verificar | |
| Catastro de campamentos (MINVU / TECHO) | Ubicación de campamentos | Punto / polígono | Por verificar | |

## Precios

| Fuente | Qué aporta | Estado | Notas |
|---|---|---|---|
| Toc Toc | Avisos con precio UF/CLP, m², dormitorios, baños, coordenadas | **Confirmada** | Fuente principal. Ver [factibilidad-scraping.md](factibilidad-scraping.md) |
| Portal Inmobiliario | Avisos con precio, sin coordenadas en la búsqueda | **Confirmada** | Complemento para medianas comunales |
| Informes públicos (CChC, GlobalProperty, índice Banco Central) | Precio de referencia comunal | Por verificar | Respaldo cuando no hay scraping |
| SII, avalúo fiscal | Valor de suelo por predio | Por verificar | Falta confirmar si se puede descargar masivamente |

## Servicios

| Fuente | Qué aporta | Granularidad | Estado | Notas |
|---|---|---|---|---|
| IDE-Minsal | 5.295 establecimientos de salud vigentes (CESFAM, SAPU, SAR, hospitales, clínicas), con dependencia y tipo de atención | Punto | **Confirmada** | Shapefile WGS84, versión del 12-06-2026 ([geoportal](https://www.minsal.cl/ide-minsal-geoportal-descarga-de-datos/)) |
| Mineduc, capas de establecimientos | Colegios y jardines (incluye JUNJI e Integra) | Punto | **Parcial** | Capas ArcGIS con corte a 2021; hay que buscar una versión más reciente o actualizar con el directorio oficial |
| Agencia de Calidad de la Educación | SIMCE y categoría de desempeño (alto, medio, medio-bajo, insuficiente) | Colegio (RBD) | **Parcial** | Tiene bases descargables; falta ubicar el enlace vigente |
| DEMRE | Resultados PAES por colegio | Colegio | Por verificar | |
| Farmacias (Minsal) | Ubicación y farmacias de turno | Punto | **Parcial** | No hay API pública documentada; el buscador oficial está en seremienlinea.minsal.cl. Alternativa: OSM |
| OSM | Supermercados, malls, bancos, cajeros, bomberos, ferias, comercio | Punto | Por verificar | Validar cobertura de supermercados por cadena |

## Transporte y conectividad

| Fuente | Qué aporta | Estado | Notas |
|---|---|---|---|
| GTFS DTPM | Buses RED, Metro, EFE y bus al aeropuerto (425 rutas), con horarios | **Confirmada** | Vigente del 25-04-2026 al 31-12-2026 ([MobilityData](https://mobilitydatabase.org/feeds/gtfs/mdb-3357)); confirmar la URL en dtpm.cl |
| OSM | Autopistas, accesos, avenidas troncales, ciclovías | Por verificar | |
| Proyectos futuros (Metro L7, L8, L9; trenes; autopistas) | Trazados y fechas | Por verificar | |

## Medio ambiente y riesgos

| Fuente | Qué aporta | Estado | Notas |
|---|---|---|---|
| Mapa de ruido del Gran Santiago (MMA) | Niveles de ruido día y noche | **Parcial** | Actualización con datos 2023, presentada en abril de 2024; cubre 35 comunas urbanas ([minuta MMA](https://ruido.mma.gob.cl/wp-content/uploads/2024/04/Minuta_Mapa_de_Ruido_Gran_Santiago_DRLO_MMA_2024.pdf)). Falta encontrar los archivos geográficos |
| Sentinel-2 | Vegetación (NDVI) | Por verificar | Imágenes gratuitas (Copernicus) |
| Landsat | Temperatura de superficie (islas de calor) | Por verificar | |
| SINCA | Calidad del aire | Por verificar | |
| SERNAGEOMIN / PRMS | Inundación, remoción en masa, Falla San Ramón | Por verificar | |

## Hallazgos importantes de esta primera revisión

1. **El Censo 2024 por manzana ya existe** (diciembre de 2025). Es la base más fina y actual
   para lo socioeconómico; permite calcular un índice tipo ISMT con datos de 2024 en vez de 2017.
2. **Las fuentes comunales no cubren las 52 comunas por igual:** el ICVU incluye solo 42
   de la RM y el mapa de ruido 35. Las comunas rurales tendrán que marcarse como "sin dato"
   en esas dimensiones, sin penalizarlas.
3. **Toc Toc entrega coordenadas exactas**, lo que permite precios comparables por cercanía
   real y no solo por comuna.
4. **Los establecimientos educacionales con coordenadas tienen corte a 2021**: hay que
   buscar una versión más reciente.

## Próximos pasos de la Fase 1

- Confirmar las fuentes en estado **Parcial**: CEAD, SINIM, Mineduc, Agencia de Calidad, mapa de ruido.
- Revisar las fuentes **Por verificar**.
- Descargar las fuentes confirmadas a `data/raw/` con un trabajo del pipeline por fuente.
- Armar la ficha de las 52 comunas con los indicadores comunales.
