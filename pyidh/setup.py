from setuptools import setup, find_packages
import sys
import platform
import os
from pathlib import Path

def get_target_platform():
    """Get target platform information"""
    target_platform = os.environ.get("IDH_TARGET_PLATFORM")
    if target_platform:
        return target_platform

    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        if machine in ["x86_64", "amd64"]:
            return "win_amd64"
        elif machine in ["aarch64", "arm64"]:
            return "win_arm64"
    elif system == "linux":
        if machine in ["x86_64", "amd64"]:
            return "linux_x86_64"
        elif machine in ["aarch64", "arm64"]:
            return "linux_aarch64"

    return f"{machine}_{system}"

def get_precompiled_library_files(target_platform):
    """Get precompiled library files (relative to pyidh/)"""
    platform_dir = Path("pyidh") / target_platform
    if not platform_dir.exists():
        raise FileNotFoundError(f"Precompiled library directory not found: {platform_dir}")

    library_files = []
    for pattern in ["*.dll", "*.so", "*.so.*", "*.dylib"]:
        for f in platform_dir.glob(pattern):
            if f.is_file():
                # Return paths relative to pyidh/
                rel_path = str(f.relative_to("pyidh"))
                library_files.append(rel_path)

    return library_files

def get_install_requires(target_platform):
    base_requires = []
    if target_platform.startswith("win_"):
        base_requires.append("pywin32>=305")
    return base_requires

target_platform = get_target_platform()
print(f"Building for target platform: {target_platform}")

try:
    library_files = get_precompiled_library_files(target_platform)
    print(f"Found precompiled libraries: {library_files}")
except FileNotFoundError as e:
    print(f"Warning: {e}")
    library_files = []

setup(
    name="pyidh",
    version="0.1.7",
    packages=find_packages(),
    package_data={
        "pyidh": library_files,   # Include binaries under pyidh/<platform>
    },
    include_package_data=True,
    install_requires=get_install_requires(target_platform),
    author="Yongming Wang",
    author_email="wangym@gmail.com",
    description=f"Python wrapper for Industry Data Hub ({target_platform})",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ymwang78/IndustryDataHub",
    project_urls={
        "Bug Reports": "https://github.com/ymwang78/IndustryDataHub/issues",
        "Source": "https://github.com/ymwang78/IndustryDataHub",
        "Documentation": "https://github.com/ymwang78/IndustryDataHub/wiki",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
        "Topic :: Communications",
        "Operating System :: Microsoft :: Windows" if target_platform.startswith("win_")
        else "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
    keywords="industrial automation, data communication, OPC, modbus, multi-platform",
    zip_safe=False,
    options={
        "bdist_wheel": {
            "plat_name": target_platform
        }
    }
)
