"""
增强版GraphRAG Web界面 - 集成基于技能的知识验证系统
基于Flask的Web应用，提供图形化界面进行知识图谱问答和高质量知识点提取
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
from src.knowledge_extraction import KnowledgeExtractor, KnowledgeExtractionConfig
from src.enhanced_knowledge_extraction import EnhancedKnowledgeExtractor, EnhancedExtractionConfig

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 获取项目根目录的绝对路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_folder = os.path.join(project_root, 'templates')
static_folder = os.path.join(project_root, 'static')

app = Flask(__name__,
           template_folder=template_folder,
           static_folder=static_folder)

# 使用应用上下文存储系统实例
rag_system = None
knowledge_extractor = None
enhanced_knowledge_extractor = None

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

def get_knowledge_extractor():
    """获取或初始化知识点提取器"""
    global knowledge_extractor
    if knowledge_extractor is not None:
        return knowledge_extractor
    
    # 如果提取器未初始化，尝试初始化
    if knowledge_extractor is None:
        logger.info("🔄 首次提取时初始化知识点提取器...")
        return init_knowledge_extractor()
    
    return None

def get_enhanced_knowledge_extractor():
    """获取或初始化增强版知识点提取器"""
    global enhanced_knowledge_extractor
    if enhanced_knowledge_extractor is not None:
        return enhanced_knowledge_extractor
    
    # 如果提取器未初始化，尝试初始化
    if enhanced_knowledge_extractor is None:
        logger.info("🔄 首次提取时初始化增强版知识点提取器...")
        return init_enhanced_knowledge_extractor()
    
    return None

def init_rag_system():
    """初始化GraphRAG系统"""
    global rag_system
    
    # 检查是否为快速启动模式
    fast_start = os.getenv('FAST_START', 'false').lower() == 'true'
    
    if fast_start:
        logger.info("🚀 快速启动模式：跳过系统初始化，将在首次查询时初始化")
        return None
    
    max_retries = 2
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 尝试初始化GraphRAG系统 (第{attempt + 1}次)...")
            
            # 检查环境变量
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "aixi1314")
            api_key = os.getenv("ZHIPUAI_API_KEY", "")
            api_model = os.getenv("ZHIPUAI_MODEL", "glm-4-flash")
            
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

def init_knowledge_extractor():
    """初始化基础知识点提取器"""
    global knowledge_extractor
    
    try:
        logger.info("🔄 初始化基础知识点提取器...")
        
        # 检查环境变量
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "aixi1314")
        api_key = os.getenv("ZHIPUAI_API_KEY", "")
        api_model = os.getenv("ZHIPUAI_MODEL", "glm-4-flash")
        
        config = KnowledgeExtractionConfig(
            neo4j_uri=neo4j_uri,
            neo4j_auth=(neo4j_user, neo4j_password),
            openai_api_key=api_key,
            openai_model=api_model,
            confidence_threshold=0.6
        )
        
        knowledge_extractor = KnowledgeExtractor(config)
        logger.info("✅ 基础知识点提取器初始化完成")
        return knowledge_extractor
        
    except Exception as e:
        logger.error(f"❌ 基础知识点提取器初始化失败: {e}")
        knowledge_extractor = None
        return None

def init_enhanced_knowledge_extractor():
    """初始化增强版知识点提取器（带技能验证）"""
    global enhanced_knowledge_extractor
    
    try:
        logger.info("🔄 初始化增强版知识点提取器（带技能验证）...")
        
        # 检查环境变量
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "aixi1314")
        api_key = os.getenv("ZHIPUAI_API_KEY", "")
        api_model = os.getenv("ZHIPUAI_MODEL", "glm-4-flash")
        
        # 检查是否启用验证
        enable_validation = os.getenv("ENABLE_SKILL_VALIDATION", "true").lower() == "true"
        
        config = EnhancedExtractionConfig(
            neo4j_uri=neo4j_uri,
            neo4j_auth=(neo4j_user, neo4j_password),
            openai_api_key=api_key,
            openai_model=api_model,
            confidence_threshold=0.6,
            
            # 验证配置
            enable_validation=enable_validation,
            min_validation_confidence=float(os.getenv("MIN_VALIDATION_CONFIDENCE", "0.6")),
            auto_filter_invalid=os.getenv("AUTO_FILTER_INVALID", "true").lower() == "true",
            retry_on_validation_failure=os.getenv("RETRY_ON_VALIDATION_FAILURE", "true").lower() == "true",
            
            # 反馈学习配置
            enable_feedback_learning=os.getenv("ENABLE_FEEDBACK_LEARNING", "true").lower() == "true"
        )
        
        enhanced_knowledge_extractor = EnhancedKnowledgeExtractor(config)
        
        if enable_validation:
            logger.info("✅ 增强版知识点提取器初始化完成（技能验证已启用）")
        else:
            logger.info("✅ 增强版知识点提取器初始化完成（技能验证已禁用）")
            
        return enhanced_knowledge_extractor
        
    except Exception as e:
        logger.error(f"❌ 增强版知识点提取器初始化失败: {e}")
        enhanced_knowledge_extractor = None
        return None

@app.route('/')
def index():
    """主页"""
    return render_template('integrated_index.html')

@app.route('/api/query', methods=['POST'])
def query():
    """处理查询请求"""
    rag_system = get_rag_system()
    if not rag_system:
        return jsonify({
            "error": "GraphRAG系统未初始化",
            "answer": "系统初始化失败，请检查Neo4j数据库和智谱AI API配置"
        }), 503
    
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
                "nodes": response["graph_data"].get("nodes", [])[:10],
                "relationships": response["graph_data"].get("relationships", [])[:10]
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

@app.route('/api/extract_knowledge', methods=['POST'])
def extract_knowledge():
    """提取知识点API（带技能验证）"""
    # 优先使用增强版提取器
    enhanced_extractor = get_enhanced_knowledge_extractor()
    use_enhanced = enhanced_extractor is not None
    
    # 如果增强版不可用，回退到基础版
    if not use_enhanced:
        knowledge_extractor = get_knowledge_extractor()
        if not knowledge_extractor:
            return jsonify({
                "error": "知识点提取器未初始化",
                "message": "系统初始化失败，请检查Neo4j数据库配置"
            }), 503
    
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        use_validation = data.get('use_validation', True)  # 允许前端选择是否使用验证
        
        if not content:
            return jsonify({
                "error": "内容不能为空",
                "message": "请输入要提取的文档内容"
            }), 400
        
        # 处理内容并保存到Neo4j
        logger.info(f"🔄 开始提取知识点，内容长度: {len(content)} 字符")
        logger.info(f"📊 使用{'增强版' if use_enhanced else '基础版'}提取器")
        
        if use_enhanced and use_validation:
            # 使用增强版提取器（带验证）
            try:
                result = enhanced_extractor.process_course_content_with_validation(content, save_to_graph=True)
                
                # 添加验证统计信息
                validation_stats = result.get('validation_stats', {})
                valid_keywords = [kw for kw in result.get('keywords', []) if kw.get('validation', {}).get('is_valid', False)]
                valid_relationships = [rel for rel in result.get('relationships', []) if rel.get('validation', {}).get('is_valid', False)]
                
                # 构建详细消息
                message_parts = []
                
                stats = result.get('stats', {})
                if stats.get('nodes_created', 0) > 0:
                    message_parts.append(f"创建了 {stats['nodes_created']} 个新节点")
                
                if stats.get('nodes_updated', 0) > 0:
                    message_parts.append(f"更新了 {stats['nodes_updated']} 个现有节点")
                
                if stats.get('relationships_created', 0) > 0:
                    message_parts.append(f"创建了 {stats['relationships_created']} 个新关系")
                
                if stats.get('errors', 0) > 0:
                    message_parts.append(f"遇到 {stats['errors']} 个错误")
                
                # 添加验证信息
                if validation_stats.get('total_validations', 0) > 0:
                    message_parts.append(f"验证了 {validation_stats.get('total_validations', 0)} 个项目")
                    message_parts.append(f"通过率 {validation_stats.get('validity_rate', 0):.1%}")
                
                if not message_parts:
                    message_parts.append("没有检测到新的知识点或关系")
                
                detailed_message = "知识点提取完成（已验证）：" + "，".join(message_parts)
                
                # 添加解释
                explanation = ""
                if stats.get('nodes_created', 0) == 0 and stats.get('nodes_updated', 0) > 0:
                    explanation = "💡 提示：提取的关键词已存在于数据库中，因此更新了现有节点而不是创建新节点。"
                
                if len(valid_keywords) < len(result.get('keywords', [])):
                    explanation += f"\n🔍 经过技能验证，过滤了 {len(result.get('keywords', [])) - len(valid_keywords)} 个无效知识点。"
                
                if len(valid_relationships) < len(result.get('relationships', [])):
                    explanation += f"\n🔍 经过技能验证，过滤了 {len(result.get('relationships', [])) - len(valid_relationships)} 个无效关系。"
                
                # 返回增强版结果
                response_data = {
                    "success": True,
                    "keywords": result.get('keywords', []),
                    "relationships": result.get('relationships', []),
                    "valid_keywords": valid_keywords,
                    "valid_relationships": valid_relationships,
                    "stats": stats,
                    "validation_stats": validation_stats,
                    "content_length": result.get('content_length', 0),
                    "message": detailed_message,
                    "explanation": explanation,
                    "summary": f"提取了 {len(result.get('keywords', []))} 个关键字和 {len(result.get('relationships', []))} 个关系（有效：{len(valid_keywords)} 个关键字，{len(valid_relationships)} 个关系）",
                    "extraction_mode": "enhanced_with_validation"
                }
            except Exception as e:
                logger.error(f"增强版提取失败: {e}")
                # 回退到基础版提取
                use_enhanced = False
            
        else:
            # 使用基础版提取器
            try:
                result = knowledge_extractor.process_course_content(content, save_to_graph=True)
                
                # 构建详细消息
                message_parts = []
                
                stats = result.get('stats', {})
                if stats.get('nodes_created', 0) > 0:
                    message_parts.append(f"创建了 {stats['nodes_created']} 个新节点")
                
                if stats.get('nodes_updated', 0) > 0:
                    message_parts.append(f"更新了 {stats['nodes_updated']} 个现有节点")
                
                if stats.get('relationships_created', 0) > 0:
                    message_parts.append(f"更新了 {stats['relationships_created']} 个新关系")
                
                if stats.get('errors', 0) > 0:
                    message_parts.append(f"遇到 {stats['errors']} 个错误")
                
                if not message_parts:
                    message_parts.append("没有检测到新的知识点或关系")
                
                detailed_message = "知识点提取完成：" + "，".join(message_parts)
                
                # 添加解释
                explanation = ""
                if stats.get('nodes_created', 0) == 0 and stats.get('nodes_updated', 0) > 0:
                    explanation = "💡 提示：提取的关键词已存在于数据库中，因此更新了现有节点而不是创建新节点。"
                
                if use_enhanced and not use_validation:
                    explanation += "\n⚠️ 技能验证已禁用，建议启用以提高提取质量。"
                
                # 返回基础版结果
                response_data = {
                    "success": True,
                    "keywords": result.get('keywords', []),
                    "relationships": result.get('relationships', []),
                    "stats": stats,
                    "content_length": result.get('content_length', 0),
                    "message": detailed_message,
                    "explanation": explanation,
                    "summary": f"提取了 {len(result.get('keywords', []))} 个关键字和 {len(result.get('relationships', []))} 个关系",
                    "extraction_mode": "basic"
                }
            except Exception as e:
                logger.error(f"基础版提取失败: {e}")
                # 如果两种提取方式都失败，返回错误
                return jsonify({
                    "error": str(e),
                    "message": "知识点提取失败，请检查输入内容或稍后再试"
                }), 500
        
        logger.info(f"✅ 知识点提取完成: {response_data['message']}")
        return jsonify(response_data)
        
    except Exception as e:
            logger.error(f"❌ 知识点提取失败: {e}")
            return jsonify({
                "error": str(e),
                "message": "知识点提取失败，请稍后再试"
            }), 500

@app.route('/api/submit_feedback', methods=['POST'])
def submit_feedback():
    """提交反馈API"""
    enhanced_extractor = get_enhanced_knowledge_extractor()
    if not enhanced_extractor or not enhanced_extractor.config.enable_feedback_learning:
        return jsonify({
            "error": "反馈功能未启用",
            "message": "反馈学习功能未启用或系统未初始化"
        }), 503
    
    try:
        data = request.get_json()
        item_type = data.get('item_type', '')  # 'knowledge' 或 'relationship'
        item = data.get('item', {})
        is_correct = data.get('is_correct', False)
        correction = data.get('correction', {})
        
        if not item_type or not item:
            return jsonify({
                "error": "参数不完整",
                "message": "请提供完整的反馈信息"
            }), 400
        
        # 提�交反馈
        enhanced_extractor.submit_feedback(item_type, item, is_correct, correction)
        
        # 获取反馈摘要
        feedback_summary = enhanced_extractor.get_feedback_summary()
        
        return jsonify({
            "success": True,
            "message": "反馈提交成功",
            "feedback_summary": feedback_summary
        })
        
    except Exception as e:
            logger.error(f"❌ 反馈提交失败: {e}")
            return jsonify({
                "error": str(e),
                "message": "反馈提交失败，请稍后再试"
            }), 500

@app.route('/api/validation_stats')
def get_validation_stats():
    """获取验证统计信息"""
    enhanced_extractor = get_enhanced_knowledge_extractor()
    if not enhanced_extractor or not enhanced_extractor.validation_system:
        return jsonify({
            "error": "验证系统未启用",
            "message": "技能验证系统未启用或未初始化"
        }), 503
    
    try:
        stats = enhanced_extractor.validation_system.get_validation_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"❌ 获取验证统计失败: {e}")
        return jsonify({
            "error": str(e),
            "message": "获取验证统计失败"
        }), 500

@app.route('/api/config')
def get_config():
    """获取前端配置"""
    # 检查是否启用了技能验证
    enhanced_extractor = get_enhanced_knowledge_extractor()
    skill_validation_enabled = enhanced_extractor is not None and enhanced_extractor.config.enable_validation
    
    return jsonify({
        "features": {
            "voice_input": True,
            "history": True,
            "export": True,
            "theme": True,
            "fullscreen": True,
            "knowledge_extraction": True,  # 知识点提取功能
            "skill_validation": skill_validation_enabled,  # 技能验证功能
            "feedback_learning": enhanced_extractor.config.enable_feedback_learning if enhanced_extractor else False
        },
        "limits": {
            "max_query_length": 1000,
            "max_history_items": 20,
            "max_content_length": 10000  # 内容长度限制
        },
        "validation": {
            "enabled": skill_validation_enabled,
            "min_confidence": enhanced_extractor.config.min_validation_confidence if enhanced_extractor else 0.6,
            "auto_filter": enhanced_extractor.config.auto_filter_invalid if enhanced_extractor else True
        }
    })

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
    enhanced_extractor = get_enhanced_knowledge_extractor()
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_initialized": rag_system is not None,
        "enhanced_extractor_initialized": enhanced_extractor is not None,
        "skill_validation_enabled": enhanced_extractor.config.enable_validation if enhanced_extractor else False
    })

def main():
    """主函数"""
    # 初始化系统
    init_success = init_rag_system()
    if not init_success:
        logger.warning("⚠️ GraphRAG系统初始化失败，但Web应用仍可启动（部分功能受限）")
    
    # 初始化增强版知识点提取器
    enhanced_init_success = init_enhanced_knowledge_extractor()
    if not enhanced_init_success:
        logger.warning("⚠️ 增强版知识点提取器初始化失败，将回退到基础版提取器")
    
    # 创建模板目录
    try:
        if not os.path.exists(template_folder):
            os.makedirs(template_folder)
            logger.info("✅ 创建模板目录成功")
    except Exception as e:
        logger.error(f"❌ 创建模板目录失败: {e}")
    
    # 创建静态文件目录
    try:
        if not os.path.exists(static_folder):
            os.makedirs(static_folder)
            logger.info("✅ 创建静态文件目录成功")
    except Exception as e:
        logger.error(f"❌ 创建静态文件目录失败: {e}")
    
    # 启动Web应用
    logger.info("🚀 启动增强版GraphRAG Web应用（带技能验证）")
    app.run(debug=False, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
