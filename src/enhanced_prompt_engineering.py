"""
增强的提示工程模块
提供严格约束、领域知识库参考和证据要求的提示模板
"""

import os
import re
import json
import logging
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PromptEngineeringConfig:
    """提示工程配置"""
    openai_api_key: str = os.getenv("ZHIPUAI_API_KEY", "")
    openai_model: str = "glm-4-flash"
    openai_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_auth: Tuple[str, str] = ("neo4j", "aixi1314")
    
    # 约束配置
    strict_mode: bool = True  # 严格模式
    require_evidence: bool = True  # 要求证据
    min_confidence_threshold: float = 0.7  # 最小置信度阈值
    max_hallucination_risk: float = 0.3  # 最大幻觉风险阈值
    
    # 知识库参考配置
    enable_knowledge_reference: bool = True  # 启用知识库参考
    max_reference_items: int = 10  # 最大参考项数
    reference_similarity_threshold: float = 0.8  # 参考相似度阈值

class EnhancedPromptEngineering:
    """增强的提示工程系统"""
    
    def __init__(self, config: PromptEngineeringConfig):
        self.config = config
        self.driver = None
        self._init_neo4j()
        
        # 预定义的网络领域知识库
        self.domain_knowledge_base = self._load_domain_knowledge_base()
        
        # 严格的约束规则
        self.constraint_rules = self._load_constraint_rules()
        
        # 证据要求模板
        self.evidence_templates = self._load_evidence_templates()
    
    def _init_neo4j(self):
        """初始化Neo4j连接"""
        try:
            self.driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=self.config.neo4j_auth
            )
            self.driver.verify_connectivity()
            logger.info("✅ 成功连接Neo4j数据库")
        except Exception as e:
            logger.error(f"❌ 连接Neo4j失败: {str(e)}")
            self.driver = None
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info("🔌 已关闭Neo4j连接")
    
    def _load_domain_knowledge_base(self) -> Dict[str, Any]:
        """加载领域知识库"""
        return {
            "protocols": {
                "TCP": {
                    "type": "Protocol",
                    "layer": "传输层",
                    "description": "传输控制协议，提供可靠的面向连接的数据传输服务",
                    "features": ["面向连接", "可靠传输", "流量控制", "拥塞控制", "三次握手", "四次挥手"],
                    "ports": ["20", "21", "22", "23", "25", "53", "80", "110", "143", "443", "993", "995"],
                    "related_protocols": ["IP", "UDP", "HTTP", "HTTPS"]
                },
                "UDP": {
                    "type": "Protocol",
                    "layer": "传输层",
                    "description": "用户数据报协议，提供无连接的数据传输服务",
                    "features": ["无连接", "不可靠传输", "低延迟", "简单高效"],
                    "ports": ["53", "67", "68", "69", "123", "161", "162"],
                    "related_protocols": ["IP", "TCP", "DNS", "DHCP", "SNMP"]
                },
                "HTTP": {
                    "type": "Protocol",
                    "layer": "应用层",
                    "description": "超文本传输协议，用于传输超媒体文档",
                    "features": ["请求-响应模型", "无状态", "可扩展", "文本协议"],
                    "methods": ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"],
                    "status_codes": ["200", "301", "302", "400", "401", "403", "404", "500"],
                    "related_protocols": ["TCP", "HTTPS", "HTML", "CSS", "JS"]
                },
                "HTTPS": {
                    "type": "Protocol",
                    "layer": "应用层",
                    "description": "安全的超文本传输协议，通过SSL/TLS加密的HTTP",
                    "features": ["加密传输", "身份验证", "数据完整性", "端口443"],
                    "related_protocols": ["HTTP", "SSL", "TLS", "TCP"]
                }
            },
            "devices": {
                "路由器": {
                    "type": "Device",
                    "layer": "网络层",
                    "description": "网络设备，用于在不同网络之间转发数据包",
                    "functions": ["路由选择", "数据包转发", "网络地址转换", "访问控制"],
                    "protocols": ["IP", "ICMP", "OSPF", "BGP", "RIP"],
                    "related_devices": ["交换机", "防火墙", "网关"]
                },
                "交换机": {
                    "type": "Device",
                    "layer": "数据链路层",
                    "description": "网络设备，用于在局域网内转发数据帧",
                    "functions": ["MAC地址学习", "帧转发", "VLAN划分", "端口安全"],
                    "protocols": ["Ethernet", "STP", "RSTP", "LLDP"],
                    "related_devices": ["路由器", "集线器", "网桥"]
                },
                "防火墙": {
                    "type": "Device",
                    "layer": "网络层/应用层",
                    "description": "网络安全设备，用于控制网络访问和保护网络安全",
                    "functions": ["包过滤", "状态检测", "应用层网关", "VPN"],
                    "technologies": ["ACL", "NAT", "IDS", "IPS", "DMZ"],
                    "related_devices": ["路由器", "交换机", "入侵检测系统"]
                }
            },
            "layers": {
                "应用层": {
                    "type": "Layer",
                    "osi_layer": 7,
                    "description": "OSI模型的第七层，为应用程序提供网络服务",
                    "protocols": ["HTTP", "HTTPS", "FTP", "SMTP", "DNS", "DHCP", "SSH", "Telnet"],
                    "examples": ["网页浏览", "电子邮件", "文件传输", "远程登录"]
                },
                "传输层": {
                    "type": "Layer",
                    "osi_layer": 4,
                    "description": "OSI模型的第四层，提供端到端的可靠数据传输",
                    "protocols": ["TCP", "UDP", "SCTP"],
                    "functions": ["端口寻址", "可靠传输", "流量控制", "拥塞控制"]
                },
                "网络层": {
                    "type": "Layer",
                    "osi_layer": 3,
                    "description": "OSI模型的第三层，负责数据包的路由和转发",
                    "protocols": ["IP", "ICMP", "ARP", "OSPF", "BGP"],
                    "functions": ["路由选择", "数据包转发", "地址管理"]
                },
                "数据链路层": {
                    "type": "Layer",
                    "osi_layer": 2,
                    "description": "OSI模型的第二层，负责相邻节点间的可靠数据传输",
                    "protocols": ["Ethernet", "PPP", "HDLC", "STP"],
                    "functions": ["帧同步", "错误控制", "流量控制", "MAC地址管理"]
                }
            }
        }
    
    def _load_constraint_rules(self) -> Dict[str, Any]:
        """加载约束规则"""
        return {
            "keyword_extraction": {
                "must_be_network_related": "提取的关键词必须属于计算机网络领域",
                "must_have_valid_type": "关键词类型必须是预定义的类型之一",
                "must_have_min_confidence": f"关键词置信度必须大于等于{self.config.min_confidence_threshold}",
                "must_have_evidence": "每个关键词必须有文本证据支持",
                "no_hallucination": "不允许提取文本中不存在的关键词"
            },
            "relationship_extraction": {
                "must_use_valid_type": "关系类型必须是预定义的类型之一",
                "must_be_logical": "关系必须符合逻辑，不能违反网络原理",
                "must_have_evidence": "每个关系必须有文本证据支持",
                "no_circular_logic": "不允许循环逻辑的关系",
                "must_consider_direction": "关系方向必须正确"
            },
            "semantic_validation": {
                "must_cross_reference": "必须与领域知识库交叉验证",
                "must_check_consistency": "必须检查内部一致性",
                "must_require_evidence": "必须有足够的证据支持",
                "must_assess_risk": "必须评估幻觉风险"
            }
        }
    
    def _load_evidence_templates(self) -> Dict[str, str]:
        """加载证据要求模板"""
        return {
            "keyword_evidence": """
            请为每个提取的关键词提供以下证据：
            1. 文本位置：指出关键词在原文中的具体位置
            2. 上下文：提供关键词前后的上下文（至少50个字符）
            3. 支持理由：说明为什么认为这是计算机网络领域的知识点
            4. 类型依据：说明为什么选择该类型
            5. 置信度依据：说明置信度评分的依据
            """,
            
            "relationship_evidence": """
            请为每个提取的关系提供以下证据：
            1. 文本位置：指出关系在原文中的具体位置
            2. 上下文：提供关系描述前后的上下文（至少50个字符）
            3. 逻辑依据：说明为什么认为这两个实体之间存在这种关系
            4. 方向依据：如果是有向关系，说明为什么选择这个方向
            5. 置信度依据：说明置信度评分的依据
            """,
            
            "validation_evidence": """
            请为验证结果提供以下证据：
            1. 领域知识库对比：与已知领域知识的对比结果
            2. 逻辑一致性检查：内部逻辑一致性的检查结果
            3. 文本支持度：原文对该知识点/关系的支持程度
            4. 风险评估：幻觉风险的评估结果和依据
            """
        }
    
    def get_domain_knowledge_reference(self, term: str, item_type: str = None) -> Dict[str, Any]:
        """获取领域知识库参考"""
        if not self.config.enable_knowledge_reference:
            return {}
        
        term_lower = term.lower()
        references = []
        
        # 搜索预定义的知识库
        for category, items in self.domain_knowledge_base.items():
            for key, value in items.items():
                if term_lower in key.lower() or key.lower() in term_lower:
                    # 如果指定了类型，只返回匹配类型的结果
                    if item_type and value.get("type", "").lower() != item_type.lower():
                        continue
                    
                    references.append({
                        "name": key,
                        "type": value.get("type", ""),
                        "description": value.get("description", ""),
                        "category": category,
                        "similarity": 1.0 if term_lower == key.lower() else 0.8
                    })
                    
                    if len(references) >= self.config.max_reference_items:
                        break
            if len(references) >= self.config.max_reference_items:
                break
        
        # 如果没有找到预定义的参考，尝试从Neo4j中搜索
        if not references and self.driver:
            references = self._search_neo4j_knowledge(term, item_type)
        
        return {
            "term": term,
            "references": references,
            "has_reference": len(references) > 0,
            "confidence": max([r["similarity"] for r in references]) if references else 0.0
        }
    
    def _search_neo4j_knowledge(self, term: str, item_type: str = None) -> List[Dict[str, Any]]:
        """从Neo4j搜索知识库"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                # 构建查询
                if item_type:
                    cypher = """
                    MATCH (n:%s)
                    WHERE toLower(n.name) CONTAINS toLower($term)
                    RETURN n.name as name, n.description as description, labels(n) as types
                    LIMIT $limit
                    """ % item_type.replace(' ', '_')
                else:
                    cypher = """
                    MATCH (n)
                    WHERE toLower(n.name) CONTAINS toLower($term)
                    RETURN n.name as name, n.description as description, labels(n) as types
                    LIMIT $limit
                    """
                
                result = session.run(cypher, {
                    "term": term,
                    "limit": self.config.max_reference_items
                })
                
                references = []
                for record in result:
                    name = record["name"]
                    description = record.get("description", "")
                    types = record["types"]
                    node_type = types[0] if types else "Unknown"
                    
                    # 计算相似度
                    similarity = 1.0 if name.lower() == term.lower() else 0.7
                    
                    if similarity >= self.config.reference_similarity_threshold:
                        references.append({
                            "name": name,
                            "type": node_type,
                            "description": description,
                            "category": "neo4j",
                            "similarity": similarity
                        })
                
                return references
                
        except Exception as e:
            logger.error(f"从Neo4j搜索知识库失败: {e}")
            return []
    
    def build_enhanced_keyword_extraction_prompt(self, text: str) -> Dict[str, str]:
        """构建增强的关键词提取提示"""
        # 获取文本中可能的关键词参考
        potential_keywords = self._extract_potential_keywords(text)
        keyword_references = {}
        for keyword in potential_keywords:
            keyword_references[keyword] = self.get_domain_knowledge_reference(keyword)
        
        system_prompt = f"""
你是一个计算机网络领域的专家，请从给定的文本中提取重要的知识点关键字。

# 严格约束
{self.constraint_rules["keyword_extraction"]["must_be_network_related"]}
{self.constraint_rules["keyword_extraction"]["must_have_valid_type"]}
{self.constraint_rules["keyword_extraction"]["must_have_min_confidence"]}
{self.constraint_rules["keyword_extraction"]["must_have_evidence"]}
{self.constraint_rules["keyword_extraction"]["no_hallucination"]}

# 领域知识库参考
以下是计算机网络领域的标准知识点，请参考这些标准来提取和验证关键词：
{json.dumps(self.domain_knowledge_base, ensure_ascii=False, indent=2)}

# 证据要求
{self.evidence_templates["keyword_evidence"]}

# 输出格式要求
1. 必须返回有效的JSON格式
2. 每个关键词必须包含以下字段：
   - name: 关键词名称
   - type: 类型（必须是Protocol、Device、Layer、Knowledge、SecurityConcept、NetworkType、Problem、Solution之一）
   - confidence: 置信度（0-1之间的数值）
   - description: 描述
   - evidence: 证据对象，包含：
     * text_position: 文本位置
     * context: 上下文
     * support_reason: 支持理由
     * type_basis: 类型依据
     * confidence_basis: 置信度依据
   - domain_reference: 领域知识库参考（如果有）

# 风险控制
- 如果对某个关键词不确定，宁可降低置信度也不要猜测
- 如果文本中没有足够证据支持，不要提取该关键词
- 置信度低于{self.config.min_confidence_threshold}的关键词将被视为低质量

请返回JSON格式的结果，确保格式正确且完整。
"""
        
        user_prompt = f"""
请从以下文本中提取计算机网络知识点关键字：

文本内容：
{text}

潜在关键词参考：
{json.dumps(keyword_references, ensure_ascii=False, indent=2)}

请返回JSON格式的结果。
"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    def build_enhanced_relationship_extraction_prompt(self, text: str, keywords: List[Dict[str, Any]]) -> Dict[str, str]:
        """构建增强的关系提取提示"""
        # 获取关键词的知识库参考
        keyword_references = {}
        for keyword in keywords:
            name = keyword.get("name", "")
            if name:
                keyword_references[name] = self.get_domain_knowledge_reference(name, keyword.get("type"))
        
        system_prompt = f"""
你是一个计算机网络领域的专家，请从给定的文本和关键词中提取知识点之间的关系。

# 严格约束
{self.constraint_rules["relationship_extraction"]["must_use_valid_type"]}
{self.constraint_rules["relationship_extraction"]["must_be_logical"]}
{self.constraint_rules["relationship_extraction"]["must_have_evidence"]}
{self.constraint_rules["relationship_extraction"]["no_circular_logic"]}
{self.constraint_rules["relationship_extraction"]["must_consider_direction"]}

# 有效的关系类型
- APPLY_TO: 应用于（如：TCP应用于传输层）
- DEPENDS_ON: 依赖于（如：HTTP依赖于TCP）
- RELATED_TO: 相关于（一般相关关系）
- WORKS_WITH: 协同工作（如：路由器与交换机协同工作）
- PROTECTS: 保护（如：防火墙保护网络）
- ATTACKS: 攻击（如：DDoS攻击服务器）
- SOLVED_BY: 通过...解决（如：网络问题通过路由器解决）
- BELONGS_TO: 属于（如：TCP属于传输层协议）
- HAS_FUNCTION: 具有功能（如：路由器具有路由功能）
- BETWEEN: 介于之间（如：网关介于两个网络之间）

# 证据要求
{self.evidence_templates["relationship_evidence"]}

# 输出格式要求
1. 必须返回有效的JSON格式
2. 每个关系必须包含以下字段：
   - source: 源节点对象，包含name和type
   - target: 目标节点对象，包含name和type
   - type: 关系类型（必须是上述有效类型之一）
   - confidence: 置信度（0-1之间的数值）
   - description: 关系描述
   - evidence: 证据对象，包含：
     * text_position: 文本位置
     * context: 上下文
     * logic_basis: 逻辑依据
     * direction_basis: 方向依据
     * confidence_basis: 置信度依据
   - domain_reference: 领域知识库参考（如果有）

# 风险控制
- 如果对某个关系不确定，宁可降低置信度也不要猜测
- 如果文本中没有足够证据支持，不要提取该关系
- 置信度低于{self.config.min_confidence_threshold}的关系将被视为低质量
- 确保关系符合计算机网络的基本原理

请返回JSON格式的结果，确保格式正确且完整。
"""
        
        user_prompt = f"""
请从以下文本和关键词中提取关系：

文本内容：
{text}

关键词：
{json.dumps(keywords, ensure_ascii=False, indent=2)}

关键词知识库参考：
{json.dumps(keyword_references, ensure_ascii=False, indent=2)}

请返回JSON格式的结果。
"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    def build_enhanced_validation_prompt(self, item: Dict[str, Any], item_type: str = "knowledge") -> Dict[str, str]:
        """构建增强的验证提示"""
        # 获取项目的知识库参考
        if item_type == "knowledge":
            name = item.get("name", "")
            item_type_value = item.get("type", "")
            domain_reference = self.get_domain_knowledge_reference(name, item_type_value)
            item_content = f"知识点: {name} (类型: {item_type_value})"
        else:
            source_name = item.get("source", {}).get("name", "")
            target_name = item.get("target", {}).get("name", "")
            rel_type = item.get("type", "")
            domain_reference = {}  # 关系的领域参考较复杂，这里简化处理
            item_content = f"关系: {source_name} --[{rel_type}]--> {target_name}"
        
        system_prompt = f"""
你是一个计算机网络领域的专家，请验证以下{item_type}的合理性和准确性。

# 严格约束
{self.constraint_rules["semantic_validation"]["must_cross_reference"]}
{self.constraint_rules["semantic_validation"]["must_check_consistency"]}
{self.constraint_rules["semantic_validation"]["must_require_evidence"]}
{self.constraint_rules["semantic_validation"]["must_assess_risk"]}

# 领域知识库
以下是计算机网络领域的标准知识点，请参考这些标准来验证：
{json.dumps(self.domain_knowledge_base, ensure_ascii=False, indent=2)}

# 证据要求
{self.evidence_templates["validation_evidence"]}

# 验证标准
1. 领域一致性：是否符合计算机网络领域的基本原理
2. 内部一致性：内部属性是否一致
3. 证据充分性：是否有足够的证据支持
4. 幻觉风险评估：评估幻觉风险（0-1，越高风险越大）

# 输出格式要求
必须返回有效的JSON格式，包含以下字段：
- is_valid: 是否有效（布尔值）
- confidence: 置信度（0-1之间的数值）
- reason: 验证原因
- suggestions: 改进建议（字符串数组）
- domain_consistency: 领域一致性评分（0-1）
- internal_consistency: 内部一致性评分（0-1）
- evidence_sufficiency: 证据充分性评分（0-1）
- hallucination_risk: 幻觉风险评估（0-1）
- domain_reference: 领域知识库参考结果

# 风险控制
- 幻觉风险高于{self.config.max_hallucination_risk}的项目应标记为无效
- 综合置信度低于{self.config.min_confidence_threshold}的项目应标记为无效
- 必须提供明确的验证理由和改进建议

请返回JSON格式的结果，确保格式正确且完整。
"""
        
        user_prompt = f"""
请验证以下{item_type}的合理性：

{item_content}

描述: {item.get('description', item.get('context', ''))}

领域知识库参考：
{json.dumps(domain_reference, ensure_ascii=False, indent=2)}

请返回JSON格式的验证结果。
"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    def _extract_potential_keywords(self, text: str) -> List[str]:
        """从文本中提取潜在的关键词"""
        # 这里使用简单的方法提取潜在关键词，实际应用中可以使用更复杂的NLP技术
        import re
        
        # 提取可能的技术术语（大写字母开头的词、包含特定关键词的词等）
        potential_keywords = set()
        
        # 匹配大写字母开头的词（可能是协议名、技术名等）
        uppercase_words = re.findall(r'\b[A-Z]{2,}\b', text)
        potential_keywords.update(uppercase_words)
        
        # 匹配常见的网络关键词
        network_terms = ['tcp', 'udp', 'http', 'https', 'ip', 'dns', 'dhcp', 'ftp', 'smtp', '路由器', '交换机', '防火墙', '协议', '网络', '层']
        for term in network_terms:
            if term.lower() in text.lower():
                potential_keywords.add(term)
        
        # 匹配中文技术术语（可能包含"协议"、"技术"、"方法"等）
        chinese_terms = re.findall(r'[\u4e00-\u9fa5]+(?:协议|技术|方法|机制|算法|设备|系统)', text)
        potential_keywords.update(chinese_terms)
        
        return list(potential_keywords)
    
    def call_llm_with_enhanced_prompt(self, prompt_data: Dict[str, str], temperature: float = 0.3, max_tokens: int = 1500) -> Dict[str, Any]:
        """使用增强的提示调用LLM"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.openai_model,
                "messages": [
                    {"role": "system", "content": prompt_data["system_prompt"]},
                    {"role": "user", "content": prompt_data["user_prompt"]}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 确保URL以/chat/completions结尾
            base_url = self.config.openai_base_url
            if not base_url.endswith('/chat/completions'):
                if base_url.endswith('/'):
                    base_url += 'chat/completions'
                else:
                    base_url += '/chat/completions'
            
            response = requests.post(
                base_url,
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # 解析JSON响应
            try:
                # 处理可能包含代码块标记的JSON
                json_content = content
                if content.startswith('```json'):
                    json_content = content[7:]  # 移除```json
                elif content.startswith('```'):
                    json_content = content[3:]  # 移除```
                if json_content.endswith('```'):
                    json_content = json_content[:-3]  # 移除结尾的```
                json_content = json_content.strip()
                
                # 尝试解析JSON
                try:
                    return json.loads(json_content)
                except json.JSONDecodeError:
                    # 尝试从内容中提取JSON部分
                    json_pattern = r'\{.*\}'
                    match = re.search(json_pattern, json_content, re.DOTALL)
                    if match:
                        json_str = match.group(0)
                        return json.loads(json_str)
                    else:
                        raise json.JSONDecodeError("无法提取有效JSON", content, 0)
                        
            except json.JSONDecodeError as e:
                logger.error(f"LLM返回的不是有效JSON: {content}")
                logger.error(f"解析错误: {e}")
                return {"error": "JSON解析失败", "content": content}
                
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return {"error": str(e)}

def main():
    """主函数，用于测试"""
    # 配置系统
    config = PromptEngineeringConfig(
        openai_api_key=os.getenv("ZHIPUAI_API_KEY", ""),
        openai_model=os.getenv("ZHIPUAI_MODEL", "glm-4-flash"),
        strict_mode=True,
        require_evidence=True,
        min_confidence_threshold=0.7,
        max_hallucination_risk=0.3
    )
    
    # 初始化增强提示工程系统
    prompt_engineering = EnhancedPromptEngineering(config)
    
    try:
        # 测试文本
        test_text = """
        TCP/IP协议栈是互联网的核心协议族，包括应用层、传输层、网络层和链路层。
        
        传输控制协议(TCP)是一种面向连接的、可靠的传输层协议，它通过三次握手建立连接，
        通过四次挥手断开连接。TCP提供流量控制和拥塞控制机制，确保数据可靠传输。
        
        用户数据报协议(UDP)是一种无连接的传输层协议，它不保证数据可靠传输，
        但具有低延迟的特点，适用于实时应用如视频流和在线游戏。
        
        路由器是网络层设备，负责在不同网络之间转发数据包。路由器使用路由协议如OSPF
        和BGP来学习网络拓扑，并做出转发决策。
        
        防火墙是网络安全设备，用于保护内部网络免受外部攻击。防火墙可以通过包过滤、
        状态检测和应用层网关等技术实现网络安全策略。
        """
        
        # 测试关键词提取提示
        print("=== 测试关键词提取提示 ===")
        keyword_prompt = prompt_engineering.build_enhanced_keyword_extraction_prompt(test_text)
        print("系统提示长度:", len(keyword_prompt["system_prompt"]))
        print("用户提示长度:", len(keyword_prompt["user_prompt"]))
        
        # 测试关系提取提示
        print("\n=== 测试关系提取提示 ===")
        # 假设已经提取了关键词
        test_keywords = [
            {"name": "TCP", "type": "Protocol", "confidence": 0.9},
            {"name": "UDP", "type": "Protocol", "confidence": 0.9},
            {"name": "路由器", "type": "Device", "confidence": 0.8},
            {"name": "防火墙", "type": "Device", "confidence": 0.8}
        ]
        relationship_prompt = prompt_engineering.build_enhanced_relationship_extraction_prompt(test_text, test_keywords)
        print("系统提示长度:", len(relationship_prompt["system_prompt"]))
        print("用户提示长度:", len(relationship_prompt["user_prompt"]))
        
        # 测试验证提示
        print("\n=== 测试验证提示 ===")
        test_knowledge = {"name": "TCP", "type": "Protocol", "confidence": 0.9, "description": "传输控制协议"}
        validation_prompt = prompt_engineering.build_enhanced_validation_prompt(test_knowledge, "knowledge")
        print("系统提示长度:", len(validation_prompt["system_prompt"]))
        print("用户提示长度:", len(validation_prompt["user_prompt"]))
        
        # 测试领域知识库参考
        print("\n=== 测试领域知识库参考 ===")
        tcp_reference = prompt_engineering.get_domain_knowledge_reference("TCP", "Protocol")
        print("TCP参考:", json.dumps(tcp_reference, ensure_ascii=False, indent=2))
        
        router_reference = prompt_engineering.get_domain_knowledge_reference("路由器", "Device")
        print("路由器参考:", json.dumps(router_reference, ensure_ascii=False, indent=2))
        
    finally:
        prompt_engineering.close()

if __name__ == "__main__":
    main()