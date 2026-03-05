"""
知识点提取算法与Web应用集成示例
展示如何将KnowledgeExtractor集成到现有的Flask Web应用中
"""

from flask import Flask, request, jsonify, render_template_string
import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(__file__))

from knowledge_extraction import KnowledgeExtractor, KnowledgeExtractionConfig

# 创建Flask应用
app = Flask(__name__)

# 全局变量存储提取器实例
extractor = None

def init_extractor():
    """初始化知识点提取器"""
    global extractor
    if extractor is None:
        config = KnowledgeExtractionConfig(
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_auth=(
                os.getenv("NEO4J_USER", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "aixi1314")
            ),
            openai_api_key=os.getenv("ZHIPUAI_API_KEY", "b5d49df99d88433e944ff84304d3105a.Jk57Qbo2dHO56AKS"),
            openai_model=os.getenv("ZHIPUAI_MODEL", "glm-4-flash"),
            confidence_threshold=0.6
        )
        extractor = KnowledgeExtractor(config)
    return extractor

@app.route('/')
def index():
    """主页"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>计算机网络知识点提取系统</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            textarea { width: 100%; height: 200px; margin: 10px 0; }
            button { padding: 10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
            button:hover { background-color: #45a049; }
            .result { margin-top: 20px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .keyword { margin: 5px 0; padding: 5px; background-color: #f0f0f0; border-radius: 3px; }
            .relationship { margin: 5px 0; padding: 5px; background-color: #e8f4fd; border-radius: 3px; }
            .stats { margin-top: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>计算机网络知识点提取系统</h1>
            <p>输入计算机网络课程内容，系统将自动提取知识点关键字及其关系。</p>
            
            <form id="extractForm">
                <label for="content">课程内容:</label><br>
                <textarea id="content" name="content" placeholder="请输入计算机网络课程内容...">TCP/IP协议栈是互联网的核心协议族，包括应用层、传输层、网络层和链路层。

传输控制协议(TCP)是一种面向连接的、可靠的传输层协议，它通过三次握手建立连接，通过四次挥手断开连接。

用户数据报协议(UDP)是一种无连接的传输层协议，它不保证数据可靠传输，但具有低延迟的特点。</textarea>
                <br>
                <button type="submit">提取知识点</button>
            </form>
            
            <div id="result" class="result" style="display: none;">
                <h3>提取结果</h3>
                <div id="keywords"></div>
                <div id="relationships"></div>
                <div id="stats"></div>
            </div>
        </div>
        
        <script>
            document.getElementById('extractForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const content = document.getElementById('content').value;
                const resultDiv = document.getElementById('result');
                const keywordsDiv = document.getElementById('keywords');
                const relationshipsDiv = document.getElementById('relationships');
                const statsDiv = document.getElementById('stats');
                
                // 显示加载状态
                resultDiv.style.display = 'block';
                keywordsDiv.innerHTML = '<p>正在提取知识点...</p>';
                relationshipsDiv.innerHTML = '';
                statsDiv.innerHTML = '';
                
                // 发送请求
                fetch('/extract', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ content: content })
                })
                .then(response => response.json())
                .then(data => {
                    // 显示关键字
                    keywordsDiv.innerHTML = '<h4>知识点关键字:</h4>';
                    data.keywords.forEach(kw => {
                        const keywordDiv = document.createElement('div');
                        keywordDiv.className = 'keyword';
                        keywordDiv.innerHTML = `<strong>${kw.name}</strong> (${kw.type}, 置信度: ${kw.confidence.toFixed(2)})`;
                        keywordsDiv.appendChild(keywordDiv);
                    });
                    
                    // 显示关系
                    relationshipsDiv.innerHTML = '<h4>知识点关系:</h4>';
                    data.relationships.forEach(rel => {
                        const relDiv = document.createElement('div');
                        relDiv.className = 'relationship';
                        relDiv.innerHTML = `<strong>${rel.source.name}</strong> --[${rel.type}]--> <strong>${rel.target.name}</strong> (置信度: ${rel.confidence.toFixed(2)})`;
                        relationshipsDiv.appendChild(relDiv);
                    });
                    
                    // 显示统计信息
                    statsDiv.innerHTML = '<h4>统计信息:</h4>';
                    statsDiv.innerHTML += `<div class="stats">内容长度: ${data.content_length} 字符</div>`;
                    statsDiv.innerHTML += `<div class="stats">提取关键字: ${data.keywords.length} 个</div>`;
                    statsDiv.innerHTML += `<div class="stats">提取关系: ${data.relationships.length} 个</div>`;
                    
                    if (data.stats) {
                        statsDiv.innerHTML += `<div class="stats">创建节点: ${data.stats.nodes_created || 0} 个</div>`;
                        statsDiv.innerHTML += `<div class="stats">更新节点: ${data.stats.nodes_updated || 0} 个</div>`;
                        statsDiv.innerHTML += `<div class="stats">创建关系: ${data.stats.relationships_created || 0} 个</div>`;
                        statsDiv.innerHTML += `<div class="stats">错误数量: ${data.stats.errors || 0} 个</div>`;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    keywordsDiv.innerHTML = '<p style="color: red;">提取失败: ' + error.message + '</p>';
                });
            });
        </script>
    </body>
    </html>
    """
    return html_template

@app.route('/extract', methods=['POST'])
def extract_knowledge():
    """提取知识点API"""
    try:
        # 获取请求内容
        data = request.get_json()
        content = data.get('content', '')
        
        if not content.strip():
            return jsonify({'error': '内容不能为空'}), 400
        
        # 初始化提取器
        extractor_instance = init_extractor()
        
        # 处理内容
        result = extractor_instance.process_course_content(content, save_to_graph=True)
        
        # 返回结果
        return jsonify({
            'keywords': result['keywords'],
            'relationships': result['relationships'],
            'stats': result['stats'],
            'content_length': result['content_length']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/extract_file', methods=['POST'])
def extract_from_file():
    """从文件提取知识点API"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'error': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 读取文件内容
        content = file.read().decode('utf-8')
        
        # 初始化提取器
        extractor_instance = init_extractor()
        
        # 处理内容
        result = extractor_instance.process_course_content(content, save_to_graph=True)
        
        # 返回结果
        return jsonify({
            'keywords': result['keywords'],
            'relationships': result['relationships'],
            'stats': result['stats'],
            'content_length': result['content_length'],
            'filename': file.filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """健康检查"""
    try:
        # 初始化提取器
        extractor_instance = init_extractor()
        # 检查Neo4j连接
        stats = extractor_instance.retriever.get_graph_stats()
        return jsonify({
            'status': 'healthy',
            'neo4j_connected': True,
            'graph_stats': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # 初始化提取器
    init_extractor()
    
    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=5001)  # 使用不同端口避免冲突