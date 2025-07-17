@echo off
chcp 65001 > nul
echo 正在安装依赖...
echo ============================

:: 检查 Python 是否安装
python --version > nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8 或更高版本
    pause
    exit /b 1
)

:: 检查是否是 Anaconda 环境
where conda > nul 2>&1
if %errorlevel% equ 0 (
    echo 检测到 Anaconda 环境
    echo 正在创建虚拟环境...
    conda create -n queuegame python=3.8 -y
    conda activate queuegame
)

:: 升级 pip
echo 正在升级 pip...
python -m pip install --upgrade pip

:: 安装依赖
echo 正在安装项目依赖...
pip install -r requirements.txt

:: 确保 PyInstaller 正确安装
echo 正在安装 PyInstaller...
pip install --upgrade pyinstaller

echo ============================
if %errorlevel% equ 0 (
    echo 依赖安装完成！
) else (
    echo [错误] 依赖安装失败，请检查错误信息
)
pause 