"""
基于技能的知识验证系统
用于提高大模型AI提取知识点的准确性和关系正确性
"""

import os
import re
import json
import logging
from typing import List, Dict, Tuple, Any, Optional, Set
from dataclasses import dataclass
from abc import ABC, abstractmethod
from neo4j import GraphDatabase
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    confidence: float
    reason: str
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

class SkillValidator(ABC):
    """技能验证器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def validate(self, item: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """验证项目"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取技能描述"""
        pass

class DomainKnowledgeValidator(SkillValidator):
    """领域知识验证技能 - 验证提取的知识点是否符合计算机网络领域"""
    
    def get_description(self) -> str:
        return "验证提取的知识点是否属于计算机网络领域"
    
    def validate(self, item: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """验证知识点是否属于计算机网络领域"""
        name = item.get('name', '').lower()
        item_type = item.get('type', '').lower()
        description = item.get('description', '').lower()
        
        # 计算机网络核心关键词
        network_core_keywords = {
            'protocols': ['tcp', 'udp', 'http', 'https', 'ftp', 'smtp', 'dns', 'dhcp', 'ip', 'icmp', 'arp'],
            'devices': ['路由器', '交换机', '防火墙', '网关', '集线器', '中继器', '网桥', 'router', 'switch', 'firewall'],
            'layers': ['应用层', '传输层', '网络层', '数据链路层', '物理层', 'application layer', 'transport layer', 'network layer'],
            'concepts': ['网络', '协议', '数据包', '帧', '端口', '地址', '连接', 'network', 'protocol', 'packet', 'frame', 'port'],
            'security': ['加密', '认证', '防火墙', 'vpn', '攻击', '防护', 'encryption', 'authentication', 'vpn', 'attack']
        }
        
        # 计算匹配度
        total_score = 0
        max_score = 0
        
        for category, keywords in network_core_keywords.items():
            for keyword in keywords:
                max_score += 1
                if keyword in name or keyword in description:
                    total_score += 1
        
        # 如果没有匹配到任何核心关键词，可能不是网络领域知识点
        if max_score == 0:
            return ValidationResult(
                is_valid=False,
                confidence=0.1,
                reason="无法确定是否属于计算机网络领域",
                suggestions=["请确认该知识点是否与计算机网络相关"]
            )
        
        confidence = total_score / max_score
        is_valid = confidence >= 0.3  # 至少匹配30%的核心关键词
        
        if not is_valid:
            return ValidationResult(
                is_valid=False,
                confidence=confidence,
                reason=f"与计算机网络领域匹配度较低 ({confidence:.2f})",
                suggestions=["请确认该知识点是否属于计算机网络领域", "考虑添加更多网络相关上下文"]
            )
        
        return ValidationResult(
            is_valid=True,
            confidence=confidence,
            reason=f"符合计算机网络领域特征 (匹配度: {confidence:.2f})"
        )

class ConsistencyValidator(SkillValidator):
    """一致性验证技能 - 验证知识点内部属性的一致性"""
    
    def get_description(self) -> str:
        return "验证知识点内部属性的一致性"
    
    def validate(self, item: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """验证知识点内部属性的一致性"""
        name = item.get('name', '')
        item_type = item.get('type', '')
        confidence = item.get('confidence', 0.5)
        description = item.get('description', '')
        
        issues = []
        suggestions = []
        
        # 检查名称和类型的一致性
        type_name_mapping = {
            'Protocol': ['协议', 'protocol'],
            'Device': ['设备', '路由器', '交换机', '防火墙', 'router', 'switch', 'firewall'],
            'Layer': ['层', 'layer'],
            'Knowledge': ['概念', '原理', '机制', 'algorithm', 'concept'],
            'SecurityConcept': ['安全', '加密', '认证', 'security', 'encryption', 'authentication'],
            'NetworkType': ['网络', 'network', 'lan', 'wan'],
            'Problem': ['问题', '故障', '错误', 'problem', 'issue', 'error'],
            'Solution': ['解决方案', '方法', '策略', 'solution', 'method', 'strategy']
        }
        
        # 检查名称是否包含类型相关的关键词
        type_keywords = type_name_mapping.get(item_type, [])
        name_lower = name.lower()
        type_match = any(kw in name_lower for kw in type_keywords)
        
        if not type_match and type_keywords:
            issues.append(f"名称'{name}'与类型'{item_type}'可能不匹配")
            suggestions.append(f"考虑确认'{name}'是否确实属于'{item_type}'类型")
        
        # 检查置信度是否合理
        if confidence > 0.9 and not description:
            issues.append("高置信度但缺少描述信息")
            suggestions.append("为高置信度知识点添加详细描述")
        
        if confidence < 0.5 and len(name) > 10:
            issues.append("低置信度但名称较长且具体")
            suggestions.append("考虑提高该知识点的置信度或重新评估")
        
        # 检查描述是否与名称一致
        if description and name.lower() not in description.lower():
            # 检查描述中是否包含类型关键词
            desc_has_type_keywords = any(kw in description.lower() for kw in type_keywords)
            if not desc_has_type_keywords:
                issues.append("描述与名称/类型可能不一致")
                suggestions.append("确保描述内容与知识点名称和类型相符")
        
        is_valid = len(issues) == 0
        overall_confidence = confidence if is_valid else max(0.1, confidence - 0.2)
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=overall_confidence,
            reason="; ".join(issues) if issues else "内部属性一致",
            suggestions=suggestions
        )

class RelationshipValidator(SkillValidator):
    """关系验证技能 - 验证知识点间关系的合理性"""
    
    def get_description(self) -> str:
        return "验证知识点间关系的合理性"
    
    def validate(self, item: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """验证知识点间关系的合理性"""
        rel_type = item.get('type', '')
        source = item.get('source', {})
        target = item.get('target', {})
        confidence = item.get('confidence', 0.5)
        
        source_name = source.get('name', '').lower()
        source_type = source.get('type', '')
        target_name = target.get('name', '').lower()
        target_type = target.get('type', '')
        
        # 定义合理的关系组合
        valid_relationships = {
            'APPLY_TO': [
                ('Protocol', 'Layer'),  # 协议应用于层
                ('Device', 'NetworkType'),  # 设备应用于网络类型
                ('Solution', 'Problem')  # 解决方案应用于问题
            ],
            'DEPENDS_ON': [
                ('Protocol', 'Protocol'),  # 协议依赖于协议
                ('Device', 'Protocol'),  # 设备依赖于协议
                ('Knowledge', 'Protocol')  # 知识依赖于协议
            ],
            'RELATED_TO': [
                # 几乎任何类型都可以相关，所以这个关系比较宽松
            ],
            'WORKS_WITH': [
                ('Protocol', 'Protocol'),  # 协议协同工作
                ('Device', 'Device'),  # 设备协同工作
                ('Solution', 'Solution')  # 解决方案协同工作
            ],
            'PROTECTS': [
                ('SecurityConcept', 'Device'),  # 安全概念保护设备
                ('SecurityConcept', 'NetworkType'),  # 安全概念保护网络
                ('Solution', 'Problem')  # 解决方案保护(解决)问题
            ],
            'ATTACKS': [
                ('Problem', 'Device'),  # 问题攻击设备
                ('Problem', 'NetworkType')  # 问题攻击网络
            ],
            'SOLVED_BY': [
                ('Problem', 'Solution'),  # 问题通过解决方案解决
                ('Problem', 'Device')  # 问题通过设备解决
            ],
            'BELONGS_TO': [
                ('Protocol', 'Layer'),  # 协议属于层
                ('Device', 'NetworkType'),  # 设备属于网络类型
                ('Knowledge', 'Layer')  # 知识属于层
            ],
            'HAS_FUNCTION': [
                ('Device', 'Knowledge'),  # 设备具有功能
                ('Protocol', 'Knowledge')  # 协议具有功能
            ],
            'BETWEEN': [
                # 这个关系比较特殊，通常涉及三个实体
            ]
        }
        
        issues = []
        suggestions = []
        
        # 检查关系类型是否有效
        if rel_type not in valid_relationships:
            issues.append(f"未知的关系类型: {rel_type}")
            suggestions.append("使用预定义的关系类型")
            return ValidationResult(
                is_valid=False,
                confidence=0.1,
                reason="; ".join(issues),
                suggestions=suggestions
            )
        
        # 检查源和目标类型组合是否合理
        valid_combinations = valid_relationships.get(rel_type, [])
        
        # 如果有预定义的有效组合，检查是否匹配
        if valid_combinations:
            type_combination = (source_type, target_type)
            if type_combination not in valid_combinations and rel_type != 'RELATED_TO':
                issues.append(f"关系{rel_type}在{source_type}和{target_type}之间可能不合理")
                suggestions.append(f"确认{source_name}和{target_name}之间确实存在{rel_type}关系")
        
        # 检查自引用关系
        if source_name == target_name:
            issues.append("存在自引用关系")
            suggestions.append("确认自引用关系是否合理")
        
        # 检查关系方向
        if rel_type == 'SOLVED_BY' and source_type == 'Solution' and target_type == 'Problem':
            issues.append("关系方向可能错误")
            suggestions.append("考虑使用SOLVES关系而不是SOLVED_BY")
        
        is_valid = len(issues) == 0
        overall_confidence = confidence if is_valid else max(0.1, confidence - 0.3)
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=overall_confidence,
            reason="; ".join(issues) if issues else "关系合理",
            suggestions=suggestions
        )

class SemanticValidator(SkillValidator):
    """语义验证技能 - 使用LLM验证语义合理性"""
    
    def get_description(self) -> str:
        return "使用大语言模型验证语义合理性"
    
    def validate(self, item: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """使用LLM验证语义合理性"""
        try:
            # 准备验证内容
            if 'source' in item and 'target' in item:
                # 关系验证
                content = f"关系: {item['source']['name']} --[{item['type']}]--> {item['target']['name']}"
                validation_type = "relationship"
            else:
                # 知识点验证
                content = f"知识点: {item.get('name', '')} (类型: {item.get('type', '')})"
                validation_type = "knowledge"
            
            # 构建LLM验证提示
            system_prompt = f"""你是一个计算机网络领域的专家，请验证以下{validation_type}的语义合理性。

要求：
1. 判断该{validation_type}在计算机网络领域是否合理
2. 给出0-1之间的置信度评分
3. 如果不合理，说明原因并提供改进建议

返回JSON格式：
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "reason": "验证原因",
    "suggestions": ["建议1", "建议2"]
}}"""
            
            user_prompt = f"""请验证以下{validation_type}的合理性：

{content}

描述: {item.get('description', item.get('context', ''))}

请返回JSON格式的验证结果。"""
            
            headers = {
                "Authorization": f"Bearer {self.config.get('openai_api_key', '')}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.get('openai_model', 'glm-4-flash'),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            # 确保URL以/chat/completions结尾
            base_url = self.config.get('openai_base_url', 'https://open.bigmodel.cn/api/paas/v4')
            if not base_url.endswith('/chat/completions'):
                if base_url.endswith('/'):
                    base_url += 'chat/completions'
                else:
                    base_url += '/chat/completions'
            
            response = requests.post(
                base_url,
                headers=headers,
                json=data,
                timeout=60  # 增加超时时间到60秒
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # 解析LLM返回结果
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
                
                # 尝试解析JSON，如果失败则尝试提取JSON部分
                try:
                    llm_result = json.loads(json_content)
                except json.JSONDecodeError:
                    # 尝试从内容中提取JSON部分
                    import re
                    json_pattern = r'\{.*\}'
                    match = re.search(json_pattern, json_content, re.DOTALL)
                    if match:
                        json_str = match.group(0)
                        llm_result = json.loads(json_str)
                    else:
                        raise json.JSONDecodeError("无法提取有效JSON", content, 0)
                
                return ValidationResult(
                    is_valid=llm_result.get('is_valid', False),
                    confidence=llm_result.get('confidence', 0.5),
                    reason=llm_result.get('reason', ''),
                    suggestions=llm_result.get('suggestions', [])
                )
            except json.JSONDecodeError as e:
                logger.warning(f"LLM返回的不是有效JSON: {content}")
                logger.warning(f"解析错误: {e}")
                
                # 尝试更灵活的JSON解析
                try:
                    # 尝试提取suggestions数组
                    suggestions = []
                    suggestions_match = re.search(r'"suggestions":\s*\[(.*?)\]', content, re.DOTALL)
                    if suggestions_match:
                        suggestions_text = suggestions_match.group(1)
                        # 提取引号内的内容
                        suggestion_items = re.findall(r'"([^"]*)"', suggestions_text)
                        suggestions = [s for s in suggestion_items if s.strip()]
                    
                    # 尝试提取is_valid
                    is_valid = True
                    if 'false' in content.lower() or '无效' in content or '不正确' in content:
                        is_valid = False
                    
                    # 尝试提取confidence
                    confidence = 0.5
                    conf_match = re.search(r'"confidence":\s*([0-9.]+)', content)
                    if conf_match:
                        try:
                            confidence = float(conf_match.group(1))
                        except ValueError:
                            pass
                    
                    # 尝试提取reason
                    reason = "JSON解析失败，但内容分析显示"
                    reason_match = re.search(r'"reason":\s*"([^"]*)"', content)
                    if reason_match:
                        reason = reason_match.group(1)
                    
                    return ValidationResult(
                        is_valid=is_valid,
                        confidence=confidence,
                        reason=reason,
                        suggestions=suggestions
                    )
                except Exception as parse_error:
                    logger.error(f"灵活解析也失败: {parse_error}")
                    # 最后的回退选项
                    if any(keyword in content.lower() for keyword in ['valid', '正确', '合理', '准确', '符合']):
                        return ValidationResult(
                            is_valid=True,
                            confidence=0.7,
                            reason="LLM返回内容显示验证通过，但JSON解析失败",
                            suggestions=["请手动验证该项目的合理性"]
                        )
                    else:
                        return ValidationResult(
                            is_valid=True,
                            confidence=0.5,
                            reason="LLM验证失败，默认通过",
                            suggestions=["请手动验证该项目的合理性"]
                        )
                
        except Exception as e:
            logger.error(f"语义验证失败: {e}")
            return ValidationResult(
                is_valid=True,
                confidence=0.3,
                reason="语义验证失败，默认通过但置信度低",
                suggestions=["请手动验证该项目的合理性"]
            )

class SkillBasedValidationSystem:
    """基于技能的验证系统"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validators = self._init_validators()
        self.validation_history = []
    
    def _init_validators(self) -> List[SkillValidator]:
        """初始化验证器"""
        return [
            DomainKnowledgeValidator(self.config),
            ConsistencyValidator(self.config),
            SemanticValidator(self.config)
        ]
    
    def add_validator(self, validator: SkillValidator):
        """添加自定义验证器"""
        self.validators.append(validator)
        logger.info(f"添加验证器: {validator.get_description()}")
    
    def validate_knowledge(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """验证单个知识点"""
        validation_results = []
        overall_confidence = 0.0
        validator_count = 0
        
        # 运行所有验证器
        for validator in self.validators:
            if isinstance(validator, RelationshipValidator):
                continue  # 跳过关系验证器
                
            result = validator.validate(knowledge)
            validation_results.append({
                'validator': validator.get_description(),
                'result': result
            })
            overall_confidence += result.confidence
            validator_count += 1
        
        # 计算平均置信度
        avg_confidence = overall_confidence / validator_count if validator_count > 0 else 0
        
        # 判断是否通过验证 - 高要求标准
        valid_count = sum(1 for r in validation_results if r['result'].is_valid)
        is_valid = valid_count > 0 and avg_confidence >= 0.4  # 恢复较高的置信度阈值
        
        # 收集所有建议
        all_suggestions = []
        for r in validation_results:
            all_suggestions.extend(r['result'].suggestions)
        
        # 更新知识点的验证信息
        validated_knowledge = knowledge.copy()
        validated_knowledge['validation'] = {
            'is_valid': is_valid,
            'confidence': avg_confidence,
            'results': validation_results,
            'suggestions': all_suggestions
        }
        
        # 记录验证历史
        self.validation_history.append({
            'type': 'knowledge',
            'item': knowledge.get('name', ''),
            'timestamp': self._get_timestamp(),
            'is_valid': is_valid,
            'confidence': avg_confidence
        })
        
        return validated_knowledge
    
    def validate_relationship(self, relationship: Dict[str, Any]) -> Dict[str, Any]:
        """验证单个关系"""
        validation_results = []
        overall_confidence = 0.0
        
        # 运行所有验证器
        for validator in self.validators:
            if isinstance(validator, RelationshipValidator) or isinstance(validator, SemanticValidator):
                result = validator.validate(relationship)
                validation_results.append({
                    'validator': validator.get_description(),
                    'result': result
                })
                overall_confidence += result.confidence
        
        # 计算平均置信度
        avg_confidence = overall_confidence / 2  # 只运行了2个验证器
        
        # 判断是否通过验证 - 高要求标准
        is_valid = all(r['result'].is_valid for r in validation_results) and avg_confidence >= 0.6
        
        # 收集所有建议
        all_suggestions = []
        for r in validation_results:
            all_suggestions.extend(r['result'].suggestions)
        
        # 更新关系的验证信息
        validated_relationship = relationship.copy()
        validated_relationship['validation'] = {
            'is_valid': is_valid,
            'confidence': avg_confidence,
            'results': validation_results,
            'suggestions': all_suggestions
        }
        
        # 记录验证历史
        self.validation_history.append({
            'type': 'relationship',
            'item': f"{relationship.get('source', {}).get('name', '')}-{relationship.get('type', '')}-{relationship.get('target', {}).get('name', '')}",
            'timestamp': self._get_timestamp(),
            'is_valid': is_valid,
            'confidence': avg_confidence
        })
        
        return validated_relationship
    
    def validate_batch(self, items: List[Dict[str, Any]], item_type: str = 'knowledge') -> List[Dict[str, Any]]:
        """批量验证"""
        validated_items = []
        
        for item in items:
            if item_type == 'knowledge':
                validated_item = self.validate_knowledge(item)
            elif item_type == 'relationship':
                validated_item = self.validate_relationship(item)
            else:
                logger.warning(f"未知的项目类型: {item_type}")
                validated_item = item
            
            validated_items.append(validated_item)
        
        return validated_items
    
    def filter_invalid_items(self, items: List[Dict[str, Any]], min_confidence: float = 0.6) -> List[Dict[str, Any]]:
        """过滤无效项目"""
        valid_items = []
        
        for item in items:
            validation = item.get('validation', {})
            if validation.get('is_valid', False) and validation.get('confidence', 0) >= min_confidence:
                valid_items.append(item)
        
        return valid_items
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        if not self.validation_history:
            return {'message': '暂无验证历史'}
        
        total_validations = len(self.validation_history)
        valid_count = sum(1 for h in self.validation_history if h['is_valid'])
        invalid_count = total_validations - valid_count
        
        avg_confidence = sum(h['confidence'] for h in self.validation_history) / total_validations
        
        # 按类型统计
        knowledge_validations = [h for h in self.validation_history if h['type'] == 'knowledge']
        relationship_validations = [h for h in self.validation_history if h['type'] == 'relationship']
        
        return {
            'total_validations': total_validations,
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'validity_rate': valid_count / total_validations,
            'average_confidence': avg_confidence,
            'knowledge_validations': len(knowledge_validations),
            'relationship_validations': len(relationship_validations),
            'knowledge_validity_rate': sum(1 for h in knowledge_validations if h['is_valid']) / len(knowledge_validations) if knowledge_validations else 0,
            'relationship_validity_rate': sum(1 for h in relationship_validations if h['is_valid']) / len(relationship_validations) if relationship_validations else 0
        }
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

def main():
    """主函数，用于测试"""
    # 配置系统
    config = {
        'openai_api_key': os.getenv("ZHIPUAI_API_KEY", ""),
        'openai_model': os.getenv("ZHIPUAI_MODEL", "glm-4-flash"),
        'openai_base_url': os.getenv("ZHIPUAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
    }
    
    # 初始化验证系统
    validation_system = SkillBasedValidationSystem(config)
    
    # 添加关系验证器
    validation_system.add_validator(RelationshipValidator(config))
    
    # 测试知识点验证
    test_knowledge = [
        {
            'name': 'TCP',
            'type': 'Protocol',
            'confidence': 0.9,
            'description': '传输控制协议，提供可靠的面向连接的数据传输服务'
        },
        {
            'name': '苹果',
            'type': 'Protocol',
            'confidence': 0.8,
            'description': '一种水果'
        },
        {
            'name': '路由器',
            'type': 'Device',
            'confidence': 0.7,
            'description': '网络设备，用于转发数据包'
        }
    ]
    
    # 测试关系验证
    test_relationships = [
        {
            'source': {'name': 'TCP', 'type': 'Protocol'},
            'target': {'name': '传输层', 'type': 'Layer'},
            'type': 'APPLY_TO',
            'confidence': 0.9
        },
        {
            'source': {'name': '苹果', 'type': 'Protocol'},
            'target': {'name': '路由器', 'type': 'Device'},
            'type': 'PROTECTS',
            'confidence': 0.8
        }
    ]
    
    # 验证知识点
    print("=== 验证知识点 ===")
    validated_knowledge = validation_system.validate_batch(test_knowledge, 'knowledge')
    
    for item in validated_knowledge:
        print(f"\n知识点: {item['name']}")
        validation = item.get('validation', {})
        print(f"有效性: {validation.get('is_valid', False)}")
        print(f"置信度: {validation.get('confidence', 0):.2f}")
        if validation.get('suggestions'):
            print("建议:")
            for suggestion in validation['suggestions']:
                print(f"  - {suggestion}")
    
    # 验证关系
    print("\n=== 验证关系 ===")
    validated_relationships = validation_system.validate_batch(test_relationships, 'relationship')
    
    for item in validated_relationships:
        source_name = item.get('source', {}).get('name', '')
        target_name = item.get('target', {}).get('name', '')
        rel_type = item.get('type', '')
        
        print(f"\n关系: {source_name} --[{rel_type}]--> {target_name}")
        validation = item.get('validation', {})
        print(f"有效性: {validation.get('is_valid', False)}")
        print(f"置信度: {validation.get('confidence', 0):.2f}")
        if validation.get('suggestions'):
            print("建议:")
            for suggestion in validation['suggestions']:
                print(f"  - {suggestion}")
    
    # 获取验证统计
    print("\n=== 验证统计 ===")
    stats = validation_system.get_validation_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()