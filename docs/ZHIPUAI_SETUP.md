# 智谱AI集成说明

本系统已成功集成智谱AI（Zhipuai）作为大语言模型提供商，替代了原有的OpenAI接口。

## 🔧 配置步骤

### 1. 获取智谱AI API密钥

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册账号并登录
3. 进入控制台 → API密钥管理
4. 创建新的API密钥
5. 复制密钥备用

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# 智谱AI配置
ZHIPUAI_API_KEY=你的API密钥
ZHIPUAI_MODEL=glm-4
ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# 其他配置保持不变...
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=aixi1314
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 🚀 启动系统

```bash
# Web界面
python run.py --mode web

# 命令行测试
python run.py --mode cli

# 系统测试
python run.py --mode test
```

## 📋 支持的模型

- **glm-4-flash**: 智谱AI最新旗舰模型，性能最佳，推荐使用
- **glm-4-air**: 轻量级模型，响应更快，成本更低
- **glm-3-turbo**: 经典模型，兼容性好

## 🔍 验证配置

启动系统后，可以通过以下方式验证智谱AI是否正常工作：

1. **Web界面测试**：
   - 访问 http://localhost:5000
   - 输入问题："TCP和UDP有什么区别？"
   - 查看是否能正常生成答案

2. **命令行测试**：
   ```bash
   python run.py --mode cli
   # 输入相同问题测试
   ```

3. **查看日志**：
   - 检查是否有智谱AI相关的错误信息
   - 确认API调用成功

## ⚠️ 常见问题

### API密钥错误
```
错误：API密钥无效或已过期
解决：检查.env文件中的ZHIPUAI_API_KEY是否正确
```

### 网络连接问题
```
错误：无法连接到 open.bigmodel.cn
解决：检查网络连接，确保能访问智谱AI服务
```

### 模型名称错误
```
错误：不支持的模型名称
解决：使用 glm-4-flash、glm-4-air 或 glm-3-turbo
```

### 配额不足
```
错误：API配额已用完
解决：登录智谱AI控制台充值或升级套餐
```

## 💡 优化建议

1. **模型选择**：
   - 日常使用推荐 `glm-4`
   - 高并发场景可考虑 `glm-3-turbo`

2. **缓存利用**：
   - 系统已启用缓存，相同问题会快速响应
   - 缓存TTL默认30分钟，可在config.py中调整

3. **成本控制**：
   - 监控API使用量
   - 合理设置缓存时间
   - 优化问题长度

## 📞 技术支持

如遇到智谱AI相关问题：

1. 查看官方文档：https://open.bigmodel.cn/dev/api
2. 联系智谱AI客服
3. 提交项目Issue

---

**注意**：智谱AI API有调用频率限制，建议合理控制请求频率。