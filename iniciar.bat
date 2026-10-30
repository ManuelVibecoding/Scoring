@echo off
rem Abre Score: levanta la API y la web en dos ventanas y abre el navegador cuando estén listas.
rem Para cerrarla, cierra las dos ventanas negras ("Score API" y "Score web").
rem La API se lanza con "python -m uvicorn" y no con uvicorn.exe: el Control inteligente de
rem aplicaciones de Windows puede bloquear los .exe que crea uv.
cd /d "%~dp0"

if not exist "data\processed\puntajes.parquet" (
  echo Faltan los datos. Generalos primero con los pasos del README ^(seccion 3^).
  pause
  exit /b 1
)

start "Score API" cmd /k "cd backend && uv run python -m uvicorn score.entrypoints.api:app_por_defecto --factory --port 8000"
start "Score web" cmd /k "cd frontend && npm run dev"

echo Cargando los datos de Score (unos 20 segundos)...
set /a intentos=0
:esperar
curl -s -o nul http://localhost:8000/api/salud && goto lista
set /a intentos+=1
if %intentos% geq 50 (
  echo.
  echo La API no respondio en 3 minutos. Revisa el error en la ventana "Score API".
  pause
  exit /b 1
)
rem Pausa de 2 segundos (ping funciona aunque no haya consola, a diferencia de timeout).
ping -n 3 127.0.0.1 >nul
goto esperar

:lista
start "" http://localhost:5173
