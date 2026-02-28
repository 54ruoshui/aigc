#!/usr/bin/env python3
"""
快速启动Web应用的脚本
使用非阻塞方式初始化系统，提高启动速度
"""

import os
import sys
import time
import subprocess
import requests
import threading
from queue import Queue, Empty

def stop_existing_server():
    """停止现有的服务器"""
    try:
        # 尝试优雅地停止服务器
        response = requests.get('http://localhost:5000/api/health', timeout=2)
        print("检测到现有服务器运行中...")
        return True
    except:
        print("没有检测到现有服务器或服务器已停止")
        return False

def read_output(process, output_queue):
    """读取进程输出的线程函数"""
    for line in process.stdout:
        output_queue.put(line.strip())

def start_server():
    """启动服务器 - 快速模式"""
    print("快速启动GraphRAG Web应用...")
    print("=" * 50)
    
    # 切换到项目根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 设置环境变量，使用快速启动模式
    env = os.environ.copy()
    env['FAST_START'] = 'true'
    
    # 启动Web应用
    cmd = [sys.executable, 'web/graph_rag_web.py']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    
    # 创建输出队列和读取线程
    output_queue = Queue()
    output_thread = threading.Thread(target=read_output, args=(process, output_queue))
    output_thread.daemon = True
    output_thread.start()
    
    print("Web应用启动中...")
    
    # 显示启动进度
    max_wait_time = 30  # 快速模式只等待30秒
    check_interval = 1  # 每1秒检查一次
    waited_time = 0
    
    while waited_time < max_wait_time:
        # 显示服务器输出
        try:
            while True:
                line = output_queue.get_nowait()
                print(f"[服务器] {line}")
        except Empty:
            pass
        
        # 检查服务器是否启动成功
        try:
            response = requests.get('http://localhost:5000/api/health', timeout=2)
            if response.status_code == 200:
                data = response.json()
                print("\n✅ Web应用启动成功！")
                print(f"   状态: {data.get('status', 'unknown')}")
                print(f"   系统初始化: {'是' if data.get('system_initialized') else '否'}")
                print(f"   初始化状态: {data.get('init_status', 'unknown')}")
                print("=" * 50)
                print("🌐 请在浏览器中访问: http://localhost:5000")
                print("💡 提示:")
                print("   - 系统正在后台初始化，可能需要等待片刻才能使用查询功能")
                print("   - 可以先访问页面，稍后再尝试查询")
                return process, output_queue, output_thread
        except Exception as e:
            if waited_time % 5 == 0:  # 每5秒显示一次等待信息
                print(f"⏳ 等待服务器启动... ({waited_time}/{max_wait_time}秒)")
        
        time.sleep(check_interval)
        waited_time += check_interval
    
    print(f"❌ 服务器启动超时，已等待{max_wait_time}秒")
    print("请检查以下可能的问题:")
    print("1. Neo4j数据库是否正在运行")
    print("2. 环境变量是否正确配置")
    print("3. 网络连接是否正常")
    return None, None, None

if __name__ == "__main__":
    stop_existing_server()
    result = start_server()
    
    if result[0]:  # process不为None
        process, output_queue, output_thread = result
        try:
            print("\n📋 服务器运行日志:")
            print("-" * 50)
            # 保持脚本运行，显示服务器输出
            while True:
                try:
                    line = output_queue.get(timeout=1)
                    print(line)
                except Empty:
                    continue
        except KeyboardInterrupt:
            print("\n正在停止服务器...")
            process.terminate()
            print("服务器已停止")
    else:
        print("启动失败，请检查错误信息")