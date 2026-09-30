@echo off
title Page Metrics - Stop App
color 0C

echo Stopping Page Metrics background processes...
taskkill /FI "IMAGENAME eq python.exe" /F > nul 2>&1
taskkill /FI "IMAGENAME eq uvicorn.exe" /F > nul 2>&1

echo Page Metrics server stopped successfully.
timeout /t 2 /nobreak > nul
