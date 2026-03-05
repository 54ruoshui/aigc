"""
增强版知识提取系统 - 集成基于技能的验证功能
提高大模型AI提取知识点的准确性和关系正确性
"""

import os
import re
import json
import logging
from typing import List, Dict, Tuple, Any, Optional, Set
from dataclasses import dataclass, field
from neo4j import GraphDatabase, exceptions
import requests
from dotenv import load_dotenv

# 导入基础知识提取器和技能验证系统
from .knowledge_extraction import KnowledgeExtractor, KnowledgeExtractionConfig
from .skill_based_validation import SkillBasedValidationSystem, ValidationResult

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedExtractionConfig(KnowledgeExtractionConfig):
    """增强版知识点提取配置"""
    # 验证配置
    enable_validation: bool = True  # 是否启用验证
    min_validation_confidence: float = 0.6  # 最小验证置信度（高要求标准）
    auto_filter_invalid: bool = True  # 是否自动过滤无效项目
    
    # 技能验证配置
    validation_skills: List[str] = field(default_factory=lambda: [
        'DomainKnowledgeValidator',
        'ConsistencyValidator', 
        'SemanticValidator',
        'RelationshipValidator'
    ])
    
    # 重试配置
    max_retry_attempts: int = 2  # 最大重试次数
    retry_on_validation_failure: bool = True  # 验证失败时是否重试
    
    # 反馈学习配置
    enable_feedback_learning: bool = True  # 是否启用反馈学习
    feedback_threshold: float = 0.7  # 反馈阈值

class EnhancedKnowledgeExtractor(KnowledgeExtractor):
    """增强版知识点提取器 - 集成技能验证"""
    
    def __init__(self, config: EnhancedExtractionConfig):
        super().__init__(config)
        self.config = config
        self.validation_system = None
        
        # 初始化验证系统
        if config.enable_validation:
            self._init_validation_system()
        
        # 反馈学习数据
        self.feedback_data = {
            'accepted_items': [],
            'rejected_items': [],
            'correction_patterns': {}
        }
    
    def _init_validation_system(self):
        """初始化验证系统"""
        try:
            validation_config = {
                'openai_api_key': self.config.openai_api_key,
                'openai_model': self.config.openai_model,
                'openai_base_url': self.config.openai_base_url
            }
            
            self.validation_system = SkillBasedValidationSystem(validation_config)
            logger.info("✅ 技能验证系统初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 验证系统初始化失败: {e}")
            self.validation_system = None
    
    def extract_and_validate_keywords(self, text: str, use_llm: bool = True) -> List[Dict[str, Any]]:
        """
        提取并验证知识点关键字
        
        Args:
            text: 输入文本
            use_llm: 是否使用LLM进行提取
            
        Returns:
            验证后的关键字列表
        """
        # 1. 提取关键词
        keywords = self.extract_keywords_from_text(text, use_llm)
        logger.info(f"初步提取到 {len(keywords)} 个关键字")
        
        # 2. 验证关键词
        if self.validation_system and self.config.enable_validation:
            validated_keywords = self._validate_and_retry_keywords(keywords, text)
            logger.info(f"验证后保留 {len(validated_keywords)} 个有效关键字")
            return validated_keywords
        
        # 如果验证未启用，为每个关键词添加默认验证信息
        for keyword in keywords:
            keyword['validation'] = {
                'is_valid': True,
                'confidence': keyword.get('confidence', 0.8),
                'reason': '验证未启用，默认通过',
                'results': [],
                'suggestions': []
            }
        
        return keywords
    
    def _validate_and_retry_keywords(self, keywords: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """验证并重试关键词"""
        validated_keywords = []
        
        for keyword in keywords:
            # 验证关键词
            validated_keyword = self.validation_system.validate_knowledge(keyword)
            validation = validated_keyword.get('validation', {})
            
            # 如果验证通过且置信度足够，直接添加
            if validation.get('is_valid', False) and validation.get('confidence', 0) >= self.config.min_validation_confidence:
                validated_keywords.append(validated_keyword)
            # 如果验证失败但启用了重试，尝试重新提取
            elif self.config.retry_on_validation_failure and len(validated_keywords) < self.config.max_keywords_per_text:
                # 确保validation是一个ValidationResult对象
                if not isinstance(validation, dict):
                    validation = {
                        'is_valid': False,
                        'confidence': 0.1,
                        'reason': '验证失败',
                        'suggestions': ['请重新提取']
                    }
                retry_keyword = self._retry_keyword_extraction(keyword, text, validation)
                if retry_keyword:
                    validated_keywords.append(retry_keyword)
                else:
                    # 重试失败，保留原始关键词但添加验证信息
                    keyword['validation'] = validation
                    validated_keywords.append(keyword)
            else:
                # 即使验证未通过，也记录原因并添加，但降低置信度
                logger.info(f"关键词验证未通过: {keyword['name']}, 原因: {validation.get('reason', '未知')}")
                # 添加验证信息到原始关键词
                keyword['validation'] = validation
                validated_keywords.append(keyword)
        
        # 如果启用了自动过滤，只返回有效的关键词
        if self.config.auto_filter_invalid:
            return self.validation_system.filter_invalid_items(validated_keywords, self.config.min_validation_confidence)
        
        return validated_keywords
    
    def _retry_keyword_extraction(self, failed_keyword: Dict[str, Any], text: str, validation_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """重试关键词提取"""
        if not self.config.openai_api_key:
            return None
        
        try:
            # 构建重试提示
            suggestions = validation_result.get('suggestions', [])
            reason = validation_result.get('reason', '')
            
            system_prompt = f"""你是一个计算机网络领域的专家，之前提取的关键词验证失败。

失败原因: {reason}
改进建议: {'; '.join(suggestions)}

请根据失败原因和改进建议，重新提取或修正这个关键词，确保它符合计算机网络领域的特征。

要求：
1. 确保关键词属于计算机网络领域
2. 确保关键词类型正确
3. 确保描述准确
4. 返回JSON格式的修正结果

返回格式：
{{
  "name": "修正后的关键词名称",
  "type": "修正后的类型",
  "confidence": 0.8,
  "description": "修正后的描述"
}}"""
            
            user_prompt = f"""原始文本：
{text}

原始提取的关键词：
{json.dumps(failed_keyword, ensure_ascii=False, indent=2)}

请返回修正后的关键词JSON。"""
            
            headers = {
                "Authorization": f"Bearer {self.config.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 500
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
                timeout=60  # 增加超时时间到60秒
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # 解析修正后的关键词
            try:
                # 处理可能包含代码块标记的JSON
                json_content = content
                if json_content.startswith('```json'):
                    json_content = json_content[7:]  # 移除```json
                elif json_content.startswith('```'):
                    json_content = json_content[3:]  # 移除```
                if json_content.endswith('```'):
                    json_content = json_content[:-3]  # 移除结尾的```
                json_content = json_content.strip()
                
                # 尝试解析JSON，如果失败则尝试提取JSON部分
                try:
                    corrected_keyword = json.loads(json_content)
                except json.JSONDecodeError:
                    # 尝试从内容中提取JSON部分
                    import re
                    json_pattern = r'\{.*\}'
                    match = re.search(json_pattern, json_content, re.DOTALL)
                    if match:
                        json_str = match.group(0)
                        corrected_keyword = json.loads(json_str)
                    else:
                        raise json.JSONDecodeError("无法提取有效JSON", content, 0)
                # 保留原始信息
                corrected_keyword['source'] = failed_keyword.get('source', 'retry_llm')
                corrected_keyword['context'] = failed_keyword.get('context', '')
                corrected_keyword['original'] = failed_keyword
                
                # 验证修正后的关键词
                try:
                    validated_corrected = self.validation_system.validate_knowledge(corrected_keyword)
                    validation = validated_corrected.get('validation', {})
                    
                    if validation.get('is_valid', False) and validation.get('confidence', 0) >= self.config.min_validation_confidence:
                        # 只有当关键词真正发生变化时才记录日志
                        if failed_keyword['name'] != corrected_keyword['name']:
                            logger.info(f"关键词修正成功: {failed_keyword['name']} -> {corrected_keyword['name']}")
                        return validated_corrected
                    else:
                        logger.warning(f"关键词修正后仍无效: {corrected_keyword['name']}")
                        return validated_corrected  # 即使验证未通过也返回，让后续逻辑处理
                except Exception as e:
                    logger.error(f"验证修正后的关键词失败: {e}")
                    return corrected_keyword  # 返回修正后的关键词，即使验证失败
                    
            except json.JSONDecodeError:
                logger.warning(f"修正后的关键词不是有效JSON: {content}")
                
        except Exception as e:
            logger.error(f"关键词重试提取失败: {e}")
        
        return None
    
    def extract_and_validate_relationships(self, text: str, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取并验证知识点之间的关系
        
        Args:
            text: 输入文本
            keywords: 已提取的关键词列表
            
        Returns:
            验证后的关系列表
        """
        # 1. 提取关系
        try:
            relationships = self.extract_relationships_from_text(text, keywords)
            logger.info(f"初步提取到 {len(relationships)} 个关系")
        except Exception as e:
            logger.error(f"关系提取失败: {e}")
            relationships = []
        
        # 2. 验证关系
        if self.validation_system and self.config.enable_validation and relationships:
            try:
                validated_relationships = self._validate_and_retry_relationships(relationships, text)
                logger.info(f"验证后保留 {len(validated_relationships)} 个有效关系")
                return validated_relationships
            except Exception as e:
                logger.error(f"关系验证失败: {e}")
                # 如果验证失败，返回原始关系
                return relationships
        
        # 如果验证未启用，为每个关系添加默认验证信息
        for relationship in relationships:
            relationship['validation'] = {
                'is_valid': True,
                'confidence': relationship.get('confidence', 0.8),
                'reason': '验证未启用，默认通过',
                'results': [],
                'suggestions': []
            }
        
        return relationships
    
    def _validate_and_retry_relationships(self, relationships: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """验证并重试关系"""
        validated_relationships = []
        
        for relationship in relationships:
            # 确保relationship是字典对象
            if not isinstance(relationship, dict):
                logger.warning(f"跳过非字典对象的关系: {type(relationship)}")
                continue
                
            try:
                # 验证关系
                validated_relationship = self.validation_system.validate_relationship(relationship)
                validation = validated_relationship.get('validation', {})
                
                # 如果验证通过且置信度足够，直接添加
                if validation.get('is_valid', False) and validation.get('confidence', 0) >= self.config.min_validation_confidence:
                    validated_relationships.append(validated_relationship)
                # 如果验证失败但启用了重试，尝试重新提取
                elif self.config.retry_on_validation_failure and len(validated_relationships) < self.config.max_relationships_per_text:
                    # 确保validation是一个ValidationResult对象
                    if not isinstance(validation, dict):
                        validation = {
                            'is_valid': False,
                            'confidence': 0.1,
                            'reason': '验证失败',
                            'suggestions': ['请重新提取']
                        }
                    retry_relationship = self._retry_relationship_extraction(relationship, text, validation)
                    if retry_relationship:
                        validated_relationships.append(retry_relationship)
                else:
                    # 即使验证未通过，也记录原因并添加，但降低置信度
                    source_name = relationship.get('source', {}).get('name', '') if isinstance(relationship.get('source'), dict) else str(relationship.get('source', ''))
                    target_name = relationship.get('target', {}).get('name', '') if isinstance(relationship.get('target'), dict) else str(relationship.get('target', ''))
                    rel_type = relationship.get('type', '')
                    
                    logger.info(f"关系验证未通过: {source_name}-{rel_type}-{target_name}, 原因: {validation.get('reason', '未知')}")
                    # 添加验证信息到原始关系
                    relationship['validation'] = validation
                    validated_relationships.append(relationship)
            except Exception as e:
                logger.error(f"验证关系时出错: {e}, 关系: {relationship}")
                # 如果验证过程出错，仍然尝试保留原始关系
                if relationship.get('confidence', 0) >= 0.7:
                    validated_relationships.append(relationship)
        
        # 如果启用了自动过滤，只返回有效的关系
        if self.config.auto_filter_invalid:
            try:
                return self.validation_system.filter_invalid_items(validated_relationships, self.config.min_validation_confidence)
            except Exception as e:
                logger.error(f"过滤无效关系时出错: {e}")
                return validated_relationships
        
        return validated_relationships
    
    def _retry_relationship_extraction(self, failed_relationship: Dict[str, Any], text: str, validation_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """重试关系提取"""
        if not self.config.openai_api_key:
            return None
        
        try:
            # 构建重试提示
            suggestions = validation_result.get('suggestions', [])
            reason = validation_result.get('reason', '')
            
            source_name = failed_relationship.get('source', {}).get('name', '')
            target_name = failed_relationship.get('target', {}).get('name', '')
            rel_type = failed_relationship.get('type', '')
            
            system_prompt = f"""你是一个计算机网络领域的专家，之前提取的关系验证失败。

失败原因: {reason}
改进建议: {'; '.join(suggestions)}

请根据失败原因和改进建议，重新提取或修正这个关系，确保它在计算机网络领域中是合理的。

要求：
1. 确保关系类型正确
2. 确保关系方向合理
3. 确保源和目标节点之间的关系符合逻辑
4. 返回JSON格式的修正结果

返回格式：
{{
  "source": {{"name": "源节点名称", "type": "源节点类型"}},
  "target": {{"name": "目标节点名称", "type": "目标节点类型"}},
  "type": "修正后的关系类型",
  "confidence": 0.8,
  "description": "关系描述"
}}"""
            
            user_prompt = f"""原始文本：
{text}

原始提取的关系：
{json.dumps(failed_relationship, ensure_ascii=False, indent=2)}

请返回修正后的关系JSON。"""
            
            headers = {
                "Authorization": f"Bearer {self.config.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 500
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
                timeout=60  # 增加超时时间到60秒
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # 解析修正后的关系
            try:
                # 处理可能包含代码块标记的JSON
                json_content = content
                if json_content.startswith('```json'):
                    json_content = json_content[7:]  # 移除```json
                elif json_content.startswith('```'):
                    json_content = json_content[3:]  # 移除```
                if json_content.endswith('```'):
                    json_content = json_content[:-3]  # 移除结尾的```
                json_content = json_content.strip()
                
                # 尝试解析JSON，如果失败则尝试提取JSON部分
                try:
                    corrected_relationship = json.loads(json_content)
                except json.JSONDecodeError:
                    # 尝试从内容中提取JSON部分
                    import re
                    json_pattern = r'\{.*\}'
                    match = re.search(json_pattern, json_content, re.DOTALL)
                    if match:
                        json_str = match.group(0)
                        corrected_relationship = json.loads(json_str)
                    else:
                        raise json.JSONDecodeError("无法提取有效JSON", content, 0)
                # 保留原始信息
                corrected_relationship['extraction_method'] = 'retry_llm'
                corrected_relationship['context'] = failed_relationship.get('context', '')
                corrected_relationship['original'] = failed_relationship
                
                # 验证修正后的关系
                try:
                    validated_corrected = self.validation_system.validate_relationship(corrected_relationship)
                    validation = validated_corrected.get('validation', {})
                    
                    if validation.get('is_valid', False) and validation.get('confidence', 0) >= self.config.min_validation_confidence:
                        logger.info(f"关系修正成功: {source_name}-{rel_type}-{target_name}")
                        return validated_corrected
                    else:
                        logger.warning(f"关系修正后仍无效: {corrected_relationship}")
                        return validated_corrected  # 即使验证未通过也返回，让后续逻辑处理
                except Exception as e:
                    logger.error(f"验证修正后的关系失败: {e}")
                    return corrected_relationship  # 返回修正后的关系，即使验证失败
                    
            except json.JSONDecodeError:
                logger.warning(f"修正后的关系不是有效JSON: {content}")
                
        except Exception as e:
            logger.error(f"关系重试提取失败: {e}")
        
        return None
    
    def process_course_content_with_validation(self, content: str, save_to_graph: bool = True, use_validation: bool = True) -> Dict[str, Any]:
        """
        处理课程内容，提取知识点和关系，并进行验证
        
        Args:
            content: 课程内容文本
            save_to_graph: 是否保存到知识图谱
            use_validation: 是否使用验证
            
        Returns:
            处理结果，包括提取的关键词、关系、验证结果和统计信息
        """
        logger.info("开始处理课程内容（增强版）...")
        logger.info(f"验证状态: {'启用' if use_validation else '禁用'}")
        
        # 初始化结果
        keywords = []
        relationships = []
        stats = {}
        validation_stats = {}
        
        try:
            # 1. 提取并验证关键词
            logger.info("提取并验证知识点关键字...")
            if use_validation and self.config.enable_validation:
                keywords = self.extract_and_validate_keywords(content)
            else:
                keywords = self.extract_keywords_from_text(content)
            logger.info(f"最终保留 {len(keywords)} 个关键字")
        except Exception as e:
            logger.error(f"关键词提取和验证失败: {e}")
            keywords = []
        
        try:
            # 2. 提取并验证关系
            logger.info("提取并验证知识点关系...")
            if use_validation and self.config.enable_validation:
                relationships = self.extract_and_validate_relationships(content, keywords)
            else:
                relationships = self.extract_relationships_from_text(content, keywords)
            logger.info(f"最终保留 {len(relationships)} 个关系")
        except Exception as e:
            logger.error(f"关系提取和验证失败: {e}")
            relationships = []
        
        # 3. 保存到知识图谱
        if save_to_graph:
            try:
                logger.info("保存到知识图谱...")
                stats = self.save_to_neo4j(keywords, relationships)
            except Exception as e:
                logger.error(f"保存到知识图谱失败: {e}")
                stats = {'errors': 1, 'message': str(e)}
        
        # 4. 获取验证统计
        try:
            if self.validation_system and use_validation and self.config.enable_validation:
                validation_stats = self.validation_system.get_validation_stats()
            else:
                # 如果验证未启用，返回空统计信息
                validation_stats = {
                    'total_validations': 0,
                    'validity_rate': 0,
                    'average_confidence': 0,
                    'message': '验证未启用'
                }
        except Exception as e:
            logger.error(f"获取验证统计失败: {e}")
            validation_stats = {
                'total_validations': 0,
                'validity_rate': 0,
                'average_confidence': 0,
                'error': str(e)
            }
        
        # 5. 返回结果
        result = {
            'keywords': keywords,
            'relationships': relationships,
            'stats': stats,
            'validation_stats': validation_stats,
            'content_length': len(content),
            'extraction_config': {
                'enable_validation': self.config.enable_validation,
                'min_validation_confidence': self.config.min_validation_confidence,
                'auto_filter_invalid': self.config.auto_filter_invalid
            }
        }
        
        logger.info("课程内容处理完成（增强版）")
        return result
    
    def submit_feedback(self, item_type: str, item: Dict[str, Any], is_correct: bool, correction: Dict[str, Any] = None):
        """
        提交反馈，用于改进提取质量
        
        Args:
            item_type: 项目类型 ('knowledge' 或 'relationship')
            item: 提取的项目
            is_correct: 项目是否正确
            correction: 如果不正确，提供修正信息
        """
        if not self.config.enable_feedback_learning:
            return
        
        feedback_entry = {
            'item': item,
            'is_correct': is_correct,
            'correction': correction,
            'timestamp': self._get_timestamp()
        }
        
        if is_correct:
            self.feedback_data['accepted_items'].append(feedback_entry)
        else:
            self.feedback_data['rejected_items'].append(feedback_entry)
            
            # 分析修正模式
            if correction:
                self._analyze_correction_pattern(item, correction)
        
        logger.info(f"收到{item_type}反馈: {'正确' if is_correct else '错误'}")
    
    def _analyze_correction_pattern(self, original: Dict[str, Any], correction: Dict[str, Any]):
        """分析修正模式，用于改进提取算法"""
        # 这里可以实现更复杂的模式分析逻辑
        # 简化版本：记录类型修正模式
        if 'type' in original and 'type' in correction:
            original_type = original['type']
            corrected_type = correction['type']
            
            if original_type != corrected_type:
                pattern_key = f"{original_type}->{corrected_type}"
                self.feedback_data['correction_patterns'][pattern_key] = \
                    self.feedback_data['correction_patterns'].get(pattern_key, 0) + 1
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """获取反馈摘要"""
        if not self.config.enable_feedback_learning:
            return {'message': '反馈学习未启用'}
        
        total_accepted = len(self.feedback_data['accepted_items'])
        total_rejected = len(self.feedback_data['rejected_items'])
        total_feedback = total_accepted + total_rejected
        
        if total_feedback == 0:
            return {'message': '暂无反馈数据'}
        
        return {
            'total_feedback': total_feedback,
            'accepted_items': total_accepted,
            'rejected_items': total_rejected,
            'acceptance_rate': total_accepted / total_feedback,
            'correction_patterns': self.feedback_data['correction_patterns']
        }

def main():
    """主函数，用于测试"""
    # 配置系统
    config = EnhancedExtractionConfig(
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_auth=(
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "aixi1314")
        ),
        openai_api_key=os.getenv("ZHIPUAI_API_KEY", ""),
        openai_model=os.getenv("ZHIPUAI_MODEL", "glm-4-flash"),
        
        # 验证配置
        enable_validation=True,
        min_validation_confidence=0.6,
        auto_filter_invalid=True,
        retry_on_validation_failure=True,
        
        # 反馈学习配置
        enable_feedback_learning=True
    )
    
    # 初始化增强版提取器
    extractor = EnhancedKnowledgeExtractor(config)
    
    try:
        # 示例课程内容（包含一些可能提取错误的内容）
        sample_content = """
        TCP/IP协议栈是互联网的核心协议族，包括应用层、传输层、网络层和链路层。
        
        传输控制协议(TCP)是一种面向连接的、可靠的传输层协议，它通过三次握手建立连接，
        通过四次挥手断开连接。TCP提供流量控制和拥塞控制机制，确保数据可靠传输。
        
        用户数据报协议(UDP)是一种无连接的传输层协议，它不保证数据可靠传输，
        但具有低延迟的特点，适用于实时应用如视频流和在线游戏。
        
        路由器是网络层设备，负责在不同网络之间转发数据包。路由器使用路由协议如OSPF
        和BGP来学习网络拓扑，并做出转发决策。
        
        苹果是一种水果，通常为红色或绿色，味道酸甜。
        
        防火墙是网络安全设备，用于保护内部网络免受外部攻击。防火墙可以通过包过滤、
        状态检测和应用层网关等技术实现网络安全策略。
        
        当网络出现故障时，需要使用网络诊断工具如ping和traceroute来定位问题。
        常见的网络问题包括网络不通、网速慢和DNS解析失败等。
        
        汽车使用TCP协议进行通信。
        """
        
        # 处理课程内容
        result = extractor.process_course_content_with_validation(sample_content)
        
        # 打印结果
        print("\n=== 提取并验证的关键词 ===")
        for kw in result['keywords']:
            validation = kw.get('validation', {})
            print(f"- {kw['name']} ({kw['type']}, 置信度: {kw.get('confidence', 0):.2f})")
            print(f"  验证: {'通过' if validation.get('is_valid', False) else '失败'} "
                  f"(验证置信度: {validation.get('confidence', 0):.2f})")
            if validation.get('suggestions'):
                print(f"  建议: {'; '.join(validation['suggestions'])}")
        
        print("\n=== 提取并验证的关系 ===")
        for rel in result['relationships']:
            source_name = rel.get('source', {}).get('name', '')
            target_name = rel.get('target', {}).get('name', '')
            rel_type = rel.get('type', '')
            validation = rel.get('validation', {})
            
            print(f"- {source_name} --[{rel_type}]--> {target_name} "
                  f"(置信度: {rel.get('confidence', 0):.2f})")
            print(f"  验证: {'通过' if validation.get('is_valid', False) else '失败'} "
                  f"(验证置信度: {validation.get('confidence', 0):.2f})")
            if validation.get('suggestions'):
                print(f"  建议: {'; '.join(validation['suggestions'])}")
        
        print(f"\n=== 统计信息 ===")
        for key, value in result['stats'].items():
            print(f"- {key}: {value}")
        
        print(f"\n=== 验证统计 ===")
        for key, value in result['validation_stats'].items():
            print(f"- {key}: {value}")
        
        # 模拟提交反馈
        if result['keywords']:
            # 提交一个正确关键词的反馈
            extractor.submit_feedback('knowledge', result['keywords'][0], True)
            
            # 提交一个错误关键词的反馈（假设最后一个关键词是错误的）
            if len(result['keywords']) > 1:
                extractor.submit_feedback('knowledge', result['keywords'][-1], False, 
                                         {'name': '修正后的关键词', 'type': 'CorrectType'})
        
        # 获取反馈摘要
        feedback_summary = extractor.get_feedback_summary()
        print(f"\n=== 反馈摘要 ===")
        for key, value in feedback_summary.items():
            print(f"- {key}: {value}")
    
    finally:
        extractor.close()

if __name__ == "__main__":
    main()