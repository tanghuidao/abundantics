# Compute Heat Rate（CHR）vs TEPI 逐条对比

> 数据截至 2026-08-31。CHR 数据源：SSRN 论文（Abstract 6322318）、ComputeHeatRate.com/chr-index、New Project Media 访谈、PJM 白皮书。TEPI 数据源：方法论 v0.1 中文版 + 附录 A 已发布数据（2026-08-16）。

---

## 0. 一句话定位

| | CHR | TEPI |
|---|---|---|
| 全称 | Compute Heat Rate（计算热率） | Token Energy Parity Index（Token 能量平价指数） |
| 提出者 | Hans Royal（独立研究，本职 Schneider Electric 高管） | tanghuidao（丰裕学实证研究） |
| 首发 | 2026-02-28（SSRN），2026-06-04 修订 | 2026-08 起发布日频序列 |
| 一句话 | "AI 负载还能承受多高的电价才不亏本" | "每度电给 AI 推理和比特币挖矿各带来多少毛收入，比值怎么变" |
| 血统 | 天然气 heat rate 的需求侧类比 | 购买力平价（PPP）的"焦耳当共同货币"类比 |

两者是**目前唯二站在"能量 × 价格"交叉点上的指标**，但方向相反：CHR 是"能量 → 价格容忍度"（单侧），TEPI 是"能量 → 收入"的**跨部门比值**（AI 侧 vs 比特币侧）。

---

## 1. 口径（Scope）

| 维度 | CHR | TEPI |
|---|---|---|
| 覆盖对象 | **只算 AI**（6 类 workload，含训练+推理） | **跨部门**：AI 推理 vs 比特币挖矿 |
| 训练是否计入 | ✅ 有（Frontier Model Training） | ❌ 只算推理 |
| 成本/利润口径 | **净口径**：扣除非电力成本 + 30% 利润率 | **毛口径**：纯毛收入，不扣任何成本（即 L1 缺失环） |
| 篮子 | 6 tier，从前沿训练到商品化推理 | 4 个前沿 reasoning 模型 |
| 价格源 | **厂商直连** API 定价（Anthropic/OpenAI/Google） | OpenRouter 聚合价 |
| 利用率假设 | 隐含（按已部署商业推理用电量收入加权） | 100% 满负荷（L3） |
| 跨部门比值 | 无（单侧绝对值） | 有（Λ = RA/RM） |
| 时间粒度 | 季度 | 日频 |

**核心差异一句话**：CHR 问的是"AI 这一侧自己还能扛多贵的电"，TEPI 问的是"同样一度电，AI 和比特币谁赚得多"。

---

## 2. 公式（Formula）

### CHR

```
CHR_w = (R_w − C_non-elec) / (1 + m)
```

| 符号 | 含义 | 单位 |
|---|---|---|
| R_w | workload w 每 MWh 计算产生的**毛收入** | $/MWh |
| C_non-elec | 非电力运营成本（冷却、网络、地产、劳动力、**硬件摊销**） | $/MWh |
| m | 必需回报率边际 = **0.30**（30%） | 无量纲 |
| CHR_w | 该 workload 仍能盈利的**最高可承受电价** | $/MWh |

**R_w 的换算**（论文隐含）：R_w = 3.6×10⁹ × (价格/token) ÷ jᵢ，其中 3.6×10⁹ 是每 MWh 的焦耳数，jᵢ 是每 token 能耗。

### TEPI

```
RM = k · PBTC / εBTC          （k = 3.6×10⁶ J/kWh）
RA = k · Σᵢ wᵢ · pᵢ / jᵢ       （每个模型先除再加权）
Λ  = RA / RM                  （能量套利比）
Ω  = ln Λ + 质量项            （质量调整后的平价偏离指数）
```

| 符号 | 含义 | 单位 |
|---|---|---|
| RM | 挖矿每度电毛收入 | $/kWh |
| RA | 推理每度电毛收入 | $/kWh |
| pᵢ / jᵢ | 模型 i 的每 token 价 / 每 token 能耗 | $/token 与 J/token |
| Λ | 能量套利比 | 无量纲 |

**形式上的同源**：CHR 的 R_w 与 TEPI 的 RA 是**同一物理量**（每单位电的 AI 毛收入），仅差一个 1000 倍单位换算（MWh↔kWh）。CHR 多做了"扣 C_non-elec、扣利润率 m"这一步，TEPI 停在毛收入。

---

## 3. 单位（Units）

| | CHR | TEPI |
|---|---|---|
| 主输出单位 | **$/MWh**（美元/兆瓦时） | **$/kWh**（美元/千瓦时） |
| 换算 | 1 $/MWh = 0.001 $/kWh | 1 $/kWh = 1000 $/MWh |
| 比值量 | 相对天然气基准的**倍数**（127×） | Λ 无量纲比值、Ω 对数 |
| 物理公分母 | MWh（焦耳） | kWh（焦耳）——**同族** |

两者都用"焦耳"当物理公分母，只是粒度不同：CHR 用 MWh（电网/发电行业习惯），TEPI 用 kWh（终端电费习惯）。

---

## 4. 数据来源（Data Sources）

### CHR（论文 + chr-index 披露）

| 类别 | 具体来源 |
|---|---|
| GPU 规格/基准 | NVIDIA 官方文档（H100/B200/GB200）、MLPerf 推理基准 |
| API 定价 | Anthropic（Opus 4.7：$5/$25；Sonnet 4.6：$3/$15 每百万 token）、OpenAI（GPT-5.5：$5/$30；GPT-5.4：$2.50/$15）、Google（Gemini 3.1 Pro：$2/$12） |
| 云计算费率 | AWS、Google Cloud、Azure 按需 GPU 实例 |
| 设施成本 | Cushman & Wakefield、JLL 数据中心报告、超大规模厂商 SEC 文件 |
| 能源数据 | EIA（Henry Hub 气价、批发电价）、PJM LMP、ERCOT 结算价、EIA-930 |
| 权重 | 超大规模厂商财报、API 流量估算、McKinsey/Goldman Sachs/IEA 行业调查 |

### TEPI

| 类别 | 具体来源 |
|---|---|
| 币价 | CoinGecko |
| 挖矿收入 | Luxor Hashprice、mempool.space |
| 模型价 | OpenRouter 聚合价 |
| 挖矿效率 η | CBECI（剑桥，20 J/TH） |
| 质量分 sᵢ | Artificial Analysis Intelligence Index |
| 每 token 能耗 jᵢ | 人工设定（1.0–3.0 J/token，加权 2.2） |

**对比**：CHR 的 GPU 规格 + 云费率 + 设施成本这条链，恰好是 TEPI 的 jᵢ 溯源（O3）**最需要的交叉数据源**——CHR 已经用 NVIDIA/MLPerf/设施报告把"每 token 能耗"隐含地解了出来（见 §8 发现 B）。

---

## 5. 是否开源（Open Source）

| | CHR | TEPI |
|---|---|---|
| 代码仓库 | ❌ 无 GitHub | ✅ github.com/tanghuidao/token-parity |
| 数据可下载 | ❌ 无 CSV / 无 API | ✅ raw/ 归档 + parity_series.csv 全公开 |
| 复现方式 | 人工读论文 PDF + 网站 HTML 表格 | 一键跑 `parity_index.py`，自动化 workflow |
| 更新机制 | 人工季度发布 | GitHub Actions 日频自动更新 |
| 治理纪律 | 无（个人研究） | "只记不回溯" + changelog |
| 同行评审 | 0 引用、未评审（SSRN 工作论文） | 开源社区可审、可 fork |

**这是 TEPI 对 CHR 最大的结构性优势**：CHR 的数值只能"信 Hans Royal 算的对"，TEPI 的每个数都能被任何人复算。CHR 想要长期站住，必须补上"开源 + 机器可读数据"这一课——而 TEPI 天生就有。

---

## 6. 已有数据（Existing Data）

### CHR（季度参考值，$/MWh）

| Workload Tier | Q1 2026 | Q2 2026 | 环比 |
|---|---|---|---|
| Frontier Inference（Opus 4.7/GPT-5.5） | 53,650 | 60,770 | ↑13% |
| Mid-Tier Inference（Sonnet 4.6/GPT-5.4） | 8,120 | 11,730 | ↑45% |
| Enterprise Agentic AI | 8,080 | 9,230 | ↑14% |
| Enterprise Contracted | 1,270 | 1,730 | ↑36% |
| Commodity Inference（mini/nano） | ~800† | 1,465 | ↑83% |
| Frontier Model Training | ~500† | ~500† | 持平 |
| **混合平均（收入加权）** | **6,350** | **~8,000** | **↑27%** |

> † 独立 CHR 为负，靠组合交叉补贴解释。历史仅 2 个季度（2026.3 起）。

### TEPI（2026-08-16 发布数据）

| 量 | 值 |
|---|---|
| RM | 0.065870 $/kWh |
| RA | 15.4088 $/kWh |
| Λ | 233.93 |
| Ω | 5.738（e^Ω ≈ 310） |

> 日频序列，含 raw/ 归档，规划历史回填（O1）。

**对比**：CHR 历史仅 2 个季度、覆盖 6 个 tier；TEPI 日频、但当前序列也还很短。**两者都是"新生指标"，都还没有足够长的序列来讲趋势故事。**

---

## 7. 局限（Limitations）

### CHR 的局限

1. **未评审 + 0 引用**：SSRN 工作论文，个人研究，无同行评审背书。
2. **不开放、不机器可读**：无 CSV/API/代码，复现成本极高，是它作为"标准指标"的最大短板。
3. **C_non-elec 和 m=0.30 是假设值**：分 tier 但估值粗糙，尤其硬件摊销（占大头）敏感性未充分披露。
4. **权重主观**：收入加权基于行业调查（McKinsey/Goldman/IEA），非硬数据。
5. **部分 tier 独立 CHR 为负**：training/commodity 需交叉补贴解释，口径复杂、易被误读。
6. **历史极短**（2 季度）：无法谈趋势，只能谈水平值。
7. **未处理推理模型的"思考 token"口径**：用的 Opus 4.7/GPT-5.5 都是 reasoning 模型，但未区分思考 token 是否计入。

### TEPI 的局限（作者自述 L1–L6，我核对认可）

1. **L1 毛收入非利润**：不扣成本——恰好是 CHR 补齐的那一环。
2. **L2 只计输出 token**：忽略输入 token 收入与 prefill 能耗。
3. **L3 满负荷惯例**：100% 可计费利用率，RA/Λ 是上界。
4. **L4 人工 η**：20 J/TH，±25% 使 Λ 对数水平动 ±0.22。
5. **L5 最薄弱输入 jᵢ**：1.0–3.0 J/token 人工设定。
6. **L6 单链单一价格源**：OpenRouter 单源。

---

## 8. 关键发现（三组交叉验证）

### 发现 A｜CHR 独立印证了 TEPI 的 RA 量级，Λ=234 不是"算错了"

用 CHR 的 Q1 混合平均 R_w = $12,500/MWh 换算成 $12.5/kWh，对比 TEPI 的 RA = $15.4/kWh：

| 口径 | 值 | 对 RM 的比值 Λ |
|---|---|---|
| TEPI 前沿篮子 | $15.4/kWh | **234×** |
| CHR 混合平均 | $12.5/kWh | **190×** |
| CHR 走量（commodity） | $1.85/kWh | **28×**（= 产业界 20–25 倍区间） |

**结论**：之前"Λ 被高估约一个数量级"的说法需要**彻底收回**。真相是——Λ 的水平值**完全由"篮子选什么模型"决定**：
- 选前沿模型（TEPI 篮子、CHR 的前沿/中端 tier）→ Λ ≈ 190–234 倍；
- 选走量模型（产业界引用的 mini/nano）→ Λ ≈ 20–28 倍。

**两者都自洽，没有谁"算错"。** CHR 用完全独立的数据源（厂商直连定价 + NVIDIA/MLPerf + 设施报告）也得出了与 TEPI 同量级的 RA，这反而是对 TEPI 方法论的一次**强有力的独立背书**。真正值得讨论的是"篮子代表性"（是否应纳入 commodity 模型），而非"口径错误"——这正是我之前已识别、建议另立议题的"篮子选价问题"。

### 发现 B｜CHR 的隐含 jᵢ 与 TEPI 收敛（1–3 J/token）

反推 CHR 各 tier 隐含的"每 token 能耗"：

| Tier | 隐含 jᵢ |
|---|---|
| Frontier Inf（GPT-5.5 $30/百万） | 1.30 J/token |
| Frontier Inf（Opus 4.7 $25/百万） | 1.08 J/token |
| Mid-Tier（Sonnet 4.6 $15/百万） | 2.77 J/token |
| Commodity（mini ~$0.60/百万） | 0.38 J/token |

前沿/中端模型的隐含 jᵢ ≈ **1.1–2.8 J/token**，与 TEPI 的 1.0–3.0 J/token **完全收敛**。

**结论**：两个独立方法（TEPI 用 OpenRouter 价 + jᵢ 假设；CHR 用厂商直连价 + GPU/MLPerf 基准反推）对"前沿推理每 token 能耗"的估计**独立收敛在 1–3 J/token**。这彻底坐实了之前 ji 附录的更正——**jᵢ 并不系统性偏低，"jᵢ 偏低 10 倍"是错误归因**。TEPI 的 jᵢ 与国外最接近的独立估计一致。

### 发现 C｜CHR 与 TEPI 是"镜像互补"，各自补对方的结构性缺口

| 缺口 | 谁缺 | 谁有 |
|---|---|---|
| 毛收入 → 利润（扣成本+利润率） | TEPI（L1） | **CHR**（C_non-elec + m） |
| 跨部门比值（AI vs 比特币） | CHR | **TEPI**（Λ） |
| 开源 + 日频序列 | CHR | **TEPI** |
| 多 tier + 训练 + 厂商直连价 | TEPI | **CHR** |
| 质量分（sᵢ） | CHR | **TEPI**（Artificial Analysis） |

这不是竞争关系，而是**可以互相喂料的镜像**：CHR 的 C_non-elec 分解就是 TEPI O2（Λ′ 净利率变体）的现成模板；TEPI 的开源 + 跨部门比值是 CHR 目前最缺的。

---

## 9. 对 TEPI 的启示（可执行建议）

1. **把 CHR 列为正式对标**（README + 方法论），取代之前"只提 CBECI/Artificial Analysis"的定位——它才是真正同赛道的对标，且方向互补。

2. **复用 CHR 的数据源做 jᵢ 溯源（O3 落地）**：CHR 用的 NVIDIA 官方文档 + MLPerf + Cushman&Wakefield/JLL 设施报告，恰好是 TEPI jᵢ 附录最需要的第三方交叉数据源。

3. **借鉴 CHR 的 C_non-elec 分解，落地 O2（Λ′ 净利率变体）**：CHR 把非电力成本拆成冷却/网络/地产/劳动力/硬件摊销五块，TEPI 可照此给 RA 扣成本，得到与 CHR 直接可比的"净口径"。

4. **引入厂商直连价做第二价格源（L6 缓解）**：CHR 的 Anthropic/OpenAI/Google 直连价 vs TEPI 的 OpenRouter 聚合价，天然构成稳健性对照。

5. **守住 TEPI 的护城河**：CHR 历史仅 2 个季度、且不开放数据——TEPI 的日频序列 + 开源是决定性优势，任何改进都不应牺牲这一点。

6. **审慎处理"篮子代表性"议题**：既然 Λ 的水平值取决于篮子，应明确"TEPI 度量的是前沿推理 vs 挖矿"，并在文档中显式声明这一范围边界，避免读者把 234 倍误解为"整个 AI 行业"。

---

## 附：CHR 关键事实速查

- **提出者**：Hans Royal，Schneider Electric 高级总监（可再生能源与碳咨询），18 年能源老兵；CHR 为**独立个人研究**（SSRN 署名 "Independent"，"Views are my own"），非 Schneider 官方成果。
- **时间线**：2026-02-28 SSRN 首发 → 2026-05 被 PJM《Powering Reliability Through Market Design》白皮书 p49–50 点名引用（"CEO-signed"）→ 2026-06 修订 + 发布 Q2 参考值。
- **商业属性**：非商业化（个人研究 + 网站/Substack/LinkedIn），有 partnership/speaking 渠道但无收费产品。
- **核心数值**：混合平均 CHR ≈ $6,350/MWh（Q1）→ ~$8,000（Q2），相对天然气 heat rate 基准 ~$50/MWh 的 **127 倍**；前沿推理高达 $53,650–60,770/MWh。
- **行业影响**：已被用于解读 NextEra/Dominion 并购、PJM 容量价格暴涨（$28.92→$333.44/MW-day）、需求侧响应设计。
