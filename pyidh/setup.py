from setuptools import setup, find_packages
import sys
import platform
import os
from pathlib import Path

LINUX_WHEEL_PLATFORM_TAGS = {
    "linux_x86_64": "manylinux_2_28_x86_64",
    "linux_aarch64": "manylinux_2_28_aarch64",
}

PACKAGE_PLATFORM_ALIASES = {
    wheel_tag: package_platform
    for package_platform, wheel_tag in LINUX_WHEEL_PLATFORM_TAGS.items()
}

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

def get_package_platform(target_platform):
    """Get the package directory that contains precompiled libraries."""
    return PACKAGE_PLATFORM_ALIASES.get(target_platform, target_platform)

def get_wheel_platform_tag(target_platform):
    """Get the wheel platform tag advertised to installers."""
    wheel_platform_tag = os.environ.get("IDH_WHEEL_PLATFORM_TAG")
    if wheel_platform_tag:
        return wheel_platform_tag

    return LINUX_WHEEL_PLATFORM_TAGS.get(target_platform, target_platform)

def get_precompiled_library_files(target_platform):
    """Get precompiled library files (relative to pyidh/)"""
    package_platform = get_package_platform(target_platform)
    platform_dir = Path("pyidh") / package_platform
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
wheel_platform_tag = get_wheel_platform_tag(target_platform)
print(f"Building for target platform: {target_platform}")
print(f"Using wheel platform tag: {wheel_platform_tag}")

try:
    library_files = get_precompiled_library_files(target_platform)
    print(f"Found precompiled libraries: {library_files}")
except FileNotFoundError as e:
    print(f"Warning: {e}")
    library_files = []

setup(
    name="pyidh",
    version="26.6.0",
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
            "plat_name": wheel_platform_tag
        }
    }
)
