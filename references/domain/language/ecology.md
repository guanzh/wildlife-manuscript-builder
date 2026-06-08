# Ecology & Biodiversity — Terminology and Language Guide

> 生态学/生物多样性领域的学科语言规范。
> 用于 argument-terminology-contract 和 discussion-conclusion-quality-gate 的术语锁定。
> 与 `conservation.md`（保护生物学特化语言）互补。

## 1. 物种命名规范

### 二名法 (Binomial Nomenclature)

- 首次出现：完整属名 + 种加词，斜体（*Panthera tigris*）
- 再次出现：属名缩写 + 种加词（*P. tigris*）
- 未定种：`sp.`（单数）/ `spp.`（复数），正体（*Rattus* sp.）
- 分类权威：需要时可加命名人（*Panthera tigris* Linnaeus, 1758），中文期刊通常省略

### 常用表达

| 中文 | English |
|------|---------|
| 物种丰富度 | species richness |
| 物种多样性 | species diversity（需说明指数：Shannon, Simpson, Fisher's α 等） |
| 物种均匀度 | species evenness |
| 功能多样性 | functional diversity |
| 分类多样性 | taxonomic diversity |
| 系统发育多样性 | phylogenetic diversity |
| 群落组成 | community composition |
| 多度 | abundance |
| 出现/占据 | occurrence / occupancy |
| 检测概率 | detection probability |

### 常见陷阱

- **"biodiversity" ≠ species richness**：生物多样性是多维概念（分类/功能/系统发育多样性），不要用 richness 单独代表
- **"diversity" 需要指明指数**：Shannon 指数、Simpson 指数、Fisher's α 不可互换，每个指数的生态学含义不同
- **"community" vs "assemblage"**：community 暗示物种间存在相互作用，assemblage 更中性（共享时空分布的物种集合）
- **"population" 需谨慎**：野外监测数据通常只能推断"site-level occurrence"或"relative abundance"，不能直接等同于 population size

## 2. 生境与生态系统分类

### 生境描述

| 术语 | 含义 | 注意事项 |
|------|-----|---------|
| habitat | 物种赖以生存的环境条件集合 | 是 species-specific 的，不是通用描述词 |
| habitat type | 生境类型（如阔叶林、灌丛、草地） | 需要定义分类标准和分辨率 |
| habitat quality | 生境质量 | 需要明确指标（食物、遮蔽、繁殖资源），不可仅用植被覆盖代理 |
| habitat suitability | 生境适宜性 | 模型输出，不是实测 | 
| habitat use | 生境利用 | 基于观测记录，不直接等同于 preference 或 selection |
| habitat selection | 生境选择 | 需要与可用性对比（use vs availability design） |
| habitat preference | 生境偏好 | 比 selection 更强的推断，需要排除其他解释 |

### 生态系统类型（中英文对照）

| 中文 | English |
|------|---------|
| 森林生态系统 | forest ecosystem |
| 草地生态系统 | grassland ecosystem |
| 湿地生态系统 | wetland ecosystem |
| 淡水生态系统 | freshwater ecosystem |
| 海洋生态系统 | marine ecosystem |
| 农田生态系统 | agroecosystem |
| 城市生态系统 | urban ecosystem |

## 3. 采样方法标准术语

| 中文 | English | 典型使用 |
|------|---------|---------|
| 样方 | quadrat / plot | 植物群落调查 |
| 样线 | transect | 动物痕迹/鸟类/植物调查 |
| 样点 | point / station | 红外相机/声学监测/点计数 |
| 红外相机监测 | camera-trap monitoring | 兽类/地栖鸟类 |
| 标记-重捕获 | mark-recapture | 种群生态学 |
| 距离采样 | distance sampling | 密度估计 |
| 占域模型 | occupancy modeling | 分布/生境关联 |
| 环境 DNA | environmental DNA (eDNA) | 物种检测/生物多样性 |
| 宏条形码 | metabarcoding | 群落组成/食性分析 |
| 遥感 | remote sensing | 生境/土地覆盖变化 |

## 4. 统计/分析术语

| 术语 | 注意事项 |
|------|---------|
| 显著 (significant) | 必须附带 p 值或贝叶斯后验概率。不要写"显著"而不给数值 |
| 不显著 | 不等于"无效应"。使用 "no clear statistical association detected" 或 "the effect was not statistically distinguishable from zero" |
| 相关 (correlation/association) | 不是因果。使用 "associated with", "correlated with", 不用 "caused by", "driven by" |
| 效应量 (effect size) | 报告具体数值（Cohen's d, R², β coefficient）和置信区间 |
| 零值过多 (zero-inflated) | 需要明确是多少比例的零值，以及采用的建模策略 |
| 空间自相关 (spatial autocorrelation) | 需要报告是否检验和处理（Moran's I, spatial random effects 等） |
| 伪重复 (pseudoreplication) | 需要明确是否存在于设计中，以及如何处理 |

## 5. 管理与保护术语

| 术语 | 注意事项 |
|------|---------|
| 保护成效 (conservation effectiveness) | 需要 counterfactual design（BACI 或控制-干预对比），不能仅凭前后对比 |
| 威胁 (threat) | 需要定义具体的威胁类型（IUCN 威胁分类），不是笼统的"人为干扰" |
| 恢复 (restoration/recovery) | 需要明确恢复目标、时间框架和判定标准 |
| 可持续 (sustainable) | 需要说明可持续性的具体维度和测度 |
| 生态系统服务 (ecosystem services) | 需要指明服务类型（供给/调节/支持/文化）和评估方法 |
| 保护区 (protected area) | 需要说明 IUCN 分类（如适用）或管理类型 |

## 6. 措辞强度阶梯

从弱到强的动词选择：

```
描述格局 (describe/document/record) → 评估关联 (assess/evaluate/examine) 
→ 检测效应 (detect/identify) → 支持假设 (support/are consistent with) 
→ 证明 (demonstrate/show) → 确定 (establish/confirm/prove)
```

- 观测研究通常停留在 "assess/detect/support" 级别
- "demonstrate" 需要排除主要替代解释
- "prove" 和 "establish" 在生态学中极少适用
- 中文同理："表明" > "提示" > "支持" > "证实" > "证明"

## 7. 中文生态学写作常见问题

| 问题 | 修正 |
|------|-----|
| "生物多样性较高" — 未说明哪个维度 | "物种丰富度较高（Shannon 指数 = 2.8）" |
| "生境质量良好" — 未说明用什么指标衡量 | "冠层盖度 > 60%，倒木密度 > 5 根/100m²" |
| "人类活动干扰严重" — 未定义干扰类型和强度 | "人为活动指数（RAI）为 0.42 ± 0.15 events/camera-day" |
| "具有重要保护价值" — 空洞 | "记录到 3 种 IUCN 濒危物种、6 种 CITES 附录 I/II 物种" |
| "为保护管理提供科学依据" — 空洞结尾 | "建议将边缘社区林地纳入连续监测样点，并分开记录村民通行、犬只和家畜活动" |

## 使用规则

- 在 Gate 4.5 (Argument and Terminology Contract) 时加载此文件，作为 terminology ledger 的参考
- 与 `conservation.md` 互补：conservation.md 侧重保护生物学特化语言（因果推断边界、管理建议措辞），此文件侧重通用生态学术语
- 写 Discussion 时对照"措辞强度阶梯"，确保动词强度与证据层次匹配
