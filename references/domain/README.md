# Domain-Specific Reference Files

此目录存放按生态学数据类型/子领域拆分的特化规则。

## 子目录

| 目录 | 维度 | 文件数 |
|------|------|--------|
| `objections/` | 审稿人常见 objection | 按数据类型 |
| `interpretation/` | Discussion 中的解释规则 | 按数据类型/方法 |
| `overclaims/` | 常见过度推断模式 | 按数据类型 |
| `language/` | 学科语言/措辞指南 | 按子领域 |
| `method-checks/` | 方法完整性检查清单 | 按方法类型 |

## 加载规则

`data-type-routing.md` 中的每种数据类型在对应子目录中应有匹配文件。
Agent 根据当前路由的数据类型自动加载相关 domain 文件。
