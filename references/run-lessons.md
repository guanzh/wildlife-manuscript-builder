# Run Lessons (Self-Learning)

> 从 AutoResearchClaw 的 MetaClaw 吸收。每次 manuscript build 结束后自动捕获教训，转为可复用的 skill，注入后续运行。

## Lesson Capture（步骤 31 之后自动执行）

### What went well

记录本次 build 中运作良好的决策或方法：

```markdown
- data contract caught 3 count mismatches before drafting — avoided Results revision
- deep research using Semantic Scholar + arXiv found 42 verified sources
- reviewer simulation caught 2 overclaims before they reached the manuscript
```

### What went wrong

记录本次 build 中的失败、警告或低效：

```markdown
- Deep research initially missed 5 key Chinese-language papers — retry with CNKI search needed
- Discussion overclaimed on management implication ("should be implemented") — caught late at Gate 4
- Camera trap data assumed independence without checking spatial autocorrelation
```

### Lessons extracted

将教训转为结构化条目：

```json
{
  "lesson_id": "L20260608001",
  "category": "data_check",
  "severity": "warning",
  "pattern": "camera trap data → must check spatial autocorrelation before occupancy modeling",
  "trigger": "data_type = camera_trap_data AND analysis_method = occupancy",
  "action": "Run Moran's I or semivariogram on detection data before Gate 3",
  "source_run": "alpha_project_20260608"
}
```

## Skill Conversion

高 severity（>= warning）的 lesson 自动转为 Hermes skill：

```bash
# 存入 ~/.hermes/skills/research/arc-wmb-<category>/
# 例如: arc-wmb-camera-trap/SKILL.md
```

Skill 格式：

```yaml
---
name: arc-wmb-camera-trap
description: Auto-generated lesson: check spatial autocorrelation before occupancy modeling with camera trap data.
---
# Camera Trap Data: Spatial Autocorrelation Check

**Trigger:** When data_type is `camera_trap_data` and analysis method includes `occupancy`

**Action:** Before proceeding to Statistical Delivery Gate, run Moran's I or semivariogram...

**Source:** Learned from run alpha_project_20260608
```

## Skill Injection

后续 manuscript build 时，如果数据包匹配 trigger 条件，自动预加载对应 skill：

```bash
hermes -s arc-wmb-camera-trap,arc-wmb-claim-boundary ...
```

## Decay

- Lessons 保留 90 天
- 如果连续 3 次运行未触发该 lesson，降级为 `archived`
- 如果后续运行发现 lesson 不再适用，标记为 `superseded`
