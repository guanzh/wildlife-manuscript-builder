# Evidence Quality Assessment for Ecological Studies

> 适配自 GRADE 框架和生态学证据评估实践。
> 用于 manuscript-potential-rubric 的增强版证据质量维度。

## 生态学证据层次

生态学以观测研究为主，证据层次不同于医学 RCT 体系：

| 层次 | 研究设计 | 可支持的推断强度 |
|------|---------|----------------|
| **I** | 系统综述/荟萃分析（多研究、多地点、多方法） | 强 — 可支持推广性结论 |
| **II** | 长期监测（≥5 年重复采样，标准方法） | 较强 — 可检测趋势，区分年际变异 |
| **III** | 重复调查（≥2 次采样，标准方法） | 中等 — 可检测变化方向，审慎归因 |
| **IV** | 单次系统调查（标准方法，≥1 季） | 有限 — 可描述格局，不可推断趋势 |
| **V** | 机会性记录 / 公民科学（方法不统一，effort 未控制） | 弱 — 可生成假设，不可做结论性推断 |

**注意**：高层级设计不一定质量更高。一个精心设计的单次调查（IV）可能比一个存在严重方法缺陷的长期监测（II）更有价值。

## 证据质量降级因素

每个因素可将证据质量降一级。生态学语境下的常见降级因素：

### 1. 检测/观测偏倚（Detection/Observation Bias）

- 检测概率未建模（occupancy 模型 vs 原始 encounter rate）
- 分类器/鉴定准确率未经独立验证
- 观测者效应未控制（不同观测者/设备/季节）
- 伪重复（同一站点重复采样未处理空间自相关）

**对应 ecology skill gate**: Gate 5.5 (Statistical Delivery), Gate 5.6 (Acoustic Method Completeness)

### 2. 混杂与间接性（Confounding & Indirectness）

- 关键混杂变量未测量或未控制
- 空间梯度是代理变量而非直接测量（如边界距离 vs 实际生境质量）
- 时间尺度不匹配（如用单年数据推断长期趋势）
- 研究种群/地点与推断目标不一致

**对应 ecology skill gate**: Gate 8.3 (Conclusion-Strength Audit), claim-boundaries.md

### 3. 不精确性（Imprecision）

- 样本量小（站点数 < 10、有效记录少、零值过多）
- 置信区间过宽（CI 跨零或包含临床/生态学显著阈值）
- Effort 不平衡（不同站点/季节 effort 差异大，未加权或未建模）

**对应 ecology skill gate**: Gate 1 (Data Contract): survey effort; Gate 5.5: model diagnostics

### 4. 不一致性（Inconsistency）

- 不同分析方法得出不同结论（未做敏感性分析）
- 结果高度依赖特定模型设定（如独立事件时间窗口、分类阈值）
- 文献中类似研究报告矛盾结果

**对应 ecology skill gate**: Gate 8.5 (Reviewer-Objection Simulation): literature comparison

### 5. 发表偏倚（Publication Bias）

- 正结果更可能被报告（"显著"梯度、强效应物种被突出）
- 阴性/零结果在文献中缺失
- 仅报告"显著"物种，未报告全部测试物种

**对应 ecology skill gate**: Gate 6 (Result Cards): report all results; Gate 8.2: species-level heterogeneity

## 证据质量升级因素

在观测研究中，以下情况可提升证据信心：

### 1. 大效应量

- 效应量远大于典型测量误差（如 occupancy 差异 > 0.3）
- 效应在不同分类群/功能群中一致

### 2. 梯度/剂量-反应关系

- 生态梯度上呈现单调变化趋势
- 多个独立梯度（空间 + 时间 + 管理强度）收敛于同一结论

### 3. 多渠道验证

- 多种数据源（红外相机 + 样线 + eDNA）指向同一结论
- 观测数据 + 实验数据 + 模型模拟收敛

### 4. 合理的混杂方向

- 未测量的混杂因素如果存在，其效应方向与观测效应相反
- 例如：如果未控制的人为干扰倾向于减少生物多样性，那么观测到的"保护区内部多样性 > 边缘"的结论是保守的（真实差异可能更大）

## 证据质量综合评级

| 评级 | 标准 | ecology skill 对应 |
|------|-----|-------------------|
| **A — 高** | ≥II 级设计，无降级因素，或有大效应量+多渠道验证 | manuscript-potential: high; delivery: Level 3+ |
| **B — 中** | II-IV 级设计，1 个降级因素，已充分讨论局限 | manuscript-potential: medium; delivery: Level 2+ |
| **C — 低** | ≥1 个严重降级因素，结论需大幅收窄 | manuscript-potential: low; delivery: Level 1-2 |
| **D — 极低** | 多个严重降级因素，不应做推断性结论 | manuscript-potential: low → downgrade to data note/baseline |

## 与 manuscript-potential-rubric 的整合

在评估 manuscript potential 时，将证据质量作为独立维度加入：

```
Manuscript Potential = f(
    研究设计层级,
    证据质量评级 A-D,
    样本量与 Effort,
    新颖性与文献空白,
    方法匹配度,
    管理与保护意义
)
```

如果一个研究在"设计层级"上较低（如单次调查），但通过严谨的检测建模、充足的样本量和多渠道验证获得 B 级证据质量，仍可支持一个有价值的 manuscript。

## 使用规则

- 在 Gate 2 (Manuscript Potential Grade) 评估时加载此文件
- 证据质量评级不替代 manuscript-potential-rubric，而是增强其"数据质量"维度的系统性
- 评级结果记录在 manuscript potential rubric 的 evidence_quality 字段中
