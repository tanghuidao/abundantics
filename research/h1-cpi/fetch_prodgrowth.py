#!/usr/bin/env python3
"""
说明书 D 腿一：ProdGrowth_k —— 近20年劳动生产率年化增长率
========================================================

数据源：BLS v2 API，IP survey（Industry Productivity）。
measure：
    L000000000 = Labor productivity (output per hour) 指数（index）
    L001000000 = Labor productivity 逐年百分比变化（percent change）
    制造业/零售/信息业通常有 L000000000 指数；医疗等部分服务业只有 L001000000。

series ID 格式（已实测确认）：
    IPU + [sector 1位] + N + [NAICS 6位，左对齐右补下划线] + [measure 9位]
    例：IPUEN315___L000000000 = 制造业 NAICS 315 服装制造的劳动生产率指数
         IPURN622AL001000000 = 医院（NAICS 622A）劳动生产率百分比变化

sector 字母映射（已实测确认的部分）：
    E = 制造业 Manufacturing (NAICS 31-33)
    J = 信息业 Information (NAICS 51)
    H = 零售 Retail trade (NAICS 44-45)
    T = 餐饮住宿 Accommodation & food (NAICS 72)
    M = 专业服务 Professional services (NAICS 54)
    Z = 矿业 Mining (NAICS 21)
    R = 医疗保健 Health care (NAICS 62)
    其余服务业字母（运输/金融/房地产/娱乐/其他服务等）由脚本自动遍历探测。

年化增长率口径：
    g_k = (I_end / I_start) ^ (1 / (Y_end - Y_start)) - 1
    若仅拿到百分比变化系列（L001000000），则先累积成指数再算年化。
    窗口：2006-2025（"近20年"完整年度；BLS 单次请求最多 10 年，故分 2 段拉取）。
    若首年无数据则用最早可用年，窗口如实记录，不强行统一。

运行环境：GitHub Actions runner（api.bls.gov 仅 runner 可达，本地沙盒 403）。
    免费 key 限制 500 请求/天、50 series/次、10 年/次。
    本脚本逐个 series POST（避免批量含无效 series 导致整批 REQUEST_FAILED）。
"""

import csv
import os
import sys
from datetime import datetime

import requests

API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
API_KEY = os.environ.get("BLS_API_KEY", "")

START_YEAR = 2006          # "近20年" 窗口起点（2006-2025 = 20 个完整年度）
END_YEAR = 2025            # 末年（2026 年数据尚未发布完整年度）
MAX_YEARS = 10             # BLS 单次请求最多 10 年

# NAICS 前2位 -> sector 字母（已实测确认）
SECTOR_MAP = {
    "31": "E", "32": "E", "33": "E",  # 制造业
    "51": "J",                          # 信息业
    "44": "H", "45": "H",              # 零售
    "54": "M",                          # 专业服务
    "72": "T",                          # 餐饮住宿
    "21": "Z",                          # 矿业
    "62": "R",                          # 医疗保健
}

ALL_SECTORS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# measure 优先级：指数优先，百分比变化兜底
MEASURES = ["L000000000", "L001000000"]

CROSSWALK = "research/h1-cpi/naics_crosswalk.csv"
OUTPUT = "research/h1-cpi/prodgrowth.csv"


def build_series_id(naics, sector, measure="L000000000"):
    """构造 BLS IP series ID：IPU + sector + N + NAICS(左对齐右补_) + measure"""
    naics6 = naics.ljust(6, "_")
    return f"IPU{sector}N{naics6}{measure}"


def read_crosswalk():
    """读 naics_crosswalk.csv，返回 (行列表, 去重NAICS->首行映射)"""
    with open(CROSSWALK, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    naics_map = {}
    for r in rows:
        code = r["NAICS代码"].strip()
        if code and code not in naics_map:
            naics_map[code] = r
    return rows, naics_map


def post_series(series_id, start_year, end_year):
    """单个 series POST，返回 data 列表（可能为空 = 无观测/系列不存在）。
    健壮处理 BLS 的各种返回结构（REQUEST_FAILED / Results=null / data=[]）。"""
    payload = {
        "seriesid": [series_id],
        "startyear": str(start_year),
        "endyear": str(end_year),
        "registrationkey": API_KEY,
    }
    try:
        resp = requests.post(API_URL, json=payload, timeout=180)
        resp.raise_for_status()
        body = resp.json()
        results = body.get("Results") or {}
        for series in (results.get("series") or []):
            if series.get("seriesID") == series_id:
                return series.get("data") or []
    except Exception as e:
        print(f"    [warn] {series_id} POST 失败: {e}", flush=True)
    return []


def annual_observations(data):
    """从 BLS data 列表提取年度观测：[(year:int, value:float), ...] 升序。
    value 对 L000000000 是指数；对 L001000000 是逐年百分比变化。"""
    obs = []
    for d in data:
        if d.get("period") != "A01":  # 只取年度值（A01 = Annual）
            continue
        try:
            yr = int(d["year"])
            val = float(d["value"])
        except (KeyError, ValueError, TypeError):
            continue
        obs.append((yr, val))
    obs.sort()
    return obs


def to_index_series(obs, measure):
    """把观测统一成指数序列 [(year, index)]。
    若 measure 是 L001000000（百分比变化），则从基年 100 起累积成指数。"""
    if not obs:
        return []
    if measure == "L001000000":
        idx = []
        base = 100.0
        for i, (yr, val) in enumerate(obs):
            if i == 0:
                idx.append((yr, base))
            else:
                base = base * (1.0 + val / 100.0)
                idx.append((yr, base))
        return idx
    # L000000000 指数，直接用（滤掉非正）
    return [(yr, val) for (yr, val) in obs if val > 0]


def annualized_growth(index_series):
    """从指数序列算年化增长率 g = (I_end/I_start)^(1/(Y_end-Y_start)) - 1。
    返回 dict 或 None（观测不足两年）。"""
    if len(index_series) < 2:
        return None
    y0, v0 = index_series[0]
    y1, v1 = index_series[-1]
    if v0 <= 0 or y1 <= y0:
        return None
    g = (v1 / v0) ** (1.0 / (y1 - y0)) - 1.0
    return {
        "start_year": y0,
        "start_value": round(v0, 3),
        "end_year": y1,
        "end_value": round(v1, 3),
        "annualized_growth_pct": round(g * 100, 3),
    }


def fetch_full(series_id):
    """分 2 段拉全 2006-2025，合并成年度观测列表。"""
    all_data = []
    s = START_YEAR
    while s <= END_YEAR:
        e = min(s + MAX_YEARS - 1, END_YEAR)
        all_data.extend(post_series(series_id, s, e))
        s = e + 1
    return all_data


def probe_naics(code):
    """探测 NAICS 的正确 sector+measure，返回 (series_id, 指数序列) 或 (None, None)。
    顺序：首选 sector 优先；每个 sector 先试指数 measure，再试百分比 measure。
    遍历探测（无首选 sector）只试指数 measure，控制 500 次/天请求限额。"""
    has_primary = code[:2] in SECTOR_MAP
    sectors = []
    if has_primary:
        sectors.append(SECTOR_MAP[code[:2]])
    for s in ALL_SECTORS:
        if s not in sectors:
            sectors.append(s)

    measures = MEASURES if has_primary else ["L000000000"]

    for s in sectors:
        for measure in measures:
            sid = build_series_id(code, s, measure)
            # 第一段（最新 10 年）探测
            seg1_start = END_YEAR - MAX_YEARS + 1
            data1 = post_series(sid, seg1_start, END_YEAR)
            if not data1:
                continue
            # 命中：补第二段（更早 10 年）
            data2 = post_series(sid, START_YEAR, END_YEAR - MAX_YEARS)
            obs = annual_observations(data1 + data2)
            idx = to_index_series(obs, measure)
            if idx and len(idx) >= 2:
                return sid, idx
    return None, None


def main():
    rows, naics_map = read_crosswalk()
    codes = sorted(naics_map.keys())
    print(f"[腿一] naics_crosswalk 去重 NAICS 数: {len(codes)}", flush=True)
    primary = [c for c in codes if c[:2] in SECTOR_MAP]
    probe = [c for c in codes if c[:2] not in SECTOR_MAP]
    print(f"[腿一] 首选 sector 命中 {len(primary)} 个，需遍历探测 {len(probe)} 个", flush=True)

    found = {}   # naics -> (series_id, index_series)
    missing = {}  # naics -> 备注
    for code in codes:
        sid, idx = probe_naics(code)
        if sid:
            found[code] = (sid, idx)
            g = annualized_growth(idx)
            print(f"  命中 {code:>6} -> {sid}  ({len(idx)} 个年度观测)", flush=True)
        else:
            missing[code] = "BLS IP 无该 NAICS 行业的劳动生产率数据（服务业选择性覆盖/教育无数据）"
            print(f"  缺失 {code:>6}", flush=True)

    print(f"[腿一] 探测完成：命中 {len(found)} 个，无数据 {len(missing)} 个", flush=True)

    # ---- 写 prodgrowth.csv ----
    fieldnames = [
        "series_id", "中文品类名", "H1分组", "NAICS代码", "NAICS行业名",
        "BLS系列ID", "数据起始年", "起始指数", "数据末年", "末年指数",
        "年化增长率_pct", "数据可用性", "备注",
    ]
    n_have = 0
    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            code = r["NAICS代码"].strip()
            hit = found.get(code)
            row = {
                "series_id": r["series_id"],
                "中文品类名": r["中文品类名"],
                "H1分组": r["H1分组"],
                "NAICS代码": code,
                "NAICS行业名": r["NAICS行业名"],
                "BLS系列ID": "",
                "数据起始年": "", "起始指数": "", "数据末年": "", "末年指数": "",
                "年化增长率_pct": "", "数据可用性": "",
                "备注": "",
            }
            if hit:
                sid, idx = hit
                g = annualized_growth(idx)
                row["BLS系列ID"] = sid
                if g:
                    row.update({
                        "数据起始年": g["start_year"],
                        "起始指数": g["start_value"],
                        "数据末年": g["end_year"],
                        "末年指数": g["end_value"],
                        "年化增长率_pct": g["annualized_growth_pct"],
                        "数据可用性": "有",
                        "备注": r.get("备注", ""),
                    })
                    n_have += 1
                else:
                    row["数据可用性"] = "观测不足"
                    row["备注"] = "观测不足两年，无法计算年化增长率"
            else:
                row["数据可用性"] = "无 BLS IP 数据"
                row["备注"] = missing.get(code, r.get("备注", ""))
            w.writerow(row)

    print(f"[腿一] prodgrowth.csv 已写：共 {len(rows)} 行，其中可算年化增长率 {n_have} 行", flush=True)


if __name__ == "__main__":
    if not API_KEY:
        print("错误：未设置 BLS_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)
    main()
