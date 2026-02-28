# 🚀 快速安装指南

看到你遇到了依赖冲突问题，这里是最简单的解决方案：

## 🔧 问题原因

你的错误是因为 `sentence-transformers` 包引入了大量依赖冲突：
- `datasets` 需要 `requests>=2.32.2`，但你有 `2.31.0`
- `streamlit` 需要 `protobuf<6.32.1`，但你有 `protobuf 6.32.1`
- 这些冲突导致安装失败

## ✅ 最简单的解决方案

### 方案1：使用最小化依赖（推荐）

```bash
# 激活你的aigc环境
conda activate aigc

# 只安装核心必需的包
pip install -r requirements-minimal.txt

# 验证安装
python -c "import neo4j, requests, flask, python_dotenv; print('✅ 核心依赖安装成功')"
```

### 方案2：强制忽略版本冲突

```bash
# 激活环境
conda activate aigc

# 强制安装，忽略版本冲突
pip install --force-reinstall -r requirements-minimal.txt
```

### 方案3：降级到Python 3.11（最稳定）

```bash
# 创建新环境
conda create -n graphrag-stable python=3.11
conda activate graphrag-stable

# 安装依赖
pip install -r requirements-minimal.txt
```

## 🎯 安装成功后的步骤

1. **配置智谱AI**：
   ```bash
   cp .env.example .env
   # 编辑.env文件，设置你的智谱AI API密钥
   ```

2. **启动系统**：
   ```bash
   python run.py --mode web
   # 访问 http://localhost:5000
   ```

3. **测试功能**：
   ```bash
   python run.py --mode test
   ```

## 📋 核心功能说明

即使使用最小化依赖，系统仍然具备：
- ✅ 图数据检索（Neo4j）
- ✅ 智能问答（智谱AI）
- ✅ Web可视化界面
- ✅ 缓存优化
- ✅ 多种查询模式

## 🔍 如果最小化安装仍有问题

请尝试以下命令：

```bash
# 清理环境
conda activate aigc
pip uninstall -y -r requirements-minimal.txt

# 重新安装
pip install --no-deps --force-reinstall neo4j==5.15.0 requests==2.31.0 flask==3.0.0 python-dotenv==1.0.0

# 或者使用conda直接安装
conda install neo4j requests flask python-dotenv
```

现在你应该能够成功安装并运行GraphRAG系统了！