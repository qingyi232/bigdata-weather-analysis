@echo off
chcp 65001 >nul
echo ======================================
echo   启动前端服务
echo ======================================
echo.

cd /d %~dp0..\frontend

echo 检查依赖...
if not exist "node_modules\" (
    echo 首次运行，正在安装依赖...
    call npm install
)

echo.
echo 启动开发服务器...
call npm run dev

pause


