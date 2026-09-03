#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H1 世纪图表 CPI 逐月归档（h1_cpi_archive v1.0）
================================================

只归档，不计算，不进任何指数、不上任何网页。
本模块是独立旁路：不改 parity_index.py / build_site.py / daily.yml 的既有 job。

数据源（说明书 A 已核验，见 abundantics 仓 category_mapping.csv 与《BLS品类映射_核验说明》）：
  BLS CPI-U（未季调）月度序列，接口：
    POST https://api.bls.gov/publicAPI/v2/timeseries/data/
    body: {"seriesid": [...], "startyear": "...", "endyear": "...", "registrationkey": KEY}
  BLS 免费 key 单次请求有 20 年跨度限制（超 20 年只返回 startyear 起 20 年），
  故按 ≤20 年分块拉取后合并。

序列清单：
  从同目录 category_mapping.csv 读取（单一信息源，不在此硬编码第二份清单），
  且只取「状态 == 已核实」的行。说明书 A 将「大学教科书」降级为聚合层 CUUR0000SEEA
  （含文具、宽于大学教科书），并非确认映射，故按说明书 B 要求「没确认就先空着」，
  本脚本不抓取该降级序列、不硬填不确定的代码。

数据窗口：
  1998 至今（世纪图表窗口；12 个序列起始年份均早于 1998，见核验说明第四节）。
  value 为 "-"（如 2025-10 因政府拨款中断未发布）时原样保留，由后续 analyze 层处理。

归档内容：
  raw_h1_cpi/YYYY-MM-DD.json（纯 JSON，ensure_ascii=False，紧凑分隔符（无缩进）压缩体积；
  全样本扩展后 ~130 序列约 3.5MB/月，不需 gzip）。
  结构自描述：archive_date / fetched_at / source / fetch_status / 各序列 meta + 原始 BLS
  series 数据（按 year+period 去重、升序）。当日重复运行覆盖当日文件。

失败策略（核心数据，fail loud）：
  全部序列都拿到才写文件；任何请求失败 / 序列缺失则报错退出（非零），不写半成品，
  保留已有归档不动，让 workflow 变红提醒人工介入。

用法：
  BLS_API_KEY=xxx python h1_cpi_archive.py                # 归档今天
  BLS_API_KEY=xxx python h1_cpi_archive.py --date 2026-09-02   # 归档指定日期（补跑/重跑）
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone, date as date_cls

import requests

# --------------------------------------------------------------------------
# 常量
# --------------------------------------------------------------------------
BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
MAPPING_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "category_mapping.csv")
ARCHIVE_DIR = "raw_h1_cpi"
START_YEAR = 1998          # 世纪图表窗口起点（说明书 A）
CHUNK_YEARS = 20           # BLS 免费 key 单次请求最大跨度（时间维度）
BLS_BATCH = 50             # BLS v2 带 key 单请求序列数上限（序列维度，跨品类分批）
TIMEOUT = 60
UA = "h1-cpi-archive/1.0 (monthly archive; see github.com/tanghuidao/token-parity)"
# 大学教科书：说明书 A 降级为 SEEA，非确认映射 → 本脚本不抓（只归档 status == 已核实）
STATUS_CONFIRMED = "已核实"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_confirmed_series() -> list:
    """从 category_mapping.csv 读取「已核实」序列清单（排除降级的大学教科书）。"""
    if not os.path.exists(MAPPING_CSV):
        raise FileNotFoundError(f"mapping 文件不存在：{MAPPING_CSV}")
    rows = []
    with open(MAPPING_CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            sid = (r.get("series_id") or "").strip()
            status = (r.get("状态") or "").strip()
            if not sid:
                continue
            if status != STATUS_CONFIRMED:
                continue  # 只抓已核实的；降级/未确认的序列不硬填
            rows.append({
                "series_id": sid,
                "category_zh": (r.get("中文品类名") or "").strip(),
                "category_en": (r.get("BLS_item_title") or "").strip(),
                "level": (r.get("层级") or "").strip(),
                "status": status,
                "data_start_year": (r.get("数据起始年份") or "").strip(),
                "note": (r.get("备注") or "").strip(),
            })
    if not rows:
        raise RuntimeError("category_mapping.csv 中没有 status==已核实 的序列")
    return rows


def fetch_chunk(series_ids, key, start_year, end_year) -> list:
    """拉取一个时间块，返回 BLS 的 series 列表（原始结构）。"""
    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
        "registrationkey": key,
    }
    resp = requests.post(BLS_API, json=payload, timeout=TIMEOUT,
                         headers={"User-Agent": UA, "Accept": "application/json"})
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS status={data.get('status')} message={data.get('message')}")
    return data.get("Results", {}).get("series", [])


def fetch_and_merge(series_ids, key, start_year, end_year) -> list:
    """分块（时间 ≤20 年）并分批（序列 ≤50）拉取后合并，返回 {series_id: [原始 data points 升序去重]}。"""
    merged = {sid: {} for sid in series_ids}
    cur = start_year
    while cur <= end_year:
        chunk_end = min(cur + CHUNK_YEARS - 1, end_year)
        n_batches = (len(series_ids) - 1) // BLS_BATCH + 1
        for i in range(0, len(series_ids), BLS_BATCH):
            batch = series_ids[i:i + BLS_BATCH]
            print(f"[h1_cpi] fetching {cur}-{chunk_end} batch {i // BLS_BATCH + 1}/{n_batches}...",
                  file=sys.stderr)
            for r in fetch_chunk(batch, key, cur, chunk_end):
                sid = r.get("seriesID")
                if sid not in merged:
                    continue
                for d in r.get("data", []):
                    k = (d.get("year"), d.get("period"))
                    merged[sid][k] = d
        cur = chunk_end + 1
    return merged


def build_series(sid, points_map, meta) -> dict:
    """把合并后的 points 组装成自描述序列（原始 BLS 结构 + meta）。"""
    data = list(points_map.values())
    data.sort(key=lambda d: (d.get("year", ""), d.get("period", "")))
    return {
        "seriesID": sid,
        "category_zh": meta.get("category_zh", ""),
        "category_en": meta.get("category_en", ""),
        "level": meta.get("level", ""),
        "data_start_year": meta.get("data_start_year", ""),
        "note": meta.get("note", ""),
        "data": data,
    }


def write_archive(doc: dict, day: str) -> str:
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    path = os.path.join(ARCHIVE_DIR, f"{day}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="H1 世纪图表 CPI 逐月归档")
    ap.add_argument("--date", default=None, help="归档日期 YYYY-MM-DD（默认今天）")
    args = ap.parse_args()

    key = os.environ.get("BLS_API_KEY", "").strip()
    if not key:
        print("[h1_cpi] ERROR: BLS_API_KEY env var not set.", file=sys.stderr)
        return 1

    try:
        meta_rows = load_confirmed_series()
    except Exception as exc:
        print(f"[h1_cpi] ERROR: load mapping failed: {exc}", file=sys.stderr)
        return 1

    series_ids = [m["series_id"] for m in meta_rows]
    meta_by_id = {m["series_id"]: m for m in meta_rows}
    end_year = datetime.now().year
    day = args.date or date_cls.today().isoformat()

    try:
        merged = fetch_and_merge(series_ids, key, START_YEAR, end_year)
    except Exception as exc:
        print(f"[h1_cpi] ERROR: BLS request failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    missing = [sid for sid in series_ids if not merged.get(sid)]
    if missing:
        print(f"[h1_cpi] ERROR: BLS response missing series {missing}; "
              f"aborting to preserve existing archive.", file=sys.stderr)
        return 1

    doc = {
        "archive_date": day,
        "fetched_at": now_iso(),
        "source": "bls_cpi_u_not_seasonally_adjusted",
        "source_endpoint": BLS_API,
        "fetch_status": "ok",
        "start_year": START_YEAR,
        "end_year": end_year,
        "series_count": len(series_ids),
        "series_ids": series_ids,
        "note": ("只归档 status==已核实 的序列；大学教科书(college textbooks) 说明书A 已降级为 "
                 "聚合层 CUUR0000SEEA（非确认映射），按说明书B要求留空、未硬填。"),
        "series": [build_series(sid, merged[sid], meta_by_id[sid]) for sid in series_ids],
    }

    path = write_archive(doc, day)
    total_points = sum(len(s["data"]) for s in doc["series"])
    print(f"[h1_cpi] OK: archived {len(series_ids)} series ({total_points} points) to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
