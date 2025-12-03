@echo off
chcp 65001 >nul
echo 智慧物业管理系统 - 前端启动脚本
echo ================================
echo.

REM 检查Node.js是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Node.js，请先安装Node.js
    pause
    exit /b 1
)

REM 检查node_modules是否存在
if not exist node_modules (
    echo 正在安装依赖包...
    call npm install
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo ================================
echo 启动开发服务器...
echo 访问地址: http://localhost:8080
echo ================================
echo.

npm run serve
