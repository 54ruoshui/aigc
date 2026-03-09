"""
计算机网络课程内容知识点提取与关系识别算法
能够自动识别课程内容中的知识点关键字及其关系，并写入Neo4j知识图谱
"""

import os
import re
import json
import logging
from typing import List, Dict, Tuple, Any, Optional, Set
from dataclasses import dataclass
from neo4j import GraphDatabase, exceptions
import requests
from dotenv import load_dotenv
from .enhanced_prompt_engineering import EnhancedPromptEngineering, PromptEngineeringConfig

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KnowledgeExtractionConfig:
    """知识点提取配置"""
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_auth: Tuple[str, str] = ("neo4j", "aixi1314")
    openai_api_key: str = os.getenv("ZHIPUAI_API_KEY", "")
    openai_model: str = "glm-4-flash"
    openai_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    
    # 提取参数
    min_keyword_length: int = 2  # 最小关键字长度
    max_keywords_per_text: int = 20  # 每段文本最大关键字数
    confidence_threshold: float = 0.7  # 置信度阈值
    
    # 关系提取参数
    max_relationships_per_text: int = 10  # 每段文本最大关系数
    relationship_types: List[str] = None  # 支持的关系类型

class KnowledgeExtractor:
    """知识点提取器"""
    
    def __init__(self, config: KnowledgeExtractionConfig):
        self.config = config
        self.driver = None
        self._init_neo4j()
        
        # 初始化增强的提示工程系统
        prompt_config = PromptEngineeringConfig(
            openai_api_key=config.openai_api_key,
            openai_model=config.openai_model,
            openai_base_url=config.openai_base_url,
            neo4j_uri=config.neo4j_uri,
            neo4j_auth=config.neo4j_auth,
            strict_mode=True,
            require_evidence=True,
            min_confidence_threshold=0.7,
            max_hallucination_risk=0.3
        )
        self.prompt_engineering = EnhancedPromptEngineering(prompt_config)
        
        # 预定义的网络领域关键词字典
        self.network_keywords = self._load_network_keywords()
        
        # 预定义的关系模式
        self.relationship_patterns = self._load_relationship_patterns()
        
        # 预定义的节点类型
        self.node_types = {
            'Protocol': ['协议', 'protocol', 'TCP', 'UDP', 'HTTP', 'HTTPS', 'FTP', 'SMTP', 'DNS', 'DHCP'],
            'Device': ['设备', '路由器', '交换机', '防火墙', '网关', '集线器', '中继器', '网桥'],
            'Layer': ['层', '应用层', '传输层', '网络层', '数据链路层', '物理层', '表示层', '会话层'],
            'Knowledge': ['概念', '原理', '机制', '算法', '过程', '方法', '技术'],
            'SecurityConcept': ['安全', '加密', '认证', '授权', '防火墙', 'VPN', '攻击', '防护'],
            'NetworkType': ['网络', '局域网', '广域网', '城域网', '互联网', '以太网', '无线网'],
            'Problem': ['问题', '故障', '错误', '异常', '风险', '威胁'],
            'Solution': ['解决方案', '方法', '策略', '措施', '优化']
        }
    
    def _init_neo4j(self):
        """初始化Neo4j连接"""
        try:
            # 简化连接参数，避免版本兼容性问题
            self.driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=self.config.neo4j_auth
            )
            # 验证连接
            self.driver.verify_connectivity()
            logger.info("✅ 成功连接Neo4j数据库")
        except Exception as e:
            logger.error(f"❌ 连接Neo4j失败: {str(e)}")
            # 尝试不带数据库参数的连接
            try:
                self.driver = GraphDatabase.driver(
                    self.config.neo4j_uri,
                    auth=self.config.neo4j_auth
                )
                # 测试基本连接
                with self.driver.session() as session:
                    session.run("RETURN 1")
                logger.info("✅ 成功连接Neo4j数据库（备用方式）")
            except Exception as e2:
                logger.error(f"❌ Neo4j备用连接也失败: {str(e2)}")
                raise ConnectionError("无法连接到Neo4j数据库，请检查连接配置")
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info("🔌 已关闭Neo4j连接")
        
        if self.prompt_engineering:
            self.prompt_engineering.close()
            logger.info("🔌 已关闭提示工程系统")
    
    def _load_network_keywords(self) -> Dict[str, List[str]]:
        """加载网络领域关键词字典"""
        return {
            'protocols': [
                'TCP', 'UDP', 'HTTP', 'HTTPS', 'FTP', 'SFTP', 'SMTP', 'POP3', 'IMAP', 'DNS', 'DHCP',
                'Telnet', 'SSH', 'SNMP', 'LDAP', 'Kerberos', 'SIP', 'TLS', 'DTLS', 'IPSec', 'GRE',
                'L2TP', 'MPLS', 'VRRP', 'HSRP', 'GLBP', 'EIGRP', 'OSPF', 'BGP', 'RIP', 'IS-IS',
                'STP', 'RSTP', 'MSTP', 'LACP', 'LLDP', 'CDP', 'PAgP', 'PPPoE', 'VXLAN', 'GVRP',
                '802.1Q', '802.1X', 'BFD', 'PCEP', 'NetFlow', 'IPFIX', 'gRPC', 'NETCONF', 'RESTCONF',
                'QUIC', 'SCTP', 'DCCP', 'WebSocket', 'WebRTC', 'OAuth', 'OpenID', 'JWT', 'SAML',
                'RADIUS', 'TACACS', 'DIAMETER', 'CoAP', 'MQTT', 'AMQP', 'OPC UA', 'Modbus', 'Profinet'
            ],
            'devices': [
                '路由器', '交换机', '防火墙', '网关', '集线器', '中继器', '网桥', '三层交换机',
                '负载均衡器', '代理服务器', '缓存服务器', 'VPN网关', '入侵检测系统', '入侵防御系统',
                'Web应用防火墙', '上网行为管理', '流量分析器', '光端机', '调制解调器', 'DSLAM',
                'OLT', 'ONU', 'BRAS', 'SD-WAN控制器', '核心交换机', '接入交换机', '汇聚交换机',
                '无线接入点', '无线控制器', '网络时间服务器', '网络准入控制器', '网络探针',
                'SDN交换机', '网络编排器', 'AI网络分析器', 'PCE服务器', '网络遥测收集器',
                '网络配置管理器', '工业网关', 'PLC', 'DCS', 'SCADA', 'WiFi 6E AP', 'WiFi 7 AP'
            ],
            'layers': [
                '应用层', '表示层', '会话层', '传输层', '网络层', '数据链路层', '物理层',
                'TCP/IP模型', 'OSI模型', '网际层', '网络接口层'
            ],
            'concepts': [
                '三次握手', '四次挥手', '拥塞控制', '流量控制', 'CSMA/CD', 'IP地址分类', '子网掩码',
                'NAT', 'VLAN', 'MTU', 'DNS解析过程', 'HTTP状态码', 'TCP标志位', 'TCP滑动窗口',
                'MSS', 'TCP_NODELAY', 'Nagle算法', 'Delayed ACK', 'TIME_WAIT状态', '半连接队列',
                '全连接队列', 'UDP hole punching', 'IP分片', 'IP选项字段', 'TTL', 'TOS字段',
                'AnyCast', 'CIDR', '私有地址范围', '环回地址', '链路本地地址', 'ARP表', 'Proxy ARP',
                'Gratuitous ARP', 'VLAN tagging', 'VLAN间路由', 'STP端口状态', 'STP端口角色',
                'PortFast', 'BPDU Guard', 'UplinkFast', 'BackboneFast', '以太网帧格式', 'Jumbo Frame',
                'CSMA/CA', 'Wi-Fi标准演进', 'MIMO技术', '波束成形', '频谱分析', 'SSID广播', 'WPA3'
            ],
            'security': [
                '加密', '防火墙', '入侵检测系统', '入侵防御系统', 'DDoS攻击', 'ARP欺骗', 'SQL注入',
                '中间人攻击', '钓鱼攻击', '跨站脚本攻击', '跨站请求伪造', '暴力破解', '端口扫描',
                'SYN洪水攻击', 'UDP洪水攻击', 'IP欺骗', 'MAC地址欺骗', 'STP攻击', 'VLAN跳跃攻击',
                'DHCP欺骗', 'DNS劫持', 'SSL剥离', '零信任架构', '微隔离', '网络访问控制',
                '安全编排', 'XDR', 'CASB', 'CWP', '同态加密', '安全多方计算', '联邦学习',
                '差分隐私', '可信执行环境', '数字水印', '区块链取证', 'AI对抗攻击', '模型可解释性'
            ],
            'network_types': [
                '局域网', '广域网', '城域网', '存储区域网络', '物联网', '车联网', '工业控制网络',
                '数据中心网络', '5G网络', '卫星网络', '量子网络', '区块链网络', '空天地一体化网络',
                '算力网络', '确定性网络', '6G网络', '元宇宙网络', '生物计算网络', '智能家居网络'
            ],
            'problems': [
                '网络不通', '网速慢', 'DNS解析失败', '网络环路', '广播风暴', 'MAC地址漂移',
                'DHCP地址耗尽', 'ARP表溢出', '交换机CPU过高', '链路抖动', '路由环路',
                'BGP邻居无法建立', 'OSPF邻居停滞', 'NAT转换失败', 'QoS不生效', 'VPN隧道不通',
                '无线网络连接慢', 'VoIP通话质量差', '存储网络性能差', 'IP地址冲突', '网络时延过高',
                'IPv6部署困难', 'BGP路由泄露', '网络自动化故障', '网络拥塞', 'MTU问题',
                'IPsec VPN故障', 'MPLS LSP故障', '云安全威胁', '量子计算威胁'
            ],
            'solutions': [
                '网络排查', '带宽扩容', 'DNS修复', '环路检测', '风暴控制', 'MAC安全加固',
                'DHCP优化', 'ARP表优化', 'CPU保护', '链路优化', '路由优化', 'BGP排错',
                'OSPF排错', 'NAT排错', 'QoS调优', 'VPN排错', '无线优化', '语音质量调优',
                'SAN优化', 'IP冲突解决', '时延优化', 'IPv6迁移策略', 'BGP安全加固', '自动化可靠性提升',
                '拥塞控制', 'MTU优化', 'IPsec故障排查', 'MPLS故障排查', '云安全加固', '后量子密码学'
            ]
        }
    
    def _load_relationship_patterns(self) -> Dict[str, Dict[str, Any]]:
        """加载关系模式字典"""
        return {
            'APPLY_TO': {
                'description': '应用于',
                'patterns': [
                    r'(\w+)\s*应用于\s*(\w+)',
                    r'(\w+)\s*工作在\s*(\w+)',
                    r'(\w+)\s*属于\s*(\w+)',
                    r'(\w+)\s*运行于\s*(\w+)'
                ],
                'confidence': 0.8
            },
            'DEPENDS_ON': {
                'description': '依赖于',
                'patterns': [
                    r'(\w+)\s*依赖于\s*(\w+)',
                    r'(\w+)\s*基于\s*(\w+)',
                    r'(\w+)\s*使用\s*(\w+)',
                    r'(\w+)\s*需要\s*(\w+)'
                ],
                'confidence': 0.8
            },
            'RELATED_TO': {
                'description': '相关于',
                'patterns': [
                    r'(\w+)\s*与\s*(\w+)\s*相关',
                    r'(\w+)\s*涉及\s*(\w+)',
                    r'(\w+)\s*包括\s*(\w+)',
                    r'(\w+)\s*包含\s*(\w+)'
                ],
                'confidence': 0.7
            },
            'WORKS_WITH': {
                'description': '协同工作',
                'patterns': [
                    r'(\w+)\s*与\s*(\w+)\s*协同工作',
                    r'(\w+)\s*配合\s*(\w+)',
                    r'(\w+)\s*结合\s*(\w+)',
                    r'(\w+)\s*和\s*(\w+)\s*一起使用'
                ],
                'confidence': 0.7
            },
            'PROTECTS': {
                'description': '保护',
                'patterns': [
                    r'(\w+)\s*保护\s*(\w+)',
                    r'(\w+)\s*防护\s*(\w+)',
                    r'(\w+)\s*防止\s*(\w+)',
                    r'(\w+)\s*防御\s*(\w+)'
                ],
                'confidence': 0.8
            },
            'ATTACKS': {
                'description': '攻击',
                'patterns': [
                    r'(\w+)\s*攻击\s*(\w+)',
                    r'(\w+)\s*入侵\s*(\w+)',
                    r'(\w+)\s*威胁\s*(\w+)',
                    r'(\w+)\s*破坏\s*(\w+)'
                ],
                'confidence': 0.8
            },
            'SOLVED_BY': {
                'description': '通过...解决',
                'patterns': [
                    r'(\w+)\s*通过\s*(\w+)\s*解决',
                    r'(\w+)\s*使用\s*(\w+)\s*解决',
                    r'(\w+)\s*由\s*(\w+)\s*解决',
                    r'解决\s*(\w+)\s*需要\s*(\w+)'
                ],
                'confidence': 0.8
            },
            'BELONGS_TO': {
                'description': '属于',
                'patterns': [
                    r'(\w+)\s*属于\s*(\w+)',
                    r'(\w+)\s*是\s*(\w+)\s*的一部分',
                    r'(\w+)\s*包含在\s*(\w+)\s*中',
                    r'(\w+)\s*归属于\s*(\w+)'
                ],
                'confidence': 0.8
            },
            'HAS_FUNCTION': {
                'description': '具有功能',
                'patterns': [
                    r'(\w+)\s*具有\s*(\w+)\s*功能',
                    r'(\w+)\s*的功能是\s*(\w+)',
                    r'(\w+)\s*用于\s*(\w+)',
                    r'(\w+)\s*实现\s*(\w+)'
                ],
                'confidence': 0.7
            },
            'BETWEEN': {
                'description': '介于之间',
                'patterns': [
                    r'(\w+)\s*介于\s*(\w+)\s*和\s*(\w+)\s*之间',
                    r'(\w+)\s*位于\s*(\w+)\s*与\s*(\w+)\s*之间',
                    r'(\w+)\s*连接\s*(\w+)\s*和\s*(\w+)'
                ],
                'confidence': 0.7
            }
        }
    
    def extract_keywords_from_text(self, text: str, use_llm: bool = True) -> List[Dict[str, Any]]:
        """
        从文本中提取知识点关键字
        
        Args:
            text: 输入文本
            use_llm: 是否使用LLM进行提取
            
        Returns:
            提取的关键字列表，每个关键字包含名称、类型、置信度等信息
        """
        keywords = []
        
        # 1. 基于规则的关键词提取
        rule_based_keywords = self._extract_keywords_by_rules(text)
        keywords.extend(rule_based_keywords)
        
        # 2. 如果启用LLM，使用LLM进行提取
        if use_llm and self.config.openai_api_key:
            llm_keywords = self._extract_keywords_by_llm(text)
            keywords.extend(llm_keywords)
        
        # 3. 去重和排序
        unique_keywords = self._deduplicate_and_rank_keywords(keywords)
        
        # 4. 限制返回数量
        return unique_keywords[:self.config.max_keywords_per_text]
    
    def _extract_keywords_by_rules(self, text: str) -> List[Dict[str, Any]]:
        """基于规则的关键词提取"""
        keywords = []
        text_lower = text.lower()
        
        # 遍历预定义的关键词字典
        for category, terms in self.network_keywords.items():
            for term in terms:
                if term.lower() in text_lower:
                    # 确定节点类型
                    node_type = self._determine_node_type(term, category)
                    
                    # 计算置信度
                    confidence = self._calculate_confidence(term, text)
                    
                    if confidence >= self.config.confidence_threshold:
                        keywords.append({
                            'name': term,
                            'type': node_type,
                            'category': category,
                            'confidence': confidence,
                            'source': 'rule_based',
                            'context': self._extract_context(text, term)
                        })
        
        return keywords
    
    def _determine_node_type(self, term: str, category: str) -> str:
        """根据术语和类别确定节点类型"""
        # 首先检查精确匹配
        for node_type, keywords in self.node_types.items():
            for keyword in keywords:
                if keyword.lower() in term.lower() or term.lower() in keyword.lower():
                    return node_type
        
        # 根据类别映射到节点类型
        category_mapping = {
            'protocols': 'Protocol',
            'devices': 'Device',
            'layers': 'Layer',
            'concepts': 'Knowledge',
            'security': 'SecurityConcept',
            'network_types': 'NetworkType',
            'problems': 'Problem',
            'solutions': 'Solution'
        }
        
        return category_mapping.get(category, 'Knowledge')
    
    def _calculate_confidence(self, term: str, text: str) -> float:
        """计算术语在文本中的置信度"""
        term_lower = term.lower()
        text_lower = text.lower()
        
        # 基础置信度
        base_confidence = 0.5
        
        # 如果术语完全匹配，提高置信度
        if term_lower in text_lower:
            base_confidence += 0.3
        
        # 如果术语是独立单词（不是其他单词的一部分），提高置信度
        word_pattern = r'\b' + re.escape(term_lower) + r'\b'
        if re.search(word_pattern, text_lower):
            base_confidence += 0.2
        
        # 如果术语出现多次，提高置信度
        count = len(re.findall(word_pattern, text_lower))
        if count > 1:
            base_confidence += min(0.2, 0.05 * (count - 1))
        
        # 如果术语长度较长，提高置信度
        if len(term) > 3:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _extract_context(self, text: str, term: str, window_size: int = 50) -> str:
        """提取术语在文本中的上下文"""
        term_lower = term.lower()
        text_lower = text.lower()
        
        # 找到术语在文本中的位置
        match = re.search(re.escape(term_lower), text_lower)
        if not match:
            return ""
        
        start = max(0, match.start() - window_size)
        end = min(len(text), match.end() + window_size)
        
        return text[start:end].strip()
    
    def _extract_keywords_by_llm(self, text: str) -> List[Dict[str, Any]]:
        """使用增强的LLM提示工程提取关键词"""
        try:
            # 使用增强的提示工程
            prompt_data = self.prompt_engineering.build_enhanced_keyword_extraction_prompt(text)
            result = self.prompt_engineering.call_llm_with_enhanced_prompt(prompt_data)
            
            # 检查是否有错误
            if "error" in result:
                logger.error(f"LLM关键词提取失败: {result['error']}")
                return []
            
            # 确保结果是列表
            if not isinstance(result, list):
                logger.warning(f"LLM返回的不是列表: {type(result)}")
                return []
            
            # 处理提取的关键词
            processed_keywords = []
            for keyword in result:
                if not isinstance(keyword, dict):
                    logger.warning(f"跳过非字典对象的关键词: {type(keyword)}")
                    continue
                
                # 添加来源标记
                keyword['source'] = 'enhanced_llm'
                
                # 添加上下文（如果没有提供）
                if 'context' not in keyword:
                    keyword['context'] = self._extract_context(text, keyword['name'])
                
                # 检查证据完整性
                if 'evidence' not in keyword:
                    logger.warning(f"关键词 {keyword['name']} 缺少证据信息")
                    # 添加基本证据信息
                    keyword['evidence'] = {
                        'text_position': '未提供',
                        'context': keyword['context'],
                        'support_reason': 'LLM提取',
                        'type_basis': 'LLM判断',
                        'confidence_basis': 'LLM评估'
                    }
                
                # 检查领域参考
                if 'domain_reference' not in keyword:
                    keyword['domain_reference'] = self.prompt_engineering.get_domain_knowledge_reference(
                        keyword['name'], keyword.get('type')
                    )
                
                processed_keywords.append(keyword)
            
            logger.info(f"增强LLM提取到 {len(processed_keywords)} 个关键词")
            return processed_keywords
                
        except Exception as e:
            logger.error(f"增强LLM关键词提取失败: {e}")
            return []
    
    def _deduplicate_and_rank_keywords(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重和排序关键词"""
        # 按名称去重，保留置信度最高的
        unique_keywords = {}
        for keyword in keywords:
            name = keyword['name'].lower()
            if name not in unique_keywords or keyword['confidence'] > unique_keywords[name]['confidence']:
                unique_keywords[name] = keyword
        
        # 按置信度排序
        return sorted(unique_keywords.values(), key=lambda x: x['confidence'], reverse=True)
    
    def extract_relationships_from_text(self, text: str, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从文本中提取知识点之间的关系
        
        Args:
            text: 输入文本
            keywords: 已提取的关键词列表
            
        Returns:
            提取的关系列表
        """
        relationships = []
        
        try:
            # 1. 基于规则的关系提取
            rule_based_relationships = self._extract_relationships_by_rules(text, keywords)
            # 确保只添加字典对象
            for rel in rule_based_relationships:
                if isinstance(rel, dict):
                    relationships.append(rel)
                else:
                    logger.warning(f"跳过非字典对象的关系: {type(rel)}")
            
            # 2. 如果启用LLM，使用LLM进行提取
            if self.config.openai_api_key:
                llm_relationships = self._extract_relationships_by_llm(text, keywords)
                # 确保只添加字典对象
                for rel in llm_relationships:
                    if isinstance(rel, dict):
                        relationships.append(rel)
                    else:
                        logger.warning(f"跳过非字典对象的关系: {type(rel)}")
        except Exception as e:
            logger.error(f"关系提取过程中出错: {e}")
            relationships = []
        
        # 3. 去重和排序
        try:
            unique_relationships = self._deduplicate_and_rank_relationships(relationships)
        except Exception as e:
            logger.error(f"关系去重和排序失败: {e}")
            unique_relationships = relationships
        
        # 4. 限制返回数量
        return unique_relationships[:self.config.max_relationships_per_text]
    
    def _extract_relationships_by_rules(self, text: str, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于规则的关系提取"""
        relationships = []
        
        try:
            keyword_names = [kw['name'].lower() for kw in keywords if isinstance(kw, dict)]
            
            # 遍历关系模式
            for rel_type, rel_info in self.relationship_patterns.items():
                for pattern in rel_info['patterns']:
                    try:
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            # 提取匹配的实体
                            entities = []
                            for i in range(1, len(match.groups()) + 1):
                                entity = match.group(i).strip()
                                entity_lower = entity.lower()
                                
                                # 检查是否是已知关键词
                                if entity_lower in keyword_names:
                                    # 找到对应的关键词对象
                                    for kw in keywords:
                                        if isinstance(kw, dict) and kw['name'].lower() == entity_lower:
                                            entities.append(kw)
                                            break
                                else:
                                    # 如果不是已知关键词，创建一个新的关键词对象
                                    node_type = self._determine_node_type(entity, 'concepts')
                                    entities.append({
                                        'name': entity,
                                        'type': node_type,
                                        'confidence': 0.5,
                                        'source': 'rule_based_relationship',
                                        'context': self._extract_context(text, entity)
                                    })
                            
                            # 如果找到了至少两个实体，创建关系
                            if len(entities) >= 2:
                                relationships.append({
                                    'source': entities[0],
                                    'target': entities[1],
                                    'type': rel_type,
                                    'confidence': rel_info['confidence'],
                                    'context': match.group(0),
                                    'extraction_method': 'rule_based'
                                })
                    except Exception as e:
                        logger.error(f"关系模式匹配失败: {e}, 模式: {pattern}")
                        continue
        except Exception as e:
            logger.error(f"基于规则的关系提取失败: {e}")
        
        return relationships
    
    def _extract_relationships_by_llm(self, text: str, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用增强的LLM提示工程提取关系"""
        try:
            # 使用增强的提示工程
            prompt_data = self.prompt_engineering.build_enhanced_relationship_extraction_prompt(text, keywords)
            result = self.prompt_engineering.call_llm_with_enhanced_prompt(prompt_data)
            
            # 检查是否有错误
            if "error" in result:
                logger.error(f"LLM关系提取失败: {result['error']}")
                return []
            
            # 确保结果是列表
            if not isinstance(result, list):
                logger.warning(f"LLM返回的不是列表: {type(result)}")
                return []
            
            # 处理提取的关系
            processed_relationships = []
            for rel in result:
                if not isinstance(rel, dict):
                    logger.warning(f"跳过非字典对象的关系: {type(rel)}")
                    continue
                
                # 添加提取方法标记
                rel['extraction_method'] = 'enhanced_llm'
                
                # 添加上下文（如果没有提供）
                if 'context' not in rel:
                    rel['context'] = text
                
                # 确保source和target是字典对象
                if 'source' in rel and not isinstance(rel['source'], dict):
                    rel['source'] = {'name': str(rel['source']), 'type': 'Unknown'}
                
                if 'target' in rel and not isinstance(rel['target'], dict):
                    rel['target'] = {'name': str(rel['target']), 'type': 'Unknown'}
                
                # 检查证据完整性
                if 'evidence' not in rel:
                    logger.warning(f"关系 {rel.get('source', {}).get('name', '')}-{rel.get('type', '')}-{rel.get('target', {}).get('name', '')} 缺少证据信息")
                    # 添加基本证据信息
                    rel['evidence'] = {
                        'text_position': '未提供',
                        'context': rel['context'],
                        'logic_basis': 'LLM判断',
                        'direction_basis': 'LLM判断',
                        'confidence_basis': 'LLM评估'
                    }
                
                # 检查领域参考
                if 'domain_reference' not in rel:
                    source_name = rel.get('source', {}).get('name', '')
                    source_type = rel.get('source', {}).get('type', '')
                    target_name = rel.get('target', {}).get('name', '')
                    target_type = rel.get('target', {}).get('type', '')
                    
                    rel['domain_reference'] = {
                        'source': self.prompt_engineering.get_domain_knowledge_reference(source_name, source_type),
                        'target': self.prompt_engineering.get_domain_knowledge_reference(target_name, target_type)
                    }
                
                processed_relationships.append(rel)
            
            logger.info(f"增强LLM提取到 {len(processed_relationships)} 个关系")
            return processed_relationships
                
        except Exception as e:
            logger.error(f"增强LLM关系提取失败: {e}")
            return []
    
    def _deduplicate_and_rank_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重和排序关系"""
        # 按源、目标、类型去重，保留置信度最高的
        unique_relationships = {}
        for rel in relationships:
            # 确保rel是字典对象
            if not isinstance(rel, dict):
                logger.warning(f"跳过非字典对象的关系: {type(rel)}")
                continue
                
            try:
                # 安全获取源、目标和类型
                source = rel.get('source', {})
                target = rel.get('target', {})
                rel_type = rel.get('type', '')
                
                # 确保source和target是字典对象
                if not isinstance(source, dict):
                    source = {'name': str(source), 'type': 'Unknown'}
                
                if not isinstance(target, dict):
                    target = {'name': str(target), 'type': 'Unknown'}
                
                source_name = source.get('name', '').lower()
                target_name = target.get('name', '').lower()
                
                if not source_name or not target_name or not rel_type:
                    logger.warning(f"跳过不完整的关系: {rel}")
                    continue
                
                key = (source_name, target_name, rel_type)
                if key not in unique_relationships or rel.get('confidence', 0) > unique_relationships[key].get('confidence', 0):
                    unique_relationships[key] = rel
            except Exception as e:
                logger.error(f"处理关系时出错: {e}, 关系: {rel}")
                continue
        
        # 按置信度排序
        try:
            return sorted(unique_relationships.values(), key=lambda x: x.get('confidence', 0), reverse=True)
        except Exception as e:
            logger.error(f"关系排序失败: {e}")
            return list(unique_relationships.values())
    
    def save_to_neo4j(self, keywords: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        将提取的关键词和关系保存到Neo4j知识图谱
        
        Args:
            keywords: 关键词列表
            relationships: 关系列表
            
        Returns:
            保存统计信息
        """
        stats = {
            'nodes_created': 0,
            'nodes_updated': 0,
            'relationships_created': 0,
            'errors': 0
        }
        
        with self.driver.session() as session:
            try:
                # 1. 保存/更新节点
                for keyword in keywords:
                    try:
                        # 构建属性字典
                        props = {
                            'name': keyword['name'],
                            'confidence': keyword.get('confidence', 0.5),
                            'source': keyword.get('source', 'unknown'),
                            'context': keyword.get('context', '')
                        }
                        
                        # 如果有描述信息，添加到属性中
                        if 'description' in keyword:
                            props['description'] = keyword['description']
                        
                        # 构建Cypher查询 - 确保节点标签不包含空格
                        node_label = keyword['type'].replace(' ', '_')
                        cypher = f"""
                        MERGE (n:{node_label} {{name: $name}})
                        SET n += $props
                        RETURN n
                        """
                        
                        result = session.run(cypher, name=keyword['name'], props=props)
                        
                        # 检查是创建还是更新
                        if result.single():
                            stats['nodes_updated'] += 1
                        else:
                            stats['nodes_created'] += 1
                            
                    except Exception as e:
                        logger.error(f"保存节点失败 {keyword['name']}: {e}")
                        stats['errors'] += 1
                
                # 2. 保存关系
                for rel in relationships:
                    try:
                        # 构建关系属性
                        rel_props = {
                            'confidence': rel.get('confidence', 0.5),
                            'context': rel.get('context', ''),
                            'extraction_method': rel.get('extraction_method', 'unknown')
                        }
                        
                        # 如果有描述信息，添加到属性中
                        if 'description' in rel:
                            rel_props['description'] = rel['description']
                        
                        # 构建Cypher查询 - 确保节点标签不包含空格
                        source_label = rel['source']['type'].replace(' ', '_')
                        target_label = rel['target']['type'].replace(' ', '_')
                        cypher = f"""
                        MATCH (a:{source_label} {{name: $source_name}})
                        MATCH (b:{target_label} {{name: $target_name}})
                        MERGE (a)-[r:{rel['type']}]->(b)
                        SET r += $props
                        RETURN r
                        """
                        
                        session.run(
                            cypher,
                            source_name=rel['source']['name'],
                            target_name=rel['target']['name'],
                            props=rel_props
                        )
                        
                        stats['relationships_created'] += 1
                        
                    except Exception as e:
                        logger.error(f"保存关系失败 {rel['source']['name']}-{rel['type']}-{rel['target']['name']}: {e}")
                        stats['errors'] += 1
                
                logger.info(f"知识图谱更新完成: {stats}")
                
            except Exception as e:
                logger.error(f"保存到Neo4j失败: {e}")
                stats['errors'] += 1
        
        return stats
    
    def process_course_content(self, content: str, save_to_graph: bool = True) -> Dict[str, Any]:
        """
        处理课程内容，提取知识点和关系
        
        Args:
            content: 课程内容文本
            save_to_graph: 是否保存到知识图谱
            
        Returns:
            处理结果，包括提取的关键词、关系和统计信息
        """
        logger.info("开始处理课程内容...")
        
        # 1. 提取关键词
        logger.info("提取知识点关键字...")
        keywords = self.extract_keywords_from_text(content)
        logger.info(f"提取到 {len(keywords)} 个关键字")
        
        # 2. 提取关系
        logger.info("提取知识点关系...")
        relationships = self.extract_relationships_from_text(content, keywords)
        logger.info(f"提取到 {len(relationships)} 个关系")
        
        # 3. 保存到知识图谱
        stats = {}
        if save_to_graph:
            logger.info("保存到知识图谱...")
            stats = self.save_to_neo4j(keywords, relationships)
        
        # 4. 返回结果
        result = {
            'keywords': keywords,
            'relationships': relationships,
            'stats': stats,
            'content_length': len(content)
        }
        
        logger.info("课程内容处理完成")
        return result
    
    def process_course_file(self, file_path: str, save_to_graph: bool = True) -> Dict[str, Any]:
        """
        处理课程文件，提取知识点和关系
        
        Args:
            file_path: 课程文件路径
            save_to_graph: 是否保存到知识图谱
            
        Returns:
            处理结果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"处理文件: {file_path}")
            return self.process_course_content(content, save_to_graph)
            
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
            return {'error': str(e)}

def main():
    """主函数，用于测试"""
    # 配置系统
    config = KnowledgeExtractionConfig(
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_auth=(
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "aixi1314")
        ),
        openai_api_key=os.getenv("ZHIPUAI_API_KEY", ""),
        openai_model=os.getenv("ZHIPUAI_MODEL", "glm-4-flash")
    )
    
    # 初始化提取器
    extractor = KnowledgeExtractor(config)
    
    try:
        # 示例课程内容
        sample_content = """
        TCP/IP协议栈是互联网的核心协议族，包括应用层、传输层、网络层和链路层。
        
        传输控制协议(TCP)是一种面向连接的、可靠的传输层协议，它通过三次握手建立连接，
        通过四次挥手断开连接。TCP提供流量控制和拥塞控制机制，确保数据可靠传输。
        
        用户数据报协议(UDP)是一种无连接的传输层协议，它不保证数据可靠传输，
        但具有低延迟的特点，适用于实时应用如视频流和在线游戏。
        
        路由器是网络层设备，负责在不同网络之间转发数据包。路由器使用路由协议如OSPF
        和BGP来学习网络拓扑，并做出转发决策。
        
        防火墙是网络安全设备，用于保护内部网络免受外部攻击。防火墙可以通过包过滤、
        状态检测和应用层网关等技术实现网络安全策略。
        
        当网络出现故障时，需要使用网络诊断工具如ping和traceroute来定位问题。
        常见的网络问题包括网络不通、网速慢和DNS解析失败等。
        """
        
        # 处理课程内容
        result = extractor.process_course_content(sample_content)
        
        # 打印结果
        print("\n=== 提取的关键词 ===")
        for kw in result['keywords']:
            print(f"- {kw['name']} ({kw['type']}, 置信度: {kw['confidence']:.2f})")
        
        print("\n=== 提取的关系 ===")
        for rel in result['relationships']:
            print(f"- {rel['source']['name']} --[{rel['type']}]--> {rel['target']['name']} (置信度: {rel['confidence']:.2f})")
        
        print(f"\n=== 统计信息 ===")
        for key, value in result['stats'].items():
            print(f"- {key}: {value}")
    
    finally:
        extractor.close()

if __name__ == "__main__":
    main()