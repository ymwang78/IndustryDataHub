# x64_windows 预编译库

请将您的Windows x64预编译库文件放在此目录中。

## 需要的文件

- `libidh.dll` - 主要的IDH库
- 其他依赖的DLL文件（如果有）

## 文件要求

- 所有DLL文件必须是为Windows x64架构编译的
- 确保所有依赖项都包含在内
- 文件应该是Release版本以获得最佳性能

## 示例文件结构

```
win_amd64/
├── libidh.dll
├── dependency1.dll
└── dependency2.dll
