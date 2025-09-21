# Windows PowerShell 构建脚本
# Windows PowerShell Build Script

param(
    [string]$Platform = "windows",
    [string]$Architecture = "x64",
    [string]$Configuration = "Release",
    [switch]$Clean,
    [switch]$Install,
    [switch]$Python,
    [switch]$Tests,
    [switch]$Examples
)

# 设置错误处理
$ErrorActionPreference = "Stop"

# 获取脚本目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host "=== IDH Multi-Platform Build Script ===" -ForegroundColor Green
Write-Host "Platform: $Platform" -ForegroundColor Cyan
Write-Host "Architecture: $Architecture" -ForegroundColor Cyan
Write-Host "Configuration: $Configuration" -ForegroundColor Cyan

# 设置构建目录
$BuildDir = Join-Path $RootDir "build\$Platform-$Architecture"
$InstallDir = Join-Path $RootDir "install\$Platform-$Architecture"

# 清理构建目录
if ($Clean -and (Test-Path $BuildDir)) {
    Write-Host "Cleaning build directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $BuildDir
}

# 创建构建目录
if (!(Test-Path $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir | Out-Null
}

# 设置CMake参数
$CMakeArgs = @(
    "-S", $RootDir,
    "-B", $BuildDir,
    "-DCMAKE_BUILD_TYPE=$Configuration",
    "-DCMAKE_INSTALL_PREFIX=$InstallDir"
)

# 根据架构设置生成器和工具集
switch ($Architecture) {
    "x64" {
        $CMakeArgs += "-A", "x64"
    }
    "x86" {
        $CMakeArgs += "-A", "Win32"
    }
    "arm64" {
        $CMakeArgs += "-A", "ARM64"
    }
    "arm" {
        $CMakeArgs += "-A", "ARM"
    }
}

# 设置构建选项
if ($Python) {
    $CMakeArgs += "-DBUILD_PYTHON_BINDINGS=ON"
} else {
    $CMakeArgs += "-DBUILD_PYTHON_BINDINGS=OFF"
}

if ($Tests) {
    $CMakeArgs += "-DBUILD_TESTS=ON"
} else {
    $CMakeArgs += "-DBUILD_TESTS=OFF"
}

if ($Examples) {
    $CMakeArgs += "-DBUILD_EXAMPLES=ON"
} else {
    $CMakeArgs += "-DBUILD_EXAMPLES=OFF"
}

try {
    # 配置项目
    Write-Host "Configuring project..." -ForegroundColor Yellow
    & cmake @CMakeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "CMake configuration failed"
    }

    # 构建项目
    Write-Host "Building project..." -ForegroundColor Yellow
    & cmake --build $BuildDir --config $Configuration --parallel
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed"
    }

    # 安装项目
    if ($Install) {
        Write-Host "Installing project..." -ForegroundColor Yellow
        & cmake --install $BuildDir --config $Configuration
        if ($LASTEXITCODE -ne 0) {
            throw "Installation failed"
        }
    }

    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Build directory: $BuildDir" -ForegroundColor Cyan
    if ($Install) {
        Write-Host "Install directory: $InstallDir" -ForegroundColor Cyan
    }

} catch {
    Write-Host "Build failed: $_" -ForegroundColor Red
    exit 1
}
