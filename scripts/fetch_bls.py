#!/usr/bin/env python3
"""
fetch_bls.py

拉取世纪图表（H1）的 12 个 BLS CPI-U（未季调）序列月度数据，
写入 public/api/bls/series.json（主数据，前端渲染用）与 series_long.csv（长表，分析用）。

设计约定：
- 序列清单从 category_mapping.csv 读取（单一信息源，不在此硬编码第二份清单）。
- 数据窗口 1998 至今（世纪图表窗口；12 序列起始年份均早于 1998，见核验说明）。
- BLS_API_KEY 从环境变量读取（GitHub Actions Secret）。
- BLS 免费 key 单次请求有 20 年跨度限制，故按 ≤20 年分块拉取后合并（否则只返回
  startyear 起的 20 年，最新年份会被截断）。
- 原子写入：全部序列都拿到才写文件；任何序列缺失/请求失败则报错退出（非零），
  保留已有数据不动，让 workflow 变红（主数据不做静默降级）。
- BLS CPI 月度发布 + 历史会 revision，故每日全量重拉（数据量小，自愈安全）。
- value 为 "-"（如 2025-10 因政府拨款中断未发布）时记为 null。

用法：BLS_API_KEY=xxx python scripts/fetch_bls.py
"""

import csv
import json
import os
import sys
from datetime import datetime

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPING_CSV = os.path.join(ROOT, "category_mapping.csv")
OUTPUT_DIR = os.path.join(ROOT, "public", "api", "bls")
BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
START_YEAR = 1998
CHUNK_YEARS = 20  # BLS 免费 key 单次请求最大跨度


def load_mapping():
    """从 category_mapping.csv 读取序列清单。"""
    rows = []
    with open(MAPPING_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            sid = (r.get("series_id") or "").strip()
            if not sid:
                continue
            rows.append({
                "series_id": sid,
                "category_zh": (r.get("中文品类名") or "").strip(),
                "category_en": (r.get("BLS_item_title") or "").strip(),
                "level": (r.get("层级") or "").strip(),
                "status": (r.get("状态") or "").strip(),
                "data_start_year": (r.get("数据起始年份") or "").strip(),
                "note": (r.get("备注") or "").strip(),
            })
    return rows


def fetch_chunk(series_ids, key, start_year, end_year):
    """拉取一个时间块，返回 BLS series 列表。"""
    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
        "registrationkey": key,
    }
    resp = requests.post(BLS_API, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS status={data.get('status')} message={data.get('message')}")
    return data.get("Results", {}).get("series", [])


def fetch_all(series_ids, key, start_year, end_year):
    """分块拉取并合并，返回 {series_id: {date_key: data_point}}。"""
    merged = {sid: {} for sid in series_ids}
    cur = start_year
    while cur <= end_year:
        chunk_end = min(cur + CHUNK_YEARS - 1, end_year)
        print(f"[fetch_bls] fetching {cur}-{chunk_end}...", file=sys.stderr)
        for r in fetch_chunk(series_ids, key, cur, chunk_end):
            sid = r["seriesID"]
            if sid not in merged:
                continue
            for d in r.get("data", []):
                merged[sid][f"{d.get('year')}-{d.get('period')}"] = d
        cur = chunk_end + 1
    return merged


def parse_point(d):
    """把单个 data point 解析为结构化对象。"""
    raw = d.get("value")
    try:
        value = float(raw) if raw not in (None, "", "-") else None
    except (TypeError, ValueError):
        value = None
    period = d.get("period", "")
    month = period.lstrip("M") if period else ""
    date = f"{d.get('year', '')}-{month}" if d.get("year") and month else ""
    footnotes = "".join(fn.get("code", "") for fn in (d.get("footnotes") or []))
    return {
        "date": date,
        "value": value,
        "period": period,
        "periodName": d.get("periodName", ""),
        "footnotes": footnotes,
    }


def build_series(sid, points, meta):
    """把合并后的 points 组装成序列结构（升序）。"""
    data = [parse_point(p) for p in points.values()]
    data.sort(key=lambda x: x["date"])
    return {
        "series_id": sid,
        "category_zh": meta.get("category_zh", ""),
        "category_en": meta.get("category_en", ""),
        "level": meta.get("level", ""),
        "status": meta.get("status", ""),
        "data_start_year": meta.get("data_start_year", ""),
        "note": meta.get("note", ""),
        "data": data,
    }


def main():
    key = os.environ.get("BLS_API_KEY", "").strip()
    if not key:
        print("[fetch_bls] ERROR: BLS_API_KEY env var not set.", file=sys.stderr)
        return 1

    meta = load_mapping()
    if not meta:
        print("[fetch_bls] ERROR: no series found in category_mapping.csv.", file=sys.stderr)
        return 1
    series_ids = [m["series_id"] for m in meta]
    meta_by_id = {m["series_id"]: m for m in meta}
    end_year = datetime.now().year

    try:
        merged = fetch_all(series_ids, key, START_YEAR, end_year)
    except Exception as e:
        print(f"[fetch_bls] ERROR: BLS request failed: {e}", file=sys.stderr)
        return 1

    missing = [sid for sid in series_ids if not merged.get(sid)]
    if missing:
        print(
            f"[fetch_bls] ERROR: BLS response missing series {missing}; "
            f"aborting to preserve existing data.",
            file=sys.stderr,
        )
        return 1

    series_out = [build_series(sid, merged[sid], meta_by_id.get(sid, {})) for sid in series_ids]

    output = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "U.S. Bureau of Labor Statistics, CPI-U (not seasonally adjusted)",
        "startyear": START_YEAR,
        "series": series_out,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "series.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with open(os.path.join(OUTPUT_DIR, "series_long.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "series_id", "category_zh", "category_en", "value", "period", "footnotes"])
        for s in series_out:
            for d in s["data"]:
                w.writerow([
                    d["date"],
                    s["series_id"],
                    s["category_zh"],
                    s["category_en"],
                    "" if d["value"] is None else d["value"],
                    d["period"],
                    d["footnotes"],
                ])

    total_points = sum(len(s["data"]) for s in series_out)
    print(f"[fetch_bls] OK: wrote {len(series_out)} series ({total_points} points) to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
