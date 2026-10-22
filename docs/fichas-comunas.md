# Fichas de las 52 comunas de la Región Metropolitana

Generado automáticamente el 2026-10-22 con `uv run score comunas`.
Datos completos (43 indicadores por comuna) en `data/processed/comunas.csv`.

**Fuentes:** Censo 2024 (INE), pobreza comunal SAE Casen 2024 (MDSF), casos policiales
2025 (CEAD), establecimientos de salud (Minsal, jun-2026), directorio de establecimientos
educacionales 2025 (Mineduc), GTFS Red Metropolitana (DTPM, oct-2026), ICVU 2025
(CChC + IEUT UC).

**Cómo leerla:**
- **DMCS:** delitos de mayor connotación social por cada 100 mil habitantes en 2025.
  Las comunas con mucho comercio u oficinas (Santiago, Providencia, Estación Central)
  aparecen infladas porque se divide por residentes, no por la gente que circula.
- **Violentos:** robos con violencia o intimidación, robo violento de vehículo, robo por
  sorpresa y homicidios.
- **Paraderos:** solo la red RED/Transantiago; las comunas rurales tienen buses rurales
  que no están en el GTFS, por eso aparecen con 0.
- **ICVU:** el informe publica niveles, no puntajes; cubre 42 comunas de la RM. "—" = sin dato.

| Comuna | Provincia | Población | Hab/km² | Escolaridad (años) | Pobreza ingresos | Pobreza multidim. | DMCS /100 mil | Violentos /100 mil | Hogares arrendatarios | Metro | Paraderos | Urgencias | Colegios | ICVU 2025 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Colina | Chacabuco | 173.293 | 179 | 12,7 | 11,7% | 27,5% | 2.053 | 456 | 20,3% | 0 | 9 | 2 | 77 | Medio alto |
| Lampa | Chacabuco | 145.160 | 322 | 12,2 | 15,8% | 25,7% | 1.824 | 454 | 18,2% | 0 | 60 | 2 | 60 | Medio bajo |
| Tiltil | Chacabuco | 19.742 | 30 | 11,5 | 13,7% | 21,3% | 2.477 | 395 | 15,5% | 0 | 0 | 2 | 19 | — |
| Pirque | Cordillera | 29.060 | 65 | 12,5 | 12,8% | 17,5% | 1.177 | 114 | 12,3% | 0 | 26 | 1 | 12 | — |
| Puente Alto | Cordillera | 568.086 | 6.438 | 12,3 | 13,8% | 22,1% | 2.175 | 640 | 18,8% | 5 | 1.001 | 7 | 213 | Medio bajo |
| San José de Maipo | Cordillera | 17.441 | 4 | 12,4 | 14,1% | 14,9% | 2.414 | 195 | 18,0% | 0 | 0 | 1 | 12 | — |
| Buin | Maipo | 116.969 | 538 | 12,3 | 16,5% | 17,9% | 2.119 | 384 | 17,0% | 0 | 7 | 4 | 51 | Medio bajo |
| Calera de Tango | Maipo | 25.491 | 348 | 12,1 | 11,3% | 19,5% | 2.185 | 255 | 14,7% | 0 | 2 | 1 | 16 | — |
| Paine | Maipo | 78.828 | 116 | 11,3 | 15,8% | 20,2% | 2.068 | 397 | 17,8% | 0 | 2 | 2 | 40 | Bajo |
| San Bernardo | Maipo | 306.371 | 2.004 | 11,8 | 17,8% | 25,4% | 2.982 | 913 | 22,4% | 1 | 645 | 8 | 143 | Medio bajo |
| Alhué | Melipilla | 7.768 | 9 | 10,9 | 23,2% | 20,2% | 1.236 | 26 | 18,5% | 0 | 0 | 1 | 5 | — |
| Curacaví | Melipilla | 35.165 | 51 | 11,7 | 19,6% | 23,8% | 2.181 | 259 | 14,8% | 0 | 0 | 1 | 21 | — |
| María Pinto | Melipilla | 15.352 | 39 | 10,8 | 18,3% | 25,0% | 1.316 | 111 | 8,6% | 0 | 0 | 1 | 7 | — |
| Melipilla | Melipilla | 136.325 | 101 | 11,3 | 21,4% | 24,1% | 2.223 | 360 | 21,0% | 0 | 0 | 4 | 72 | Bajo |
| San Pedro | Melipilla | 11.108 | 14 | 10,0 | 22,2% | 29,8% | 1.846 | 99 | 15,8% | 0 | 0 | 1 | 12 | — |
| Cerrillos | Santiago | 85.041 | 5.068 | 11,8 | 17,6% | 21,7% | 4.633 | 1.555 | 22,3% | 1 | 289 | 2 | 37 | Medio bajo |
| Cerro Navia | Santiago | 127.250 | 11.467 | 10,7 | 19,0% | 35,9% | 2.210 | 898 | 25,0% | 0 | 262 | 4 | 52 | Bajo |
| Conchalí | Santiago | 121.587 | 10.944 | 11,7 | 15,8% | 23,8% | 2.556 | 1.003 | 31,4% | 3 | 313 | 3 | 63 | Bajo |
| El Bosque | Santiago | 155.257 | 10.867 | 11,3 | 20,1% | 29,0% | 2.283 | 661 | 23,6% | 3 | 261 | 4 | 92 | Bajo |
| Estación Central | Santiago | 181.049 | 12.614 | 12,5 | 15,5% | 23,0% | 5.447 | 2.279 | 59,2% | 5 | 312 | 5 | 63 | Medio alto |
| Huechuraba | Santiago | 101.808 | 2.268 | 12,9 | 11,2% | 22,9% | 3.237 | 968 | 21,6% | 0 | 210 | 2 | 32 | Alto |
| Independencia | Santiago | 116.943 | 15.898 | 12,9 | 11,7% | 18,7% | 3.221 | 1.099 | 65,9% | 2 | 153 | 5 | 41 | Medio alto |
| La Cisterna | Santiago | 103.157 | 10.337 | 13,0 | 12,2% | 14,5% | 4.249 | 1.575 | 44,2% | 3 | 233 | 1 | 67 | Medio alto |
| La Florida | Santiago | 374.836 | 5.292 | 13,0 | 11,9% | 13,9% | 2.942 | 795 | 29,8% | 9 | 767 | 11 | 204 | Medio bajo |
| La Granja | Santiago | 112.022 | 11.103 | 11,2 | 18,8% | 29,8% | 2.782 | 1.233 | 24,7% | 2 | 260 | 3 | 57 | Bajo |
| La Pintana | Santiago | 175.421 | 5.758 | 10,4 | 23,3% | 36,9% | 2.193 | 836 | 18,3% | 0 | 397 | 5 | 70 | Bajo |
| La Reina | Santiago | 89.870 | 3.834 | 15,0 | 5,9% | 6,3% | 2.951 | 461 | 26,9% | 3 | 270 | 2 | 57 | Alto |
| Las Condes | Santiago | 296.134 | 2.990 | 15,7 | 2,8% | 4,9% | 2.279 | 345 | 40,8% | 6 | 454 | 7 | 108 | Alto |
| Lo Barnechea | Santiago | 112.620 | 110 | 14,7 | 2,8% | 11,7% | 1.405 | 126 | 23,1% | 0 | 207 | 2 | 40 | Alto |
| Lo Espejo | Santiago | 87.295 | 10.596 | 10,7 | 22,0% | 34,5% | 2.572 | 1.052 | 20,5% | 0 | 219 | 4 | 39 | Bajo |
| Lo Prado | Santiago | 91.290 | 13.916 | 11,4 | 16,3% | 25,2% | 2.917 | 1.136 | 32,1% | 4 | 195 | 4 | 36 | Bajo |
| Macul | Santiago | 123.800 | 9.643 | 13,5 | 13,5% | 10,6% | 2.929 | 993 | 39,4% | 8 | 267 | 1 | 42 | Medio bajo |
| Maipú | Santiago | 503.635 | 3.658 | 12,7 | 12,0% | 17,0% | 2.441 | 885 | 21,6% | 5 | 873 | 6 | 210 | Medio alto |
| Pedro Aguirre Cerda | Santiago | 96.062 | 10.971 | 11,4 | 20,6% | 27,1% | 2.564 | 990 | 25,9% | 2 | 190 | 3 | 50 | Bajo |
| Peñalolén | Santiago | 236.478 | 4.411 | 12,4 | 13,0% | 22,9% | 2.078 | 556 | 24,7% | 3 | 421 | 6 | 76 | Medio alto |
| Providencia | Santiago | 143.974 | 9.998 | 16,2 | 1,2% | 1,8% | 8.026 | 2.189 | 51,1% | 11 | 249 | 8 | 81 | Alto |
| Pudahuel | Santiago | 227.820 | 1.155 | 11,9 | 15,4% | 22,4% | 3.053 | 1.124 | 23,2% | 3 | 541 | 6 | 68 | Medio bajo |
| Quilicura | Santiago | 205.624 | 3.587 | 12,3 | 13,7% | 19,9% | 2.763 | 1.131 | 26,0% | 4 | 409 | 3 | 65 | Medio bajo |
| Quinta Normal | Santiago | 129.351 | 10.946 | 12,4 | 12,4% | 19,5% | 3.749 | 1.587 | 45,5% | 2 | 280 | 2 | 71 | Medio bajo |
| Recoleta | Santiago | 154.615 | 9.795 | 11,8 | 14,5% | 25,8% | 4.820 | 2.101 | 43,3% | 7 | 328 | 4 | 73 | Medio alto |
| Renca | Santiago | 143.622 | 6.046 | 11,2 | 18,7% | 27,9% | 2.646 | 1.026 | 23,8% | 0 | 293 | 3 | 58 | Medio bajo |
| San Joaquín | Santiago | 95.602 | 9.611 | 12,1 | 14,6% | 21,0% | 3.222 | 1.281 | 32,9% | 0 | 243 | 2 | 41 | Medio bajo |
| San Miguel | Santiago | 150.829 | 15.687 | 14,3 | 10,4% | 9,9% | 3.950 | 1.467 | 51,9% | 6 | 179 | 3 | 74 | Alto |
| San Ramón | Santiago | 76.002 | 12.108 | 10,9 | 19,7% | 30,4% | 3.331 | 1.188 | 23,1% | 1 | 200 | 4 | 38 | Bajo |
| Santiago | Santiago | 438.856 | 18.986 | 14,0 | 10,2% | 17,9% | 7.514 | 3.623 | 72,1% | 19 | 582 | 8 | 150 | Alto |
| Vitacura | Santiago | 86.420 | 3.039 | 16,0 | 0,8% | 2,1% | 2.100 | 354 | 34,2% | 0 | 197 | 3 | 29 | Alto |
| Ñuñoa | Santiago | 241.467 | 14.315 | 15,5 | 5,7% | 4,2% | 3.508 | 1.165 | 45,7% | 8 | 367 | 3 | 101 | Alto |
| El Monte | Talagante | 37.497 | 326 | 11,1 | 19,7% | 21,7% | 1.392 | 221 | 17,1% | 0 | 0 | 1 | 24 | — |
| Isla de Maipo | Talagante | 39.274 | 207 | 11,4 | 16,2% | 21,2% | 1.334 | 194 | 15,0% | 0 | 0 | 2 | 17 | — |
| Padre Hurtado | Talagante | 81.243 | 1.002 | 12,3 | 15,0% | 17,9% | 1.448 | 327 | 17,7% | 0 | 50 | 1 | 39 | Bajo |
| Peñaflor | Talagante | 94.402 | 1.362 | 12,1 | 15,7% | 17,0% | 1.794 | 303 | 19,3% | 0 | 0 | 3 | 58 | Medio bajo |
| Talagante | Talagante | 76.429 | 604 | 12,0 | 17,9% | 20,2% | 2.320 | 326 | 19,6% | 0 | 0 | 4 | 54 | Bajo |
