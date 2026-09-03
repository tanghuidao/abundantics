# -*- coding: utf-8 -*-
"""
H1 诊断：医疗护理服务（SAM2）样本外转负是否为 BLS 健康保险 CPI 核算故障所致
================================================================================
背景：复核意见指出——SAM2 内含健康保险子项（SEME），其"留存收益法"在疫情期间失灵，
     2022-09 同比一度 +28.2%，随后暴跌（2024-06 同比 -4.2%，2026-07 同比 -8.0%），
     BLS 已于 2023-10 按国家院 CNSTAT 建议改用半年更新 + 两年移动平均。
     该故障横跨整个样本外窗口（2022-01 → 2026-07）。

方法：SAM2 = 专业服务(SEMC) + 医院及相关服务(SEMD) + 健康保险(SEME)（BLS 官方层级）。
     用 Laspeyres 近似：g_SAM2(t) = s_C·g_SEMC(t) + s_D·g_SEMD(t) + s_E·g_SEME(t)，
     g_i(t) = I_i(t)/I_i(0)。权重先用 BLS 官方相对重要性（Dec 2021：51.5/37.0/11.5），
     再用约束最小二乘（s≥0, Σs=1）拟合实际 SAM2 路径做稳健性对照。
     排除健康保险口径：g_exHI(t) = (s_C·g_SEMC + s_D·g_SEMD)/(s_C+s_D)。

数据来源（本地 BLS 地域封锁，经服务端网页读取，2026-09-02 落盘）：
  - SEME/SEMC/SEMD：https://data.bls.gov/timeseries/{ID}?output_view=data
    （未季调；SEME base Dec2005=100，SEMC base 1982-84=100，SEMD base Dec2024=100；
      2025-10 为 X = 拨款中断停发月，与 raw JSON 的 dash 月一致）
  - SAM2（CUUR0000SAM2）、CPI 总指数（CUUR0000SA0）：本地 raw_h1_cpi/2026-09-02.json

输出：各组件与 ex-HI 口径在样本外窗口（2022-01 → 2026-07, T=4.5 年）的相对漂移 δ̂，
     及健康保险拖累的定量归因。核心窗口（2000-2021）污染量级核查。
"""
import json
import math
import os

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_h1_cpi", "2026-09-02.json")

# ---- 服务端抓取的月度指数（2021-01 → 2026-07；None = 2025-10 停发月）----
SEME = {  # 健康保险 CUUR0000SEME（Dec 2005=100）
    2021: [177.079,176.390,175.082,173.396,171.600,169.900,168.868,167.834,166.229,169.540,172.437,175.263],
    2022: [180.070,183.578,187.599,191.433,195.213,199.279,203.690,208.603,213.036,204.489,195.796,189.070],
    2023: [182.312,174.883,167.618,161.226,155.288,149.684,143.612,138.443,133.557,135.000,136.472,137.923],
    2024: [139.891,140.498,142.123,142.540,143.303,143.455,142.822,143.026,143.544,144.240,144.499,144.482],
    2025: [145.551,145.972,146.540,147.173,147.508,148.380,149.036,149.222,149.597,None,145.312,143.744],
    2026: [142.337,140.749,138.741,138.169,138.018,137.379,137.122],
}
SEMC = {  # 专业服务 CUUR0000SEMC（1982-84=100）
    2021: [395.911,400.762,401.208,400.834,401.147,401.227,402.687,403.860,403.271,403.378,404.220,404.764],
    2022: [406.197,406.917,408.052,408.209,408.873,411.550,411.626,413.590,416.501,416.720,416.614,416.732],
    2023: [417.035,416.709,416.899,416.998,416.998,418.410,419.559,421.297,421.462,419.663,421.347,422.433],
    2024: [424.531,424.859,424.972,425.213,426.244,427.285,427.954,427.816,431.141,432.587,433.998,434.095],
    2025: [433.646,434.984,435.565,436.794,436.581,439.338,442.517,442.955,442.367,None,443.599,444.798],
    2026: [448.191,450.994,453.288,454.136,456.401,455.871,457.746],
}
SEMD = {  # 医院及相关服务 CUUR0000SEMD（Dec 2024=100）
    2021: [85.159,85.365,85.815,85.931,85.872,85.914,86.326,86.896,87.045,87.545,87.295,87.112],
    2022: [88.199,88.280,88.730,89.020,89.171,89.282,89.804,90.419,90.474,90.509,90.056,91.090],
    2023: [91.715,91.813,91.591,91.981,92.681,93.001,92.854,93.572,94.695,95.614,95.693,96.162],
    2024: [97.692,97.425,98.625,99.201,99.493,99.605,98.616,98.992,99.259,99.706,99.774,100.000],
    2025: [100.864,101.092,102.423,102.973,103.386,103.820,104.277,104.256,105.063,None,105.756,106.704],
    2026: [107.801,108.762,108.961,108.687,109.362,109.498,109.941],
}

OOS_START = (2022, 1)
OOS_END = (2026, 7)   # 与 h1_analyze.py 样本外窗口严格一致
T_YEARS = 4.5

def flat(series):
    """{(year,month): value}，跳过 None（停发月）。"""
    out = {}
    for y, vals in series.items():
        for m, v in enumerate(vals, 1):
            if v is not None:
                out[(y, m)] = v
    return out

def mkey(y, m):
    return (y, m)

def main():
    # 本地 raw：SAM2 + CPI 总指数
    with open(RAW, encoding="utf-8") as f:
        raw = json.load(f)
    pts = {}
    for s in raw["series"]:
        sid = s["seriesID"]
        pts[sid] = {(int(p["year"]), int(p["period"][1:])): float(p["value"])
                    for p in s["data"] if p["value"] not in ("-", "")}

    sam2, cpi = pts["CUUR0000SAM2"], pts["CUUR0000SA0"]
    seme, semc, semd = flat(SEME), flat(SEMC), flat(SEMD)

    k0, k1 = mkey(*OOS_START), mkey(*OOS_END)
    months = [mkey(y, m) for y in range(OOS_START[0], OOS_END[0] + 1)
              for m in range(1, 13)
              if OOS_START <= (y, m) <= OOS_END]

    def drift(series):
        v0, v1 = series[k0], series[k1]
        c0, c1 = cpi[k0], cpi[k1]
        return (math.log(v1 / v0) - math.log(c1 / c0)) / T_YEARS * 100

    print("=" * 74)
    print("H1 诊断：样本外窗口 %d-%02d → %d-%02d（T=%.1f 年，相对 CPI 总指数）"
          % (OOS_START + OOS_END + (T_YEARS,)))
    print("=" * 74)
    print("各组件相对漂移 δ̂（%/年）：")
    print("  医疗护理服务 SAM2（实际，含健康保险）: %+7.3f" % drift(sam2))
    print("  健康保险   SEME（故障子项）        : %+7.3f" % drift(seme))
    print("  专业服务   SEMC                    : %+7.3f" % drift(semc))
    print("  医院及相关 SEMD                    : %+7.3f" % drift(semd))
    print("  （对照）CPI 总指数名义年化         : %+7.3f"
          % ((math.log(cpi[k1] / cpi[k0])) / T_YEARS * 100))
    print()

    # ---- Laspeyres 分解：g_SAM2(t) ≈ s_C·g_C + s_D·g_D + s_E·g_E ----
    def gs(series):
        return {k: series[k] / series[k0] for k in months if k in series}

    g_act = gs(sam2)   # 实际 SAM2 累计增长
    gC, gD, gE = gs(semc), gs(semd), gs(seme)

    # ① BLS 官方相对重要性权重（Dec 2021，医疗护理服务内部）
    sRI = {"C": 0.515, "D": 0.370, "E": 0.115}
    # ② 约束最小二乘拟合权重（s≥0，Σ=1）——粗到细网格
    def sse(wC, wD, wE):
        e = 0.0
        for k, g in g_act.items():
            pred = wC * gC.get(k, g) + wD * gD.get(k, g) + wE * gE.get(k, g)
            e += (pred - g) ** 2
        return e

    best = None
    step = 0.05
    grid = [i * step for i in range(int(1 / step) + 1)]
    for wC in grid:
        for wD in grid:
            wE = round(1.0 - wC - wD, 10)
            if wE < -1e-9:
                continue
            e = sse(wC, wD, max(wE, 0.0))
            if best is None or e < best[0]:
                best = (e, wC, wD, max(wE, 0.0))
    step = 0.005
    e0, bC, bD, bE = best
    for wC in [bC + i * step for i in range(-10, 11)]:
        for wD in [bD + i * step for i in range(-10, 11)]:
            wE = round(1.0 - wC - wD, 10)
            if wE < -1e-9 or wC < 0 or wD < 0:
                continue
            e = sse(wC, wD, wE)
            if e < best[0]:
                best = (e, wC, wD, wE)
    _, fC, fD, fE = best

    # 拟合优度（官方 RI 权重 vs 实际路径）
    def r2(wC, wD, wE):
        ss_res = sse(wC, wD, wE)
        m = sum(g_act.values()) / len(g_act)
        ss_tot = sum((g - m) ** 2 for g in g_act.values())
        return 1 - ss_res / ss_tot if ss_tot else float("nan")

    print("Laspeyres 分解（g_SAM2 = s_C·g_SEMC + s_D·g_SEMD + s_E·g_SEME）：")
    print("  官方 RI 权重（Dec 2021）: s_C=%.3f s_D=%.3f s_E=%.3f   路径拟合 R²=%.4f"
          % (sRI["C"], sRI["D"], sRI["E"], r2(sRI["C"], sRI["D"], sRI["E"])))
    print("  LS 拟合权重            : s_C=%.3f s_D=%.3f s_E=%.3f   路径拟合 R²=%.4f"
          % (fC, fD, fE, r2(fC, fD, fE)))
    print()

    # ---- 排除健康保险口径的样本外 δ̂ ----
    print("排除健康保险（ex-HI）口径的样本外 δ̂（%/年）：")
    for label, (wC, wD, wE) in [("官方 RI 权重", (sRI["C"], sRI["D"], sRI["E"])),
                                ("LS 拟合权重", (fC, fD, fE))]:
        # ex-HI 聚合：g_ex(t) = (s_C·g_C + s_D·g_D)/(s_C+s_D)
        g0 = (wC * gC[k1] + wD * gD[k1]) / (wC + wD)
        nom = math.log(g0) / T_YEARS * 100
        rel = nom - (math.log(cpi[k1] / cpi[k0])) / T_YEARS * 100
        # 健康保险的拖累（对 SAM2 相对漂移的贡献，百分点/年）
        drag = wE * (math.log(gE[k1]) - math.log(g0)) / T_YEARS * 100
        print("  [%s] ex-HI 名义年化 %+7.3f → 相对 δ̂ = %+7.3f   （HI 拖累约 %.3f pp/年）"
              % (label, nom, rel, drag))
    print()

    # ---- 核心窗口（2000-2021）污染量级核查 ----
    # 故障峰值在 2022-09 之后，核心窗口终点 2021-12 之前健康保险基本走平（2021 全年 -1.0%）。
    hi_2021 = (SEME[2021][11] / SEME[2021][0] - 1) * 100
    drag_2021 = sRI["E"] * hi_2021
    print("核心窗口污染核查：健康保险 2021 全年 %+0.1f%%，对 SAM2 2021 年水平的影响 ≈ %.2f pp，"
          % (hi_2021, drag_2021))
    print("摊到 22 年核心窗口 ≈ %.4f pp/年 —— 量级可忽略，核心窗口结论不受影响。"
          % (drag_2021 / 22))
    print()

    # ---- 附：健康保险同比轨迹（供简报引述）----
    print("健康保险（SEME）同比轨迹（7 月值，%）：")
    for y in range(2022, 2027):
        k, kprev = (y, 7), (y - 1, 7)
        if k in seme and kprev in seme:
            print("  %d-07: %+6.1f%%" % (y, (seme[k] / seme[kprev] - 1) * 100))
    peak = max(seme.items(), key=lambda kv: kv[1])
    print("  指数峰值：%d-%02d = %.3f（Dec 2021 = %.3f，随后崩塌）"
          % (peak[0][0], peak[0][1], peak[1], SEME[2021][11]))
    print("=" * 74)

if __name__ == "__main__":
    main()
