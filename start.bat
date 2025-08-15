@echo off
echo ==============================================================
echo                    NEXUS-RSI LAUNCHER
echo           Hyperfast Iteration - Auto-Improvement
echo ==============================================================
echo.

cd /d C:\Users\Jean-SamuelLeboeuf\NEXUS-RSI

echo [INFO] Installing/Updating dependencies...
pip install -r requirements.txt --quiet 2>nul

echo [INFO] Starting NEXUS-RSI System...
python launch_nexus.py

pause