@echo off
chcp 65001 > nul
echo 正在启动游戏队列管理器...
echo ============================

:: 检查配置文件是否存在
if not exist "config.json" (
    echo [错误] 未找到配置文件 config.json
    pause
    exit /b 1
)

:: 设置控制台标题
title 游戏队列管理器

:: 运行程序
python queueGame.py

:: 如果程序异常退出，显示错误信息
if errorlevel 1 (
    echo ============================
    echo [错误] 程序异常退出，请检查错误信息
    pause
) 