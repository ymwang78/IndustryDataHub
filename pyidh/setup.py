from setuptools import setup, find_packages
import os
import sys
import ctypes
from ctypes import wintypes

def check_vc140_runtime():
    """检查是否安装了 VC140 运行时"""
    try:
        # 尝试加载 VC140 运行时
        ctypes.WinDLL('vcruntime140.dll')
        return True
    except OSError:
        return False

def get_vc140_installer_url():
    """获取 VC140 运行时安装程序 URL"""
    if sys.maxsize > 2**32:
        return "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    else:
        return "https://aka.ms/vs/17/release/vc_redist.x86.exe"

class VCRuntimeError(Exception):
    """VC140 运行时缺失错误"""
    pass

# 检查 VC140 运行时
if not check_vc140_runtime():
    raise VCRuntimeError(
        "Microsoft Visual C++ 2015-2022 Redistributable (VC140) is required.\n"
        f"Please download and install it from: {get_vc140_installer_url()}"
    )

setup(
    name="pyidh",
    version="0.1.1",
    packages=find_packages(),
    package_data={
        "pyidh": ["libidh.dll"],
    },
    install_requires=[
        "pywin32>=305",
    ],
    author="Yongming Wang",
    author_email="wangym@gmail.com",
    description="Python wrapper for Industry Data Hub",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ymwang78/IndustryDataHub",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
) 