@echo off
rem Double-click to open the RAG study kit in your browser. Close this window to stop it.
cd /d "%~dp0.."
uv run python study\app\server.py
pause
