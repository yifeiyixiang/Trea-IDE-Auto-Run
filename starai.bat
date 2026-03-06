 @echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: 切换到脚本所在目录
cd /d "%~dp0"
E:\pycharm\AI-IDE-Auto-Run-main\Scripts\python.exe cmdtest.py