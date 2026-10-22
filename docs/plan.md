# Plan del proyecto

Plan aprobado el 2026-10-22. Las decisiones que lo ajustan están en [decisiones.md](decisiones.md).

## 1. Concepto

Al tocar un punto en el mapa, la app entrega:

1. **Puntaje 0–100 y letra (A–E):** el veredicto.
2. **Desglose en 8 dimensiones** que explican el puntaje.
3. **Contexto:** percentil del punto dentro de su comuna y de la RM.
4. **Precio aparte:** arriendos y ventas comparables de la zona y relación calidad/precio.

Dos niveles de información:

- **Macro (comuna):** seguridad, socioeconómico, gestión municipal, precios de referencia.
- **Micro (punto):** cercanía a servicios, transporte, carreteras, áreas verdes, ruido y riesgos.
  Se precalcula sobre una grilla de hexágonos H3 (resolución 9–10, unos 100–175 m de lado).

## 2. Dimensiones del puntaje

| # | Dimensión | Peso inicial | Nivel |
|---|---|---|---|
| 1 | Seguridad | 20% | Comuna (con ajuste por barrio si hay datos) |
| 2 | Socioeconómico y calidad de vida | 15% | Manzana y comuna |
| 3 | Servicios cercanos | 20% | Punto |
| 4 | Transporte público | 15% | Punto |
| 5 | Conectividad vial | 10% | Punto |
| 6 | Áreas verdes y medio ambiente | 10% | Punto |
| 7 | Riesgos y desamenidades | 10% | Punto |
| 8 | Proyección futura (plusvalía) | Bonus | Punto |
| — | Precio (arriendo/venta) | Fuera del puntaje | Zona |

Los pesos viven en configuración y se calibran en la Fase 3.

## 3. Datos a investigar

Cada fuente se registra en el catálogo con: origen, fecha, licencia, granularidad,
formato y cómo se actualiza. "Por verificar" significa que falta confirmar disponibilidad.

### 3.1 Seguridad
| Dato | Fuente | Uso |
|---|---|---|
| Delitos de mayor connotación social por 100 mil hab., por tipo, tendencia 5 años | CEAD (Subsecretaría de Prevención del Delito) | Base del puntaje |
| Robo en vivienda, robo con violencia, robo de vehículos | CEAD | Mayor peso (afectan al residente) |
| Homicidios | Informe Nacional de Homicidios | Ajuste por violencia grave |
| Victimización y percepción | ENUSC (INE) | Componente de percepción |
| Comisarías, PDI, retenes | OSM, datos.gob.cl | Cercanía |

Se corrige por población flotante (Santiago Centro, Providencia y otras comunas comerciales
tienen tasas infladas respecto del riesgo de quien vive ahí).

### 3.2 Socioeconómico y calidad de vida
| Dato | Fuente | Granularidad |
|---|---|---|
| Índice Socio-Material Territorial (ISMT) | Observatorio de Ciudades UC | Manzana |
| Población, edad, escolaridad, hacinamiento, densidad | Censo 2024 / 2017 (INE) | Manzana / zona |
| Pobreza por ingresos y multidimensional | CASEN (estimación comunal) | Comuna |
| Grupo socioeconómico | AIM | Comuna / zona |
| Índice de Calidad de Vida Urbana | CChC + IEUT UC | Comuna |
| Presupuesto municipal por habitante, % ingresos propios | SINIM | Comuna |
| Áreas verdes por habitante | SINIM / SIEDU | Comuna |
| Campamentos | Catastro MINVU / TECHO | Punto |
| Índice de Prioridad Social | Seremi Desarrollo Social RM | Comuna |

### 3.3 Precios (fuera del puntaje)
| Dato | Fuente |
|---|---|
| Avisos de arriendo y venta (precio, m², dormitorios, ubicación, fecha) | Scraping bajo demanda de Toc Toc y Portal Inmobiliario (ver D-006) |
| Precio de referencia comunal | Informes públicos (CChC, portales, GlobalProperty), índice de precios de vivienda del Banco Central |
| Avalúo fiscal | Cartografía SII (por verificar descarga masiva) |
| Rentabilidad bruta (arriendo × 12 / precio) | Cálculo propio |
| Permisos de edificación | INE |

### 3.4 Servicios cercanos (distancia caminando por la red de calles)
| Categoría | Fuente | Umbral ideal inicial |
|---|---|---|
| Jardines y salas cuna | JUNJI, Integra, Mineduc | ≤ 10 min a pie |
| Colegios, ponderados por calidad (SIMCE, categoría de desempeño, PAES) | Directorio Mineduc, Agencia de Calidad, DEMRE | ≤ 15 min |
| Universidades e institutos | Mineduc / OSM | Informativo |
| CESFAM, SAPU, SAR, hospitales, clínicas | DEIS MINSAL | Urgencia ≤ 10 min en auto |
| Farmacias (incluidas de turno) | API Farmanet MINSAL | ≤ 10 min |
| Supermercados | OSM + verificación por cadena | ≤ 10 min |
| Malls | OSM | ≤ 15 min |
| Bancos y cajeros | OSM / CMF | ≤ 15 min |
| Bomberos | OSM / Bomberos de Chile | ≤ 5 min en auto |
| Ferias libres, restaurantes, cafés, gimnasios | OSM, municipios | Densidad en 500 m |

### 3.5 Transporte público
| Dato | Fuente | Uso |
|---|---|---|
| Metro, Tren Nos, EFE | Metro / OSM | Distancia a pie |
| Paraderos, recorridos y frecuencia en punta | GTFS Red Metropolitana (DTPM) | Ponderar por buses por hora |
| Tiempo de viaje a centros de trabajo (Centro, Providencia, El Golf, Ciudad Empresarial) | Cálculo propio sobre GTFS (OpenTripPlanner o r5) | Métrica principal de movilidad |
| Ciclovías | OSM | Bonus |

### 3.6 Conectividad vial
| Dato | Fuente | Uso |
|---|---|---|
| Accesos a autopistas urbanas (enlaces) | OSM | Lo que cuenta es el acceso, no la autopista |
| Tiempo en auto a aeropuerto, Ruta 5, 68, 78 | OSRM | Puntaje |
| Avenidas troncales | OSM | Puntaje |
| Vivienda a menos de 150 m de una autopista | Cálculo propio | Penalización por ruido |

### 3.7 Áreas verdes y medio ambiente
| Dato | Fuente |
|---|---|
| Plazas y parques con su tamaño | OSM, catastro SIEDU/MINVU |
| Vegetación en 500 m (NDVI) | Sentinel-2 |
| Islas de calor | Landsat |
| Ruido | Mapa de ruido del Gran Santiago (MMA) |
| Calidad del aire | SINCA |

### 3.8 Riesgos y desamenidades
- Zonas inundables, remoción en masa, Falla San Ramón (SERNAGEOMIN, PRMS).
- Cercanía a cárceles, vertederos, industrias peligrosas, líneas de alta tensión, ruta de
  aproximación al aeropuerto.
- Pendiente del terreno (modelo de elevación).

### 3.9 Proyección futura
- Nuevas líneas de Metro (L7, L8, L9, extensiones), Tren Alameda–Melipilla, Tren
  Santiago–Batuco, Costanera Central, AVO tramo 2 (fechas por verificar).
- Permisos de edificación recientes y cambios en planes reguladores.

## 4. Metodología del puntaje

1. **Cercanías:** función de decaimiento por categoría (ej. Metro: 5 min = 100,
   10 min = 80, 20 min = 40, 30+ min = 0). Cuenta la cantidad y calidad, no solo el más cercano.
2. **Indicadores comunales:** se convierten a percentiles dentro de la RM.
3. **Puntaje final:** promedio ponderado, convertido a letra (A ≥ 80, B ≥ 65, …).
4. **Confianza por dimensión:** indica si el dato es fino (punto) o grueso (comuna), y
   distingue "valor bajo" de "sin dato".
5. **Validación:** comparar con el ranking ICVU y revisar 20–30 lugares conocidos.

## 5. Funcionalidades

**MVP**
- Mapa de la RM con búsqueda por dirección.
- Panel al tocar un punto: puntaje, 8 dimensiones, lo más cercano (nombre y minutos),
  datos de la comuna y precios comparables (instantáneos si hay caché, si no en ≤ 1 min).
- Capas: mapa de calor del puntaje y de cada dimensión, comunas coloreadas por indicador.
- Isócronas de 5, 10 y 15 minutos caminando.
- Exportar ficha 16:9 (PNG, PDF, PPTX).

**Versión 2**
- Comparador de 2 a 4 puntos.
- Búsqueda inversa (presupuesto → mejores zonas).
- Detector de oportunidades (calidad vs. precio).
- Puntos guardados.
- Veredicto escrito por IA (opcional).

## 6. Ficha exportable (16:9, 4 cuadrantes)

```
┌──────────────────────────┬──────────────────────────┐
│ 1. EL PUNTO              │ 2. CERCANÍAS             │
│ Foto de calle (Mapillary)│ Metro, supermercado,     │
│ + minimapa con isócrona  │ salud, colegios, acceso  │
│ Dirección, coordenadas   │ a autopista (minutos)    │
├──────────────────────────┼──────────────────────────┤
│ 3. LA COMUNA Y EL PRECIO │ 4. VEREDICTO             │
│ Delitos vs. promedio RM  │ Puntaje y letra          │
│ Arriendo y UF/m² de zona │ Radar de 8 dimensiones   │
│ ICVU, pobreza, GSE       │ 3 fortalezas, 3 debilid. │
└──────────────────────────┴──────────────────────────┘
          Fuentes y fecha de los datos al pie
```

## 7. Fases

| Fase | Entregable |
|---|---|
| F1. Investigación | Catálogo de fuentes y ficha de las 52 comunas; prueba de factibilidad del scraping |
| F2. Procesamiento geográfico | Red de calles, puntos de interés limpios, distancias por hexágono |
| F3. Modelo de puntaje | Puntajes calibrados y validados |
| F4. App MVP | Mapa, panel, precios bajo demanda, exportación |
| F5. Versión 2 | Comparador, búsqueda inversa, plusvalía |

## 8. Limitaciones conocidas

- La seguridad pública está mayormente a nivel comunal; si no hay datos más finos se
  complementa con el ISMT por manzana y la app lo indica.
- Los portales pueden cambiar o bloquear; los precios siempre tienen un respaldo comunal.
- Puntuar barrios con datos socioeconómicos es sensible: cada dato muestra fuente y fecha.
