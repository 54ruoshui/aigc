# 增强版GraphRAG Web应用使用指南

## 概述

增强版GraphRAG Web应用集成了基于技能的知识验证系统，提供了更高质量的知识点提取功能。通过多层次验证机制，有效解决了大模型AI提取知识点时可能不准确或关系错误的问题。

## 新增功能

### 1. 技能验证系统
- **领域知识验证**: 确保提取的知识点属于计算机网络领域
- **一致性验证**: 验证知识点内部属性的一致性
- **关系验证**: 验证知识点间关系的合理性
- **语义验证**: 使用大语言模型进行语义合理性验证

### 2. 反馈学习系统
- 收集用户反馈
- 分析修正模式
- 持续改进提取质量

### 3. 增强的用户界面
- 验证开关控制
- 实时验证统计
- 详细验证结果展示
- 反馈提交界面

## 快速开始

### 1. 环境配置

在启动应用前，请确保配置以下环境变量：

```bash
# 基础配置
ZHIPUAI_API_KEY=your-api-key
ZHIPUAI_MODEL=glm-4-flash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# 技能验证配置
ENABLE_SKILL_VALIDATION=true
MIN_VALIDATION_CONFIDENCE=0.6
AUTO_FILTER_INVALID=true
RETRY_ON_VALIDATION_FAILURE=true
ENABLE_FEEDBACK_LEARNING=true
```

### 2. 启动应用

```bash
# 方法1: 使用启动脚本
python run_enhanced_web_app.py

# 方法2: 直接运行
python web/enhanced_graph_rag_web.py
```

### 3. 访问应用

打开浏览器访问: http://localhost:5000

## 功能详解

### 知识点提取

#### 基础提取
1. 在文本框中输入要提取的内容
2. 点击"提取知识点"按钮
3. 查看提取结果

#### 验证增强提取
1. 确保"启用技能验证"开关已打开
2. 输入要提取的内容
3. 点击"提取知识点"按钮
4. 系统会自动验证并过滤无效内容

### 验证结果解读

#### 关键点验证状态
- ✅ **有效**: 通过所有验证检查
- ❌ **无效**: 未通过验证检查

#### 验证详情
- **验证原因**: 说明验证通过或失败的具体原因
- **改进建议**: 针对无效项目的改进建议

#### 验证统计
- **验证通过率**: 显示整体验证通过的比例
- **总验证数**: 显示验证的项目总数
- **平均置信度**: 显示所有项目的平均置信度

### 反馈功能

#### 提交反馈
1. 在提取结果页面，找到"反馈与改进"区域
2. 选择反馈类型：
   - **全部正确**: 所有提取结果都正确
   - **部分正确**: 部分结果正确
   - **需要修正**: 需要修正错误结果
3. 如果选择"部分正确"或"需要修正"，在文本框中描述具体问题
4. 点击"提交反馈"

#### 反馈效果
- 系统会记录反馈信息
- 分析常见错误模式
- 持续改进验证算法
- 提高未来提取质量

## 配置选项

### 技能验证配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| ENABLE_SKILL_VALIDATION | true | 是否启用技能验证 |
| MIN_VALIDATION_CONFIDENCE | 0.6 | 最小验证置信度 |
| AUTO_FILTER_INVALID | true | 是否自动过滤无效项目 |
| RETRY_ON_VALIDATION_FAILURE | true | 验证失败时是否重试 |
| ENABLE_FEEDBACK_LEARNING | true | 是否启用反馈学习 |

### 性能优化配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| FAST_START | false | 是否快速启动（延迟初始化） |
| FLASK_DEBUG | false | 是否启用调试模式 |
| PORT | 5000 | Web服务端口 |
| HOST | 0.0.0.0 | 监听地址 |

## API接口

### 1. 提取知识点

**请求**:
```http
POST /api/extract_knowledge
Content-Type: application/json

{
    "content": "要提取的文本内容",
    "use_validation": true
}
```

**响应**:
```json
{
    "success": true,
    "keywords": [...],
    "relationships": [...],
    "valid_keywords": [...],
    "valid_relationships": [...],
    "stats": {...},
    "validation_stats": {...},
    "message": "提取完成",
    "extraction_mode": "enhanced_with_validation"
}
```

### 2. 提交反馈

**请求**:
```http
POST /api/submit_feedback
Content-Type: application/json

{
    "item_type": "knowledge",
    "item": {...},
    "is_correct": false,
    "correction": {...}
}
```

**响应**:
```json
{
    "success": true,
    "message": "反馈提交成功",
    "feedback_summary": {...}
}
```

### 3. 获取验证统计

**请求**:
```http
GET /api/validation_stats
```

**响应**:
```json
{
    "total_validations": 100,
    "valid_count": 85,
    "invalid_count": 15,
    "validity_rate": 0.85,
    "average_confidence": 0.75
}
```

### 4. 获取系统配置

**请求**:
```http
GET /api/config
```

**响应**:
```json
{
    "features": {
        "skill_validation": true,
        "feedback_learning": true
    },
    "validation": {
        "enabled": true,
        "min_confidence": 0.6,
        "auto_filter": true
    }
}
```

## 故障排除

### 常见问题

#### 1. 技能验证未启用
**症状**: 界面显示"技能验证已禁用"
**解决方案**:
- 检查环境变量 `ENABLE_SKILL_VALIDATION=true`
- 确认API密钥配置正确
- 重启应用

#### 2. 验证通过率低
**症状**: 大部分项目被标记为无效
**解决方案**:
- 降低 `MIN_VALIDATION_CONFIDENCE` 值
- 检查输入内容是否属于目标领域
- 提交反馈帮助系统学习

#### 3. 反馈提交失败
**症状**: 点击反馈按钮无响应
**解决方案**:
- 确认 `ENABLE_FEEDBACK_LEARNING=true`
- 检查网络连接
- 查看浏览器控制台错误信息

#### 4. 性能问题
**症状**: 提取速度慢
**解决方案**:
- 启用 `FAST_START=true`
- 调整验证阈值
- 考虑禁用部分验证功能

### 日志查看

应用启动后，可以在控制台查看详细日志：

```bash
# 查看启动日志
INFO: 🔄 初始化增强版知识点提取器（带技能验证）...
INFO: ✅ 增强版知识点提取器初始化完成（技能验证已启用）

# 查看提取日志
INFO: 🔄 开始提取知识点，内容长度: 1234 字符
INFO: 📊 使用增强版提取器
INFO: ✅ 知识点提取完成: 创建了 5 个新节点，验证了 8 个项目，通过率 87.5%
```

## 最佳实践

### 1. 内容输入建议
- **内容长度**: 建议输入500-2000字符的内容
- **领域相关**: 确保内容与计算机网络领域相关
- **结构清晰**: 使用段落分隔，避免长段落

### 2. 验证配置建议
- **初学者**: 启用所有验证功能，使用默认阈值
- **高级用户**: 根据需要调整验证阈值
- **生产环境**: 启用自动过滤和反馈学习

### 3. 反馈提交建议
- **及时反馈**: 提取后立即提交反馈
- **具体描述**: 详细说明错误和期望结果
- **一致性**: 使用统一的反馈标准

### 4. 性能优化建议
- **批量处理**: 对于大量内容，分批处理
- **缓存利用**: 重复内容会使用缓存结果
- **阈值调整**: 根据实际需求调整验证阈值

## 扩展开发

### 添加自定义验证器

```python
from skill_based_validation import SkillValidator, ValidationResult

class CustomValidator(SkillValidator):
    def get_description(self) -> str:
        return "自定义验证器"
    
    def validate(self, item, context=None):
        # 实现验证逻辑
        return ValidationResult(
            is_valid=True,
            confidence=0.8,
            reason="通过自定义验证"
        )

# 注册验证器
enhanced_extractor.validation_system.add_validator(CustomValidator(config))
```

### 集成外部验证服务

```python
class ExternalAPIValidator(SkillValidator):
    def validate(self, item, context=None):
        # 调用外部API
        response = requests.post('https://api.example.com/validate', json=item)
        # 处理响应
        pass
```

## 版本更新

### v1.0 (当前版本)
- 基础技能验证功能
- 反馈学习系统
- 增强版Web界面

### 计划功能
- 更多验证器类型
- 可视化验证结果
- 批量处理优化
- 更多自定义选项

## 技术支持

如需技术支持，请：
1. 查看控制台日志
2. 检查环境变量配置
3. 参考故障排除指南
4. 提交详细的错误信息

---

**文档版本**: 1.0  
**最后更新**: 2026年3月2日  
**作者**: Kilo Code