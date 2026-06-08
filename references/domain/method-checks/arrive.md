# ARRIVE 2.0 — Animal Research Reporting Guidelines

> ARRIVE (Animal Research: Reporting of In Vivo Experiments) 是动物研究的标准报告指南。
> 大多数生态学/野生动物/生物多样性期刊要求或推荐遵循 ARRIVE。
> 完整指南见 https://arriveguidelines.org/

## ARRIVE Essential 10 — 与 ecology-manuscript-builder Gate 对应

以下 10 项是 ARRIVE 2.0 的核心条目（Essential 10），标注了与 ecology skill 现有 gate 的对应关系：

| # | ARRIVE Essential 10 | ecology-manuscript-builder 对应位置 |
|---|---|---|
| 1 | **Study design** — 说明实验/观测设计，包括分组数量和实验单元 | Gate 1 (Data Contract): sampling design, site independence |
| 2 | **Sample size** — 说明样本量及确定依据（功效分析或实际约束） | Gate 1 (Data Contract): survey effort; Gate 5.5 (Statistical Delivery): sample context |
| 3 | **Inclusion and exclusion criteria** — 明确定义纳入/排除规则 | Gate 1 (Data Contract): exclusion rules, independent-event rules |
| 4 | **Randomisation** — 说明随机化方法（如适用） | Gate 5 (Analysis Plan): method assumptions |
| 5 | **Blinding** — 说明是否设盲及方法（如适用） | Gate 5.6 (Automated-Recognition): double-review status |
| 6 | **Outcome measures** — 明确定义所有结局指标及测量方法 | Gate 6 (Result Cards): response variable, units, uncertainty |
| 7 | **Statistical methods** — 说明每个分析的统计方法 | Gate 5 (Analysis Plan); Gate 5.5 (Statistical Delivery) |
| 8 | **Experimental animals** — 说明物种、品系、性别、年龄、来源等 | Gate 1 (Data Contract): species, taxonomy; Minimum Input Contract |
| 9 | **Experimental procedures** — 详细描述操作流程（何时、何地、如何） | Gate 8 (Manuscript Draft): Methods detail recovery |
| 10 | **Results** — 报告每个分析的效应量及不确定性 | Gate 6 (Result Cards); Gate 8.2 (Discussion/Conclusion Quality) |

## ARRIVE Recommended Set

以下 11 项为推荐条目。对于生态学野外研究，以下条目尤为重要：

| # | ARRIVE Recommended | 关键注意事项（生态学语境） |
|---|---|---|
| 11 | **Abstract** — 包含物种、关键方法、主要发现 | Gate 7.5 (Introduction Quality): abstract appeal plan |
| 12 | **Background** — 科学背景、研究理由、具体目标/假设 | Gate 7.5: four-part introduction; Gate 3: answerable question |
| 13 | **Objectives** — 明确说明研究目标或假设 | Gate 3.5 (Answerable Unanswered Question); Gate 4.5 (Argument Contract) |
| 14 | **Ethical statement** — 伦理审批及许可证编号 | Gate 0 (Permission and Sensitivity); Gate 1.6 (Submission Metadata) |
| 15 | **Housing and husbandry** — 圈养条件（野外研究通常不适用） | 如适用，见 Gate 1 (Data Contract): processing notes |
| 16 | **Animal care and monitoring** — 动物福利措施 | 野外研究：麻醉/捕获/标记/遥测的伦理审批 |
| 17 | **Interpretation / scientific implications** — 结合研究目标和现有文献解释结果 | Gate 8.2 (Discussion Quality): result → literature → explanation |
| 18 | **Generalisability / translation** — 评估外部效度 | Gate 8.2: claim boundary; Gate 8.3 (Conclusion-Strength Audit) |
| 19 | **Protocol registration** — 是否预先注册研究方案 | 可选：鼓励预注册但非强制 |
| 20 | **Data access** — 说明数据/代码获取方式 | Gate 8.75 (Data Availability and Source Data) |
| 21 | **Declaration of interests** — 利益冲突声明 | Gate 1.6 (Submission Metadata): conflicts |

## 使用规则

- 当 manuscript target 涉及 **动物实验或野外动物研究** 时，自动加载此文件。
- 将 ARRIVE 条目与 ecology skill 现有 gate 对齐——ARRIVE 提供报告框架，gate 提供检查清单。
- 不通过 ARRIVE 全部条目不代表 block，标注哪些条目因研究设计不适用（如野外观测研究无随机化/盲法）即可。
- 在 pre-submission-review-gates 的 information-gap list 中标注未满足的 ARRIVE 条目。
