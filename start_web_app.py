#!/usr/bin/env python3
"""
GraphRAG Web应用启动脚本
一键启动计算机网络知识图谱问答系统
"""

import os
import sys
import webbrowser
import time
from threading import Timer
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def check_dependencies():
    """检查依赖是否安装"""
    required_modules = [
        'flask', 'neo4j', 'requests', 'dotenv'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ 缺少以下依赖模块:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\n请运行以下命令安装依赖:")
        print("pip install flask neo4j requests python-dotenv")
        return False
    
    print("✅ 所有依赖模块已安装")
    return True

def check_environment():
    """检查环境配置"""
    required_env_vars = [
        'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD', 
        'ZHIPUAI_API_KEY', 'ZHIPUAI_MODEL'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ 缺少以下环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n请检查 .env 文件是否正确配置")
        return False
    
    print("✅ 环境配置检查通过")
    return True

def open_browser():
    """延迟打开浏览器"""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 GraphRAG Web应用启动器")
    print("   计算机网络知识图谱问答系统")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 设置Flask应用
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = 'True'
    
    print("\n🌐 正在启动Web服务器...")
    print("📍 访问地址: http://localhost:5000")
    print("🔄 按 Ctrl+C 停止服务器")
    print("-" * 60)
    
    # 延迟打开浏览器
    Timer(2, open_browser).start()
    
    try:
        # 导入并启动Flask应用
        from web.graph_rag_web import app, init_rag_system
        
        # 初始化GraphRAG系统
        print("🔧 正在初始化GraphRAG系统...")
        init_rag_system()
        
        # 启动Web应用
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # 避免重复初始化
        )
        
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n请检查:")
        print("1. Neo4j数据库是否正在运行")
        print("2. 网络连接是否正常")
        print("3. 环境变量是否正确配置")
        sys.exit(1)

if __name__ == '__main__':
    main()