# Python版本兼容性说明

## 🐍 Python 3.12 兼容性问题

你在使用Python 3.12时可能遇到依赖安装问题，这是因为某些包的版本兼容性。以下是解决方案：

## 🔧 解决方案

### 方案1：升级pip和setuptools（推荐）

```bash
# 升级pip到最新版本
python -m pip install --upgrade pip

# 升级setuptools
python -m pip install --upgrade setuptools

# 升级wheel
python -m pip install --upgrade wheel

# 清理缓存
python -m pip cache purge
```

### 方案2：使用conda环境（推荐）

```bash
# 创建新的conda环境
conda create -n graphrag python=3.11
conda activate graphrag

# 安装依赖
pip install -r requirements.txt
```

### 方案3：降级到Python 3.11

如果你不想使用conda，可以降级到Python 3.11：

```bash
# 下载并安装Python 3.11
# https://www.python.org/downloads/release/python-3118/

# 安装后验证版本
python --version
```

## 📋 依赖包兼容性

### 已测试的版本组合

| Python版本 | Neo4j | Requests | Flask | 状态 |
|-----------|---------|----------|-------|------|
| 3.8+ | ✅ | ✅ | ✅ | 完全兼容 |
| 3.9+ | ✅ | ✅ | ✅ | 完全兼容 |
| 3.10+ | ✅ | ✅ | ✅ | 完全兼容 |
| 3.11+ | ✅ | ✅ | ✅ | 完全兼容 |
| 3.12+ | ⚠️ | ✅ | ✅ | 需要升级pip |

### 问题分析

1. **dataclasses模块**：
   - Python 3.7+ 内置，无需单独安装
   - requirements.txt中已移除该依赖

2. **pip构建问题**：
   - 主要是setuptools版本过旧
   - 升级pip和setuptools可解决

3. **numpy编译问题**：
   - Python 3.12可能需要更新编译器
   - 建议使用conda管理

## 🚀 推荐的安装流程

### 使用conda（最稳定）

```bash
# 1. 安装Miniconda（如果没有）
# https://docs.conda.io/en/latest/miniconda.html

# 2. 创建专用环境
conda create -n graphrag python=3.11
conda activate graphrag

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
python -c "import neo4j, requests, flask; print('✅ 所有依赖安装成功')"
```

### 使用虚拟环境

```bash
# 1. 创建虚拟环境
python -m venv graphrag-env

# 2. 激活环境
# Windows
graphrag-env\Scripts\activate
# Linux/Mac
source graphrag-env/bin/activate

# 3. 升级pip
python -m pip install --upgrade pip setuptools wheel

# 4. 安装依赖
pip install -r requirements.txt
```

## 🔍 故障排除

### 常见错误及解决方案

#### 1. "module 'pkgutil' has no attribute 'ImpImporter'"

```bash
# 解决方案：升级setuptools
pip install --upgrade setuptools
```

#### 2. "Microsoft Visual C++ 14.0 is required"

```bash
# 解决方案1：使用conda
conda install numpy

# 解决方案2：安装预编译包
pip install --only-binary=all
```

#### 3. "Failed building wheel for package"

```bash
# 解决方案：跳过构建
pip install --no-build-isolation
```

## ✅ 验证安装

运行以下命令验证系统是否正常：

```bash
# 1. 检查Python版本
python --version

# 2. 测试导入
python -c "
import neo4j
import requests  
import flask
import python_dotenv
print('✅ 所有核心依赖导入成功')
"

# 3. 测试系统
python run.py --mode test
```

## 📞 如果仍有问题

如果按照上述步骤仍有问题，请：

1. 提供完整的错误信息
2. 说明你的Python版本：`python --version`
3. 说明你的操作系统：Windows/Linux/Mac
4. 说明pip版本：`pip --version`

这样我可以提供更针对性的解决方案。