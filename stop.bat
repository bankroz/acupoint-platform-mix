@echo off
title 停止穴位导航系统

echo(
echo   ============================================================
echo     停止 AI 经络/穴位导航系统
echo   ============================================================
echo(

echo   正在停止后端服务 (端口 8765)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
    echo   终止进程 PID=%%a
    taskkill /PID %%a /F >nul 2>&1
)

echo   正在停止前端服务 (端口 5173)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
    echo   终止进程 PID=%%a
    taskkill /PID %%a /F >nul 2>&1
)

REM 关闭相关 cmd 窗口 (按标题匹配)
taskkill /FI "WINDOWTITLE eq 后端-穴位导航" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 前端-穴位导航" /F >nul 2>&1

echo(
echo   [OK] 系统已停止
echo(
pause
