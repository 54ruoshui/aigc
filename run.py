#!/usr/bin/env python3
"""
GraphRAG系统启动脚本
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='计算机网络知识图谱GraphRAG系统')
    parser.add_argument('--mode', choices=['web', 'cli', 'test'], default='web',
                      help='运行模式: web(网页界面), cli(命令行), test(测试)')
    parser.add_argument('--host', default='0.0.0.0', help='Web服务器主机地址')
    parser.add_argument('--port', type=int, default=5000, help='Web服务器端口')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    if args.mode == 'web':
        print("🌐 启动GraphRAG Web界面...")
        from web.graph_rag_web import app
        
        # 设置Flask配置
        app.config['DEBUG'] = args.debug
        app.config['HOST'] = args.host
        app.config['PORT'] = args.port
        
        print(f"📍 访问地址: http://{args.host}:{args.port}")
        print("🔄 按 Ctrl+C 停止服务器")
        
        try:
            app.run(host=args.host, port=args.port, debug=args.debug)
        except KeyboardInterrupt:
            print("\n👋 服务器已停止")
    
    elif args.mode == 'cli':
        print("💻 启动GraphRAG命令行界面...")
        from src.graph_rag_system import main as cli_main
        cli_main()
    
    elif args.mode == 'test':
        print("🧪 运行GraphRAG系统测试...")
        from src.graph_rag_system import main
        main()

if __name__ == '__main__':
    main()