# x64_linux 预编译库

请将您的Linux x64预编译库文件放在此目录中。

## 需要的文件

- `libidh.so` - 主要的IDH共享库
- 其他依赖的共享库文件（如果有）

## 文件要求

- 所有共享库文件必须是为Linux x64架构编译的
- 确保所有依赖项都包含在内
- 文件应该是Release版本以获得最佳性能
- 建议使用相对较老的glibc版本以确保兼容性

## 示例文件结构

```
linux_x86_64/
├── libidh.so
├── libdependency1.so
└── libdependency2.so
```

## 注意事项

- 确保库文件具有正确的执行权限
- 检查库的依赖关系：`ldd libidh.so`
- 建议在CentOS 7或Ubuntu 18.04等较老系统上编译以确保兼容性
