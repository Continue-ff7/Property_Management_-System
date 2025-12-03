@echo off
chcp 65001 >nul
echo 物业管理系统后端服务启动脚本
echo ================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查是否安装了依赖
echo 检查依赖...
::pip show fastapi >nul 2>&1
::if errorlevel 1 (
::    echo 正在安装依赖包...
    ::pip install -r requirements.txt
::    if errorlevel 1 (
::        echo [错误] 依赖安装失败
::        pause
::        exit /b 1
 ::   )
::)

REM 检查.env文件
if not exist .env (
    echo 请修改.env文件中的配置，特别是数据库连接信息
    echo.
)

echo ================================
echo 启动服务...
echo 访问地址: http://localhost:8088
echo API文档: http://localhost:8088/docs
echo ================================
echo.

uvicorn main:app --reload --host 127.0.0.1 --port 8088

pause
