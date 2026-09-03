#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h1_verify_series.py —— H1 品类 seriesID 存在性核验（BLS v2 API catalog 权威核验）
====================================================================================

用途：
  把 category_mapping.csv 中「待核实」的 seriesID 逐一与 BLS 权威目录比对，
  确认存在则翻「已核实」并回填「数据起始年份」，不存在则 fail loud 并在报告中列出。

为什么用 BLS v2 API（catalog=true）而非 cu.series 扁平文件：
  最初设计用 download.bls.gov 的 cu.series 扁平文件（免 key、一次拿全目录）。
  实测发现 download.bls.gov 对 GitHub Action runner 的 IP 段同样返回 403
  （Akamai 封锁，本地网络与 runner 网络都不可直连；仅 WebFetch 服务端网络可读，
   但文件过大、AI 摘要无法做 137 项的精确匹配）。
  BLS v2 API（api.bls.gov）经实测在 GitHub Action runner 上可达（abundantics 的
  bls-daily 已稳定成功），且支持 catalog=true 返回每个 series 的官方元数据
  （series_title / seasonality / survey_name / measure_data_type / area 等），
  可精确判断存在性并核对官方标题。

存在性判断（关键，规避「年份无数据」干扰）：
  BLS 对「格式正确但不存在的 seriesid」返回 message "Series does not exist..."，
  且该 series 的 catalog 为空；对「存在但请求年份无数据」的 series 返回
  "No Data Available for Series X Year: YYYY"，但 catalog 仍非空。
  因此以 catalog 是否含 series_title 作为「存在」的唯一判据，不依赖 data 是否非空。

数据起始年份（BLS v2 API 局限下的降级方案）：
  BLS v2 API 的 catalog 对象**不返回 begin_year**（官方字段仅 series_title /
  series_id / seasonality / survey_name / survey_abbreviation / measure_data_type /
  area 等）。真实 begin_year 只能从 download.bls.gov 的 cu.series 扁平文件
  （runner 403）或多次回溯 data 请求获取。
  本项目世纪图表窗口为 1998 至今（BLS CPI 1998 年细项目录重组，为稳定起点），
  故「数据起始年份」回填「窗口内最早观测年份」：
    · 最早观测 = 1998 → 填「≤1998」（覆盖世纪窗口起点，真实 begin_year ≤ 1998）
    · 最早观测 > 1998 → 填精确年份（1998 后新增的系列）
  该字段语义为「世纪窗口内最早有效年份」，与老品类的真实 begin_year 不同，
  在核验报告中一并说明。

时间窗口（BLS 注册 key 单次 ≤20 年）：
  主块 1998-2017（20 年）覆盖世纪窗口起点 + 老系列；副块 2018-2025（8 年）覆盖
  近年新增系列。主块未命中（catalog 空）的 seriesID 进入副块二次确认，两块都空
  才判「不存在」。

环境要求：
  需 BLS_API_KEY（GitHub Actions Secret，api.bls.gov 免费 key）。本地开发网络
  无法直连 api.bls.gov，故实际运行放在 GitHub Action。本地仅可
  `--catalog <fixture.json>` 用预抓取的目录映射做离线回归。

行为：
  · 只处理「状态 == 待核实」的行（老「已核实」/「降级」行不动，「已核实」做
    sanity check 报告）。
  · 存在 → 状态翻「已核实」，数据起始年份 = 窗口内最早观测年份（≤1998 / 精确值）。
  · 不存在 → 保持「待核实」，写入报告「未通过核验」清单，进程以非零退出（fail loud）。
  · 始终写回 category_mapping.csv（存在的已转正）+ docs/h1_series_verification.md 报告。
  单一信息源：category_mapping.csv 仍是被 fetch/analyze 只读的源头，本脚本只是其核验器。

用法：
  python h1_verify_series.py                  # 在线：BLS v2 API 核验（GitHub Action 用）
  python h1_verify_series.py --catalog cat.json   # 离线：读本地目录 fixture 核验/回归
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone

import requests

# --------------------------------------------------------------------------
# 常量
# --------------------------------------------------------------------------
BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
MAPPING_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "category_mapping.csv")
REPORT_MD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "h1_series_verification.md")

PREFIX = "CUUR0000"       # 全国 CPI-U 未季调（本项目的唯一口径）
STATUS_TODO = "待核实"
STATUS_DONE = "已核实"
STATUS_DOWNGRADE = "降级"

BATCH = 50                # BLS 注册 key 单次查询最多 50 series
WINDOW_START = 1998       # 世纪图表窗口起点（BLS CPI 1998 细项目录重组）
BLOCK_MAIN = ("1998", "2017")    # 主时间块：覆盖世纪窗口起点 + 绝大多数老系列
BLOCK_RECENT = ("2018", "2025")  # 副时间块：覆盖近年新增系列
TIMEOUT = 60

# category_mapping.csv 的列顺序（写回时固定，避免列序漂移）
COLS = ["中文品类名", "BLS_item_title", "series_id", "层级", "状态", "数据起始年份", "数据起始年份_口径", "备注", "H1分组"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def load_mapping(path: str) -> list:
    if not os.path.exists(path):
        raise FileNotFoundError(f"mapping 文件不存在：{path}")
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if (r.get("series_id") or "").strip():
                rows.append(r)
    return rows


def write_mapping(rows: list, path: str) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: (r.get(c) or "") for c in COLS})


def query_batch(series_ids: list, key: str, startyear: str, endyear: str) -> dict:
    """POST 一批 seriesid，返回 {series_id: {"title": str, "earliest": int|None}}。
    title 空 = 不存在（catalog 空）；earliest = 该窗口内最早观测年份。"""
    payload = {
        "seriesid": series_ids,
        "startyear": startyear,
        "endyear": endyear,
        "registrationkey": key,
        "catalog": True,
    }
    resp = requests.post(BLS_API, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS status={data.get('status')} message={data.get('message')}")
    out = {}
    for s in data.get("Results", {}).get("series", []):
        sid = s.get("seriesID", "")
        cat = s.get("catalog") or {}
        title = str(cat.get("series_title") or "").strip()
        earliest = None
        for d in s.get("data", []):
            try:
                y = int(d.get("year"))
            except (TypeError, ValueError):
                continue
            if earliest is None or y < earliest:
                earliest = y
        out[sid] = {"title": title, "earliest": earliest}
    return out


def build_catalog_online(series_ids: list, key: str) -> dict:
    """在线核验：两时间块分批查询，返回 {series_id: {"title", "earliest"}}（仅存在的 series）。"""
    result = {}
    # 主块
    for batch in chunks(series_ids, BATCH):
        got = query_batch(batch, key, *BLOCK_MAIN)
        for sid in batch:
            info = got.get(sid)
            if info and info["title"]:
                result[sid] = info
    # 副块：主块未命中的
    remaining = [sid for sid in series_ids if sid not in result]
    if remaining:
        for batch in chunks(remaining, BATCH):
            got = query_batch(batch, key, *BLOCK_RECENT)
            for sid in batch:
                info = got.get(sid)
                if info and info["title"]:
                    result[sid] = info
    return result


def load_catalog_fixture(path: str) -> dict:
    """离线回归：读本地目录 fixture（{series_id: {"title":..., "earliest":...}}）。"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError("目录 fixture 需为 JSON object")
    out = {}
    for k, v in data.items():
        v = v or {}
        out[k] = {
            "title": str(v.get("title") or v.get("series_title") or "").strip(),
            "earliest": v.get("earliest"),
        }
    return out


def begin_year_label(earliest) -> str:
    """把「窗口内最早观测年份」格式化为「数据起始年份」回填值。"""
    if earliest is None:
        return ""
    if earliest <= WINDOW_START:
        return f"≤{WINDOW_START}"
    return str(earliest)


def write_report(report: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    L = []
    L.append("# H1 品类 seriesID 核验报告\n")
    L.append(f"- 核验时间：{report['verified_at']}")
    L.append(f"- 数据源：BLS v2 API（`{BLS_API}`，`catalog=true`，口径 {PREFIX} 全国 CPI-U 未季调）")
    L.append(f"- 核验对象：category_mapping.csv 中「待核实」的 {report['todo_total']} 个 seriesID")
    L.append(f"- 结论：✅ 通过 {report['found_count']} 项 / ⚠️ 未通过 {report['not_found_count']} 项")
    L.append(f"- 说明：「数据起始年份」回填的是世纪窗口内最早观测年份（窗口起点 {WINDOW_START}，BLS CPI 1998 细项目录重组）；≤{WINDOW_START} 表示真实 begin_year ≤ {WINDOW_START}，BLS v2 API catalog 不提供真实 begin_year\n")

    L.append("## 一、未通过核验（需人工复核，seriesID 在 BLS 目录中不存在）\n")
    if report["not_found"]:
        L.append("| series_id | item_code | 中文品类名 | H1分组 | 备注 |")
        L.append("|---|---|---|---|---|")
        for it in report["not_found"]:
            L.append(f"| `{it['series_id']}` | `{it['item_code']}` | {it['zh']} | {it['group']} | {it['note']} |")
    else:
        L.append("（无）")
    L.append("")

    L.append("## 二、通过核验（已转正为「已核实」，并回填起始年份）\n")
    if report["found"]:
        L.append("| series_id | 中文品类名 | 官方 series_title | H1分组 | 起始年份 |")
        L.append("|---|---|---|---|---|")
        for it in report["found"]:
            L.append(f"| `{it['series_id']}` | {it['zh']} | {it['series_title']} | {it['group']} | {it['begin_year']} |")
    else:
        L.append("（无）")
    L.append("")

    L.append("## 三、老品类「已核实」sanity check（不动，仅复核存在性）\n")
    L.append("| series_id | 中文品类名 | 在 BLS 目录 | 窗口内最早年份 |")
    L.append("|---|---|---|---|")
    for it in report["old_check"]:
        mark = "✅" if it["in_catalog"] else "❌"
        L.append(f"| `{it['series_id']}` | {it['zh']} | {mark} | {it['earliest']} |")
    L.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="H1 品类 seriesID 存在性核验（BLS v2 API catalog）")
    ap.add_argument("--catalog", default=None, help="本地目录 fixture JSON 路径（离线回归用）；缺省在线 BLS v2 API")
    ap.add_argument("--mapping", default=MAPPING_CSV, help=f"category_mapping.csv 路径（缺省 {MAPPING_CSV}）")
    ap.add_argument("--report", default=REPORT_MD, help=f"核验报告输出路径（缺省 {REPORT_MD}）")
    args = ap.parse_args()
    mapping_csv = args.mapping
    report_md = args.report

    rows = load_mapping(mapping_csv)

    # 1) 收集需查询的 seriesID（待核实 + 已核实做 sanity check；降级不动）
    todo_ids, done_rows = [], []
    for r in rows:
        sid = (r.get("series_id") or "").strip()
        status = (r.get("状态") or "").strip()
        if status == STATUS_TODO:
            todo_ids.append(sid)
        elif status == STATUS_DONE:
            done_rows.append(r)
    query_ids = todo_ids + [r.get("series_id", "").strip() for r in done_rows]

    # 2) 取目录
    if args.catalog:
        catalog = load_catalog_fixture(args.catalog)
        source_note = args.catalog
    else:
        key = os.environ.get("BLS_API_KEY", "").strip()
        if not key:
            print("[h1_verify] ERROR: BLS_API_KEY env var not set.", file=sys.stderr)
            return 1
        try:
            catalog = build_catalog_online(query_ids, key)
        except Exception as exc:
            print(f"[h1_verify] ERROR: BLS API 核验失败：{type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        source_note = BLS_API
    print(f"[h1_verify] 目录载入：{len(catalog)} 条命中（{source_note}）", file=sys.stderr)

    # 3) 分类处理
    found, not_found, old_check = [], [], []
    todo_total = len(todo_ids)
    for r in rows:
        sid = (r.get("series_id") or "").strip()
        status = (r.get("状态") or "").strip()
        code = sid[len(PREFIX):] if sid.startswith(PREFIX) else sid
        if status == STATUS_TODO:
            info = catalog.get(sid)
            if info and info["title"]:
                label = begin_year_label(info["earliest"])
                r["状态"] = STATUS_DONE
                r["数据起始年份"] = label
                r["数据起始年份_口径"] = "窗口最早观测年份"
                found.append({
                    "series_id": sid,
                    "zh": (r.get("中文品类名") or "").strip(),
                    "series_title": info["title"],
                    "group": (r.get("H1分组") or "").strip(),
                    "begin_year": label,
                })
            else:
                not_found.append({
                    "series_id": sid,
                    "item_code": code,
                    "zh": (r.get("中文品类名") or "").strip(),
                    "group": (r.get("H1分组") or "").strip(),
                    "note": (r.get("备注") or "").strip(),
                })
        elif status == STATUS_DONE:
            info = catalog.get(sid)
            in_cat = bool(info and info["title"])
            label = begin_year_label(info["earliest"]) if info else ""
            # 回填：早期核验轮次（v2 脚本）翻「已核实」时未回填起始年份，
            # 这里对「已核实但起始年份为空」的项补上（仅空值，不覆盖已有值）。
            if in_cat and label and not (r.get("数据起始年份") or "").strip():
                r["数据起始年份"] = label
                r["数据起始年份_口径"] = "窗口最早观测年份"
            old_check.append({
                "series_id": sid,
                "zh": (r.get("中文品类名") or "").strip(),
                "in_catalog": in_cat,
                "earliest": label,
            })
        # 降级/其它状态：不动

    # 4) 写回 mapping + 报告
    write_mapping(rows, mapping_csv)
    report = {
        "verified_at": now_iso(),
        "todo_total": todo_total,
        "found_count": len(found),
        "not_found_count": len(not_found),
        "found": found,
        "not_found": not_found,
        "old_check": old_check,
    }
    write_report(report, report_md)

    print(f"[h1_verify] 待核实 {todo_total} → 通过 {len(found)} / 未通过 {len(not_found)}", file=sys.stderr)
    print(f"[h1_verify] 报告已写：{report_md}", file=sys.stderr)
    if not_found:
        print(f"[h1_verify] FAIL: 以下 seriesID 未通过核验（详见报告）：", file=sys.stderr)
        for it in not_found:
            print(f"    {it['series_id']}  {it['zh']}", file=sys.stderr)
        return 2  # fail loud：有未通过项
    return 0


if __name__ == "__main__":
    sys.exit(main())
