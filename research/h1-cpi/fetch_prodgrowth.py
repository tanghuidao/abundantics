#!/usr/bin/env python3
"""
说明书 D 腿一：ProdGrowth_k —— 近20年劳动生产率年化增长率（混合口径版）
====================================================================

口径（用户 2026-09-03 拍板「混合口径」）：
    R 组（可自动化/制造业+信息业）→ BLS Industry Productivity（IP，详细行业，`IPU` 系列）
    N 组（难自动化/服务业）       → BLS Multifactor Productivity for Major Industries（MFP，主要行业，`MPU` 系列）
    原因：IP survey 对服务业（教育61/金融52/专业54/其他81/房地产53/运输48/娱乐71）无详细行业
          series，N 组在 IP 口径下 22 品类全缺失；MFP 主要行业覆盖上述全部服务业。

IP survey（R 组）series ID（已实测）：
    IPU + [sector 1位] + N + [NAICS 6位，左对齐右补下划线] + [measure 9位]
    例：IPUEN315___L000000000 = 制造业 NAICS 315 服装制造劳动生产率指数
    measure L000000000 = 劳动生产率指数（2017=100）；L001000000 = 逐年百分比变化（需累积）。

MFP major industries（N 组）series ID（已实测确认 8 个行业）：
    MPU + [sector 4位] + [measure 2位] + [duration 1位]
    sector 4位 = "00" + NAICS 2位（右对齐前补0）；48-49 运输仓储取 "0048"。
    measure：01=TFP，06=劳动生产率(LP)；duration：2=指数(2017=100)，3=同比(% change)。
    LP 指数数据窗口 2014-2024（11 年，MFP 主要行业 LP 指标 2021 年才新增，历史只到 2014）。
    例：MPU0062062 = 医疗 NAICS 62 劳动生产率指数；MPU0081063 = 其他服务 NAICS 81 劳动生产率同比。

年化增长率口径：
    g_k = (I_end / I_start) ^ (1 / (Y_end - Y_start)) - 1
    指数序列直接算；同比序列（LP 同比 / L001000000）先累积成指数（基年=首年 100）再算。
    窗口：IP 2006-2025；MFP 2014-2024。窗口如实记录，不强行统一。

运行环境：GitHub Actions runner（api.bls.gov 仅 runner 可达，本地沙盒 403）。
    免费 key 限制 500 请求/天、50 series/次、10 年/次。
    本脚本逐个 series POST（避免批量含无效 series 导致整批 REQUEST_FAILED）。
"""

import csv
import os
import sys

import requests

API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
API_KEY = os.environ.get("BLS_API_KEY", "")

START_YEAR = 2006          # IP 窗口起点（2006-2025 = 20 个完整年度）
END_YEAR = 2025            # 末年（2026 年数据尚未发布完整年度）
MAX_YEARS = 10             # BLS 单次请求最多 10 年

# ---- R 组：IP survey（详细行业） ----

# NAICS 前2位 -> sector 字母（已实测确认）
IP_SECTOR_MAP = {
    "31": "E", "32": "E", "33": "E",  # 制造业
    "51": "J",                          # 信息业
    "44": "H", "45": "H",              # 零售
    "54": "M",                          # 专业服务
    "72": "T",                          # 餐饮住宿
    "21": "Z",                          # 矿业
    "62": "R",                          # 医疗保健
}
IP_ALL_SECTORS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
# measure 优先级：指数优先，百分比变化兜底
IP_MEASURES = ["L000000000", "L001000000"]

# ---- N 组：MFP major industries（主要行业） ----

# NAICS 前2位 -> MFP sector code（4位，已实测确认）
MFP_SECTOR_MAP = {
    "48": "0048", "49": "0048",  # 运输仓储 48-49
    "52": "0052",                # 金融保险
    "53": "0053",                # 房地产与租赁
    "54": "0054",                # 专业/科学技术服务
    "61": "0061",                # 教育
    "62": "0062",                # 医疗与社会援助
    "71": "0071",                # 艺术/娱乐/休闲
    "81": "0081",                # 其他服务（除政府）
}
# MFP measure+duration 候选：LP指数(06+2) 优先，LP同比(06+3) 兜底（81 只有同比）
MFP_MEASURES = [("06", "2", "LP指数"), ("06", "3", "LP同比")]

CROSSWALK = "research/h1-cpi/naics_crosswalk.csv"
OUTPUT = "research/h1-cpi/prodgrowth.csv"


def read_crosswalk():
    """读 naics_crosswalk.csv，返回行列表。"""
    with open(CROSSWALK, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows


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
    period A01 = Annual。value 对指数系列是指数，对同比系列是百分比变化。"""
    obs = []
    for d in data:
        if d.get("period") != "A01":
            continue
        try:
            yr = int(d["year"])
            val = float(d["value"])
        except (KeyError, ValueError, TypeError):
            continue
        obs.append((yr, val))
    obs.sort()
    return obs


def accumulate_pct_to_index(obs):
    """把逐年百分比变化序列 [(year, pct_change), ...] 累积成指数（基年=首年 100）。
    用于 IP 的 L001000000 和 MFP 的 LP 同比（06+3）。"""
    if not obs:
        return []
    idx = []
    base = 100.0
    for i, (yr, val) in enumerate(obs):
        if i == 0:
            idx.append((yr, base))
        else:
            base = base * (1.0 + val / 100.0)
            idx.append((yr, base))
    return idx


def to_index_series(obs, is_percent_change):
    """统一成指数序列 [(year, index)]。is_percent_change=True 时先累积。"""
    if not obs:
        return []
    if is_percent_change:
        return accumulate_pct_to_index(obs)
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
    """分 10 年/段拉全 START_YEAR-END_YEAR，返回原始 data 列表。"""
    all_data = []
    s = START_YEAR
    while s <= END_YEAR:
        e = min(s + MAX_YEARS - 1, END_YEAR)
        all_data.extend(post_series(series_id, s, e))
        s = e + 1
    return all_data


# ---------------------------------------------------------------------------
# R 组：IP survey 探测
# ---------------------------------------------------------------------------

def build_ip_series_id(naics, sector, measure="L000000000"):
    naics6 = naics.ljust(6, "_")
    return f"IPU{sector}N{naics6}{measure}"


def probe_ip(naics):
    """探测 IP survey 的正确 sector+measure，返回 (series_id, 指数序列, 口径标签) 或 None。
    顺序：首选 sector 优先；每个 sector 先试指数 measure，再试百分比 measure。"""
    has_primary = naics[:2] in IP_SECTOR_MAP
    sectors = []
    if has_primary:
        sectors.append(IP_SECTOR_MAP[naics[:2]])
    for s in IP_ALL_SECTORS:
        if s not in sectors:
            sectors.append(s)

    measures = IP_MEASURES if has_primary else ["L000000000"]

    for s in sectors:
        for measure in measures:
            sid = build_ip_series_id(naics, s, measure)
            data = fetch_full(sid)
            if not data:
                continue
            obs = annual_observations(data)
            idx = to_index_series(obs, is_percent_change=(measure == "L001000000"))
            if idx and len(idx) >= 2:
                label = "IP(详细行业·LP指数)" if measure == "L000000000" else "IP(详细行业·LP同比→累积)"
                return sid, idx, label
    return None, None, None


# ---------------------------------------------------------------------------
# N 组：MFP major industries 探测
# ---------------------------------------------------------------------------

def probe_mfp(naics):
    """探测 MFP major industries 的 LP series，返回 (series_id, 指数序列, 口径标签) 或 None。
    顺序：LP 指数(06+2) 优先，LP 同比(06+3) 兜底（其他服务 81 只有同比）。"""
    sector = MFP_SECTOR_MAP.get(naics[:2])
    if not sector:
        return None, None, None

    for measure, duration, tag in MFP_MEASURES:
        sid = f"MPU{sector}{measure}{duration}"
        data = fetch_full(sid)
        if not data:
            continue
        obs = annual_observations(data)
        idx = to_index_series(obs, is_percent_change=(duration == "3"))
        if idx and len(idx) >= 2:
            label = "MFP(主要行业·LP指数)" if duration == "2" else "MFP(主要行业·LP同比→累积)"
            return sid, idx, label
    return None, None, None


def main():
    rows = read_crosswalk()
    codes = sorted({r["NAICS代码"].strip() for r in rows if r["NAICS代码"].strip()})
    print(f"[腿一] naics_crosswalk 去重 NAICS 数: {len(codes)}", flush=True)

    found = {}     # naics -> (series_id, index_series, 口径标签)
    missing = {}   # naics -> 备注

    for code in codes:
        group = next((r["H1分组"] for r in rows if r["NAICS代码"].strip() == code), "")
        if group == "R":
            sid, idx, label = probe_ip(code)
            if sid:
                found[code] = (sid, idx, label)
                g = annualized_growth(idx)
                print(f"  命中(R/IP) {code:>6} -> {sid}  ({len(idx)} 个年度观测, {g['annualized_growth_pct'] if g else 'NA'}%)", flush=True)
            else:
                missing[code] = "BLS IP 无该 NAICS 行业的劳动生产率数据（制造业细分层级未发布/服务业无 IP 覆盖）"
                print(f"  缺失(R/IP) {code:>6}", flush=True)
        else:
            sid, idx, label = probe_mfp(code)
            if sid:
                found[code] = (sid, idx, label)
                g = annualized_growth(idx)
                print(f"  命中(N/MFP) {code:>6} -> {sid}  ({len(idx)} 个年度观测, {g['annualized_growth_pct'] if g else 'NA'}%)", flush=True)
            else:
                missing[code] = "BLS MFP 主要行业无该 NAICS 的劳动生产率数据"
                print(f"  缺失(N/MFP) {code:>6}", flush=True)

    n_hit = len(found)
    print(f"[腿一] 探测完成：命中 {n_hit} 个，无数据 {len(missing)} 个", flush=True)

    # ---- 写 prodgrowth.csv ----
    fieldnames = [
        "series_id", "中文品类名", "H1分组", "NAICS代码", "NAICS行业名",
        "BLS系列ID", "口径来源", "数据起始年", "起始指数", "数据末年", "末年指数",
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
                "口径来源": "",
                "数据起始年": "", "起始指数": "", "数据末年": "", "末年指数": "",
                "年化增长率_pct": "", "数据可用性": "",
                "备注": "",
            }
            if hit:
                sid, idx, label = hit
                g = annualized_growth(idx)
                row["BLS系列ID"] = sid
                row["口径来源"] = label
                if g:
                    row.update({
                        "数据起始年": g["start_year"],
                        "起始指数": g["start_value"],
                        "数据末年": g["end_year"],
                        "末年指数": g["end_value"],
                        "年化增长率_pct": g["annualized_growth_pct"],
                        "数据可用性": "有",
                    })
                    note = r.get("备注", "")
                    if "同比→累积" in label:
                        note = (note + "；" if note else "") + "同比序列累积成指数，基年=首年100，仅年化增长率可跨口径比较，指数水平不可比"
                    if label.startswith("MFP"):
                        note = (note + "；" if note else "") + "MFP 主要行业 LP 数据窗口 2014-2024"
                    row["备注"] = note
                    n_have += 1
                else:
                    row["数据可用性"] = "观测不足"
                    row["备注"] = "观测不足两年，无法计算年化增长率"
            else:
                row["数据可用性"] = "无 BLS 数据"
                row["备注"] = missing.get(code, r.get("备注", ""))
            w.writerow(row)

    print(f"[腿一] prodgrowth.csv 已写：共 {len(rows)} 行，其中可算年化增长率 {n_have} 行", flush=True)


if __name__ == "__main__":
    if not API_KEY:
        print("错误：未设置 BLS_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)
    main()
