# 贡献指南

感谢关注本项目！欢迎通过 Issue 反馈问题、通过 Pull Request 贡献代码。

## 提交前检查

- [ ] Python 代码通过 `python -m py_compile` 检查
- [ ] Shell 脚本通过 `bash -n` 语法检查
- [ ] 不引入数据文件、仿真产物或大文件（模型权重等）
- [ ] 不引入任何密钥：API key 一律通过环境变量读取（如 `DEEPSEEK_API_KEY`）
- [ ] 新增依赖请同步更新根目录 README 的依赖表

## 提交信息规范

```
<类型>: <简要描述>

类型：feat / fix / docs / refactor / test / chore
```

## 开发建议

- 批量仿真改动建议先用 `--use-mock` 模式冒烟测试，再上真实 COMSOL
- 涉及优化器的改动请保持三种优化器（Bayesian / GA / PSO）接口一致
