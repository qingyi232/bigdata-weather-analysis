@echo off
chcp 65001 >nul
echo ======================================
echo   启动后端服务
echo ======================================
echo.

cd /d %~dp0..

echo [1/3] 启动 Flask API 服务...
start "Flask API" cmd /k "cd backend\api && python app.py"
timeout /t 3 >nul

echo [2/3] 启动 Kafka 数据采集服务...
start "Kafka Producer" cmd /k "cd backend\data_collection && python kafka_producer.py"
timeout /t 3 >nul

echo [3/3] 启动 Spark 批处理服务（可选）...
REM start "Spark Analysis" cmd /k "cd backend\batch_processing && python spark_analysis.py"

echo.
echo ✅ 后端服务启动完成！
echo.
echo 服务访问地址:
echo   - API 服务: http://localhost:5000
echo   - API 文档: http://localhost:5000/api/v1/health
echo.
pause


