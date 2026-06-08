# Branch Exploration (Experimental)

> 从 AutoResearchClaw 的 branch exploration 吸收。当 manuscript potential 为 medium+ 且有 >= 2 个方向时，可并行探索。

## ⚠️ Experimental

此功能标记为 experimental — token 消耗增加 ~3-5x。仅在以下条件全部满足时使用：
- manuscript_potential >= medium
- 用户显式要求 ("explore multiple directions")
- 有 >= 2 个候选 writing direction

## Protocol

### Step 1: Fork

对每个候选方向：
1. 生成 mini data contract（只冻结该方向需要的核心变量）
2. 跑轻量级 analysis（不做完整 result card，只做核心统计）
3. 生成 one-paragraph summary：question → evidence → risk

### Step 2: Compare

| 维度 | Direction A | Direction B |
|------|------------|------------|
| Evidence strength | medium | weak |
| Novelty | moderate | high |
| Data support | strong (n=118) | weak (n=42) |
| Deliverability | high | medium |
| Risk | low | high (sample size) |

### Step 3: Select

选择最可交付的方向（不是最 ambitious 的）。
其他方向：
- 合并为 supplementary analysis（如果互补）
- 存档为 future work（如果数据不足）
- 记录到 decision_log 说明为什么不选

## Fallback

如果所有方向都无法通过 Gate 2（answerable question），对所有方向 DOWNGRADE。
