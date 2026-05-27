@echo off
chcp 65001 >nul
echo ======================================
echo   初始化数据库
echo ======================================
echo.

cd /d %~dp0..\backend

echo 初始化数据库表结构...
python data_storage/mysql_manager.py

echo.
echo ✅ 数据库初始化完成！
echo.
pause


