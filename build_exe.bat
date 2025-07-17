@echo off
chcp 65001 > nul
echo 正在打包程序...
echo ============================

:: 检查 Anaconda 环境
where conda > nul 2>&1
if %errorlevel% equ 0 (
    echo 检测到 Anaconda 环境
    set PYTHON_PATH=D:\Anaconda3
    set PYTHON_SCRIPTS=%PYTHON_PATH%\Scripts
) else (
    :: 获取普通 Python 安装路径
    for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i
    set PYTHON_SCRIPTS=%PYTHON_PATH:python.exe=Scripts%
)

:: 检查是否安装了 pyinstaller
echo 正在检查 PyInstaller...
pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)

:: 清理旧的构建文件和exe
echo 正在清理旧文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /f /q *.spec
if exist "QueueGame.exe" del /f /q QueueGame.exe

:: 打包程序
echo 正在打包程序...
python -m PyInstaller --noconfirm --clean ^
    --name "QueueGame" ^
    --onefile ^
    --add-data "config.json;." ^
    --hidden-import requests ^
    --hidden-import colorama ^
    --hidden-import psutil ^
    --hidden-import urllib3 ^
    --hidden-import charset_normalizer ^
    --hidden-import idna ^
    --hidden-import certifi ^
    queueGame.py

:: 移动文件
echo 正在移动文件...
if exist "dist\QueueGame.exe" (
    move /Y "dist\QueueGame.exe" "."
)

:: 彻底清理临时文件和目录
echo 正在清理临时文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "*.spec" del /f /q *.spec
if exist "*.pyc" del /f /q *.pyc

echo ============================
if exist "QueueGame.exe" (
    echo 打包完成！
    echo 生成文件：QueueGame.exe
) else (
    echo [错误] 打包失败，请检查错误信息
)
pause 