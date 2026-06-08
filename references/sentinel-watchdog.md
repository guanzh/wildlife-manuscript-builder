# Sentinel Watchdog

> 从 AutoResearchClaw 的 Sentinel Watchdog 吸收。贯穿 pipeline 的持续质量监控——不是为了取代 gate，而是在 gate 之间持续守护。

## Watchdog 1: NaN/Inf Guard

**触发:** 每个 result card 写入后
**检查:** result card 中的数值是否包含 NaN、Inf、-Inf
**动作:** 发现 → 标记 result card 为 `blocked`，追溯来源数据，写入 conflict_log
**跳过:** 如果数据本身确实不能产生数值（如定性描述）

## Watchdog 2: Consistency Guard

**触发:** 每次 draft 更新后（步骤 22-28）
**检查:**
- draft 中引用的样本量是否与 data contract 一致
- draft 中报告的效应量是否与 result card 一致
- draft 中的方法描述是否与 code file 一致
**动作:** 不一致 → 写入 conflict_log，标记受影响的段落

## Watchdog 3: Citation Guard

**触发:** 每次 reference list 更新后（步骤 12, 19, 30）
**检查:**
- draft 中每个 `@` 或 `[author, year]` 引用是否在 reference list 中存在
- reference list 中的每个条目是否标记为 verified / unverified
- 是否有 AI-generated 或 unverified 引用
**动作:** 缺失引用 → 写入 info-gap list；unverified 引用 → 标记为需验证

## Watchdog 4: Claim Guard

**触发:** 每次 claim ledger 更新后（步骤 21, 24, 29）
**检查:**
- draft 中的每个核心声明是否在 claim ledger 中有对应条目
- claim ledger 中标记为 "unsupported" 的声明是否仍在 draft 中
**动作:** 无 ledger 条目的声明 → 新建条目，标记为 `needs_evidence`；unsupported 声明仍在 draft → 标记需删除或移入 Limitations

## Watchdog 5: Sensitive Data Guard

**触发:** 每次 output 生成后（步骤 27, 31）
**检查:**
- 公开输出中是否包含精确坐标（纬度/经度数值）
- 是否包含 patrol-sensitive 信息
- data availability statement 是否正确处理了 sensitive data
**动作:** 泄露 → BLOCK publication status，写入 conflict_log

## Sentinel Report

每次 manuscript build 结束时（步骤 31 之后），生成 sentinel report：

```markdown
## Sentinel Watchdog Report

| Watchdog | Status | Issues Found |
|----------|--------|-------------|
| NaN/Inf Guard | PASS | 0 |
| Consistency Guard | WARN | 2 (sample size mismatch in Discussion) |
| Citation Guard | PASS | 0 |
| Claim Guard | WARN | 1 (unsupported claim still in draft) |
| Sensitive Data Guard | PASS | 0 |
```
