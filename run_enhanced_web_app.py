"""
启动增强版GraphRAG Web应用（带技能验证）
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    logger.info("🚀 启动增强版GraphRAG Web应用（带技能验证）")
    
    # 检查环境变量
    api_key = os.getenv("ZHIPUAI_API_KEY")
    if not api_key or api_key == "your-zhipuai-api-key":
        logger.warning("⚠️ 警告: 未检测到有效的API密钥")
        logger.warning("请设置环境变量 ZHIPUAI_API_KEY")
        logger.warning("部分功能可能无法正常工作")
    
    # 检查技能验证配置
    enable_validation = os.getenv("ENABLE_SKILL_VALIDATION", "true").lower() == "true"
    if enable_validation:
        logger.info("✅ 技能验证已启用")
        logger.info(f"   最小验证置信度: {os.getenv('MIN_VALIDATION_CONFIDENCE', '0.6')}")
        logger.info(f"   自动过滤无效项目: {os.getenv('AUTO_FILTER_INVALID', 'true')}")
        logger.info(f"   验证失败重试: {os.getenv('RETRY_ON_VALIDATION_FAILURE', 'true')}")
        logger.info(f"   反馈学习: {os.getenv('ENABLE_FEEDBACK_LEARNING', 'true')}")
    else:
        logger.info("⚠️ 技能验证已禁用")
    
    # 导入并运行Web应用
    try:
        from web.enhanced_graph_rag_web import app
        
        # 设置端口
        port = int(os.getenv("PORT", 5000))
        host = os.getenv("HOST", "0.0.0.0")
        debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
        
        logger.info(f"🌐 Web应用将在 http://{host}:{port} 启动")
        logger.info("📚 功能特性:")
        logger.info("   - 知识图谱问答")
        logger.info("   - 知识点提取")
        logger.info("   - 技能验证" if enable_validation else "   - 基础提取")
        logger.info("   - 反馈学习" if enable_validation else "")
        logger.info("   - 图谱可视化")
        logger.info("   - 数据导出")
        
        # 启动应用
        app.run(debug=debug, host=host, port=port)
        
    except ImportError as e:
        logger.error(f"❌ 导入失败: {e}")
        logger.error("请确保所有依赖项已正确安装")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()