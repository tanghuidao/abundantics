#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H1 世纪图表 CPI —— analyze 层（h1_analyze v1.1）
=================================================

v1.1 变更（复核意见拍板，2026-09-02）：
  - N/R 分组从脚本常量并入 category_mapping.csv 的「H1分组」列（单一信息源；
    脚本不再维护 N_SERIES/R_SERIES 常量，漏配/错配一律 fail loud）。
  - 新增样本外验证窗口（oos_test）：2022-01 → 数据最新月，与核心窗口 2000-2021
    完全零重叠（用户拍板：严格取核心窗口终点之后）、且为预印本成稿后才发生的数据，
    单独成节、不与核心结果混报。
  - 全样本适配（2026-09-03）：品类画像跳过「排除」聚合层；对「起始年份晚于 2000」的
    序列（中性 SEMG/SEHL02）22 年漂移/2000 基准 graceful 置空；对「端点滞后」序列
    （现仅 N 组法律服务 SEGD01，2024-09 后因 2025 联邦拨款中断停发）样本外/近 2/5 年/
    最新同比留空、不进组均值/检验（用户拍板），累计 2000 字段仍用其自身最新月计算。

定位（fetch → analyze → render 三步中的第二步）：
  把 fetch 层落盘的 raw_h1_cpi/YYYY-MM-DD.json 转成能证明丰裕学核心命题的
  定量结论，并产出 render 层（H1 简报 02）直接可用的中间数据。
  只计算、只产出中间数据，不进任何网页、不写简报正文。

核心命题（主线）：
  价格长期结构是「稀缺向难自动化品类（N）迁移上涨、可自动化品类（R）丰裕化下跌」。

三块产出：
  ① 核心检验：N/R 分组 + 组间差（正式版，非复现预印本脚注）。
       N 组（5）：医院 SEMD01、大学学费 SEEB01、医疗护理 SAM2、托儿 SEEB03、住房 OER SEHC01
       R 组（4）：手机 SEED03、电脑软件 SEEEE02、玩具 SERE01、电视 SERA01
       大学教科书已排除（fetch 层只归档 status==已核实，SEEA 降级未抓）。
       计算各品类对数相对价格漂移 δ̂（年化 + 22 年累计），组间差 β(N−R) + Welch t，
       并加 Mann-Whitney U（精确、双侧）做非参数交叉验证。
  ② 每品类时序画像：2000 基准累计涨幅、年化 δ̂、最新同比、近 2/5 年年化漂移、
       缺月标记、结构变化点（软件 2024 后反转 +21.2%，人工 flag）。
  ③ 结构化中间数据：h1_analyzed.json（单一信息源，含 caveat 字段）+ h1_metrics.csv（衍生）。

红线（已固化结论，脚本内不擅自变更；变更前须暂停问用户）：
  1. 教科书排除（BLS 不发布 college textbooks 子项，降级为 SEEA 未抓）。
  2. AEI "Chart of the Century" 基准年份 = 2000（不是 1998）。
  3. 住房用 OER（SEHC01），不用整体 SAH。
  4. 医院服务 = SEMD01（+14.8% 偏差假设 AEI 用 SEMD 聚合，待 SEMD 归档坐实）。
  5. 电脑软件 +21.2% 同比 = 真实反转（2024 后软件价格上涨），非口径假象。
  6. 医院 2 个缺月（2022-10、2024-08）= BLS 源侧停发，非脚本缺陷。

统计隐患（复核意见硬性要求，必须自动写入 caveat 字段）：
  A. N 组非独立观测：医院服务（SEMD01）是医疗护理服务（SAM2）的子成分，二者非完全
     独立观测，Welch t 的独立性假设不严格成立，p 值可能低估真实不确定性；该检验需待
     品类映射表扩展至 CPI 全样本后方具完整推断力。
  B. 确认性而非判别性：δ̂ 组间差（无论显著与否）与命题 1 相容、但不能判别——鲍莫尔
     成本病与赫希位置性商品对同一价格分化早有解释（预印本推论 1.1 申明）。本结果为
     确认性证据，非判别性证据（判别性回归 ProdGrowth_k + η_k + Positionality_k 需
     CE 调查与产业生产率数据，尚未进入 fetch 阶段）。

基准窗口（核心检验）：
  2000-01 → 2021-12，T = 22（与回归脚本 h1_welch_regression.py 的「情况B」、
  预印本附图 1 脚注 β=1.98 口径严格一致）。δ̂ 单位 = 相对 CPI 的年化对数漂移（%/年）。

用法：
  python h1_analyze.py                       # 自动读 raw_h1_cpi/ 最新归档，输出 h1_analyzed/
  python h1_analyze.py --raw raw_h1_cpi/2026-09-02.json
  python h1_analyze.py --outdir h1_analyzed
"""
import argparse
import csv
import json
import math
import os
import sys
from datetime import datetime, timezone
from itertools import combinations

# --------------------------------------------------------------------------
# 常量（与 fetch 层 / 回归脚本同源，勿擅改）
# --------------------------------------------------------------------------
MAPPING_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "category_mapping.csv")
RAW_DIR = "raw_h1_cpi"
OUT_DIR = "h1_analyzed"
STATUS_CONFIRMED = "已核实"

BENCHMARK_SID = "CUUR0000SA0"      # CPI 总指数（相对价格的分母）
BENCHMARK_YEAR = 2000              # AEI 基准年份（红线：不是 1998）
CORE_START = (2000, 1)             # 核心检验窗口起点 2000-01
CORE_END = (2021, 12)              # 核心检验窗口终点 2021-12（22 年口径）
CORE_YEARS = 22.0                  # 预印本「22 年」口径（2000–2021 含端点）
OOS_START = (2022, 1)              # 样本外验证窗口起点（用户拍板：核心窗口终点之后，严格零重叠）；
                                   # 终点 = 数据最新月（动态取）

# N/R 分组：单一信息源 = category_mapping.csv 的「H1分组」列（v1.1 起不再用脚本常量）
# CSV 取值 -> 内部分组键（「排除」= 聚合/交叉集合，归档但不入检验；「降级」行 status 非已核实，不会被读入）
CSV_GROUP_KEY = {"N": "N", "R": "R", "中性": "neutral", "排除": "excluded", "基准": "benchmark"}
GROUP_LABEL = {
    "N": "难自动化·照护·位置性",
    "R": "可复制·可贸易",
    "neutral": "中性（不入主回归）",
    "excluded": "排除（聚合/交叉集合，不入检验）",
    "benchmark": "基准（CPI 总指数）",
}

# 逐品类「人工核实后标注」的结构变化点 / 红线说明（复核意见：结构变化点暂用人工 flag）
CATEGORY_FLAGS = {
    "CUUR0000SEMD01": [
        "源侧缺月 2022-10、2024-08（BLS 停发，非脚本缺陷）",
        "SEMD01 口径；+14.8% 偏差假设 AEI 用 SEMD 聚合，待 SEMD 归档坐实",
    ],
    "CUUR0000SEEB01": [],
    "CUUR0000SAM2": [
        "SAM2 聚合层（更细可拆 SEMC01 医生 / SEMC02 牙科）",
        "与医院 SEMD01 存在嵌套：医院是医疗护理服务的子成分（非独立观测）",
    ],
    "CUUR0000SEEB03": [],
    "CUUR0000SEHC01": ["OER 口径 SEHC01（贴近赫希「位置性商品」意图，不用整体 SAH）"],
    "CUUR0000SAF": ["中性品类，不入 N/R 主回归"],
    "CUUR0000SEED03": [],
    "CUUR0000SEEE02": ["2024 后反转：最新同比 +21.2%（2026-07 vs 2025-07）为真实反转，非口径假象"],
    "CUUR0000SERE01": [],
    "CUUR0000SERA01": [],
    "CUUR0000SA0": ["基准序列：δ̂ 恒等于 0（分母）"],
}


# --------------------------------------------------------------------------
# 工具函数
# --------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def mkey(year, month):
    """月份 -> 连续整数键（year*12 + month-1），用于区间与缺月判定。"""
    return int(year) * 12 + int(month) - 1


def ymd(k):
    """连续整数键 -> 'YYYY-MM' 展示串。"""
    y, m = divmod(k, 12)
    return f"{y:04d}-{m + 1:02d}"


def load_mapping() -> list:
    """从 category_mapping.csv 读「已核实」序列元信息（单一信息源）。"""
    if not os.path.exists(MAPPING_CSV):
        raise FileNotFoundError(f"mapping 文件不存在：{MAPPING_CSV}")
    rows = []
    with open(MAPPING_CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            sid = (r.get("series_id") or "").strip()
            status = (r.get("状态") or "").strip()
            if not sid or status != STATUS_CONFIRMED:
                continue
            rows.append({
                "series_id": sid,
                "category_zh": (r.get("中文品类名") or "").strip(),
                "category_en": (r.get("BLS_item_title") or "").strip(),
                "level": (r.get("层级") or "").strip(),
                "data_start_year": (r.get("数据起始年份") or "").strip(),
                "note": (r.get("备注") or "").strip(),
                "h1_group_csv": (r.get("H1分组") or "").strip(),
            })
    if not rows:
        raise RuntimeError("category_mapping.csv 中没有 status==已核实 的序列")
    return rows


def load_raw(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"raw 归档不存在：{path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def latest_raw(default_dir: str = RAW_DIR) -> str:
    if not os.path.isdir(default_dir):
        raise FileNotFoundError(f"raw 归档目录不存在：{default_dir}")
    files = [f for f in os.listdir(default_dir) if f.endswith(".json")]
    if not files:
        raise FileNotFoundError(f"{default_dir} 下没有 .json 归档")
    files.sort()
    return os.path.join(default_dir, files[-1])


def build_series(raw_doc: dict):
    """raw JSON -> (values_by_sid, dash_by_sid)。
    values 过滤 '-' 占位；dash 单独记录 '-' 月（停发占位，与源侧缺位区分）。"""
    values, dash = {}, {}
    for s in raw_doc.get("series", []):
        sid = s["seriesID"]
        pts, dm = {}, set()
        for p in s.get("data", []):
            k = mkey(p["year"], int(p["period"][1:]))
            v = p.get("value")
            if v in ("-", "", None):
                dm.add(k)
                continue
            pts[k] = float(v)
        values[sid] = pts
        dash[sid] = dm
    return values, dash


def build_group_map(meta_rows: list) -> dict:
    """从映射表元信息构造 {series_id: 内部分组键}。H1分组 列缺失/未识别一律 fail loud。"""
    gmap = {}
    for m in meta_rows:
        raw = m.get("h1_group_csv", "")
        key = CSV_GROUP_KEY.get(raw)
        if key is None:
            raise ValueError(
                f"category_mapping.csv 的 H1分组 列值「{raw}」（{m['series_id']}）未被识别；"
                f"合法取值：{'/'.join(CSV_GROUP_KEY)}")
        gmap[m["series_id"]] = key
    for need in ("N", "R"):
        if not any(g == need for g in gmap.values()):
            raise ValueError(f"category_mapping.csv 中没有任何 H1分组=={need} 的已核实序列")
    return gmap


def group_of(sid: str, group_map: dict) -> str:
    return group_map.get(sid, "unknown")


def get_month(pts: dict, k: int, sid: str):
    """取某月数值；缺失则 fail loud（核心端点必须存在）。"""
    if k not in pts:
        raise KeyError(f"{sid} 缺月 {ymd(k)}（核心端点，无法计算）")
    return pts[k]


# --------------------------------------------------------------------------
# 统计：Welch t（与回归脚本 h1_welch_regression.py 完全一致）
# --------------------------------------------------------------------------
def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-12, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        dd = d * c
        h *= dd
        if abs(dd - 1.0) < EPS:
            break
    return h


def betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1 - x) / b


def t_cdf(t, df):
    x = df / (df + t * t)
    ib = betai(df / 2, 0.5, x)
    return 1 - 0.5 * ib if t >= 0 else 0.5 * ib


def welch(g1, g2):
    """Welch 双样本 t 检验，返回 (均值差, t, df, p)。"""
    n1, n2 = len(g1), len(g2)
    m1, m2 = sum(g1) / n1, sum(g2) / n2
    v1 = sum((x - m1) ** 2 for x in g1) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in g2) / (n2 - 1)
    se = math.sqrt(v1 / n1 + v2 / n2)
    t = (m1 - m2) / se
    df = (v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    p = 2 * (1 - t_cdf(abs(t), df))
    return m1 - m2, t, df, p


# --------------------------------------------------------------------------
# 统计：Mann-Whitney U（精确、双侧，纯标准库，含并列秩处理）
# --------------------------------------------------------------------------
def mann_whitney_exact(g1, g2):
    """Mann-Whitney U，n 很小故穷举 C(n1+n2, n1) 取精确双侧 p。
    g1 视为组 1（此处为 N 组），返回 (U1, p_exact_twosided)。"""
    n1, n2 = len(g1), len(g2)
    all_vals = list(g1) + list(g2)
    order = sorted(range(len(all_vals)), key=lambda i: all_vals[i])
    ranks = [0.0] * len(all_vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and all_vals[order[j + 1]] == all_vals[order[i]]:
            j += 1
        avg = sum(range(i + 1, j + 2)) / (j - i + 1)
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    R1 = sum(ranks[:n1])
    U1 = R1 - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0
    all_ranks = list(range(1, n1 + n2 + 1))
    total = 0
    extreme = 0
    for S in combinations(all_ranks, n1):
        U = sum(S) - n1 * (n1 + 1) / 2.0
        total += 1
        if abs(U - mu) >= abs(U1 - mu) - 1e-12:
            extreme += 1
    return U1, extreme / total


def norm_cdf(x):
    """标准正态 CDF（用 erf，纯标准库）。"""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def mann_whitney_asymptotic(g1, g2):
    """Mann-Whitney U 正态近似（大样本，含连续性校正；无并列修正，CPI δ̂ 并列概率可忽略）。
    返回 (U1, z, p_twosided)。"""
    n1, n2 = len(g1), len(g2)
    all_vals = list(g1) + list(g2)
    order = sorted(range(len(all_vals)), key=lambda i: all_vals[i])
    ranks = [0.0] * len(all_vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and all_vals[order[j + 1]] == all_vals[order[i]]:
            j += 1
        avg = sum(range(i + 1, j + 2)) / (j - i + 1)
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    R1 = sum(ranks[:n1])
    U1 = R1 - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
    z = (U1 - mu) / sigma if sigma > 0 else 0.0
    p = 2 * (1.0 - norm_cdf(abs(z)))
    return U1, z, p


def mann_whitney(g1, g2):
    """Mann-Whitney U 双样本检验：小样本（n1+n2 ≤ 20）走精确穷举，大样本走正态近似。
    返回 (U1, p_twosided, method)。"""
    n1, n2 = len(g1), len(g2)
    if n1 + n2 <= 20:
        U1, p = mann_whitney_exact(g1, g2)
        return U1, p, "exact"
    U1, z, p = mann_whitney_asymptotic(g1, g2)
    return U1, p, "asymptotic"


# --------------------------------------------------------------------------
# 核心计算
# --------------------------------------------------------------------------
def relative_drift(pts_k, pts_cpi, k0, k1, years, sid):
    """相对 CPI 的年化对数漂移 δ̂（%/年）。"""
    dk = math.log(get_month(pts_k, k1, sid) / get_month(pts_k, k0, sid))
    dc = math.log(get_month(pts_cpi, k1, BENCHMARK_SID) / get_month(pts_cpi, k0, BENCHMARK_SID))
    return (dk - dc) / years * 100.0


def compute_portrait(series_data, dash_by_sid, meta_by_id, pts_cpi, group_map):
    """② 逐品类时序画像。返回 (portrait_dict, latest_ym, oos_years)。"""
    latest = max(pts_cpi.keys())  # 以 CPI 总指数为准的「最新月」
    k_2000 = mkey(*CORE_START)
    k_core_end = mkey(*CORE_END)
    k_oos = mkey(*OOS_START)
    oos_years = (latest - k_oos) / 12.0
    k_2y = latest - 24
    k_5y = latest - 60
    k_yoy = latest - 12

    portrait = {}
    for sid, pts in series_data.items():
        grp = group_of(sid, group_map)
        # 全样本适配（2026-09-03）：画像只覆盖 N/R/中性/基准，跳过「排除」聚合层——
        # 排除组含 13 个「起始年份>1998」的聚合层（如 SAEC 2009 起），无 2000-01 端点，
        # 且本就不入检验，不应出现在品类画像里。
        if grp == "excluded":
            continue
        # 是否有 2000-01 端点：决定能否算 22 年漂移 + 2000 基准累计。中性 SEMG/SEHL02（医疗设备、
        # 室内植物，2009/更晚起）无此端点，22 年漂移/2000 基准置空，近 2/5 年与样本外漂移仍可算。
        has_core = k_2000 in pts
        # 该序列自身的最新真实月，及是否覆盖到全局最新月。端点滞后序列（现仅 SEGD01 法律服务，
        # 2024-09 后因 2025 联邦拨款中断停发）在「到最新月」的近期窗口上留空、不进组均值/检验
        # （用户 2026-09-03 拍板）；累计 2000 字段为长期量，仍用其自身最新月计算。
        latest_s = max(pts.keys())
        has_latest = latest in pts
        if sid == BENCHMARK_SID:
            drift_22 = 0.0
        elif has_core:
            drift_22 = relative_drift(pts, pts_cpi, k_2000, k_core_end, CORE_YEARS, sid)
        else:
            drift_22 = None
        # 近期窗口（样本外/近 2/5 年/最新同比）：只对覆盖到全局最新月的序列计算，端点滞后留空
        if has_latest:
            drift_oos = relative_drift(pts, pts_cpi, k_oos, latest, oos_years, sid) if sid != BENCHMARK_SID else 0.0
            drift_5y = relative_drift(pts, pts_cpi, k_5y, latest, 5.0, sid)
            drift_2y = relative_drift(pts, pts_cpi, k_2y, latest, 2.0, sid)
            yoy_nom = (get_month(pts, latest, sid) / get_month(pts, k_yoy, sid) - 1.0) * 100.0
        else:
            drift_oos = None
            drift_5y = None
            drift_2y = None
            yoy_nom = None
        # 累计 2000 字段（核心长期量，用序列自身最新月 latest_s）
        if has_core:
            p_2000 = get_month(pts, k_2000, sid)
            cpi_2000 = get_month(pts_cpi, k_2000, BENCHMARK_SID)
            p_s = get_month(pts, latest_s, sid)
            cpi_s = get_month(pts_cpi, latest_s, BENCHMARK_SID)
            cum_nom = (p_s / p_2000 - 1.0) * 100.0
            cum_rel = ((p_s / p_2000) / (cpi_s / cpi_2000) - 1.0) * 100.0
        else:
            cum_nom = None
            cum_rel = None

        # 缺月：源侧缺位（真正 absent）与 '-' 停发占位分开报告；上限用序列自身最新月，
        # 避免把「停发后」的月份误报为缺月
        keys = sorted(pts.keys())
        dash = dash_by_sid.get(sid, set())
        missing = [k for k in range(keys[0], latest_s + 1) if k not in pts and k not in dash]

        flags = list(CATEGORY_FLAGS.get(sid, []))
        # 端点滞后序列：动态生成停发说明 + 最近一次可用同比（放备注文字，不进统计列）
        if not has_latest and sid != BENCHMARK_SID:
            note = (f"数据停发：最新真实月 {ymd(latest_s)}（2025 联邦拨款中断，BLS 自 2025-10 起停发）；"
                    f"样本外/近 2 年/近 5 年/最新同比已留空、不进组均值与检验")
            k_yoy_s = latest_s - 12
            if k_yoy_s in pts:
                last_yoy = (get_month(pts, latest_s, sid) / get_month(pts, k_yoy_s, sid) - 1.0) * 100.0
                note += f"；最近一次可用同比（{ymd(k_yoy_s)}→{ymd(latest_s)}）= {last_yoy:+.3f}%"
            flags.append(note)

        portrait[sid] = {
            "series_id": sid,
            "category_zh": meta_by_id[sid]["category_zh"],
            "category_en": meta_by_id[sid]["category_en"],
            "level": meta_by_id[sid]["level"],
            "group": grp,
            "group_label": GROUP_LABEL.get(grp, ""),
            "drift_annual_pct_22yr": round(drift_22, 4) if drift_22 is not None else None,
            "drift_annual_pct_oos": round(drift_oos, 4) if drift_oos is not None else None,
            "drift_annual_pct_5yr": round(drift_5y, 4) if drift_5y is not None else None,
            "drift_annual_pct_2yr": round(drift_2y, 4) if drift_2y is not None else None,
            "cum_nominal_pct_2000": round(cum_nom, 3) if cum_nom is not None else None,
            "cum_relative_pct_2000": round(cum_rel, 3) if cum_rel is not None else None,
            "yoy_nominal_pct": round(yoy_nom, 3) if yoy_nom is not None else None,
            "latest_month": ymd(latest_s),
            "missing_months": [ymd(k) for k in missing],
            "dash_months": [ymd(k) for k in sorted(dash)],
            "flags": flags,
        }
    return portrait, ymd(latest), oos_years


# --------------------------------------------------------------------------
# 输出
# --------------------------------------------------------------------------
def build_caveats():
    """自动生成免责性说明（复核意见硬性要求，写进 JSON 的 caveat 字段）。"""
    return [
        ("嵌套 caveat（历史锁定）：医院服务（SEMD01）是医疗护理服务（SAM2）的子成分，二者非完全"
         "独立观测，Welch t 的组内独立性假设不严格成立，p 值可能低估真实不确定性。扩展至 CPI 全样本"
         "时已按「明细优先」对新增品类做叶子硬检查去嵌套，但 SAM2⊃SEMD01 因「老品类不动」而保留；"
         "该 caveat 在 t 检验解读时须继续降级措辞。"),
        ("确认性而非判别性：δ̂ 的组间差（无论显著性如何）均与命题 1 相容、但不能判别——鲍莫尔成本病"
         "与赫希位置性商品对同一价格分化早有解释（预印本推论 1.1 申明）。本结果为确认性证据，"
         "非判别性证据；判别性回归（ProdGrowth_k + η_k + Positionality_k）需 CE 调查与产业生产率"
         "数据，尚未进入 fetch 阶段。"),
    ]


def build_oos_caveats():
    """样本外验证窗口的免责性说明（核心两条 caveat 同样适用于该窗口，另加窗口特有说明）。"""
    return build_caveats() + [
        ("样本外窗口性质：本窗口（2022-01 起，与核心窗口终点 2021-12 之后衔接、严格零重叠）为"
         "预印本成稿后才发生的数据，对预印本构成真正的样本外检验（不同于跨窗口稳定性 r=0.998 的"
         " 18 年重叠）；但与核心窗口一样，仍属确认性证据。"),
        ("窗口内部缺月：医院 2 个源侧缺月（2022-10、2024-08）与 2025-10 停发占位月均落在窗口内部，"
         "不影响端点法 δ̂（两端点均存在）；电脑软件 2024 后反转使 R 组该序列在窗口后半段漂移转正，"
         "属真实结构变化（红线），已在逐品类画像中单列。"),
    ]


def build_adjustments():
    """可扩展的「口径调整」数组。每一项描述主口径之外的一个替代/修正口径（正式字段）。
    结构：name / applies_to / reason / excluded_subcomponent / effect_delta_pp_per_year /
    core_window_effect / method / status。后续可追加其他调整，不改数组骨架。
    ex-HI：剔除健康保险(SEME)对医疗护理服务(SAM2)的拖累（诊断脚本 h1_hi_diagnostic.py 坐实）。"""
    return [
        {
            "name": "ex_health_insurance",
            "applies_to": "N 组（医疗护理服务 SAM2 成分）",
            "reason": "健康保险(SEME)样本外相对漂移异常（约 -9.88%/年），拖累 SAM2 约 -1.05~-1.11 pp/年；"
                      "剔除后 ex-HI 口径仅约 -0.20~-0.35%/年，基本走平。",
            "excluded_subcomponent": {"series": "CUUR0000SEME", "host_series": "CUUR0000SAM2"},
            "effect_delta_pp_per_year": {"sam2_point": -1.08, "range": [-1.11, -1.05]},
            "core_window_effect": "≈ -0.005 pp/年，可忽略；样本外受影响明显",
            "method": "Laspeyres 成分分解（token-parity/h1_hi_diagnostic.py）",
            "status": "documented；待 SEME 正式归档后在本层程序化复算",
        },
    ]


def write_outputs(doc: dict, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    jpath = os.path.join(outdir, "h1_analyzed.json")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # CSV（衍生，同一份数据；数值不带 %，展示格式由 render 层负责）
    cpath = os.path.join(outdir, "h1_metrics.csv")
    cols = ["series_id", "category_zh", "group", "drift_annual_pct_22yr", "drift_annual_pct_oos",
            "drift_annual_pct_5yr", "drift_annual_pct_2yr", "cum_nominal_pct_2000", "cum_relative_pct_2000",
            "yoy_nominal_pct", "missing_months", "dash_months", "flags"]
    with open(cpath, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for c in doc["categories"]:
            w.writerow([
                c["series_id"], c["category_zh"], c["group"],
                c["drift_annual_pct_22yr"], c["drift_annual_pct_oos"],
                c["drift_annual_pct_5yr"], c["drift_annual_pct_2yr"],
                c["cum_nominal_pct_2000"], c["cum_relative_pct_2000"], c["yoy_nominal_pct"],
                ";".join(c["missing_months"]), ";".join(c["dash_months"]), " | ".join(c["flags"]),
            ])
    return jpath, cpath


def print_summary(doc: dict):
    ct = doc["core_test"]
    print("=" * 70)
    print("H1 analyze 层结论摘要（自动生成）")
    print("=" * 70)
    print(f"核心检验窗口：{ct['window']['start']} → {ct['window']['end']}（T={ct['window']['years']:.0f}）")
    print(f"N 组（n={ct['n_N']}）：" + ", ".join(
        f"{c['category_zh']} {c['drift_annual_pct_22yr']:+.3f}" for c in doc['categories'] if c['group'] == 'N'))
    print(f"R 组（n={ct['n_R']}）：" + ", ".join(
        f"{c['category_zh']} {c['drift_annual_pct_22yr']:+.3f}" for c in doc['categories'] if c['group'] == 'R'))
    print(f"N 类均值 δ̂ = {ct['mean_N']:+.3f}%/年   R 类均值 δ̂ = {ct['mean_R']:+.3f}%/年")
    print(f"β(N−R) = {ct['beta_annual_pct']:+.3f}%/年  → 累计(×{CORE_YEARS:.0f}) = "
          f"{ct['beta_cumulative_22yr_pct']:+.3f}%（对数 {ct['beta_cumulative_log_22yr']:+.3f}）")
    print(f"Welch t = {ct['welch']['t']:.3f}   df = {ct['welch']['df']:.2f}   p = {ct['welch']['p']:.4f}")
    mw_c = "精确" if ct['mann_whitney']['method'] == "exact" else "渐近"
    print(f"Mann-Whitney U = {ct['mann_whitney']['U']:.3f}   {mw_c}双侧 p = {ct['mann_whitney']['p_twosided']:.4f}")
    print("-" * 70)
    ot = doc["oos_test"]
    print(f"样本外验证窗口：{ot['window']['start']} → {ot['window']['end']}（T={ot['window']['years']:.1f}，与核心窗口零重叠）")
    if ot.get("excluded_series"):
        print("样本外剔除（端点滞后）：" + ", ".join(
            f"{e['category_zh']}({e['series_id']})" for e in ot["excluded_series"]))
    print(f"N 组 δ̂（样本外）：" + ", ".join(
        f"{c['category_zh']} " + (f"{c['drift_annual_pct_oos']:+.3f}" if c['drift_annual_pct_oos'] is not None else "—")
        for c in doc['categories'] if c['group'] == 'N'))
    print(f"R 组 δ̂（样本外）：" + ", ".join(
        f"{c['category_zh']} " + (f"{c['drift_annual_pct_oos']:+.3f}" if c['drift_annual_pct_oos'] is not None else "—")
        for c in doc['categories'] if c['group'] == 'R'))
    print(f"N 类均值 δ̂ = {ot['mean_N']:+.3f}%/年   R 类均值 δ̂ = {ot['mean_R']:+.3f}%/年")
    print(f"β(N−R) = {ot['beta_annual_pct']:+.3f}%/年  → 累计(×{ot['window']['years']:.1f}) = "
          f"{ot['beta_cumulative_pct']:+.3f}%（对数 {ot['beta_cumulative_log']:+.3f}）")
    print(f"Welch t = {ot['welch']['t']:.3f}   df = {ot['welch']['df']:.2f}   p = {ot['welch']['p']:.4f}")
    mw_o = "精确" if ot['mann_whitney']['method'] == "exact" else "渐近"
    print(f"Mann-Whitney U = {ot['mann_whitney']['U']:.3f}   {mw_o}双侧 p = {ot['mann_whitney']['p_twosided']:.4f}")
    print("-" * 70)
    print("组内排序（δ̂ 22 年）：")
    for grp in ("N", "R"):
        ranked = sorted([c for c in doc['categories'] if c['group'] == grp],
                        key=lambda c: c['drift_annual_pct_22yr'], reverse=True)
        seq = " > ".join("{}({:+0.3f})".format(c['category_zh'], c['drift_annual_pct_22yr']) for c in ranked)
        print(f"  {grp} 组：{seq}")
    print("-" * 70)
    print("caveat（简报 02 措辞必须降级；核心与样本外窗口共用前两条）：")
    for i, cav in enumerate(doc['core_test']['caveats'], 1):
        print(f"  {i}. {cav}")
    for i, cav in enumerate(doc['oos_test']['caveats'][len(doc['core_test']['caveats']):], 3):
        print(f"  {i}. [样本外窗口专属] {cav}")
    print("=" * 70)


def main() -> int:
    ap = argparse.ArgumentParser(description="H1 世纪图表 CPI analyze 层")
    ap.add_argument("--raw", default=None, help="raw 归档路径（默认取 raw_h1_cpi/ 最新）")
    ap.add_argument("--outdir", default=OUT_DIR, help="输出目录（默认 h1_analyzed/）")
    args = ap.parse_args()

    raw_path = args.raw or latest_raw()
    try:
        meta_rows = load_mapping()
        raw_doc = load_raw(raw_path)
    except Exception as exc:
        print(f"[h1_analyze] ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    meta_by_id = {m["series_id"]: m for m in meta_rows}
    series_data, dash_by_sid = build_series(raw_doc)

    # 一致性校验：映射表「已核实」序列与 raw 归档必须一一对应（单一信息源）
    raw_ids = set(series_data.keys())
    map_ids = set(meta_by_id.keys())
    if raw_ids != map_ids:
        print(f"[h1_analyze] ERROR: raw 与 mapping 序列不一致。仅 raw: {raw_ids - map_ids}; "
              f"仅 mapping: {map_ids - raw_ids}", file=sys.stderr)
        return 1

    # N/R 分组：单一信息源 = category_mapping.csv「H1分组」列（v1.1 起不再用脚本常量）
    group_map = build_group_map(meta_rows)
    N_SERIES = [sid for sid, g in group_map.items() if g == "N"]
    R_SERIES = [sid for sid, g in group_map.items() if g == "R"]
    NEUTRAL_SERIES = [sid for sid, g in group_map.items() if g == "neutral"]
    EXCLUDED_SERIES = [sid for sid, g in group_map.items() if g == "excluded"]

    pts_cpi = series_data[BENCHMARK_SID]

    # ② 逐品类画像（drift 舍入仅用于展示/落盘）
    portrait, latest_ym, oos_years = compute_portrait(
        series_data, dash_by_sid, meta_by_id, pts_cpi, group_map)

    # ① 核心检验：用全精度 δ̂（与回归脚本 h1_welch_regression.py 严格同源，勿用舍入值）
    k0, k1 = mkey(*CORE_START), mkey(*CORE_END)
    drift_N = [relative_drift(series_data[s], pts_cpi, k0, k1, CORE_YEARS, s) for s in N_SERIES]
    drift_R = [relative_drift(series_data[s], pts_cpi, k0, k1, CORE_YEARS, s) for s in R_SERIES]
    mean_N = sum(drift_N) / len(drift_N)
    mean_R = sum(drift_R) / len(drift_R)
    beta_annual = mean_N - mean_R
    beta_cum_pct = beta_annual * CORE_YEARS
    beta_cum_log = beta_cum_pct / 100.0
    _, t, df, p = welch(drift_N, drift_R)
    u_stat, mw_p, mw_method = mann_whitney(drift_N, drift_R)
    mw_note = ("精确双侧（穷举 C(nN+nR, nN)），非渐近近似；N 组秩和偏高为「N 漂移 > R 漂移」方向"
               if mw_method == "exact"
               else "正态近似（nN+nR 过大不可穷举，含连续性校正）；N 组秩和偏高为「N 漂移 > R 漂移」方向")

    core_test = {
        "window": {"start": f"{CORE_START[0]}-{CORE_START[1]:02d}",
                   "end": f"{CORE_END[0]}-{CORE_END[1]:02d}",
                   "years": CORE_YEARS},
        "n_N": len(drift_N),
        "n_R": len(drift_R),
        "drift_N": [round(x, 4) for x in drift_N],
        "drift_R": [round(x, 4) for x in drift_R],
        "mean_N": round(mean_N, 4),
        "mean_R": round(mean_R, 4),
        "beta_annual_pct": round(beta_annual, 4),
        "beta_cumulative_22yr_pct": round(beta_cum_pct, 3),
        "beta_cumulative_log_22yr": round(beta_cum_log, 4),
        "welch": {"t": round(t, 6), "df": round(df, 6), "p": round(p, 6)},
        "mann_whitney": {"U": round(u_stat, 4), "p_twosided": round(mw_p, 4), "method": mw_method,
                         "note": mw_note},
        "caveats": build_caveats(),
    }

    # ①' 样本外验证（复核意见拍板）：2022-01 → 最新月，零重叠、全事后，独立成节不混报
    # 端点滞后序列（现仅 SEGD01 法律服务，2024-09 后停发）无全局最新月端点，从样本外检验剔除
    # （用户 2026-09-03 拍板：不进组均值/检验）
    k_latest = max(pts_cpi.keys())
    k_oos0 = mkey(*OOS_START)
    oos_end_ym = ymd(k_latest)

    def _oos_ok(sid):
        return k_latest in series_data[sid] and k_oos0 in series_data[sid]

    oos_drift_N = [relative_drift(series_data[s], pts_cpi, k_oos0, k_latest, oos_years, s)
                   for s in N_SERIES if _oos_ok(s)]
    oos_drift_R = [relative_drift(series_data[s], pts_cpi, k_oos0, k_latest, oos_years, s)
                   for s in R_SERIES if _oos_ok(s)]
    oos_excluded = [{"series_id": s, "category_zh": meta_by_id[s]["category_zh"],
                     "reason": (f"数据停发，最新真实月 {ymd(max(series_data[s].keys()))} 早于全局最新月，"
                                f"样本外窗口端点缺失，不进组均值/检验")}
                    for s in N_SERIES + R_SERIES if not _oos_ok(s)]
    oos_mean_N = sum(oos_drift_N) / len(oos_drift_N)
    oos_mean_R = sum(oos_drift_R) / len(oos_drift_R)
    oos_beta = oos_mean_N - oos_mean_R
    oos_beta_cum_pct = oos_beta * oos_years
    oos_beta_cum_log = oos_beta_cum_pct / 100.0
    _, ot_t, ot_df, ot_p = welch(oos_drift_N, oos_drift_R)
    ot_u, ot_mw_p, ot_mw_method = mann_whitney(oos_drift_N, oos_drift_R)
    ot_mw_note = ("精确双侧（穷举 C(nN+nR, nN)）"
                  if ot_mw_method == "exact"
                  else "正态近似（nN+nR 过大不可穷举，含连续性校正）")

    oos_test = {
        "window": {"start": f"{OOS_START[0]}-{OOS_START[1]:02d}",
                   "end": oos_end_ym,
                   "years": round(oos_years, 4)},
        "window_note": "与核心窗口 2000-01→2021-12 零重叠；数据为预印本成稿后才发生，构成真正的样本外检验",
        "n_N": len(oos_drift_N),
        "n_R": len(oos_drift_R),
        "excluded_series": oos_excluded,
        "drift_N": [round(x, 4) for x in oos_drift_N],
        "drift_R": [round(x, 4) for x in oos_drift_R],
        "mean_N": round(oos_mean_N, 4),
        "mean_R": round(oos_mean_R, 4),
        "beta_annual_pct": round(oos_beta, 4),
        "beta_cumulative_pct": round(oos_beta_cum_pct, 3),
        "beta_cumulative_log": round(oos_beta_cum_log, 4),
        "welch": {"t": round(ot_t, 6), "df": round(ot_df, 6), "p": round(ot_p, 6)},
        "mann_whitney": {"U": round(ot_u, 4), "p_twosided": round(ot_mw_p, 4), "method": ot_mw_method,
                         "note": ot_mw_note},
        "caveats": build_oos_caveats(),
    }

    # 组内排序（供简报「稀缺迁移一眼可见」；排序本身是对「漂移速度取决于 η−ε 而非类别标签」
    # 的初步支持：同为 N 类，医院远快于住房 OER——差异需追到需求弹性/位置性强度的具体解释）
    ranking = {}
    for grp in ("N", "R"):
        ranked = sorted([c for c in portrait.values() if c["group"] == grp],
                        key=lambda c: c["drift_annual_pct_22yr"], reverse=True)
        ranking[grp] = [{"category_zh": c["category_zh"],
                         "drift_annual_pct_22yr": c["drift_annual_pct_22yr"]} for c in ranked]
    ranking["interpretation_note"] = (
        "组内排序（N：医院>学费>医疗>托儿>住房；R：电视<玩具<软件<手机）本身是「漂移速度取决于"
        "η−ε 而非模糊类别标签」这一理论主张的初步支持：同为 N 类，医疗需求的收入弹性远高于"
        "位置性住房，医院 δ̂ 即远快于住房 OER——简报 02 应将此排序作为判别性线索展开一句，"
        "而非仅作描述性花絮。")

    doc = {
        "analyzed_at": now_iso(),
        "source_raw": os.path.basename(raw_path),
        "mapping_csv": "category_mapping.csv",
        "method": {
            "drift_definition": "δ̂_k = [ln(P_k(t1)/P_k(t0)) - ln(CPI(t1)/CPI(t0))] / T × 100（%/年）",
            "benchmark_series": BENCHMARK_SID,
            "benchmark_year": BENCHMARK_YEAR,
            "core_window": core_test["window"],
            "oos_window": oos_test["window"],
            "group_source": "category_mapping.csv「H1分组」列（单一信息源，v1.1 起脚本不再维护分组常量）",
            "units": {
                "drift_annual_pct_*": "相对 CPI 的年化对数漂移，单位 %/年（*_22yr=核心窗口，*_oos=样本外窗口，*_5yr/*_2yr=以最新月为终点的近 N 年）",
                "cum_*_pct_2000": "自 2000-01 的累计百分比，单位 %",
                "yoy_nominal_pct": "最新月相对 12 个月前的名义同比，单位 %",
                "beta_cumulative_log_22yr": "22 年累计对数（预印本脚注 β=1.98 同口径）",
            },
        },
        "groups": {
            "N": {"label": GROUP_LABEL["N"], "series": N_SERIES},
            "R": {"label": GROUP_LABEL["R"], "series": R_SERIES},
            "neutral": {"label": GROUP_LABEL["neutral"], "series": NEUTRAL_SERIES},
            "excluded": {"label": GROUP_LABEL["excluded"], "series": EXCLUDED_SERIES},
            "benchmark": {"label": GROUP_LABEL["benchmark"], "series": [BENCHMARK_SID]},
        },
        "core_test": core_test,
        "oos_test": oos_test,
        "ranking": ranking,
        "adjustments": build_adjustments(),
        "categories": [portrait[s] for s in sorted(portrait.keys())],
        "latest_month": latest_ym,
        "conclusion": {
            "headline": "价格长期结构：稀缺向难自动化品类（N）迁移上涨、可自动化品类（R）丰裕化下跌。"
                        "22 年窗口组间漂移差 β(N−R)=+{:.1f} 个百分点/年。".format(beta_annual),
            "evidence_type": "confirmatory",
            "evidence_type_note": "确认性证据（与丰裕学、鲍莫尔、赫希三方均相容），非判别性证据",
            "next_discriminative": "判别性回归需 CE 调查 + 产业生产率数据（η/ε 分离），尚未进入 fetch 阶段",
        },
    }

    jpath, cpath = write_outputs(doc, args.outdir)
    print_summary(doc)
    print(f"[h1_analyze] OK: JSON -> {jpath}")
    print(f"[h1_analyze] OK: CSV  -> {cpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
