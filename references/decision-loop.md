# Decision Loop

> 从 AutoResearchClaw 的 PIVOT/REFINE 机制吸收。WMB 的 5 个关键 gate 现在有明确的决策分支。

## Gate 1: Data Contract Freeze（步骤 7 之后）

| Decision | Condition | Action |
|----------|-----------|--------|
| **PROCEED** | 所有核心事实已冻结，计数核对一致 | 继续 → Gate 1.6 |
| **BLOCK** | 计数冲突、变量定义矛盾、无法 reconciliation | 输出 data-contract issue list + 最小可交付物，不写标准论文 |
| **REFINE** | 数据合同可以冻结但有 minor caveats | 标记 caveats → 继续但降低 manuscript potential |

## Gate 2: Answerable Question（步骤 13 之后）— 🟡 ADP-1 作者决策点（软停带默认）

> 这是作者决策点：摆出探索分析摘要 + 2-4 个候选方向后由作者拍板（详见 `author-decision-points.md`）。作者无响应则按推荐默认方向继续。

| Decision | Condition | Action |
|----------|-----------|--------|
| **PROCEED** | 存在具体的、文献未充分回答的、数据可回答的问题 | 继续 → 构建 argument contract |
| **REFINE** | gap 存在但方法边界模糊 | 缩小 question scope → 重新评估 → 再次检查 |
| **DOWNGRADE** | 无 answerable question | 降级为 monitoring baseline / data note / local report / methods note |
| **BLOCK** | 关键数据缺失导致无法回答任何问题 | 输出 readiness report + revision tasks，停止 |

## Gate 3: Statistical Delivery（步骤 17 之后）— 🟡 ADP-2 作者决策点（软停带默认）

> 这是作者决策点：摆出每个核心结果的 verdict 后由作者确认/要求补分析/砍结果（详见 `author-decision-points.md`）。作者无响应则按推荐默认继续。

| Decision | Condition | Action |
|----------|-----------|--------|
| **PROCEED** | 核心结果为 "ready" 或 "usable with caveat" | 继续 → 构建 result cards |
| **REFINE** | 结果为 "needs analysis" | 运行额外分析 → 重新评估 |
| **BLOCK** | 核心结果为 "not usable" | 输出 readiness report，不写 Results |

## Gate 4: Conclusion Strength（步骤 24 之后）

| Decision | Condition | Action |
|----------|-----------|--------|
| **PROCEED** | 所有强声明有直接支持 | 继续 → figure/table assembly |
| **REFINE** | 声明需要缩小范围或加 caveats | 修改 Discussion → 重新检查 |
| **BLOCK** | 存在强但不支持的声明 | 修改后再做 reviewer simulation，不继续 |

## Gate 5: Delivery Readiness（步骤 31 之后）

| Decision | Condition | Action |
|----------|-----------|--------|
| **PROCEED** | 所有 Level 4 要求已确认 | 输出 submission-ready package |
| **REFINE** | 有 minor issues | 返回 Phase E 修改 |
| **BLOCK** | 严重 reviewer objection 未解决 | 返回 Phase E，不标记 submission-ready |

## 通用规则

- **ADP（作者决策点）**：Gate 2 / Gate 3 以及 claim ledger（步骤 21，ADP-3）是三个作者决策点，均为**软停带默认**——摆出证据 + 推荐默认，作者可拍板，无响应则按最保守的推荐默认继续，不卡死无人值守的运行。详见 `author-decision-points.md`。
- **DOWNGRADE** 不是失败——是对数据承载力的诚实评估
- **REFINE** 循环最多 3 次，超过则强制 DOWNGRADE 或 BLOCK
- **BLOCK** 后必须输出明确的 task list，标注需要什么才能 unblock
