#!/bin/bash
echo "🔧 修复conda环境下的安装问题"
echo "=================================="

echo "📋 检查当前环境..."
conda info --envs

echo "📋 激活aigc环境..."
conda activate aigc

echo "📋 升级pip到最新版本..."
python -m pip install --upgrade pip setuptools wheel --no-warn-script-location

echo "📋 清理pip缓存..."
python -m pip cache purge

echo "📋 安装项目依赖..."
pip install -r requirements.txt --no-warn-script-location

echo "📋 验证安装..."
python -c "
try:
    import neo4j
    import requests
    import flask
    import python_dotenv
    print('✅ 核心依赖导入成功')
except ImportError as e:
    print(f'❌ 导入失败: {e}')
    exit(1)
"

echo "✅ 安装完成！"
echo ""
echo "🚀 现在可以运行系统："
echo "   Web界面: python run.py --mode web"
echo "   命令行: python run.py --mode cli"
echo "   测试: python run.py --mode test"