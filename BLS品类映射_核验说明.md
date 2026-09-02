# BLS 品类映射核验说明（说明书 A）

> 日期：2026-09-02。目标：为"世纪图表（H1）"建立既有品类 ↔ BLS CPI-U 序列映射，并储备扩展至 CPI 全样本的候选清单。

## 一、结论速览

- 12 个世纪图表品类已映射到 BLS CPI-U（未季调）序列，见 `category_mapping.csv`。
- **大学教科书**：BLS 不单独发布 college textbooks 子项，候选序列均不存在，已**降级**用聚合层 `CUUR0000SEEA`，并在 CSV 备注中明确标注（非悄悄替换）。

## 二、大学教科书探测（关键证据）

候选序列探测结果（逐一核对 `cu.series`，比 API 更权威，因为 API 本就建立在该文件之上）：

| 候选 series_id | 是否存在 |
|---|---|
| CUUR0000SEEA01 | ❌ 不存在 |
| CUUR0000SSEA011 | ❌ 不存在 |
| CUUR0000SSEA01 | ❌ 不存在 |
| CUUR0000SEEA02 | ❌ 不存在 |

- `cu.item` 中 SEEA（Educational books and supplies）**没有任何子项**（无 SEEA01/SEEA02），也没有以 SSEA 开头的 item_code。
- 第三方引用的 `CUUR0000SEEA01` / `CUUR0000SSEA011` 是历史 ELI 内部代码，**从未作为独立序列对外发布**。

**退用方案**：`CUUR0000SEEA`（Educational books and supplies，聚合层）。

**量级核验**（FRED 复读同一序列，未季调）：
- 2001-01 = 289.2 → 2026-07 = 776.5，累计 **+168.5%**。
- 与"2001 年以来累计约 +150%"同量级（约 150% 是 2016 前后口径，到 2026 已升至 ~168%），通过。

**重要更正**：`CUUR0000SEEA` 实际 **1967 起算**（非 2001），1998 窗口**无缺口**，不会出现"套到 1998 窗口缺数据"的问题。

## 三、数据访问受阻说明（重要）

- BLS 全站（`api.bls.gov` + `download.bls.gov`）对本地网络（沙箱出口 IP + 用户真实网络 IP）均被 Akamai **地域封锁**（HTTP 403 "Access Denied"）。
- 本地 31223 代理当前未运行；FRED、Jina Reader 亦不可达。
- 改用 **WebFetch（服务端网络）** 访问 `download.bls.gov` 扁平数据文件（cu.series / cu.item / cu.data），等价完成 API 探测。
- 含义：**BLS 数据的实际拉取应由 GitHub Action 执行**（GitHub runner 位于美国，可直连 BLS）；本地开发环境无法直连 BLS。

## 四、各品类数据起始年份（cu.series，权威）

| 中文品类名 | series_id | 起始年月 |
|---|---|---|
| CPI总指数 | CUUR0000SA0 | 1913-01 |
| 食品饮料 | CUUR0000SAF | 1967-01 |
| 医疗护理服务 | CUUR0000SAM2 | 1935-03 |
| 住房（位置性） | CUUR0000SEHC01 | 1982-12 |
| 医院服务 | CUUR0000SEMD01 | 1996-12 |
| 大学学费 | CUUR0000SEEB01 | 1977-12 |
| 托儿照护 | CUUR0000SEEB03 | 1990-12 |
| 手机通信服务 | CUUR0000SEED03 | 1997-12 |
| 电脑软件 | CUUR0000SEEE02 | 1997-12 |
| 玩具 | CUUR0000SERE01 | 1977-12 |
| 电视机 | CUUR0000SERA01 | 1950-12 |
| 大学教科书（降级为 SEEA） | CUUR0000SEEA | 1967-01 |

> 全部序列均早于 1998 起算，世纪图表 1998 窗口全量覆盖、无缺口。

## 五、储备与后续

1. `bls_cu_item_candidates.csv`：从 cu.item 提取的候选品类清单（level 0–3，约 130 项），供扩展至 CPI 全样本使用。**非原始文件**——完整原始 cu.item（含 ELI 级代码 + 精确 display_level）应由 Action 直连拉取。
2. BLS_API_KEY 已提供，待确认存储仓库后写入 GitHub Actions Secrets（命名 BLS_API_KEY）。
3. 后续拉数据走 GitHub Action：`https://api.bls.gov/publicAPI/v2/timeseries/data/`（POST，seriesid + registrationkey），或直连 `download.bls.gov/pub/time.series/cu/` 扁平文件。
