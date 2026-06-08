# Multi-Perspective Debate

> 从 AutoResearchClaw 的 multi-agent debate 吸收。在关键决策点引入多视角辩论，提升方向和结果的质量。

## When to Use

| Stage | Trigger | Debate Topic |
|-------|---------|-------------|
| Phase C, Step 12 | >= 2 candidate writing directions | 哪个方向最可交付？ |
| Phase D, Step 18 | 同一 result 有 >= 2 种解释 | 哪种解释证据最强？ |
| Phase F, Step 29 | Reviewer objection simulation | 审稿人会从哪些角度攻击？ |

## Debate Protocol

### Step 1: Generate 3 Perspectives

```
Perspective A: Conservative（保守派）
- 优先考虑证据最强的方向
- 只主张数据直接支持的结论
- 偏好 shorter、更窄的 manuscript

Perspective B: Moderate（温和派）
- 在证据和 novelty 之间平衡
- 包含合理的延伸讨论但标注 caveat
- 偏好标准长度的 manuscript

Perspective C: Ambitious（进取派）
- 优先考虑 novelty 和 impact
- 在证据边界处做最大程度的合理推断
- 偏好更长、更全面的 manuscript
```

### Step 2: Independent Output

每个视角独立产生：
- 对当前问题的回答（选哪个方向 / 怎么解释 / 审稿人会说什么）
- 支持的证据（引用具体 file_id 或 result card）
- Top 3 风险

### Step 3: Cross-Challenge

每个视角对其他 2 个视角提出 2 个质疑：
- "你忽略了什么证据？"
- "你的推断在哪一步超出了数据支持？"

### Step 4: Merge

Agent 综合 3 个视角：
- 提取共识（3/3 或 2/3 同意的点）
- 保留分歧（标记为 decision_log 待决定）
- 输出推荐方案（标注来自哪个视角 + 为什么选用这个）

## Cost Management

- Debate mode 增加 ~3x token 消耗
- 仅在高 stakes 决策点使用（Gate 2、Gate 4、Gate 5）
- 如果 `manuscript_potential = low`，跳过 debate，直接选 conservative
