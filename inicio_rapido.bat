@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ======================================================
echo    BIM-IoT-GIS Viewer - Instalacion y Arranque
echo ======================================================
echo.

:: 1. Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo Por favor, instala Python 3.9+ desde python.org
    pause
    exit /b
)

:: 2. Verificar Node/NPM
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js/NPM no esta instalado o no esta en el PATH.
    echo Por favor, instala Node.js (LTS recomendado) desde nodejs.org
    pause
    exit /b
)

:: 3. Configurar Backend (Python Virtual Environment)
echo [1/4] Configurando Backend (Python)...
if not exist "backend\venv" (
    echo     - Creando entorno virtual...
    python -m venv backend\venv
)

echo     - Instalando librerias necesarias...
call backend\venv\Scripts\activate
pip install --upgrade pip >nul
pip install -r backend\requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] No se pudieron instalar las librerias del backend.
    pause
    exit /b
)

:: 4. Configurar Frontend (Node Modules)
echo.
echo [2/4] Configurando Frontend (Node.js)...
if not exist "frontend\node_modules" (
    echo     - Instalando paquetes (esto puede tardar un poco)...
    cd frontend
    call npm install --quiet
    cd ..
)

:: 5. Arrancar Servidores
echo.
echo [3/4] Arrancando servidores...

echo     - Lanzando Backend (FastAPI en puerto 8000)...
start "Backend BIM-GIS" /B cmd /c "backend\venv\Scripts\activate && cd backend && python main.py"

echo     - Lanzando Frontend (Vite en puerto 5173)...
start "Frontend BIM-GIS" /B cmd /c "cd frontend && npm run dev"

:: 6. Abrir Navegador
echo.
echo [4/4] Esperando a que el sistema este listo...
timeout /t 8 /nobreak >nul

echo.
echo Lanzando visor en el explorador...
start http://localhost:5173

echo.
echo ======================================================
echo    LISTO! El visor esta funcionando.
echo    Para cerrar: Cierra esta ventana y presiona una tecla.
echo ======================================================
echo.
pause

echo Apagando servidores...
taskkill /FI "WINDOWTITLE eq Backend BIM-GIS*" /F /T >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend BIM-GIS*" /F /T >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
taskkill /IM python.exe /F >nul 2>&1

echo Limpieza completada.
echo.
exit /b
