@echo off
chcp 65001 >nul
echo ======================================
echo   启动 Kafka 服务
echo ======================================
echo.

REM 请根据实际安装路径修改
set KAFKA_HOME=C:\kafka

cd /d %KAFKA_HOME%

echo [1/2] 启动 Zookeeper...
start "Zookeeper" cmd /k "bin\windows\zookeeper-server-start.bat config\zookeeper.properties"
timeout /t 10 >nul

echo [2/2] 启动 Kafka...
start "Kafka" cmd /k "bin\windows\kafka-server-start.bat config\server.properties"
timeout /t 10 >nul

echo.
echo ✅ Kafka 服务启动完成！
echo.
pause


