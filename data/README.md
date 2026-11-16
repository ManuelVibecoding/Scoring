# Datos

Los datos no se versionan en Git: se regeneran con los trabajos de `backend/src/score/pipeline`.

```
data/
├─ raw/        descargas originales, tal cual vienen de la fuente
├─ interim/    datos limpios intermedios
├─ processed/  resultados listos para la app (por hexágono, por comuna)
└─ (los avisos de arriendo quedan en interim/avisos/, un archivo por corrida del scraper)
```

El catálogo de fuentes (qué se descarga, de dónde, licencia y fecha) está en
[docs/catalogo-datos.md](../docs/catalogo-datos.md).
