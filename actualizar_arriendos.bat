@echo off
rem Corre el scraper de arriendos (Toc Toc y Portal Inmobiliario) en las 52 comunas.
rem Toma alrededor de una hora. Guarda un archivo nuevo con la fecha de hoy; la app lo usa
rem sola, incluso si está abierta. Si una comuna falla, conserva sus avisos anteriores.
cd /d "%~dp0"

if not exist "data\processed\comunas.parquet" (
  echo Faltan los datos. Generalos primero con los pasos del README ^(seccion 3^).
  pause
  exit /b 1
)

echo Actualizando los avisos de arriendo de toda la RM (alrededor de una hora)...
echo Puedes seguir usando la app mientras tanto.
echo.
cd backend
uv run python -m score precios
echo.
pause
