#!/usr/bin/env python3
"""
说明书 D 腿一：ProdGrowth_k —— 近20年劳动生产率年化增长率
========================================================

数据源：BLS v2 API，IP survey（Industry Productivity）。
measure：L000000000 = Labor productivity (output per hour) 指数，2017=100。

series ID 格式（已实测确认）：
    IPU + [sector 1位] + N + [NAICS 6位，左对齐右补下划线] + [measure 9位]
    例：IPUEN315___L000000000 = 制造业 NAICS 315 服装制造的劳动生产率指数（2025=114.982）

sector 字母映射（从 popular 端点实测 + 单 series 验证）：
    E = 制造业 Manufacturing (NAICS 31-33)      —— 实测 IPUEN332322 / IPUEN315___ 均有效
    J = 信息业 Information (NAICS 51)           —— 实测 IPUJN517311 有效
    H = 零售 Retail trade (NAICS 44-45)         —— 实测 IPUHN452210 有效
    T = 餐饮住宿 Accommodation & food (NAICS 72) —— 实测 IPUTN722511 有效
    M = 专业服务 Professional services (NAICS 54) —— 实测 IPUMN541921 有效
    Z = 矿业 Mining (NAICS 21)                   —— 实测 IPUZN______ 有效（通配大类）

覆盖范围（BLS 官方）：劳动生产率覆盖 all manufacturing + all retail trade +
    selected mining / transportation / communications / services。
    → R 组（制造业/信息业）覆盖好；N 组（服务业）为"选择性覆盖"，多数行业可能无数据。
    这本身就是鲍莫尔成本病的测量难点：服务业生产率要么停滞、要么未发布。

年化增长率口径：
    g_k = (I_end / I_start) ^ (1 / (Y_end - Y_start)) - 1
    窗口：首年默认 2005（"近20年"），末年 = 该系列自身最新可用年。
    若首年无数据则用最早可用年，窗口如实记录，不强行统一（避免歪曲）。

运行环境：GitHub Actions runner（api.bls.gov 仅 runner 可达，本地沙盒 403）。
    免费 key 限制 500 请求/天、50 series/次、20 年/次。
"""

import csv
import json
import os
import sys
from datetime import datetime

import requests

API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
API_KEY = os.environ.get("BLS_API_KEY", "")

MEASURE = "L000000000"  # Labor productivity (output per hour) index, 2017=100
START_YEAR = 2005       # "近20年" 窗口起点
END_YEAR = datetime.now().year  # 末年（BLS 各系列最新年份不同，脚本取各自最新）

# NAICS 前2位 -> sector 字母（已实测确认的映射）
SECTOR_MAP = {
    "31": "E", "32": "E", "33": "E",  # 制造业
    "51": "J",                          # 信息业
    "44": "H", "45": "H",              # 零售
    "72": "T",                          # 餐饮住宿
    "54": "M",                          # 专业服务
    "21": "Z",                          # 矿业
}

# 探测兜底用的全部候选 sector 字母
ALL_SECTORS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

CROSSWALK = "research/h1-cpi/naics_crosswalk.csv"
OUTPUT = "research/h1-cpi/prodgrowth.csv"


def build_series_id(naics, sector):
    """构造 BLS IP series ID：IPU + sector + N + NAICS(左对齐右补_) + measure"""
    naics6 = naics.ljust(6, "_")
    return f"IPU{sector}N{naics6}{MEASURE}"


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


def bls_post(series_ids):
    """批量 POST BLS API（catalog=true），返回 (series_id -> dict) 映射。
    每个 dict 含 data 列表（年度观测）与 catalog（若有）。"""
    if not series_ids:
        return {}
    payload = {
        "seriesid": series_ids,
        "startyear": str(START_YEAR),
        "endyear": str(END_YEAR),
        "catalog": True,
        "registrationkey": API_KEY,
    }
    resp = requests.post(API_URL, json=payload, timeout=180)
    resp.raise_for_status()
    body = resp.json()
    out = {}
    for series in body.get("Results", {}).get("series", []):
        sid = series.get("seriesID")
        if sid:
            out[sid] = series
    return out


def annual_observations(series):
    """从 BLS series 返回里提取年度观测：[(year:int, value:float), ...] 升序"""
    obs = []
    for d in series.get("data", []):
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


def annualized_growth(obs):
    """从年度观测算年化增长率 g = (I_end/I_start)^(1/(Y_end-Y_start)) - 1。
    返回 dict 或 None（观测不足两年）。"""
    if len(obs) < 2:
        return None
    y0, v0 = obs[0]
    y1, v1 = obs[-1]
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


def main():
    rows, naics_map = read_crosswalk()
    codes = sorted(naics_map.keys())
    print(f"[腿一] naics_crosswalk 去重 NAICS 数: {len(codes)}", flush=True)

    # ---- 阶段1：探测每个 NAICS 的正确 sector + series ID ----
    # 首选 sector（SECTOR_MAP 命中）优先；未命中者遍历全部候选。
    primary = {}      # naics -> series_id（首选）
    need_probe = []   # naics 列表（需遍历候选 sector）
    for code in codes:
        sector = SECTOR_MAP.get(code[:2])
        if sector:
            primary[code] = build_series_id(code, sector)
        else:
            need_probe.append(code)

    print(f"[腿一] 首选 sector 命中 {len(primary)} 个，需探测 {len(need_probe)} 个", flush=True)

    # 批量探测首选 series
    found = {}   # naics -> series_id（已确认存在）
    missing = {}  # naics -> 备注（无数据）
    if primary:
        sid_to_naics = {sid: code for code, sid in primary.items()}
        res = bls_post(list(primary.values()))
        for sid, series in res.items():
            code = sid_to_naics.get(sid)
            if not code:
                continue
            obs = annual_observations(series)
            if obs:
                found[code] = sid
            else:
                need_probe.append(code)  # 首选 sector 无数据，转探测
        for code, sid in primary.items():
            if sid not in res:
                need_probe.append(code)  # 系列不存在

    # 遍历候选 sector 探测未命中 NAICS（批量，每批 50 series）
    for code in need_probe:
        if code in found:
            continue
        hit = None
        candidates = []
        for s in ALL_SECTORS:
            candidates.append(build_series_id(code, s))
        # 分批查询（50/批）
        for i in range(0, len(candidates), 50):
            batch = candidates[i:i + 50]
            res = bls_post(batch)
            for sid, series in res.items():
                obs = annual_observations(series)
                if obs:
                    # 取该 NAICS 命中（series ID 内嵌 NAICS，天然精确）
                    hit = sid
                    break
            if hit:
                break
        if hit:
            found[code] = hit
        else:
            missing[code] = "BLS IP 无该 NAICS 行业的劳动生产率数据（服务业选择性覆盖）"

    print(f"[腿一] 探测完成：命中 {len(found)} 个，无数据 {len(missing)} 个", flush=True)
    for code, sid in sorted(found.items()):
        print(f"  命中 {code:>6} -> {sid}", flush=True)
    for code in sorted(missing):
        print(f"  缺失 {code:>6}", flush=True)

    # ---- 阶段2：拉取命中系列的完整数据，算年化增长率 ----
    # 命中系列可能超过 50，分批；其实探测时已返回数据，但窗口可能被 startyear 截断。
    # 这里重新精确拉一次（确保窗口完整），并缓存到 sid -> obs。
    sid_obs = {}
    all_sids = sorted(set(found.values()))
    for i in range(0, len(all_sids), 50):
        batch = all_sids[i:i + 50]
        res = bls_post(batch)
        for sid, series in res.items():
            obs = annual_observations(series)
            if obs:
                sid_obs[sid] = obs

    # ---- 阶段3：写 prodgrowth.csv ----
    fieldnames = [
        "series_id", "中文品类名", "H1分组", "NAICS代码", "NAICS行业名",
        "BLS系列ID", "数据起始年", "起始指数", "数据末年", "末年指数",
        "年化增长率_pct", "数据可用性", "备注",
    ]
    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            code = r["NAICS代码"].strip()
            sid = found.get(code)
            row = {
                "series_id": r["series_id"],
                "中文品类名": r["中文品类名"],
                "H1分组": r["H1分组"],
                "NAICS代码": code,
                "NAICS行业名": r["NAICS行业名"],
                "BLS系列ID": sid or "",
                "数据起始年": "", "起始指数": "", "数据末年": "", "末年指数": "",
                "年化增长率_pct": "", "数据可用性": "",
                "备注": "",
            }
            if sid and sid in sid_obs:
                g = annualized_growth(sid_obs[sid])
                if g:
                    row.update({
                        "BLS系列ID": sid,
                        "数据起始年": g["start_year"],
                        "起始指数": g["start_value"],
                        "数据末年": g["end_year"],
                        "末年指数": g["end_value"],
                        "年化增长率_pct": g["annualized_growth_pct"],
                        "数据可用性": "有",
                        "备注": r.get("备注", ""),
                    })
                else:
                    row["数据可用性"] = "观测不足"
                    row["备注"] = "观测不足两年，无法计算年化增长率"
            elif sid:
                row["数据可用性"] = "有但窗口无年度观测"
            else:
                row["数据可用性"] = "无 BLS IP 数据"
                row["备注"] = missing.get(code, r.get("备注", ""))
            w.writerow(row)

    n_have = sum(1 for r in rows if (found.get(r["NAICS代码"].strip()) in sid_obs))
    print(f"[腿一] prodgrowth.csv 已写：共 {len(rows)} 行，其中可算年化增长率 {n_have} 行", flush=True)


if __name__ == "__main__":
    if not API_KEY:
        print("错误：未设置 BLS_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)
    main()
