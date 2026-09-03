# H1「世纪图表」CPI 研究（丰裕学）

> **仓库边界声明（2026-09-03 起）**：本目录属于 **abundantics（丰裕学）** 项目，
> 是丰裕学核心假说「稀缺向难自动化品类（N）迁移上涨、可自动化品类（R）丰裕化下跌」的
> 长期价格结构验证。**与 token-parity（TEPI，能源电力在 AI/加密领域的平价比较）无关。**
> 此前相关代码/数据被误放入 token-parity，已于 2026-09-03 迁移至此。

## 目录结构

```
research/h1-cpi/
├── README.md                      # 本文件（边界与结构说明）
├── category_mapping.csv           # 【单一信息源】N/R 分组 + 品类层级 + seriesID 映射
├── h1_cpi_archive.py              # fetch 层：月度归档 CPI 序列 → raw_h1_cpi/
├── h1_verify_series.py            # 核验器：把「待核实」seriesID 与 BLS 权威目录比对
├── h1_build_mapping.py            # 建表：从 BLS cu.series/cu.item 推导品类层级
├── h1_item_hierarchy.csv          # 品类层级中间产物
├── h1_analyze.py                  # analyze 层：raw → 画像 + 核心/样本外 Welch/MW 检验
├── h1_welch_regression.py         # 回归基线（Welch t / Mann-Whitney 复现脚注）
├── h1_hi_diagnostic.py            # 层级诊断工具
├── raw_h1_cpi/                    # 归档数据（YYYY-MM-DD.json，由 h1_cpi_archive 落盘）
└── docs/                          # 研究文档（书面规则、核验说明、简报、溯源附录）
```

## 数据流

```
BLS v2 API --h1_cpi_archive.py--> raw_h1_cpi/YYYY-MM-DD.json
raw_h1_cpi/*.json --h1_analyze.py--> h1_analyzed/h1_analyzed.json + h1_metrics.csv
```

- `category_mapping.csv` 是 N/R 分组的**单一信息源**（`H1分组` 列），fetch/analyze 均只读它。
- `h1_analyzed/` 是可从 `raw_h1_cpi/` 重算的中间产物，不入库（遵循单一信息源原则）。

## 相关 GitHub Actions（本仓库）

- `.github/workflows/h1-cpi-archive.yml` —— 月度归档（每月 16 号 UTC 05:30）
- `.github/workflows/h1-verify-series.yml` —— seriesID 核验（手动触发）
