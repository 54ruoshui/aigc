"""
计算机网络知识图谱GraphRAG系统
基于Neo4j图数据库和大模型的智能问答系统
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions
import requests
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
from src.cache import query_cache
from .enhanced_prompt_engineering import EnhancedPromptEngineering, PromptEngineeringConfig

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GraphRAGConfig:
    """GraphRAG系统配置"""
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_auth: Tuple[str, str] = ("neo4j", "aixi1314")
    openai_api_key: str = os.getenv("ZHIPUAI_API_KEY", "b5d49df99d88433e944ff84304d3105a.Jk57Qbo2dHO56AKS")
    openai_model: str = "glm-4-flash"
    max_context_length: int = 4000  # 最大上下文长度
    max_retrieved_nodes: int = 20   # 最大检索节点数
    similarity_threshold: float = 0.7  # 相似度阈值

class GraphRetriever:
    """图数据检索器"""
    
    def __init__(self, uri: str, auth: Tuple[str, str]):
        self.driver = None
        try:
            # 简化连接参数，避免版本兼容性问题
            self.driver = GraphDatabase.driver(
                uri,
                auth=auth
            )
            # 设置验证连接
            self.driver.verify_connectivity()
            logger.info("✅ 成功连接Neo4j数据库")
        except exceptions.AuthError as e:
            logger.error(f"❌ 认证失败：{e}")
            raise
        except exceptions.Neo4jError as e:
            logger.error(f"❌ 连接失败：{e}")
            raise
        except Exception as e:
            logger.error(f"❌ 连接异常：{e}")
            # 尝试不带数据库参数的连接
            try:
                self.driver = GraphDatabase.driver(
                    uri,
                    auth=auth
                )
                # 测试基本连接
                with self.driver.session() as session:
                    session.run("RETURN 1")
                logger.info("✅ 成功连接Neo4j数据库（备用方式）")
            except Exception as e2:
                logger.error(f"❌ Neo4j连接完全失败: {e2}")
                raise
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info("🔌 已关闭Neo4j连接")
    
    def keyword_search(self, query: str, limit: int = 10) -> List[Dict]:
        """关键词搜索"""
        # 检查缓存
        cached_result = query_cache.get_graph_data("keyword_search", {"query": query, "limit": limit})
        if cached_result is not None:
            logger.info(f"🎯 缓存命中: 关键词搜索 '{query}'")
            return cached_result
        
        # 防止注入，只允许字母数字和中文
        safe_query = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', query)
        if not safe_query:
            return []
            
        # 使用参数化查询，避免SQL注入，并支持大小写不敏感
        # 修复：使用正则表达式实现不区分大小写的搜索，避免对数组属性使用toString()
        cypher = """
        MATCH (n)
        WHERE (n.name IS NOT NULL AND n.name =~ $query_regex)
           OR (n.description IS NOT NULL AND n.description =~ $query_regex)
           OR (n.full_name IS NOT NULL AND n.full_name =~ $query_regex)
        RETURN n, labels(n) as types
        LIMIT $limit
        """
        # 准备正则表达式参数（不区分大小写）
        query_regex = f"(?i).*{safe_query}.*"
        with self.driver.session() as session:
            result = session.run(cypher, {"query_regex": query_regex, "limit": limit})
            nodes = []
            for record in result:
                node_data = dict(record["n"])
                # 处理labels，确保是字符串类型
                types = record["types"]
                if isinstance(types, list) and types:
                    node_type = types[0]
                else:
                    node_type = str(types) if types else "Unknown"
                node_data["type"] = node_type
                nodes.append(node_data)
            
            # 缓存结果
            query_cache.cache_graph_data("keyword_search", nodes, ttl=1800, params={"query": query, "limit": limit})
            return nodes
    
    def semantic_search(self, query: str, limit: int = 10) -> List[Dict]:
        """语义搜索（基于向量相似度）"""
        # 注意：这需要Neo4j支持向量插件或预先计算的嵌入
        cypher = """
        MATCH (n)
        WHERE n.description IS NOT NULL
        WITH n, gds.similarity.cosine(n.embedding, $query_embedding) as similarity
        WHERE similarity > $threshold
        RETURN n, labels(n) as types, similarity
        ORDER BY similarity DESC
        LIMIT $limit
        """
        # 这里需要先计算query_embedding
        # 暂时使用关键词搜索替代
        return self.keyword_search(query, limit)
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """获取图统计信息"""
        stats = {}
        cypher_queries = {
            "totalNodes": "MATCH (n) RETURN count(n) as count",
            "totalRelationships": "MATCH ()-[r]->() RETURN count(r) as count",
            "nodeTypes": "MATCH (n) RETURN DISTINCT labels(n) as types",
            "relationshipTypes": "MATCH ()-[r]->() RETURN DISTINCT type(r) as types"
        }
        
        with self.driver.session() as session:
            for key, cypher in cypher_queries.items():
                try:
                    result = session.run(cypher)
                    if key in ["totalNodes", "totalRelationships"]:
                        stats[key] = result.single()["count"]
                    else:
                        stats[key] = []
                        for record in result:
                            types = record["types"]
                            if isinstance(types, list) and types:
                                stats[key].append(types[0])
                            else:
                                stats[key].append(str(types) if types else "Unknown")
                except Exception as e:
                    logger.warning(f"获取统计信息 {key} 失败: {e}")
                    stats[key] = 0 if "total" in key else []
        
        return stats
    
    def get_neighbors(self, node_name: str, depth: int = 2) -> List[Dict]:
        """获取节点的邻居"""
        # 检查缓存
        cached_result = query_cache.get_graph_data("neighbors", {"node_name": node_name, "depth": depth})
        if cached_result is not None:
            logger.info(f"🎯 缓存命中: 节点邻居 '{node_name}'")
            return cached_result
        
        # 修复Neo4j参数化查询问题和变量长度路径问题
        if depth == 1:
            cypher = """
            MATCH (start {name: $node_name})-[r]-(neighbor)
            RETURN DISTINCT neighbor, labels(neighbor) as types, 1 as distance
            ORDER BY labels(neighbor)[0]
            LIMIT 50
            """
        elif depth == 2:
            cypher = """
            MATCH path = (start {name: $node_name})-[*1..2]-(neighbor)
            RETURN DISTINCT neighbor, labels(neighbor) as types, length(path) as distance
            ORDER BY distance, labels(neighbor)[0]
            LIMIT 50
            """
        else:
            # 对于其他深度值，使用动态构建查询
            cypher = f"""
            MATCH path = (start {{name: $node_name}})-[*1..{depth}]-(neighbor)
            RETURN DISTINCT neighbor, labels(neighbor) as types, length(path) as distance
            ORDER BY distance, labels(neighbor)[0]
            LIMIT 50
            """
            
        with self.driver.session() as session:
            result = session.run(cypher, {"node_name": node_name})
            neighbors = []
            for record in result:
                neighbor_data = dict(record["neighbor"])
                # 处理types，确保是字符串类型
                types = record["types"]
                if isinstance(types, list) and types:
                    neighbor_type = types[0]
                else:
                    neighbor_type = str(types) if types else "Unknown"
                neighbor_data["type"] = neighbor_type
                neighbor_data["distance"] = record["distance"]
                neighbors.append(neighbor_data)
            
            # 缓存结果
            query_cache.cache_graph_data("neighbors", neighbors, ttl=2400, params={"node_name": node_name, "depth": depth})
            return neighbors
    
    def get_path_between_nodes(self, start: str, end: str, max_depth: int = 3) -> List[Dict]:
        """获取两个节点之间的路径"""
        # 检查缓存
        cached_result = query_cache.get_graph_data("path", {"start": start, "end": end, "max_depth": max_depth})
        if cached_result is not None:
            logger.info(f"🎯 缓存命中: 路径搜索 '{start}' -> '{end}'")
            return cached_result
        
        # 修复Neo4j参数化查询问题
        cypher = f"""
        MATCH path = shortestPath((start {{name: $start}})-[*1..{max_depth}]-(end {{name: $end}}))
        RETURN path, length(path) as path_length
        ORDER BY path_length
        LIMIT 5
        """
        with self.driver.session() as session:
            result = session.run(cypher, {"start": start, "end": end})
            paths = []
            for record in result:
                path_info = {
                    "path_length": record["path_length"],
                    "nodes": [],
                    "relationships": []
                }
                for node in record["path"].nodes:
                    path_info["nodes"].append(dict(node))
                for rel in record["path"].relationships:
                    path_info["relationships"].append({
                        "type": rel.type,
                        "start": dict(rel.start_node)["name"],
                        "end": dict(rel.end_node)["name"]
                    })
                paths.append(path_info)
            
            # 缓存结果
            query_cache.cache_graph_data("path", paths, ttl=3000, params={"start": start, "end": end, "max_depth": max_depth})
            return paths
    
    def get_subgraph_by_query(self, query: str, limit: int = 20) -> Dict:
        """根据查询获取子图"""
        # 首先找到相关节点
        nodes = self.keyword_search(query, limit)
        if not nodes:
            return {"nodes": [], "relationships": []}
        
        # 获取这些节点之间的关系
        node_names = [node["name"] for node in nodes]
        cypher = """
        MATCH (n1)-[r]-(n2)
        WHERE n1.name IN $node_names AND n2.name IN $node_names
        RETURN n1, r, n2
        """
        with self.driver.session() as session:
            result = session.run(cypher, {"node_names": node_names})
            relationships = []
            for record in result:
                relationships.append({
                    "type": record["r"].type,
                    "start": dict(record["n1"]),
                    "end": dict(record["n2"])
                })
        
        return {"nodes": nodes, "relationships": relationships}

class LLMGenerator:
    """大模型生成器"""
    
    def __init__(self, api_key: str, model: str = "glm-4-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        # 初始化增强的提示工程系统
        prompt_config = PromptEngineeringConfig(
            openai_api_key=api_key,
            openai_model=model,
            openai_base_url="https://open.bigmodel.cn/api/paas/v4",
            strict_mode=True,
            require_evidence=True,
            min_confidence_threshold=0.7,
            max_hallucination_risk=0.3
        )
        self.prompt_engineering = EnhancedPromptEngineering(prompt_config)
    
    def format_context(self, graph_data: Dict) -> str:
        """格式化图数据为上下文"""
        context_parts = []
        
        # 格式化节点信息
        if graph_data.get("nodes"):
            context_parts.append("相关实体：")
            for node in graph_data["nodes"][:10]:  # 限制节点数量
                node_info = f"- {node.get('type', 'Unknown')}: {node.get('name', 'Unknown')}"
                if node.get('description'):
                    node_info += f" ({node['description'][:100]}...)"
                context_parts.append(node_info)
        
        # 格式化关系信息
        if graph_data.get("relationships"):
            context_parts.append("\n相关关系：")
            for rel in graph_data["relationships"][:10]:  # 限制关系数量
                rel_info = f"- {rel['start']['name']} --[{rel['type']}]--> {rel['end']['name']}"
                context_parts.append(rel_info)
        
        # 格式化路径信息
        if graph_data.get("paths"):
            context_parts.append("\n相关路径：")
            for path in graph_data["paths"][:3]:  # 限制路径数量
                path_str = " -> ".join([node["name"] for node in path["nodes"]])
                context_parts.append(f"- 路径: {path_str}")
        
        return "\n".join(context_parts)
    
    def generate_answer(self, question: str, context: str) -> str:
        """使用增强的提示工程生成答案"""
        try:
            # 构建增强的答案生成提示
            system_prompt = f"""你是一个计算机网络领域的专家，基于提供的知识图谱信息回答用户问题。

# 严格约束
1. 必须仅基于提供的上下文信息回答问题，不允许使用外部知识
2. 如果上下文信息不足，必须明确说明并提供原因
3. 回答必须准确、专业、易懂，避免模糊不清的表达
4. 可以适当扩展解释，但必须基于上下文中的事实
5. 使用中文回答，语言要流畅自然
6. 不允许编造或推测上下文中没有的信息

# 证据要求
1. 回答中的每个关键点都必须有上下文证据支持
2. 引用具体的实体、关系或路径作为证据
3. 如果信息不确定，必须明确指出不确定性程度
4. 对于技术性内容，确保术语使用准确

# 领域知识库参考
以下是计算机网络领域的标准知识点，请参考这些标准来验证答案的准确性：
{json.dumps(self.prompt_engineering.domain_knowledge_base, ensure_ascii=False, indent=2)}

# 风险控制
1. 幻觉风险评估：确保答案不包含上下文中没有的信息
2. 逻辑一致性检查：确保答案内部逻辑一致
3. 领域一致性检查：确保答案符合计算机网络领域的基本原理

# 输出格式要求
1. 提供清晰、结构化的答案
2. 使用适当的标题和分段
3. 在关键信息后提供证据引用
4. 如果信息不足，明确说明缺少哪些信息

上下文信息：
"""
            
            user_prompt = f"""
用户问题：{question}

请基于以上上下文信息回答用户问题，并遵循所有约束和要求。
"""
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt + context},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,  # 降低温度以减少创造性，增加准确性
                "max_tokens": 1500
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            
            # 对答案进行基本的质量检查
            if self._is_answer_quality_acceptable(answer, context, question):
                return answer
            else:
                logger.warning("生成的答案质量不符合要求，尝试重新生成")
                # 如果质量不符合要求，尝试重新生成（这里简化处理）
                return self._generate_fallback_answer(question, context)
            
        except Exception as e:
            logger.error(f"增强LLM生成失败: {e}")
            return self._generate_fallback_answer(question, context)
    
    def _is_answer_quality_acceptable(self, answer: str, context: str, question: str) -> bool:
        """检查答案质量是否可接受"""
        # 基本质量检查
        if not answer or len(answer.strip()) < 10:
            return False
        
        # 检查是否包含明显的拒绝回答
        refusal_phrases = ["无法回答", "不能回答", "不知道", "不清楚", "没有足够信息"]
        for phrase in refusal_phrases:
            if phrase in answer and len(context) > 100:  # 如果上下文充足但仍然拒绝
                return False
        
        # 检查是否包含明显的幻觉指示
        hallucination_indicators = ["可能", "大概", "也许", "推测", "假设", "猜测"]
        hallucination_count = sum(1 for indicator in hallucination_indicators if indicator in answer)
        
        # 如果不确定性表达过多，可能质量不高
        if hallucination_count > 3:
            return False
        
        return True
    
    def _generate_fallback_answer(self, question: str, context: str) -> str:
        """生成回退答案"""
        if not context or len(context.strip()) < 50:
            return "抱歉，根据当前的知识图谱信息，我无法找到与您的问题相关的内容。请尝试使用不同的关键词或提供更多上下文信息。"
        else:
            return f"基于提供的知识图谱信息，我找到了以下相关内容：\n\n{context}\n\n请注意，这些信息可能不足以完全回答您的问题。建议您提供更具体的问题或尝试其他相关查询。"

class GraphRAGSystem:
    """GraphRAG主系统"""
    
    def __init__(self, config: GraphRAGConfig):
        self.config = config
        self.retriever = GraphRetriever(config.neo4j_uri, config.neo4j_auth)
        self.generator = LLMGenerator(config.openai_api_key, config.openai_model)
        logger.info("🚀 GraphRAG系统初始化完成")
    
    def close(self):
        """关闭系统"""
        self.retriever.close()
    
    def query(self, question: str) -> Dict[str, Any]:
        """处理用户查询"""
        start_time = datetime.now()
        
        try:
            # 1. 检索相关图数据
            logger.info(f"🔍 开始检索: {question}")
            
            # 提取关键词
            keywords = self._extract_keywords(question)
            logger.info(f"📝 提取的关键词: {keywords}")
            
            # 多策略检索
            graph_data = self._multi_strategy_retrieval(keywords)
            logger.info(f"📊 检索到 {len(graph_data.get('nodes', []))} 个节点, {len(graph_data.get('relationships', []))} 个关系")
            
            # 2. 生成答案
            logger.info("🤖 开始生成答案")
            context = self.generator.format_context(graph_data)
            answer = self.generator.generate_answer(question, context)
            
            # 3. 构建响应
            end_time = datetime.now()
            response = {
                "question": question,
                "answer": answer,
                "context": context,
                "graph_data": graph_data,
                "processing_time": (end_time - start_time).total_seconds(),
                "timestamp": end_time.isoformat()
            }
            
            logger.info(f"✅ 查询完成，耗时: {response['processing_time']:.2f}秒")
            return response
            
        except Exception as e:
            logger.error(f"❌ 查询失败: {e}")
            return {
                "question": question,
                "answer": f"查询失败: {str(e)}",
                "context": "",
                "graph_data": {"nodes": [], "relationships": []},
                "processing_time": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_keywords(self, question: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取，实际应用中可以使用更复杂的NLP技术
        # 移除停用词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '如果', '那么', '因为', '所以', '什么', '如何', '为什么',
                     '工作原理', '有什么作用', '有什么区别', '的关系是什么', '如何解决', '什么是'}
        
        # 改进的正则表达式，支持中英文
        words = re.findall(r'[a-zA-Z]+|[\u4e00-\u9fa5]+', question.lower())
        
        # 提取更具体的关键词
        keywords = []
        for word in words:
            if word not in stop_words and len(word) > 1:
                keywords.append(word)
        
        # 尝试匹配常见网络术语，无论是否在停用词中
        common_terms = ['tcp', 'udp', 'http', 'https', 'vlan', '路由器', '交换机', '防火墙', '网络', '协议', '三次握手', '四次挥手',
                      '拥塞控制', '流量控制', 'dns', 'ip', '子网', '网关', 'nat', 'vpn', 'ospf', 'bgp', 'stp', '环路']
        
        for term in common_terms:
            if term in question.lower() and term not in keywords:
                keywords.append(term)
        
        # 特殊处理一些常见问题模式
        if '路由器' in question:
            keywords.append('路由器')
        if '网络环路' in question or '环路' in question:
            keywords.append('网络环路')
        
        return keywords
    
    def _multi_strategy_retrieval(self, keywords: List[str]) -> Dict[str, Any]:
        """多策略检索"""
        all_nodes = []
        all_relationships = []
        all_paths = []
        
        # 1. 对每个关键词进行搜索，但限制每个关键词的搜索结果
        keyword_limit = max(2, self.config.max_retrieved_nodes // len(keywords))  # 每个关键词最多搜索的节点数
        for keyword in keywords:
            # 1. 关键词搜索
            nodes = self.retriever.keyword_search(keyword, keyword_limit)
            all_nodes.extend(nodes)
        
        # 2. 去重节点
        unique_nodes = {}
        for node in all_nodes:
            key = (node["name"], node.get("type", ""))
            if key not in unique_nodes:
                unique_nodes[key] = node
        
        # 3. 根据查询类型调整检索策略
        node_list = list(unique_nodes.values())
        
        # 根据查询内容调整节点数量
        # 对于具体概念查询（如"什么是VLAN"），返回较少但更相关的节点
        # 对于比较查询（如"TCP和UDP的区别"），返回更多节点
        query_type = self._classify_query(keywords)
        
        if query_type == "definition":
            # 定义查询：返回较少但更相关的节点
            max_nodes = min(10, len(node_list))
        elif query_type == "comparison":
            # 比较查询：返回中等数量的节点
            max_nodes = min(15, len(node_list))
        elif query_type == "principle":
            # 原理查询：返回中等数量的节点
            max_nodes = min(12, len(node_list))
        elif query_type == "solution":
            # 解决方案查询：返回较少但更实用的节点
            max_nodes = min(8, len(node_list))
        else:
            # 默认：返回配置的最大节点数
            max_nodes = min(self.config.max_retrieved_nodes, len(node_list))
        
        # 按相关性排序（这里简单按名称长度排序，实际应用中可以按相关性分数排序）
        node_list.sort(key=lambda x: len(x.get("name", "")))
        
        # 只对前几个最相关的节点获取邻居
        for node in node_list[:min(2, max_nodes)]:
            neighbors = self.retriever.get_neighbors(node["name"], depth=2)
            for neighbor in neighbors:
                neighbor_key = (neighbor["name"], neighbor.get("type", ""))
                if neighbor_key not in unique_nodes:
                    unique_nodes[neighbor_key] = neighbor
        
        # 4. 寻找节点间路径（只对最相关的节点）
        node_list = list(unique_nodes.values())
        for i in range(min(2, max_nodes)):
            for j in range(i+1, min(i+3, max_nodes)):
                paths = self.retriever.get_path_between_nodes(
                    node_list[i]["name"],
                    node_list[j]["name"]
                )
                all_paths.extend(paths)
        
        # 5. 获取节点之间的关系
        if node_list:
            node_names = [node["name"] for node in node_list[:max_nodes]]
            cypher = """
            MATCH (n1)-[r]-(n2)
            WHERE n1.name IN $node_names AND n2.name IN $node_names
            RETURN n1, r, n2
            """
            with self.retriever.driver.session() as session:
                result = session.run(cypher, {"node_names": node_names})
                for record in result:
                    all_relationships.append({
                        "type": record["r"].type,
                        "start": dict(record["n1"]),
                        "end": dict(record["n2"])
                    })
        
        # 6. 去重关系
        unique_relationships = []
        seen_relationships = set()
        for rel in all_relationships:
            key = (rel["start"]["name"], rel["type"], rel["end"]["name"])
            if key not in seen_relationships:
                seen_relationships.add(key)
                unique_relationships.append(rel)
        
        # 7. 最终返回结果
        final_nodes = list(unique_nodes.values())[:max_nodes]
        
        return {
            "nodes": final_nodes,
            "relationships": unique_relationships[:max_nodes],
            "paths": all_paths[:5]  # 限制路径数量
        }
    
    def _classify_query(self, keywords: List[str]) -> str:
        """根据关键词分类查询类型"""
        # 定义查询类型的关键词
        definition_keywords = ['什么是', '定义', '解释', 'vlan', 'tcp', 'udp', 'http', 'https']
        comparison_keywords = ['区别', '对比', '比较', 'vs', '和']
        principle_keywords = ['原理', '工作原理', '如何工作', '机制']
        solution_keywords = ['如何解决', '解决', '问题', '故障', '排查']
        
        # 统计各类关键词出现次数
        definition_count = sum(1 for kw in keywords if any(dk in kw.lower() for dk in definition_keywords))
        comparison_count = sum(1 for kw in keywords if any(ck in kw.lower() for ck in comparison_keywords))
        principle_count = sum(1 for kw in keywords if any(pk in kw.lower() for pk in principle_keywords))
        solution_count = sum(1 for kw in keywords if any(sk in kw.lower() for sk in solution_keywords))
        
        # 确定查询类型
        if definition_count > 0 and definition_count >= max(comparison_count, principle_count, solution_count):
            return "definition"
        elif comparison_count > 0 and comparison_count >= max(principle_count, solution_count):
            return "comparison"
        elif principle_count > 0 and principle_count >= max(definition_count, comparison_count, solution_count):
            return "principle"
        elif solution_count > 0:
            return "solution"
        else:
            return "general"

def main():
    """主函数"""
    # 配置系统
    config = GraphRAGConfig(
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_auth=(
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "aixi1314")
        ),
        openai_api_key=os.getenv("ZHIPUAI_API_KEY", "b5d49df99d88433e944ff84304d3105a.Jk57Qbo2dHO56AKS"),
        openai_model=os.getenv("ZHIPUAI_MODEL", "glm-4-flash")
    )
    
    # 初始化系统
    rag_system = GraphRAGSystem(config)
    
    try:
        # 示例查询
        questions = [
            "TCP和UDP有什么区别？",
            "HTTP和HTTPS的关系是什么？",
            "路由器的工作原理是什么？",
            "如何解决网络环路问题？",
            "什么是VLAN，它有什么作用？"
        ]
        
        for question in questions:
            print(f"\n{'='*50}")
            print(f"问题: {question}")
            print('='*50)
            
            response = rag_system.query(question)
            print(f"答案: {response['answer']}")
            print(f"处理时间: {response['processing_time']:.2f}秒")
            
            # 可选：打印检索到的图数据
            if response['graph_data']['nodes']:
                print(f"\n检索到的实体数量: {len(response['graph_data']['nodes'])}")
                for node in response['graph_data']['nodes'][:3]:
                    print(f"  - {node.get('type', 'Unknown')}: {node.get('name', 'Unknown')}")
            
            if response['graph_data']['relationships']:
                print(f"\n检索到的关系数量: {len(response['graph_data']['relationships'])}")
                for rel in response['graph_data']['relationships'][:3]:
                    print(f"  - {rel['start']['name']} --[{rel['type']}]--> {rel['end']['name']}")
    
    finally:
        rag_system.close()

if __name__ == "__main__":
    main()
