@echo off
echo ================================================
echo Phase Balancing Controller
echo ================================================
echo.
echo Starting backend server...
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs  
echo Dashboard: Open frontend\dashboard.html in browser
echo.
echo [Press Ctrl+C to stop]
echo.

python run_server.py
pause
