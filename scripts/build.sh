#!/bin/bash
# Linux Bash 构建脚本
# Linux Bash Build Script

set -e  # 遇到错误时退出

# 默认参数
PLATFORM="linux"
ARCHITECTURE="x64"
CONFIGURATION="Release"
CLEAN=false
INSTALL=false
PYTHON=false
TESTS=false
EXAMPLES=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --arch)
            ARCHITECTURE="$2"
            shift 2
            ;;
        --config)
            CONFIGURATION="$2"
            shift 2
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --install)
            INSTALL=true
            shift
            ;;
        --python)
            PYTHON=true
            shift
            ;;
        --tests)
            TESTS=true
            shift
            ;;
        --examples)
            EXAMPLES=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --platform PLATFORM    Target platform (default: linux)"
            echo "  --arch ARCHITECTURE    Target architecture (x64, arm64, x86, arm) (default: x64)"
            echo "  --config CONFIGURATION Build configuration (Debug, Release) (default: Release)"
            echo "  --clean                 Clean build directory before building"
            echo "  --install               Install after building"
            echo "  --python                Build Python bindings"
            echo "  --tests                 Build tests"
            echo "  --examples              Build examples"
            echo "  --help                  Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== IDH Multi-Platform Build Script ==="
echo "Platform: $PLATFORM"
echo "Architecture: $ARCHITECTURE"
echo "Configuration: $CONFIGURATION"

# 设置构建目录
BUILD_DIR="$ROOT_DIR/build/$PLATFORM-$ARCHITECTURE"
INSTALL_DIR="$ROOT_DIR/install/$PLATFORM-$ARCHITECTURE"

# 清理构建目录
if [ "$CLEAN" = true ] && [ -d "$BUILD_DIR" ]; then
    echo "Cleaning build directory..."
    rm -rf "$BUILD_DIR"
fi

# 创建构建目录
mkdir -p "$BUILD_DIR"

# 设置CMake参数
CMAKE_ARGS=(
    "-S" "$ROOT_DIR"
    "-B" "$BUILD_DIR"
    "-DCMAKE_BUILD_TYPE=$CONFIGURATION"
    "-DCMAKE_INSTALL_PREFIX=$INSTALL_DIR"
)

# 根据架构设置工具链
case $ARCHITECTURE in
    "x64")
        # 默认x64构建
        ;;
    "arm64")
        CMAKE_ARGS+=("-DCMAKE_SYSTEM_PROCESSOR=aarch64")
        # 如果有交叉编译工具链，在这里设置
        if [ -n "$ARM64_TOOLCHAIN" ]; then
            CMAKE_ARGS+=("-DCMAKE_TOOLCHAIN_FILE=$ARM64_TOOLCHAIN")
        fi
        ;;
    "arm")
        CMAKE_ARGS+=("-DCMAKE_SYSTEM_PROCESSOR=arm")
        # 如果有交叉编译工具链，在这里设置
        if [ -n "$ARM_TOOLCHAIN" ]; then
            CMAKE_ARGS+=("-DCMAKE_TOOLCHAIN_FILE=$ARM_TOOLCHAIN")
        fi
        ;;
    "x86")
        CMAKE_ARGS+=("-DCMAKE_C_FLAGS=-m32" "-DCMAKE_CXX_FLAGS=-m32")
        ;;
esac

# 设置构建选项
if [ "$PYTHON" = true ]; then
    CMAKE_ARGS+=("-DBUILD_PYTHON_BINDINGS=ON")
else
    CMAKE_ARGS+=("-DBUILD_PYTHON_BINDINGS=OFF")
fi

if [ "$TESTS" = true ]; then
    CMAKE_ARGS+=("-DBUILD_TESTS=ON")
else
    CMAKE_ARGS+=("-DBUILD_TESTS=OFF")
fi

if [ "$EXAMPLES" = true ]; then
    CMAKE_ARGS+=("-DBUILD_EXAMPLES=ON")
else
    CMAKE_ARGS+=("-DBUILD_EXAMPLES=OFF")
fi

# 检查依赖
echo "Checking dependencies..."
if ! command -v cmake &> /dev/null; then
    echo "Error: CMake is not installed"
    exit 1
fi

if ! command -v make &> /dev/null && ! command -v ninja &> /dev/null; then
    echo "Error: Neither Make nor Ninja is installed"
    exit 1
fi

# 使用Ninja如果可用
if command -v ninja &> /dev/null; then
    CMAKE_ARGS+=("-G" "Ninja")
fi

# 配置项目
echo "Configuring project..."
cmake "${CMAKE_ARGS[@]}"

# 构建项目
echo "Building project..."
cmake --build "$BUILD_DIR" --config "$CONFIGURATION" --parallel

# 安装项目
if [ "$INSTALL" = true ]; then
    echo "Installing project..."
    cmake --install "$BUILD_DIR" --config "$CONFIGURATION"
fi

echo "Build completed successfully!"
echo "Build directory: $BUILD_DIR"
if [ "$INSTALL" = true ]; then
    echo "Install directory: $INSTALL_DIR"
fi
