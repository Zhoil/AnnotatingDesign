@echo off
chcp 65001 >nul
echo ========================================
echo  智能文章重点标注与分析系统 - 初始化安装
echo ========================================
echo.

:: ── 检查 Python ─────────────────────────────
echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERR] 未找到 Python，请先安装 Python 3.9+
    echo       下载地址: https://www.python.org/downloads/
    pause & exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK]  Python %PY_VER%

:: ── 检查 Node.js ─────────────────────────────
echo.
echo [2/5] 检查 Node.js 环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERR] 未找到 Node.js，请先安装 Node.js 16+
    echo       下载地址: https://nodejs.org/
    pause & exit /b 1
)
for /f %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo [OK]  Node.js %NODE_VER%

:: ── 安装 Python 依赖 ─────────────────────────
echo.
echo [3/5] 安装 Python 依赖（backend/requirements.txt）...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERR] Python 依赖安装失败，请检查网络或手动运行:
    echo       cd backend ^& pip install -r requirements.txt
    pause & exit /b 1
)
echo [OK]  Python 依赖安装完成

:: ── 配置 .env 文件 ────────────────────────────
echo.
echo [4/5] 检查 API 密钥配置...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [!]  已从模板创建 backend/.env
        echo      请用文本编辑器打开 backend/.env，填入您的真实 API 密钥：
        echo        DEEPSEEK_API_KEY=your_deepseek_api_key_here
        echo        QWEN_API_KEY=your_qwen_api_key_here
        echo      获取 DeepSeek Key: https://platform.deepseek.com/
        echo      获取 Qwen Key:     https://bailian.console.aliyun.com/
    ) else (
        echo [WARN] .env 和 .env.example 均不存在，请手动创建 backend/.env
    )
) else (
    echo [OK]  backend/.env 已存在
)
cd ..

:: ── 安装 Node.js 依赖 ─────────────────────────
echo.
echo [5/5] 安装前端依赖（frontend/node_modules）...
cd frontend
npm install
if %errorlevel% neq 0 (
    echo [ERR] 前端依赖安装失败，请手动运行: cd frontend ^& npm install
    pause & exit /b 1
)
echo [OK]  前端依赖安装完成
cd ..

echo.
echo ========================================
echo  安装完成！
echo ========================================
echo.
echo  下一步：
echo   1. 编辑 backend/.env，填入真实 API 密钥（如已填写可跳过）
echo   2. 运行 start.bat 启动系统
echo.
pause
