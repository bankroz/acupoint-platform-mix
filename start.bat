@echo off
title AI 经络穴位导航系统 - 一键启动
color 0A

echo(
echo   ============================================================
echo     AI 经络/穴位导航理疗系统 MVP v0.2.0
echo     基于 YOLOv8-Pose + MediaPipe Hands
echo   ============================================================
echo(

REM 切换到脚本所在目录
cd /d "%~dp0"

REM ========================================
REM 1. 启动后端 (FastAPI + WebSocket)
REM ========================================
echo   [1/3] 启动后端服务 (端口 8765)...
echo          YOLOv8 模型加载中，约需 10-20 秒...
start "Acupoint-Backend" cmd /k "title 后端-穴位导航 && cd /d %~dp0backend && venv\Scripts\python.exe main.py"

REM ========================================
REM 2. 等待后端初始化
REM ========================================
echo   [2/3] 等待后端就绪...
timeout /t 12 /nobreak >nul

REM ========================================
REM 3. 启动前端 (Vite React Dev Server)
REM ========================================
echo   [3/3] 启动前端服务 (端口 5173)...
set "PATH=C:\Users\diagebase\.workbuddy\binaries\node\versions\22.22.2;%PATH%"
start "Acupoint-Frontend" cmd /k "title 前端-穴位导航 && set PATH=C:\Users\diagebase\.workbuddy\binaries\node\versions\22.22.2;%%PATH%% && cd /d %~dp0frontend && npm run dev"

REM ========================================
REM 4. 等待前端编译完成后打开浏览器
REM ========================================
echo         等待 Vite 编译...
timeout /t 6 /nobreak >nul

echo         打开浏览器...
start http://localhost:5173

echo(
echo   ============================================================
echo     [OK] 启动完成!
echo(
echo     前端页面:  http://localhost:5173
echo     后端 API:  http://localhost:8765
echo     健康检查:  http://localhost:8765/api/health
echo     API 文档:  http://localhost:8765/docs
echo(
echo     关闭: 直接运行 stop.bat 或关闭两个服务窗口
echo   ============================================================
echo(
echo   按任意键关闭本窗口 (不影响后端和前端)...
pause >nul
