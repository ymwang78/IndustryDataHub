#!/usr/bin/env python3
"""
IDH Python Wheels Build Script
Used to build Python wheel packages for multiple platforms
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Supported platforms
PLATFORMS = [
    "win_amd64",
    # "win_arm64",
    "linux_x86_64",
    # "linux_aarch64"
]

def run_command(cmd, cwd=None):
    """Run a command and check the result"""
    print(f"Running command: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"Command failed: {result.stderr}")
        return False
    print(f"Command succeeded: {result.stdout}")
    return True

def check_precompiled_libs(platform):
    """Check if precompiled libraries exist"""
    platform_dir = Path("pyidh") / "pyidh" / platform
    if not platform_dir.exists():
        print(f"Warning: platform directory not found: {platform_dir}")
        return False
    
    # Check for library files
    lib_files = list(platform_dir.glob("*.dll")) + list(platform_dir.glob("*.so"))
    if not lib_files:
        print(f"Warning: no library files found in {platform_dir}")
        return False
    
    print(f"Found libraries for {platform}: {[f.name for f in lib_files]}")
    return True

def build_wheel_for_platform(platform):
    """Build wheel for a specific platform"""
    print(f"\n=== Build wheel for {platform} ===")

    if not check_precompiled_libs(platform):
        print(f"Skip {platform}, missing precompiled libraries")
        return False

    env = os.environ.copy()
    env["IDH_TARGET_PLATFORM"] = platform

    dist_dir = Path("pyidh/dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    # 1. Build wheel
    cmd = "python3 -m build --wheel"
    result = subprocess.run(cmd, shell=True, cwd="pyidh", env=env,
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"Build failed: {result.stderr}")
        return False

    print(f"Build succeeded: {result.stdout}")

    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        print("No wheel file generated")
        return False
    wheel = wheels[0]

    # 2. Auditwheel repair for Linux
    if platform.startswith("linux"):
        repaired_dir = Path("pyidh/wheelhouse")
        if repaired_dir.exists():
            shutil.rmtree(repaired_dir)

        cmd = f"auditwheel repair {wheel} -w {repaired_dir}"
        print(f"Running command: {cmd}")
        result = subprocess.run(cmd, shell=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            print("auditwheel repair failed")
            return False

        repaired_wheels = list(repaired_dir.glob("*.whl"))
        if repaired_wheels:
            print(f"auditwheel repair finished: {[w.name for w in repaired_wheels]}")
        else:
            print("auditwheel did not produce any file")
            return False
    else:
        print("Non-Linux platform, auditwheel not required")

    return True

def build_all_wheels():
    """Build wheels for all platforms"""
    print("=== IDH Python Wheels Build Script ===")
    
    # Check dependencies
    try:
        import build
    except ImportError:
        print("Installing build dependencies...")
        if not run_command("pip install build wheel setuptools auditwheel"):
            print("Failed to install dependencies")
            return False
    
    success_count = 0
    total_count = len(PLATFORMS)
    
    for platform in PLATFORMS:
        if build_wheel_for_platform(platform):
            success_count += 1
        else:
            print(f"Build failed for {platform}")
    
    print(f"\n=== Build finished ===")
    print(f"Success: {success_count}/{total_count}")
    
    if success_count > 0:
        print("\nGenerated wheel files:")
        dist_dir = Path("pyidh/dist")
        if dist_dir.exists():
            for wheel in dist_dir.glob("*.whl"):
                print(f"  {wheel}")
    
    return success_count == total_count

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Build for a specific platform
        platform = sys.argv[1]
        if platform not in PLATFORMS:
            print(f"Unsupported platform: {platform}")
            print(f"Supported platforms: {', '.join(PLATFORMS)}")
            return 1
        
        if build_wheel_for_platform(platform):
            return 0
        else:
            return 1
    else:
        # Build for all platforms
        if build_all_wheels():
            return 0
        else:
            return 1

if __name__ == "__main__":
    sys.exit(main())
