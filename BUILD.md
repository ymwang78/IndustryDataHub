# IDH Python Wheels 构建指南

## 概述

Industry Data Hub (IDH) 使用预编译库模式来构建多平台的Python wheel包。

### 支持的平台和架构

| 平台 | 架构 | 目录名 | 状态 |
|------|------|--------|------|
| Windows | x64 | win_amd64 | ✅ 支持 |
| Windows | ARM64 | win_arm64 | ✅ 支持 |
| Linux | x64 | linux_x86_64 | ✅ 支持 |
| Linux | ARM64 | linux_aarch64 | ✅ 支持 |

## 目录结构

```
IndustryDataHub/
├── pyidh/                   # Python包目录
│   ├── lib/                 # 预编译库目录
│   │   ├── win_amd64/       # Windows x64预编译库
│   │   │   ├── libidh.dll
│   │   │   └── README.md
│   │   ├── win_arm64/       # Windows ARM64预编译库
│   │   │   ├── libidh.dll
│   │   │   └── README.md
│   │   ├── linux_x86_64/    # Linux x64预编译库
│   │   │   ├── libidh.so
│   │   │   └── README.md
│   │   └── linux_aarch64/   # Linux ARM64预编译库
│   │       ├── libidh.so
│   │       └── README.md
│   ├── pyidh/               # Python源代码
│   ├── tests/               # 测试文件
│   ├── setup.py             # 包配置
│   └── README.md
├── scripts/                 # 构建脚本
│   └── build_wheels.py      # Python wheel构建脚本
└── .github/workflows/       # CI/CD配置
    └── build.yml
```

## 构建要求

### 基本要求

- Python 3.8 或更新版本
- pip 和 build 包

### 安装构建依赖

```bash
# manylinux
yum install -y patchelf
/opt/python/cp313-cp313/bin/python -m pip install build setuptools wheel
/opt/python/cp313-cp313/bin/python scripts/build_wheels.py linux_x86_64

#debian 
sudo apt install python3.13-venv,patchelf
python -m venv ~/venv
source ~/venv/bin/active
pip3 install build wheel setuptools auditwheel

python3 scripts/build_wheels.py linux_x86_64
```

## 预编译库准备

### 1. 准备预编译库文件

将您的预编译库文件放入对应的平台目录：

- **Windows x64**: `pyidh/lib/win_amd64/libidh.dll`
- **Windows ARM64**: `pyidh/lib/win_arm64/libidh.dll`  
- **Linux x64**: `pyidh/lib/linux_x86_64/libidh.so`
- **Linux ARM64**: `pyidh/lib/linux_aarch64/libidh.so`

### 2. 检查库文件

确保库文件：
- 是为正确的架构编译的
- 包含所有必要的依赖项
- 是Release版本（推荐）

## Python Wheel构建

### 使用构建脚本 (推荐)

```bash
# 构建所有平台的wheels
python scripts/build_wheels.py

# 构建特定平台的wheel
python scripts/build_wheels.py win_amd64
python scripts/build_wheels.py win_arm64
python scripts/build_wheels.py linux_x86_64
python scripts/build_wheels.py linux_aarch64
```

### 手动构建

```bash
# 设置目标平台环境变量
export IDH_TARGET_PLATFORM=win_amd64  # 或其他平台

# 构建wheel
cd pyidh
python -m build --wheel
```

### 构建输出

构建成功后，wheel文件将保存在 `pyidh/dist/` 目录中：

```
pyidh/dist/
├── pyidh-0.1.5-py3-none-win_amd64.whl     # Windows x64
├── pyidh-0.1.5-py3-none-win_arm64.whl     # Windows ARM64
├── pyidh-0.1.5-py3-manylinux_x86_64.whl   # Linux x64
└── pyidh-0.1.5-py3-manylinux_aarch64.whl  # Linux ARM64
```

## 安装和测试

### 安装wheel

```bash
# 安装特定平台的wheel
pip install pyidh/dist/pyidh-0.1.5-py3-none-win_amd64.whl

# 或者让pip自动选择合适的wheel
pip install pyidh/dist/*.whl
```

### 运行测试

```bash
cd pyidh
python -m pytest tests/ -v
```

## GitHub Actions CI/CD

项目配置了完整的CI/CD流水线，支持：

- 多平台Python wheel构建 (Windows x64/ARM64, Linux x64/ARM64)
- Python包测试 (Python 3.8-3.12)
- 自动发布到PyPI

### 触发构建

- 推送到 `main` 或 `develop` 分支
- 创建Pull Request
- 创建Release标签

## 故障排除

### 常见问题

1. **预编译库缺失**
   ```bash
   # 检查预编译库是否存在
   ls pyidh/lib/win_amd64/
   ls pyidh/lib/linux_x86_64/
   ```

2. **Python包构建失败**
   ```bash
   # 检查目标平台环境变量
   echo $IDH_TARGET_PLATFORM
   
   # 检查构建依赖
   pip list | grep build
   ```

3. **Wheel安装失败**
   ```bash
   # 检查wheel文件
   ls pyidh/dist/
   
   # 检查平台兼容性
   pip debug --verbose
   ```

### 调试构建

启用详细输出：

```bash
# 使用构建脚本的详细模式
python scripts/build_wheels.py win_amd64

# 手动构建时查看详细信息
cd pyidh
python setup.py bdist_wheel --verbose
```

## 贡献

在提交代码前，请确保：

1. 所有平台的预编译库都已准备好
2. 运行了相关的测试
3. 更新了相关文档

```bash
# 测试所有平台wheel构建
python scripts/build_wheels.py

# 运行测试
cd pyidh && python -m pytest tests/ -v
