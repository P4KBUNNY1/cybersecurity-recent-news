@echo off
title Cyber Intel Board
cd /d "%~dp0.."

if not exist "venv\Scripts\python.exe" (
  echo Could not find the venv folder in the project root.
  echo Create it first:  py -3.12 -m venv venv
  pause
  exit /b 1
)

echo.
echo [1/3] Checking Ollama...
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 (
  echo       Starting Ollama...
  start "" /min ollama serve
  for /l %%i in (1,1,40) do (
    curl -s http://localhost:11434 >nul 2>&1 && goto ollama_ready
    timeout /t 1 /nobreak >nul
  )
  echo       Ollama did not start. Is it installed? Try running: ollama --version
  pause
  exit /b 1
)
:ollama_ready
echo       Ollama is running.

if /i "%~1"=="view" (
  echo [2/3] View-only mode: skipping fetch and analysis.
) else (
  echo [2/3] Fetching posts, analyzing with AI, indexing...
  "venv\Scripts\python.exe" run.py pipeline
)

echo [3/3] Opening dashboard...
netstat -ano | findstr ":8501" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo       Dashboard is already running - opening it in your browser.
  start "" http://localhost:8501
  timeout /t 3 >nul
  exit /b 0
)
echo       Keep this window open while you use the dashboard. Close it to stop.
"venv\Scripts\python.exe" run.py dashboard
pause
