"""
GraphRAG Web界面
基于Flask的Web应用，提供图形化界面进行知识图谱问答
"""

import os
import sys
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from datetime import datetime
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.graph_rag_system import GraphRAGSystem, GraphRAGConfig

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__,
           template_folder='../templates',
           static_folder='../static')

# 使用应用上下文存储GraphRAG系统实例
rag_system = None

def get_rag_system():
    """获取或初始化GraphRAG系统"""
    global rag_system
    if rag_system is not None:
        return rag_system
    
    # 如果系统未初始化，尝试初始化
    if rag_system is None:
        logger.info("🔄 首次查询时初始化GraphRAG系统...")
        return init_rag_system()
    
    return None

def init_rag_system():
    """初始化GraphRAG系统"""
    global rag_system
    
    # 检查是否为快速启动模式
    fast_start = os.getenv('FAST_START', 'false').lower() == 'true'
    
    if fast_start:
        logger.info("🚀 快速启动模式：跳过系统初始化，将在首次查询时初始化")
        return None
    
    max_retries = 2  # 减少重试次数
    retry_delay = 1  # 减少重试延迟
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 尝试初始化GraphRAG系统 (第{attempt + 1}次)...")
            
            # 检查环境变量
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "aixi1314")
            api_key = os.getenv("ZHIPUAI_API_KEY", "your-zhipuai-api-key")
            api_model = os.getenv("ZHIPUAI_MODEL", "glm-4-flash")
            
            logger.info(f"📋 配置检查:")
            logger.info(f"  Neo4j URI: {neo4j_uri}")
            logger.info(f"  Neo4j User: {neo4j_user}")
            # 在生产环境中隐藏API密钥，仅在开发环境显示部分信息
            if os.getenv('FLASK_DEBUG', 'False').lower() == 'true':
                logger.info(f"  API Key: {api_key[:10]}..." if len(api_key) > 10 else "None")
            else:
                logger.info("  API Key: [REDACTED]")
            logger.info(f"  API Model: {api_model}")
            
            config = GraphRAGConfig(
                neo4j_uri=neo4j_uri,
                neo4j_auth=(neo4j_user, neo4j_password),
                openai_api_key=api_key,
                openai_model=api_model
            )
            
            rag_system = GraphRAGSystem(config)
            logger.info("✅ GraphRAG系统初始化完成")
            return rag_system
            
        except Exception as e:
            logger.error(f"❌ GraphRAG系统初始化失败 (第{attempt + 1}次): {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ {retry_delay}秒后重试...")
                import time
                time.sleep(retry_delay)
            else:
                logger.error("🚫 初始化失败，已达最大重试次数")
                logger.info("💡 提示: Web应用仍可启动，但查询功能可能受限")
                rag_system = None
                return None
    
    return None

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def query():
    """处理查询请求"""
    rag_system = get_rag_system()
    if not rag_system:
        return jsonify({
            "error": "GraphRAG系统未初始化",
            "answer": "系统初始化失败，请检查Neo4j数据库和智谱AI API配置"
        }), 503  # 使用503表示服务不可用
    
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                "error": "问题不能为空",
                "answer": "请输入您的问题"
            }), 400
        
        # 处理查询
        response = rag_system.query(question)
        
        # 返回结果
        result = {
            "question": response.get("question", question),
            "answer": response.get("answer", "未获取到答案"),
            "processing_time": response.get("processing_time", 0),
            "timestamp": response.get("timestamp", datetime.now().isoformat())
        }
        
        # 处理图数据
        if "graph_data" in response and response["graph_data"]:
            result["graph_data"] = {
                "nodes": response["graph_data"].get("nodes", [])[:10],  # 限制返回的节点数
                "relationships": response["graph_data"].get("relationships", [])[:10]  # 限制返回的关系数
            }
        
        return Response(
            response=json.dumps(result, ensure_ascii=False),
            status=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"查询处理失败: {e}")
        return jsonify({
            "error": str(e),
            "answer": "查询处理失败，请稍后再试"
        }), 500

@app.route('/api/graph_stats')
def graph_stats():
    """获取图统计信息"""
    rag_system = get_rag_system()
    if not rag_system:
        return jsonify({"error": "系统未初始化"}), 500
    
    try:
        stats = rag_system.retriever.get_graph_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/node_neighbors/<node_name>')
def node_neighbors(node_name):
    """获取节点邻居"""
    rag_system = get_rag_system()
    if not rag_system:
        return jsonify({"error": "系统未初始化"}), 500
    
    try:
        neighbors = rag_system.retriever.get_neighbors(node_name, depth=2)
        return jsonify({"neighbors": neighbors})
    except Exception as e:
        logger.error(f"获取节点邻居失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search_nodes')
def search_nodes():
    """搜索节点"""
    rag_system = get_rag_system()
    if not rag_system:
        return jsonify({"error": "系统未初始化"}), 500
    
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({"nodes": []})
        
        nodes = rag_system.retriever.keyword_search(query, limit=20)
        return jsonify({"nodes": nodes})
    except Exception as e:
        logger.error(f"搜索节点失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/export_graph', methods=['POST'])
def export_graph():
    """导出图谱数据"""
    rag_system = get_rag_system()
    if not rag_system:
        return jsonify({"error": "系统未初始化"}), 500
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "查询不能为空"}), 400
        
        # 获取完整的图数据（不限制节点数量）
        graph_data = rag_system.retriever.get_subgraph_by_query(query, limit=50)
        
        return jsonify({
            "graph_data": graph_data,
            "export_time": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"导出图谱失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def health_check():
    """健康检查端点"""
    rag_system = get_rag_system()
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_initialized": rag_system is not None,
        "init_status": "success" if rag_system else "failed"
    })

@app.route('/api/config')
def get_config():
    """获取前端配置"""
    return jsonify({
        "features": {
            "voice_input": True,
            "history": True,
            "export": True,
            "theme": True,
            "fullscreen": True
        },
        "limits": {
            "max_query_length": 1000,
            "max_history_items": 20
        }
    })

if __name__ == '__main__':
    # 初始化系统
    init_success = init_rag_system()
    if not init_success:
        logger.warning("⚠️ GraphRAG系统初始化失败，但Web应用仍可启动（部分功能受限）")
    
    # 创建模板目录
    try:
        if not os.path.exists('templates'):
            os.makedirs('templates')
            logger.info("✅ 创建模板目录成功")
    except Exception as e:
        logger.error(f"❌ 创建模板目录失败: {e}")
    
    # 创建静态文件目录
    try:
        if not os.path.exists('static'):
            os.makedirs('static')
            logger.info("✅ 创建静态文件目录成功")
    except Exception as e:
        logger.error(f"❌ 创建静态文件目录失败: {e}")
    
    # 启动Web应用
    app.run(debug=False, host='0.0.0.0', port=5000)
