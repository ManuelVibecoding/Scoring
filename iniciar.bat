@echo off
rem Abre Score: levanta la API y la web en dos ventanas y abre el navegador cuando estén listas.
rem Para cerrarla, cierra las dos ventanas negras ("Score API" y "Score web").
cd /d "%~dp0"

if not exist "data\processed\puntajes.parquet" (
  echo Faltan los datos. Generalos primero con los pasos del README ^(seccion 3^).
  pause
  exit /b 1
)

start "Score API" cmd /k "cd backend && uv run uvicorn score.entrypoints.api:app_por_defecto --factory --port 8000"
start "Score web" cmd /k "cd frontend && npm run dev"

echo Cargando los datos de Score (unos 20 segundos)...
:esperar
curl -s -o nul http://localhost:8000/api/salud || (timeout /t 2 /nobreak >nul & goto esperar)

start "" http://localhost:5173
