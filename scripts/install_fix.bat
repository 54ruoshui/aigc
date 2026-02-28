@echo off
echo 🔧 修复Python 3.12安装问题...
echo.

echo 📋 第1步：升级pip和setuptools
python -m pip install --upgrade pip setuptools wheel --no-warn-script-location

echo 📋 第2步：清理pip缓存
python -m pip cache purge

echo 📋 第3步：安装依赖
pip install -r requirements.txt --no-warn-script-location

echo.
echo ✅ 安装完成！
echo.
echo 🚀 现在可以运行系统：
echo    Web界面: python run.py --mode web
echo    命令行: python run.py --mode cli
echo    测试: python run.py --mode test
echo.
pause