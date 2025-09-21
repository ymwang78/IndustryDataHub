#!/usr/bin/env python3
"""
IDH Python Wheels 构建脚本
用于构建多平台的Python wheel包
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# 支持的平台
PLATFORMS = [
    "win_amd64",
    #"win_arm64", 
    #"linux_x86_64",
    #"linux_aarch64"
]

def run_command(cmd, cwd=None):
    """运行命令并检查结果"""
    print(f"运行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"命令失败: {result.stderr}")
        return False
    print(f"命令成功: {result.stdout}")
    return True

def check_precompiled_libs(platform):
    """检查预编译库是否存在"""
    platform_dir = Path("pyidh") / "pyidh" / platform
    if not platform_dir.exists():
        print(f"警告: 平台目录不存在: {platform_dir}")
        return False
    
    # 检查是否有库文件
    lib_files = list(platform_dir.glob("*.dll")) + list(platform_dir.glob("*.so"))
    if not lib_files:
        print(f"警告: 在 {platform_dir} 中没有找到库文件")
        return False
    
    print(f"找到 {platform} 的库文件: {[f.name for f in lib_files]}")
    return True

def build_wheel_for_platform(platform):
    """为指定平台构建wheel"""
    print(f"\n=== 构建 {platform} wheel ===")

    if not check_precompiled_libs(platform):
        print(f"跳过 {platform}，因为缺少预编译库")
        return False

    env = os.environ.copy()
    env["IDH_TARGET_PLATFORM"] = platform

    dist_dir = Path("pyidh/dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    # 1. 先构建 wheel
    cmd = "python -m build --wheel"
    result = subprocess.run(cmd, shell=True, cwd="pyidh", env=env,
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"构建失败: {result.stderr}")
        return False

    print(f"构建成功: {result.stdout}")

    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        print("没有生成 wheel 文件")
        return False
    wheel = wheels[0]

    # 2. Linux 平台需要 auditwheel 修复
    if platform.startswith("linux"):
        repaired_dir = Path("pyidh/wheelhouse")
        if repaired_dir.exists():
            shutil.rmtree(repaired_dir)

        cmd = f"auditwheel repair {wheel} -w {repaired_dir}"
        print(f"运行命令: {cmd}")
        result = subprocess.run(cmd, shell=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            print("auditwheel 修复失败")
            return False

        repaired_wheels = list(repaired_dir.glob("*.whl"))
        if repaired_wheels:
            print(f"auditwheel 修复完成: {[w.name for w in repaired_wheels]}")
        else:
            print("auditwheel 没有生成文件？")
            return False
    else:
        print("非 Linux 平台，无需 auditwheel")

    return True

def build_all_wheels():
    """构建所有平台的wheels"""
    print("=== IDH Python Wheels 构建脚本 ===")
    
    # 检查依赖
    try:
        import build
    except ImportError:
        print("安装构建依赖...")
        if not run_command("pip install build wheel setuptools"):
            print("安装依赖失败")
            return False
    
    success_count = 0
    total_count = len(PLATFORMS)
    
    for platform in PLATFORMS:
        if build_wheel_for_platform(platform):
            success_count += 1
        else:
            print(f"平台 {platform} 构建失败")
    
    print(f"\n=== 构建完成 ===")
    print(f"成功: {success_count}/{total_count}")
    
    if success_count > 0:
        print("\n生成的wheel文件:")
        dist_dir = Path("pyidh/dist")
        if dist_dir.exists():
            for wheel in dist_dir.glob("*.whl"):
                print(f"  {wheel}")
    
    return success_count == total_count

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 构建指定平台
        platform = sys.argv[1]
        if platform not in PLATFORMS:
            print(f"不支持的平台: {platform}")
            print(f"支持的平台: {', '.join(PLATFORMS)}")
            return 1
        
        if build_wheel_for_platform(platform):
            return 0
        else:
            return 1
    else:
        # 构建所有平台
        if build_all_wheels():
            return 0
        else:
            return 1

if __name__ == "__main__":
    sys.exit(main())
