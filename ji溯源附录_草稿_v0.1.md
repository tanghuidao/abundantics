# jᵢ（单 token 能耗）溯源附录 — 草稿 v0.1

> **状态**：草稿，仅供项目所有者审阅。**未改动任何计算逻辑、代码或已发布序列。**
> **对应路线图**：O3（jᵢ 溯源附录 + 敏感性表）
> **关联局限**：L5（工作假设性质的 jᵢ，最薄弱输入）
> **用途**：把 jᵢ 从"点值"升级为"可溯源的三档区间"，为后续"置信带发布"做准备。
> **体例**：沿用 `docs/quality_scores_lookup.md` 与 `docs/changelog.md`。

---

## 0. 摘要与一次必要的更正

本附录起草过程中，对《TEPI 改进方案 v0.1》中"发现 2"（"Λ=234 倍因 jᵢ 假设偏低被高估约一个数量级"）做了一次**溯源验证，结论需要更正**：

**更正的结论：**
1. jᵢ 作为"每输出 token 全栈能耗（含 PUE）"，公开实测的合理区间约为 **0.5–5 J/token**；TEPI 当前篮子 jᵢ = 1.0–3.0 J/token **落在该区间内，并不系统性偏低**。
2. Λ=234 与产业界"20–25 倍"的差异，**主因不是 jᵢ，而是篮子选价**：TEPI 篮子含 GPT-5.5（$30/百万 token）与 Claude Sonnet 5（$10/百万 token）两个高端 reasoning 模型，加权均价约 $11.44/百万 token，是走量模型均价（约 $1/百万 token）的 **约 10 倍**。
3. 定量验证：保持 j̄=2.2 不变、仅把篮子均价换到 $1/百万 token，Λ 即回落至 **24.8 倍**（恰在产业界 20–25 倍区间）；反之，保持篮子价不变、要把 Λ 压到 20–25 倍，需要把 jᵢ 放大 **11–14 倍**（j̄≈25–31 J/token），这已远超 jᵢ 的合理物理区间。

**因此，本附录的目的相应修正为：** 不是"用 jᵢ 校准把 Λ 打回 20–25 倍"，而是
- 消除 L5 的输入不确定性（三档区间 + 溯源）；
- 明确 reasoning token（思考 token）的口径——这是推理模型时代 L2 未覆盖的关键缺口；
- 为 O3 的落地提供第一份可复核底稿。

> 附注：篮子选价的问题属于第 6.1 节"入选原则"与篮子代表性的张力，不属本附录范围，但已在 §5 末尾以"边界声明"记录，避免读者误以为 jᵢ 校准会大幅改写 Λ。

---

## 1. 当前篮子的 jᵢ 值（v1，2026-08-16 生效）

| 模型（OpenRouter id） | 权重 w̃ᵢ | jᵢ (J/token) | 质量分 sᵢ | 口径声明 |
|---|---:|---:|---:|---|
| anthropic/claude-sonnet-5（基准） | 0.30 | **3.0** | 55 | 输出 token，全栈含 PUE |
| openai/gpt-5.5 | 0.25 | **3.0** | 56 | 输出 token，全栈含 PUE |
| google/gemini-3.7-flash | 0.25 | **1.0** | 56 | 输出 token，全栈含 PUE |
| deepseek/deepseek-v4-pro | 0.20 | **1.5** | 53 | 输出 token，全栈含 PUE |

加权均值 j̄ = 0.30×3.0 + 0.25×3.0 + 0.25×1.0 + 0.20×1.5 = **2.200 J/token**（与附录 A 的 `basket_j_per_token` 一致 ✓）。

**来源标注**：方法论符号表将 jᵢ 定义为"模型 i 每输出 token 全栈能耗，含 PUE [待核验]"。当前四个数值在 `parity_index.py` 的 `inference_basket` 中作为**人工设定的工作假设**录入，**无逐项公开出处**——这正是本附录要补的。

---

## 2. 公开实测数据源（可溯源）

| # | 来源 | 模型 / 硬件 | 口径 | 数值 | 出处 |
|---|---|---|---|---|---|
| 1 | ML.ENERGY Leaderboard | Llama 3.1 70B / 4×H100, vLLM | **GPU-only** | batch 8 = 3.76；batch 256 = 0.48；batch 1024 = 0.37 J/token | ml.energy（NeurIPS 2025 Datasets & Benchmarks） |
| 2 | ML.ENERGY Leaderboard | Llama 3.1 8B / H100 | **GPU-only** | v3 batch 64 = 0.12 J/token（v2 = 0.20） | 同上（纵向分析博客） |
| 3 | Google Gemini 全栈 | Gemini Apps 中位 text prompt | **全栈**（加速器+CPU/DRAM+空闲机+数据中心开销） | 0.24 Wh/prompt；分解 0.14+0.06+0.02+0.02 | arXiv 2508.15734 |
| 4 | Google scope factor | 同上 | 加速器→生产环境放缩 | **1.72×**；舰队平均 PUE = 1.09 | arXiv 2508.15734 |
| 5 | Google 窄口径对照 | 同上（更高效机器样本） | 仅活跃加速器 | 0.10 Wh/prompt | arXiv 2508.15734 |
| 6 | Cell/Joule 2026 综述 | Llama 3.1 70B（361 输出 token） | GPU-only | 0.04 Wh/query ≈ **0.4 J/token** | Cell, S2542-4351(26)00114-5 |
| 7 | Cell/Joule 2026 综述 | DeepSeek-V3（8968 token，H100 换算） | GPU-only | 9.30 Wh/query ≈ **3.7 J/token** | 同上 |
| 8 | Cell/Joule 2026 综述 | DeepSeek-R1（测试时缩放） | GPU-only | 20.9 Wh/query（约 V3 的 2.25×） | 同上 |
| 9 | Samsi et al. 2023 | LLaMA-65B / V100–A100 | 实测 | ~3–4 J/output token | 学术实测（via John Snow Labs 综述） |
| 10 | Lin et al. 2025 | Llama3-70B FP8 / 8×H100, vLLM | 实测（高负载优化） | ~0.39 J/token | 同上 |
| 11 | AI Energy Score | Llama-3-70B / H100 | GPU-only | 1.72 Wh/request | 与 ML.ENERGY 同一模型相差 **37×**（0.046 vs 1.72 Wh） |
| 12 | Provider PUE 因子 | OpenAI(Azure)1.20 / Anthropic(GCP)1.10 / Google 1.09 / DeepSeek 1.25 | PUE | — | arXiv 2603.23528 |

**两点必须先强调的困难：**
- **同一模型的公开实测可相差 37×**（数据源 1 的 ML.ENERGY 0.046 Wh/request vs 数据源 11 的 AI Energy Score 1.72 Wh/request），原因是 batch 大小、vLLM 版本、计量边界（GPU 计数器 vs 整机功率）不同。**任何"单点 jᵢ"本质上都是口径选择，而非客观常数。**
- **公开实测几乎全是 Llama/GPT 早期或非 reasoning 模型**，TEPI 篮子的四个模型（Claude Sonnet 5 / GPT-5.5 / Gemini 3.7 Flash / DeepSeek V4 Pro）**均无公开的逐 token 能耗实测**，只能"同架构同量级模型代理"。

---

## 3. 口径分层（本附录的核心）

jᵢ 的公开口径至少要分四层，混用会差出一个数量级：

| 层级 | 口径 | 典型量级 | 说明 |
|---|---|---|---|
| A | GPU-only，仅加速器 | 0.1–4 J/token | ML.ENERGY / AI Energy Score 的基准口径 |
| B | 全栈（× scope 1.72 + PUE 1.09–1.25） | 0.2–7 J/token | Google 的全栈口径；A × 1.72 |
| C | 全栈 + 含 reasoning token（思考 token） | 5–20+ J/token | 思考 token 能耗被分摊到输出 token 上（DeepSeek-R1 比 V3 高 2.25×） |
| D | 仅输出 token（不计思考 token） | = B | TEPI 当前名义口径 |

**TEPI 当前 jᵢ 的口径是 D（输出 token，全栈含 PUE）**，但篮子四个模型全部是 **reasoning 模型**（Claude Adaptive Reasoning、GPT-5.5 xhigh、Gemini high、DeepSeek Reasoning Max）。这意味着存在一个**未解决的口径缺口**：

- 若 OpenRouter 的"输出 token"指**可见回答 token**（不含思考 token），而模型内部为产出这些 token 消耗了额外的思考 token 能量，则"每输出 token 全栈能耗"实际应落在 **C 层**，jᵢ 会被系统性**低估**；
- 若"输出 token"已把思考 token 一并计入计价与能耗，则口径自洽，无需调整。

**这是 L2（仅计输出 token）在 reasoning 模型时代的延伸，比单纯的"数值偏高/偏低"更本质。** 建议作为 O3 的第一个待核验项（见 §6）。

---

## 4. 交叉校准：当前 jᵢ 落点评估

把当前篮子 jᵢ 与公开数据（折算到全栈口径 B）对照：

| 模型 | 当前 jᵢ | 全栈合理区间（口径 B） | 评估 |
|---|---:|---:|---|
| gemini-3.7-flash | 1.0 | 0.5–1.5（轻量 MoE，Google PUE 1.09） | ✅ 合理（低档上沿） |
| deepseek-v4-pro | 1.5 | 1.0–3.0（MoE 高效，PUE 1.25） | ✅ 合理（中档） |
| claude-sonnet-5 | 3.0 | 1.5–4.0（中型 reasoning） | ✅ 合理（中档上沿），**待核验 reasoning token** |
| gpt-5.5 | 3.0 | 1.5–5.0+（大型 reasoning） | ⚠️ 可能偏低，**待核验 reasoning token** |

**结论**：四个 jᵢ 均落在"全栈输出 token"口径的合理区间内，**没有系统性偏低 10 倍的证据**。最需要澄清的是 Claude Sonnet 5 与 GPT-5.5 这两个大型 reasoning 模型的**思考 token 是否已计入**（若未计入，二者 jᵢ 应上移 2–3×，入高档）。

---

## 5. 敏感性表（jᵢ 整体缩放 → RA / Λ / Ω）

沿用附录 A 已发布数据（RM=0.065870、RA=15.4088、Λ=233.93、Ω=5.738、j̄=2.2），做 jᵢ 整体缩放敏感性：

| α = j_real / j̄ | j_real (J/token) | RA (USD/kWh) | Λ | Ω | Δln Λ |
|---:|---:|---:|---:|---:|---:|
| 0.5 | 1.1 | 30.82 | 467.9 | 6.431 | +0.69 |
| 1（现状） | 2.2 | 15.41 | 233.9 | 5.738 | 0 |
| 1.5 | 3.3 | 10.27 | 156.0 | 5.333 | −0.41 |
| 2 | 4.4 | 7.70 | 117.0 | 5.045 | −0.69 |
| 3 | 6.6 | 5.14 | 78.0 | 4.639 | −1.10 |
| 5 | 11.0 | 3.08 | 46.8 | 4.129 | −1.61 |
| 10 | 22.0 | 1.54 | 23.4 | 3.435 | −2.30 |

**解读（更正后）：**
- jᵢ 的现实不确定性约 ±50%（α∈[0.5, 1.5]），对应 Λ∈[156, 468]，对数水平 ±0.41–0.69。**这是 jᵢ 不确定性的真实影响，量级可管理，不是数量级漂移。**
- 要"回到产业界 20–25 倍"需要 α≈10–11（j̄≈22–24 J/token），**落在 jᵢ 合理物理区间之外**——这反证了"Λ=234 偏高主因是 jᵢ"不成立。
- **边界声明（重要）**：Λ=234 相对产业界的差异，主因是**篮子选价**（加权均价 $11.44 vs 走量 $1/百万 token，约 10 倍），而非 jᵢ。jᵢ 校准**不会**把 Λ 打回 20–25 倍；任何基于"jᵢ 校准大幅改写 Λ 水平值"的预期都需据此修正。

---

## 6. 待核验项清单（O3 的首批任务）

| # | 待核验 | 建议动作 | 优先级 |
|---|---|---|---|
| V1 | Claude Sonnet 5 / GPT-5.5 的 **reasoning token 是否计入**"输出 token" | 查 OpenRouter 对 reasoning 模型的计价与 token 计数口径 | **高** |
| V2 | Gemini 3.7 Flash 在 OpenRouter 默认档是 high 还是 medium | 决定其 jᵢ 是否需按档位微调 | 中 |
| V3 | "15–20 度/百万 token（54–72 J/token）"这一国内口径的**出处与口径** | 确认它是"含思考 token 的高强度推理"，而非"输出 token" | 中 |
| V4 | Google scope factor 1.72× 对非 Google 厂商（Anthropic/OpenAI/DeepSeek）的适用性 | 用 §2 数据源 12 的 PUE 因子做差异修正 | 中 |
| V5 | 三档区间（§4 建议值）的最终定档 | 由项目所有者确认后写入 `parity_index.py`（届时才动代码） | 低 |

---

## 7. 变更登记规则（拟定）

参照质量分治理（`docs/changelog.md`），jᵢ 变更建议遵循：
- jᵢ 属**政策内参数**（方法论第 10 节：参数更新只进 changelog、不改版本号）；
- 每次变更记一行：`日期 | 模型 | 旧 jᵢ → 新 jᵢ (口径/出处)`，例如 `2026-09-xx | gpt-5.5 | 3.0 → 5.0 (含 reasoning token 分摊, 依据 XX)`；
- 已发布历史**永不回溯**；若确需更正，以追加更正行方式处理。

---

## 附：本附录与《TEPI 改进方案 v0.1》的关系

本附录是方案 P0（jᵢ 溯源 + 置信带）的**第一份落地底稿**，同时**更正了方案"发现 2"的归因**。建议下一步（需项目所有者确认后再执行）：
1. 把本附录正式化为 `token-parity/docs/ji_source.md`；
2. 完成 §6 的 V1/V2 核验（reasoning token 口径）；
3. 在 `parity_index.py` 引入三档 jᵢ 与置信带输出（**届时才动代码**）；
4. 同步更新方案文档 v0.1 中"发现 2"的表述。
