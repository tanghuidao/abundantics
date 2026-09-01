# jᵢ（单 token 能耗）溯源附录 — 修订版 v0.2（供项目所有者审阅）

> **状态**：修订稿。在草稿 v0.1 基础上完成 V1/V2 待核验项的实证调研（查询日期 2026-09-01），结论已并入。**仍未改动任何计算逻辑、代码或已发布序列。**
> **对应路线图**：O3（jᵢ 溯源附录 + 敏感性表）
> **关联局限**：L5（工作假设性质的 jᵢ，最薄弱输入）；延伸 L2（reasoning token 口径）
> **用途**：把 jᵢ 从"点值"升级为"可溯源的三档区间"，为后续"置信带发布"做准备。
> **体例**：沿用 `docs/quality_scores_lookup.md` 与 `docs/changelog.md`。

---

## 0. 摘要与口径基线

本附录对《TEPI 改进方案 v0.1》"发现 2"的两次更正（见 `CHR_vs_TEPI_逐条对比.md` 发现 A/B）予以确认并作为口径基线：

1. jᵢ 作为"每**计费输出 token** 全栈能耗（含 PUE）"，公开实测的合理区间约为 **0.5–5 J/token**；TEPI 当前篮子 jᵢ = 1.0–3.0 J/token **落在该区间内，不系统性偏低**，且与 CHR 隐含 jᵢ（1.1–2.8 J/token）独立收敛。
2. Λ=234 与产业界"20–25 倍"的差异，**主因是篮子选价**（加权均价 $11.44 vs 走量 $1/百万 token，约 10 倍），而非 jᵢ。
3. jᵢ 溯源的目的：消除 L5 输入不确定性（三档区间 + 溯源）、钉死 reasoning token 计价口径（本版已核验，见 §2）、为 O3 落地提供可复核底稿。

**v0.2 新增结论（V1/V2 核验，一手证据见 §2）：**

- **V1 成立（口径自洽）**：四家厂商的 reasoning/thinking token **均按输出 token 计价并计入计费输出用量**。TEPI 的 pᵢ（completion 价）分母已包含思考 token，因此 jᵢ 的正确口径是"全栈能耗 ÷ **计费输出 token（含思考 token）**"——草稿 v0.1 担心的"C 层系统性低估"情形**不适用于计费口径**，jᵢ 无需因此上调。
- **V2 结论与草稿假设相反**：Gemini 3.7 Flash 的 Google API 默认思考档是 **medium**（非 high）。

---

## 1. 当前篮子的 jᵢ 值（v1，2026-08-16 生效）

| 模型（OpenRouter id） | 权重 w̃ᵢ | jᵢ (J/token) | 质量分 sᵢ | 口径声明 |
|---|---:|---:|---:|---|
| anthropic/claude-sonnet-5（基准） | 0.30 | **3.0** | 55 | 输出 token，全栈含 PUE |
| openai/gpt-5.5 | 0.25 | **3.0** | 56 | 输出 token，全栈含 PUE |
| google/gemini-3.7-flash | 0.25 | **1.0** | 56 | 输出 token，全栈含 PUE |
| deepseek/deepseek-v4-pro | 0.20 | **1.5** | 53 | 输出 token，全栈含 PUE |

加权均值 j̄ = **2.200 J/token**（与附录 A 的 `basket_j_per_token` 一致）。

**来源标注**：四个数值在 `parity_index.py` 的 `inference_basket` 中作为**人工设定的工作假设**录入，v0.1 前无逐项公开出处——本附录即为其溯源底稿。注：上表"口径声明"沿引代码现有注释；其精确定义应订正为"**计费输出 token（含思考 token）**，全栈含 PUE"（依据见 §2 V1），订正属于注释级修正，待项目所有者确认后随定稿一并落地。

---

## 2. V1/V2 核验结果（v0.2 新增，一手证据）

### 2.1 V1：reasoning token 计价口径 —— 已核验，四家一致按输出 token 计费

**厂商原始口径（官方文档）：**

| 厂商 | 官方口径 | 出处 |
|---|---|---|
| OpenAI | "推理 Token……会计入输出用量，并按输出 Token 计费"；`usage.completion_tokens` 包含 `reasoning_tokens`（例：completion 1843 = 可见 1395 + 推理 448） | OpenAI 帮助中心《瞭解並計算 Token》；Azure OpenAI reasoning 文档 |
| Anthropic | "Tokens used during thinking (output tokens)"——思考 token 按标准输出价计费；计费输出数 ≠ 可见输出数（计费含原始思考，可见仅摘要） | console.anthropic.com《Building with extended thinking》 |
| Google | `usage` 中 `total_output_tokens` 包含 `total_thought_tokens`（官方示例：gemini-3.7-flash 一次请求 output 171 + thought 297 = 计费输出）；`thinking_level` 文档明示思考 token 属输出用量 | ai.google.dev《Gemini thinking》 |
| DeepSeek | 思考链 token 按 output 价计费（deepseek-reasoner 的 reasoning 内容计入 completion_tokens） | DeepSeek API 文档 |

**OpenRouter 聚合层实测（2026-09-01 直查 `/api/v1/models`，篮子四模型）：**

| 模型 | pricing.completion | pricing.internal_reasoning | 判读 |
|---|---:|---:|---|
| google/gemini-3.7-flash | $3.75/M | **$3.75/M（与 completion 同价）** | 推理 token 显式同价 |
| openai/gpt-5.5 | $30/M | （无该字段） | 按完成价计，无单独推理价 |
| anthropic/claude-sonnet-5 | $10/M | （无该字段） | 同上 |
| deepseek/deepseek-v4-pro | $2.07/M | （无该字段） | 同上 |

> OpenRouter 价格对象提供可选字段 `internal_reasoning`（"内部推理 token 单价，o1 / Claude thinking"）；篮子四模型中仅 Google 端点显式填列且**与 completion 完全同价**，其余三家不单列——与厂商原始口径一致：**reasoning token 按 completion 价计费**。TEPI 的 `parity_index.py` 取 `pricing.completion` 作为 pᵢ，因此 pᵢ 的分母（计费输出 token）**天然包含思考 token**。

**对 jᵢ 口径的直接推论（重要，替代草稿 v0.1 §3 的"未解决缺口"表述）：**

- 设一次请求的思考 token 数为 R、可见 token 数为 V，则计费输出 = R + V，能量 ≈ 全栈能耗 E。
- 若"输出 token"**只计可见**（草稿 v0.1 担心的情形），jᵢ = E/V 会被放大 (1+R/V) 倍（R/V 可达 1–2×，见 Google 示例 R=297 > V=171）——**但计费口径并非如此**。
- 实际计费口径下，jᵢ = E/(R+V) ≈ 每生成 token 的平均能耗，**与每可见 token 口径相比更低而非更高**。故：**jᵢ 不存在"因思考 token 未计入而被系统性低估"的问题**；相反，jᵢ 的目标口径是"**全栈能耗 ÷ 计费输出 token**"（介于 B 层与 C 层之间、更靠近 B 层）。
- 连带修正草稿 v0.1 §4 的落点评估：**GPT-5.5 "⚠️ 可能偏低"的警示可以降级**——分母含思考 token 后，3.0 J/token 对大型 reasoning 模型仍属中档上沿，无需因 C 层情形上调（是否因绝对能耗偏高/偏低调整，留待 V5 三档定档时统一裁量）。

### 2.2 V2：Gemini 3.7 Flash 默认思考档 —— 已核验，为 medium（非 high）

Google 官方《Gemini thinking》模型默认档表（ai.google.dev，查询 2026-09-01）：

| 模型 | 默认思考档 | 支持档位 |
|---|---|---|
| **gemini-3.7-flash** | **On (medium)** | low, medium, high |
| gemini-3.6-flash | On (medium) | minimal, low, medium, high |
| gemini-3.5-flash | On (medium) | minimal, low, medium, high |
| gemini-3-flash-preview | On (high) | minimal, low, medium, high |

OpenRouter 侧 `default_parameters` 为空对象（透传 Google 默认），OpenAI 兼容层 `reasoning_effort` 映射 `thinking_level`——**未显式指定时即 Google 默认 medium**。历史上仅 Gemini 3.0 世代 Flash 预览版默认 high，3.5 起官方改为 medium（官方变更说明："默认思考工作量现在为 medium……medium 在各种任务中都能产生非常好的结果，同时速度更快、成本效益更高"）。

**两项连带影响（均不改变已发布历史，待项目所有者拍板后才动代码）：**

1. **质量分口径（影响 quality_score）**：`quality_scores_lookup.md` 当时按"最高已评档 high = 56"录入；若改按默认档 medium，AA 分数为 **53**。这属于质量分变更，按治理规则须走 `docs/changelog.md` 登记、自确认日起生效、历史不回溯。**另注**：其余三家（Claude Max Effort / GPT-5.5 xhigh / DeepSeek Max Effort）当前录入的也是"最高已评档"而非"默认档"（OpenAI 默认 medium=51）——"选档口径"是统一按最高档还是统一按默认档，属于同一决策，需一并裁定，避免单改一家造成口径不一致。
2. **jᵢ 口径（影响 gemini-3.7-flash 的 jᵢ 定档）**：medium 档思考量低于 high 档，其全栈合理区间相对 §2.1 口径约为 0.4–1.2 J/token；当前 1.0 仍在区间内但处于上沿。是否微调留待 V5 三档定档统一处理。

---

## 3. 公开实测数据源（可溯源，承接 v0.1）

| # | 来源 | 模型 / 硬件 | 口径 | 数值 | 出处 |
|---|---|---|---|---|---|
| 1 | ML.ENERGY Leaderboard | Llama 3.1 70B / 4×H100, vLLM | **GPU-only** | batch 8 = 3.76；batch 256 = 0.48；batch 1024 = 0.37 J/token | ml.energy（NeurIPS 2025 D&B） |
| 2 | ML.ENERGY Leaderboard | Llama 3.1 8B / H100 | **GPU-only** | v3 batch 64 = 0.12 J/token（v2 = 0.20） | 同上 |
| 3 | Google Gemini 全栈 | Gemini Apps 中位 text prompt | **全栈** | 0.24 Wh/prompt；分解 0.14+0.06+0.02+0.02 | arXiv 2508.15734 |
| 4 | Google scope factor | 同上 | 加速器→生产环境放缩 | **1.72×**；舰队平均 PUE = 1.09 | arXiv 2508.15734 |
| 5 | Google 窄口径对照 | 同上（更高效机器样本） | 仅活跃加速器 | 0.10 Wh/prompt | arXiv 2508.15734 |
| 6 | Cell/Joule 2026 综述 | Llama 3.1 70B（361 输出 token） | GPU-only | 0.04 Wh/query ≈ **0.4 J/token** | Cell, S2542-4351(26)00114-5 |
| 7 | Cell/Joule 2026 综述 | DeepSeek-V3（8968 token，H100 换算） | GPU-only | 9.30 Wh/query ≈ **3.7 J/token** | 同上 |
| 8 | Cell/Joule 2026 综述 | DeepSeek-R1（测试时缩放） | GPU-only | 20.9 Wh/query（约 V3 的 2.25×） | 同上 |
| 9 | Samsi et al. 2023 | LLaMA-65B / V100–A100 | 实测 | ~3–4 J/output token | 学术实测（via John Snow Labs 综述） |
| 10 | Lin et al. 2025 | Llama3-70B FP8 / 8×H100, vLLM | 实测（高负载优化） | ~0.39 J/token | 同上 |
| 11 | AI Energy Score | Llama-3-70B / H100 | GPU-only | 1.72 Wh/request | 与 ML.ENERGY 同模型相差 **37×** |
| 12 | Provider PUE 因子 | OpenAI(Azure)1.20 / Anthropic(GCP)1.10 / Google 1.09 / DeepSeek 1.25 | PUE | — | arXiv 2603.23528 |

**两点强调的困难（不变）：**
- 同一模型公开实测可相差 **37×**（batch、vLLM 版本、计量边界不同）——单点 jᵢ 本质是口径选择。
- 篮子四模型均无逐 token 能耗公开实测，只能"同架构同量级模型代理"（CHR 隐含 jᵢ 1.1–2.8 为交叉印证，见 `CHR_vs_TEPI_逐条对比.md` §8 发现 B）。

---

## 4. 口径分层（v0.2 修订）

| 层级 | 口径 | 典型量级 | 说明 |
|---|---|---|---|
| A | GPU-only，仅加速器 | 0.1–4 J/token | ML.ENERGY / AI Energy Score 基准口径 |
| B | 全栈（× scope 1.72 + PUE 1.09–1.25） | 0.2–7 J/token | Google 全栈口径；A × 1.72 |
| C | 全栈 ÷ **可见输出 token**（思考能耗全摊给可见 token） | 5–20+ J/token | 仅当"输出 token"不计思考时才有意义 |
| **D′** | **全栈 ÷ 计费输出 token（含思考 token）——TEPI 实际口径** | **0.5–5 J/token** | v0.2 经 V1 核验确立：pᵢ 分母含思考 token，jᵢ = E/(R+V)，与 B 层量级衔接 |

**v0.1 的"D 层（仅输出 token）"存在表述歧义，已订正为 D′**：经 §2.1 核验，"输出 token"在计费语境下**包含**思考 token，故 TEPI 名义口径实际是 D′ 而非"介于 B 与 C 之间存疑"的状态。C 层口径仅在未来若改用"每可见 token 计价"的价格源时才需启用。

---

## 5. 交叉校准：当前 jᵢ 落点评估（v0.2 修订）

按 D′ 口径（全栈 ÷ 计费输出 token）对照公开数据：

| 模型 | 当前 jᵢ | D′ 合理区间 | 评估 |
|---|---:|---:|---|
| gemini-3.7-flash | 1.0 | 0.4–1.2（轻量 MoE，PUE 1.09，**默认 medium 档**） | ✅ 合理（上沿）——V2 后可复核是否微调 |
| deepseek-v4-pro | 1.5 | 1.0–3.0（MoE 高效，PUE 1.25） | ✅ 合理（中档） |
| claude-sonnet-5 | 3.0 | 1.5–4.0（中型 reasoning） | ✅ 合理（中档上沿）——V1 核验后**无需**再因思考 token 上调 |
| gpt-5.5 | 3.0 | 1.5–5.0+（大型 reasoning） | ✅ 合理（中档）——v0.1 的"⚠️ 可能偏低"**降级撤销** |

**结论**：四个 jᵢ 均落在 D′ 口径合理区间内，无系统性偏低证据；GPT-5.5 的警示经 V1 核验后撤销。与 CHR 隐含 jᵢ（1.1–2.8）的独立收敛构成第二重印证。

---

## 6. 敏感性表（jᵢ 整体缩放 → RA / Λ / Ω）

沿用附录 A 已发布数据（RM=0.065870、RA=15.4088、Λ=233.93、Ω=5.738、j̄=2.2）：

| α = j_real / j̄ | j_real (J/token) | RA (USD/kWh) | Λ | Ω | Δln Λ |
|---:|---:|---:|---:|---:|---:|
| 0.5 | 1.1 | 30.82 | 467.9 | 6.431 | +0.69 |
| 1（现状） | 2.2 | 15.41 | 233.9 | 5.738 | 0 |
| 1.5 | 3.3 | 10.27 | 156.0 | 5.333 | −0.41 |
| 2 | 4.4 | 7.70 | 117.0 | 5.045 | −0.69 |
| 3 | 6.6 | 5.14 | 78.0 | 4.639 | −1.10 |
| 5 | 11.0 | 3.08 | 46.8 | 4.129 | −1.61 |
| 10 | 22.0 | 1.54 | 23.4 | 3.435 | −2.30 |

**解读：**
- jᵢ 现实不确定性约 ±50%（α∈[0.5, 1.5]）→ Λ∈[156, 468]，对数 ±0.41–0.69，**量级可管理，非数量级漂移**。
- 要"回到产业界 20–25 倍"需 j̄≈22–24 J/token，落在合理物理区间之外——反证"Λ=234 偏高主因是 jᵢ"不成立。
- **边界声明**：Λ=234 相对产业界 20–25 倍的差异，主因是**篮子选价**（加权均价 $11.44 vs 走量 $1/百万 token，约 10 倍），而非 jᵢ。jᵢ 校准**不会**把 Λ 打回 20–25 倍。两口径对照（前沿篮子 ≈190–234× / 走量篮子 ≈20–28×，均与 CHR 独立数据互证）见 `CHR_vs_TEPI_逐条对比.md` §8 发现 A。

---

## 7. 对已发布序列的连续性承诺（v0.2 新增）

针对"指数已日更（2026-08-16 起），改动是否影响连续性/可比性"的问题，本附录明确承诺：

1. **本附录为纯方法论文档**：不改动 `parity_index.py`、不改动已发布 CSV 的任何数值。2026-08-16 起的序列原样有效。
2. **jᵢ 属政策内参数**（方法论第 10 节）：任何 jᵢ 定档变更只进 `docs/changelog.md`、不改版本号、**已发布历史永不回溯**，自变更日起生效。
3. **未来若实施三档区间/置信带（P0）**：采用"新增列"方式（如 `RA_low/mid/high`），主列 `RA` / `Lambda_chained` / `Omega` 保持现有口径与水平不变，保证序列无断点。
4. **未来若换篮子**：走 README 既定的 `basket_version` 递增 + 链式接续（chain factor）流程，正式序列用 `Lambda_chained`。

---

## 8. 待核验项清单（v0.2 更新：V1/V2 已结案）

| # | 待核验 | 状态 | 结论 / 建议动作 |
|---|---|---|---|
| V1 | Claude Sonnet 5 / GPT-5.5 的 reasoning token 是否计入"输出 token" | ✅ **已核验（2026-09-01）** | 计入：四家厂商 reasoning token 均按输出 token 计价计费（OpenAI/Anthropic/Google/DeepSeek 官方文档 + OpenRouter API 实测，见 §2.1）。jᵢ 口径为 D′，无需上调 |
| V2 | Gemini 3.7 Flash 在 OpenRouter 默认档是 high 还是 medium | ✅ **已核验（2026-09-01）** | **medium**（Google 官方默认档表）。连带影响两处待拍板：质量分选档口径（统一最高档 vs 统一默认档）、gemini jᵢ 是否微调，见 §2.2 |
| V3 | 国内"15–20 度/百万 token（54–72 J/token）"口径的出处 | ⬜ 未结案 | 确认它是"含思考 token 的高强度推理"（对应 C 层）而非计费口径（D′） |
| V4 | Google scope factor 1.72× 对非 Google 厂商的适用性 | ⬜ 未结案 | 用 §3 数据源 12 的 PUE 因子做差异修正 |
| V5 | 三档区间（§5 建议值）的最终定档 | ⬜ 未结案 | 由项目所有者确认后写入 `parity_index.py`（届时才动代码） |

---

## 9. 变更登记规则（拟定，承接 v0.1）

- jᵢ 属**政策内参数**：更新只进 changelog、不改版本号。
- 每次变更记一行：`日期 | 模型 | 旧 jᵢ → 新 jᵢ (口径/出处)`。
- 已发布历史**永不回溯**；确需更正时以追加更正行方式处理。

---

## 附：与《TEPI 改进方案 v0.1》《CHR_vs_TEPI_逐条对比.md》的关系

- 本附录是方案 P0（jᵢ 溯源 + 置信带）的第一份落地底稿；方案"发现 2"的**最终归因以 CHR 对比文档的交叉验证为准**（主因篮子选价，非 jᵢ），本附录 v0.1 的更正与其一致，v0.2 进一步以 V1/V2 一手证据钉死口径。
- 定稿后的落地动作（均需项目所有者逐项确认）：① 正式化为 `token-parity/docs/ji_source.md`；② V2 连带的质量分选档口径决策（最高档 vs 默认档）；③ V3/V4 核验；④ `parity_index.py` 引入三档 jᵢ 与置信带输出（新增列不改主列）；⑤ 同步更新方案文档"发现 2"表述与 README/方法论对标段落。
