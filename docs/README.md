# 计算机网络知识图谱GraphRAG系统

基于Neo4j图数据库和大语言模型的智能问答系统，专门用于计算机网络领域的知识检索和问答。

## 🌟 功能特点

- **智能问答**: 基于大语言模型的自然语言问答
- **图数据检索**: 从知识图谱中检索相关信息
- **可视化展示**: 交互式图谱可视化界面
- **多模式支持**: 支持Web界面、命令行和测试模式
- **实时搜索**: 实时节点搜索和建议
- **路径分析**: 查找节点间的关系路径

## 🏗️ 系统架构

```
GraphRAG System
├── 数据层 (Neo4j)
│   ├── 实体节点 (Protocol, Device, Layer, etc.)
│   └── 关系边 (APPLY_TO, WORKS_AT, RELATED_TO, etc.)
├── 检索层 (GraphRetriever)
│   ├── 关键词搜索
│   ├── 语义搜索
│   ├── 邻居检索
│   └── 路径查找
├── 生成层 (LLMGenerator)
│   ├── 上下文格式化
│   └── 答案生成
└── 应用层 (Web/CLI)
    ├── Flask Web应用
    ├── RESTful API
    └── 命令行界面
```

## 📋 知识图谱数据

系统包含以下类型的实体和关系：

### 实体类型
- **Protocol**: 网络协议 (TCP, UDP, HTTP, HTTPS, etc.)
- **Device**: 网络设备 (路由器, 交换机, 防火墙, etc.)
- **Layer**: 网络层次 (应用层, 传输层, 网络层, etc.)
- **Knowledge**: 知识点 (三次握手, 四次挥手, etc.)
- **SecurityConcept**: 安全概念 (加密, 防火墙, etc.)
- **NetworkType**: 网络类型 (局域网, 广域网, etc.)
- **Topology**: 网络拓扑 (星型, 环型, etc.)
- **Problem/Solution**: 问题和解决方案

### 关系类型
- **APPLY_TO**: 应用于
- **WORKS_AT**: 工作于
- **BELONGS_TO**: 属于
- **HAS_FUNCTION**: 具有功能
- **RELATED_TO**: 相关于
- **DEPENDS_ON**: 依赖于
- **ATTACKS**: 攻击
- **PROTECTS**: 保护
- **SOLVED_BY**: 解决方案

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd graph-rag-system

# 安装依赖
pip install -r requirements.txt

# 启动Neo4j数据库
# 确保Neo4j运行在 localhost:7687
# 默认用户名: neo4j, 密码: aixi1314
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=aixi1314
NEO4J_DATABASE=neo4j

# 智谱AI配置
ZHIPUAI_API_KEY=your-zhipuai-api-key
ZHIPUAI_MODEL=glm-4
ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# Web配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

**获取智谱AI API密钥**：
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册并登录账号
3. 在控制台创建API密钥
4. 将密钥填入 `.env` 文件中的 `ZHIPUAI_API_KEY`

### 3. 初始化知识图谱

```bash
# 运行数据写入脚本
python write_data.py
```

### 4. 启动系统

```bash
# Web界面模式
python run.py --mode web --host 0.0.0.0 --port 5000

# 命令行模式
python run.py --mode cli

# 测试模式
python run.py --mode test
```

## 📖 使用指南

### Web界面

1. 访问 `http://localhost:5000`
2. 在搜索框中输入问题，例如：
   - "TCP和UDP有什么区别？"
   - "路由器的工作原理是什么？"
   - "如何解决网络环路问题？"
3. 点击"提问"按钮或按回车键
4. 查看生成的答案和可视化图谱

### API接口

#### 提交查询
```http
POST /api/query
Content-Type: application/json

{
    "question": "TCP和UDP有什么区别？"
}
```

#### 搜索节点
```http
GET /api/search_nodes?q=TCP
```

#### 获取节点邻居
```http
GET /api/node_neighbors/TCP
```

#### 获取图统计
```http
GET /api/graph_stats
```

### 命令行界面

```bash
# 直接运行主程序
python graph_rag_system.py

# 或使用启动脚本
python run.py --mode cli
```

## 🔧 配置说明

### 检索参数
- `MAX_RETRIEVED_NODES`: 最大检索节点数 (默认: 20)
- `SEARCH_DEPTH`: 搜索深度 (默认: 2)
- `SIMILARITY_THRESHOLD`: 相似度阈值 (默认: 0.7)

### 生成参数
- `MAX_CONTEXT_LENGTH`: 最大上下文长度 (默认: 4000)
- `ZHIPUAI_MODEL`: 使用的模型 (默认: glm-4-flash)
  - `glm-4-flash`: 智谱AI最新模型，性能最佳，推荐使用
  - `glm-4-air`: 轻量级模型，响应更快，成本更低
  - `glm-3-turbo`: 经典模型，兼容性好

### 缓存配置
- `ENABLE_CACHE`: 启用缓存 (默认: True)
- `CACHE_TTL`: 缓存过期时间 (默认: 3600秒)

## 🧪 测试

运行测试套件：

```bash
# 运行系统测试
python run.py --mode test

# 或直接调用测试函数
python graph_rag_system.py test
```

测试包括：
- 基本检索功能
- 邻居检索
- 路径查找
- 完整查询流程

## 📊 性能优化

### 检索优化
- 使用索引加速查询
- 限制检索结果数量
- 实现缓存机制

### 生成优化
- 控制上下文长度
- 使用流式响应
- 批量处理请求

### 图优化
- 定期清理无用数据
- 优化Cypher查询
- 使用图算法库

## 🔍 示例查询

### 协议比较
- "TCP和UDP有什么区别？"
- "HTTP和HTTPS的关系是什么？"
- "OSPF和BGP的区别是什么？"

### 设备功能
- "路由器的工作原理是什么？"
- "交换机和集线器的区别？"
- "防火墙有哪些类型？"

### 故障排除
- "如何解决网络环路问题？"
- "网络不通怎么办？"
- "DNS解析失败如何处理？"

### 概念解释
- "什么是VLAN，它有什么作用？"
- "三次握手和四次挥手的过程是什么？"
- "什么是子网掩码，如何计算？"

## 🛠️ 开发指南

### 添加新的实体类型

1. 在 `write_data.py` 中添加数据
2. 更新 `config.py` 中的颜色映射
3. 修改前端样式（如需要）

### 扩展检索功能

1. 在 `GraphRetriever` 类中添加新方法
2. 更新 `multi_strategy_retrieval` 函数
3. 添加相应的API端点

### 自定义生成逻辑

1. 修改 `LLMGenerator` 类
2. 调整提示词模板
3. 实现新的生成策略

## 📝 日志和监控

### 日志配置
```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 日志文件
logger = logging.getLogger(__name__)
logger.info("系统启动")
```

### 监控指标
- 查询响应时间
- 检索结果数量
- 错误率统计
- 系统资源使用

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 故障排除

### 常见问题

1. **Neo4j连接失败**
   - 检查Neo4j是否运行
   - 验证用户名密码
   - 确认端口配置

2. **智谱AI API错误**
   - 检查API密钥是否正确
   - 验证网络连接到 open.bigmodel.cn
   - 确认账户余额和API配额
   - 检查模型名称是否正确 (glm-4-flash, glm-4-air, glm-3-turbo)

3. **检索结果为空**
   - 检查知识图谱数据
   - 验证搜索关键词
   - 调整检索参数

4. **Web界面无法访问**
   - 检查端口占用
   - 验证防火墙设置
   - 查看错误日志

### 调试模式

```bash
# 启用调试模式
python run.py --mode web --debug

# 查看详细日志
export LOG_LEVEL=DEBUG
python run.py --mode web
```

## 📚 参考资料

- [Neo4j官方文档](https://neo4j.com/docs/)
- [智谱AI API文档](https://open.bigmodel.cn/dev/api#glm-4)
- [Flask文档](https://flask.palletsprojects.com/)
- [D3.js可视化库](https://d3js.org/)

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 参与讨论

---

**注意**: 本系统仅用于学习和研究目的，请勿用于生产环境。