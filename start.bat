@echo off
chcp 65001 >nul
echo ========================================
echo  智能文章重点标注与分析系统
echo ========================================
echo.

echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERR] 未找到 Python，请先运行 install.bat 安装依赖
    pause & exit /b 1
)
echo [OK]  Python 已安装

echo.
echo [2/4] 检查 Node.js 环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERR] 未找到 Node.js，请先运行 install.bat 安装依赖
    pause & exit /b 1
)
echo [OK]  Node.js 已安装

echo.
echo [3/4] 检查 API 密钥配置...
if not exist "backend\.env" (
    echo [WARN] 未找到 backend\.env 文件！
    echo        请先运行 install.bat 安装并配置 API 密钥
    echo        或手动将 backend\.env.example 复制为 backend\.env 并填入密钥
    echo.
    set /p CONTINUE="是否仍然继续启动？[y/N] "
    if /i not "%CONTINUE%"=="y" (
        pause & exit /b 1
    )
) else (
    echo [OK]  backend\.env 已配置
)

echo.
echo [4/4] 启动服务...
cd backend
start "智能分析系统-后端" cmd /k "python app.py"
cd ..
timeout /t 3 >nul

cd frontend
start "智能分析系统-前端" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo  系统已启动！
echo ========================================
echo  后端地址: http://localhost:5000
echo  前端地址: http://localhost:3000
echo.
echo  请在浏览器中访问前端地址使用系统
echo  按任意键退出启动脚本（服务将继续运行）
echo ========================================
pause >nul
