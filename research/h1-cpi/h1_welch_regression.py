# -*- coding: utf-8 -*-
"""H1 组间差 Welch t 检验 —— 回归测试（h1_welch_regression）

用途：
  复现丰裕学预印本 v1.6 第五编「附图1」脚注的组间差统计量：
    β(N−R) = 1.98（对数相对价格）  Welch t = 2.74  p = 0.050
  情况A（预印本原口径）应精确复现 β=1.98 / t≈2.737 / p≈0.0499。

定位：
  H1 数据管线的推断统计回归测试。每次 analyze 层改动后跑一遍，
  防止某次重构悄悄改坏 N/R 分组口径或 δ̂（年化对数相对价格漂移率）算法。

关键时间戳（防"为让结果更好看而排除教科书"的质疑）：
  · 2026-09-02 上午 —— 说明书 A 因 BLS 不单独发布 college textbooks 子项，
    将「大学教科书」降级为聚合层 SEEA（数据不存在，非统计取舍）。
  · 2026-09-02 下午 —— 本脚本复现时发现"排除教科书后组间差更强"（t 2.74→3.70）。
  排除决定早于显著性发现，二者无因果关联；若教科书回填，t 回落至约 2.74。

纯标准库实现（不依赖 scipy）：Welch t + 不完全 Beta 函数的 t 分布 CDF。
"""
import math, json

def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-12, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN: d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        dd = d * c
        h *= dd
        if abs(dd - 1.0) < EPS:
            break
    return h

def betai(a, b, x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
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
    n1, n2 = len(g1), len(g2)
    m1, m2 = sum(g1) / n1, sum(g2) / n2
    v1 = sum((x - m1) ** 2 for x in g1) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in g2) / (n2 - 1)
    se = math.sqrt(v1 / n1 + v2 / n2)
    t = (m1 - m2) / se
    df = (v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    p = 2 * (1 - t_cdf(abs(t), df))
    return m1 - m2, t, df, p

# ============ 情况A：预印本原口径（附表 δ̂，R 类含教科书，住房 +73% 整体） ============
print("=" * 62)
print("情况A：预印本原口径（R类含教科书，住房 +73% 整体口径）")
N_A = [2.87, 2.31, 1.36, 1.13, 0.20]        # 医院 学费 医疗 托儿 住房
R_A = [-4.61, -7.92, -8.24, -18.23, 1.87]   # 手机 软件 玩具 电视 教科书
b, t, df, p = welch(N_A, R_A)
print(f"  N类均值 = {sum(N_A)/len(N_A):+.3f}%/年   R类均值 = {sum(R_A)/len(R_A):+.3f}%/年")
print(f"  β(N−R) = {b:+.3f}%/年  → 累计(×22) = {b*22:+.3f}")
print(f"  Welch t = {t:.3f}   df = {df:.2f}   p = {p:.4f}")
print("  脚注原文：β=1.98（对数相对价格），Welch t=2.74，p=0.050")

# ============ 情况B：自动化口径（raw JSON 实际数据） ============
d = json.load(open('raw_h1_cpi/2026-09-02.json', encoding='utf-8'))
pts = {}
for s in d['series']:
    sid = s['seriesID']
    pts[sid] = {(int(p['year']), p['period']): float(p['value']) for p in s['data'] if p['value'] not in ('-', '')}

def annual_drift(sid):
    v0, v1 = pts[sid][(2000, 'M01')], pts[sid][(2021, 'M12')]
    vc0, vc1 = pts['CUUR0000SA0'][(2000, 'M01')], pts['CUUR0000SA0'][(2021, 'M12')]
    return (math.log(v1 / v0) - math.log(vc1 / vc0)) / 22 * 100

print("=" * 62)
print("情况B：自动化口径（R类4个不含教科书，住房 OER/SEHC01）")
ids = {'CUUR0000SEMD01':'医院','CUUR0000SEEB01':'学费','CUUR0000SAM2':'医疗',
       'CUUR0000SEEB03':'托儿','CUUR0000SEHC01':'住房OER','CUUR0000SEED03':'手机',
       'CUUR0000SEEE02':'软件','CUUR0000SERE01':'玩具','CUUR0000SERA01':'电视'}
drif = {sid: annual_drift(sid) for sid in ids}
for sid, zh in ids.items():
    print(f"  {zh:6s} {sid}  δ̂ = {drif[sid]:+.3f}%/年")
N_B = [drif['CUUR0000SEMD01'], drif['CUUR0000SEEB01'], drif['CUUR0000SAM2'], drif['CUUR0000SEEB03'], drif['CUUR0000SEHC01']]
R_B = [drif['CUUR0000SEED03'], drif['CUUR0000SEEE02'], drif['CUUR0000SERE01'], drif['CUUR0000SERA01']]
b, t, df, p = welch(N_B, R_B)
print(f"  N类均值 = {sum(N_B)/len(N_B):+.3f}%/年   R类均值 = {sum(R_B)/len(R_B):+.3f}%/年")
print(f"  β(N−R) = {b:+.3f}%/年  → 累计(×22) = {b*22:+.3f}")
print(f"  Welch t = {t:.3f}   df = {df:.2f}   p = {p:.4f}")

# ============ 情况C：自动化口径 + 住房换整体 +73%，仍无教科书 ============
print("=" * 62)
print("情况C：自动化口径 + 住房换整体 +73%（仍无教科书）")
N_C = N_B[:4] + [0.20]
b, t, df, p = welch(N_C, R_B)
print(f"  β(N−R) = {b:+.3f}%/年  → 累计(×22) = {b*22:+.3f}")
print(f"  Welch t = {t:.3f}   df = {df:.2f}   p = {p:.4f}")
