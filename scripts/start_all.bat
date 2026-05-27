@echo off
chcp 65001 >nul
echo ======================================
echo   一键启动全部服务
echo ======================================
echo.

cd /d %~dp0

echo 启动 Kafka 服务...
call start_kafka.bat

echo.
echo 等待 Kafka 启动完成...
timeout /t 15 >nul

echo 启动后端服务...
call start_backend.bat

echo.
echo 等待后端服务启动完成...
timeout /t 10 >nul

echo 启动前端服务...
call start_frontend.bat

echo.
echo ✅ 全部服务启动完成！
echo.
echo 访问地址:
echo   - 前端页面: http://localhost:5173
echo   - API 服务: http://localhost:5000
echo.
pause


