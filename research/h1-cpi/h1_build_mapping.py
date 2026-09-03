#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h1_build_mapping.py —— H1 品类映射扩展（分类 + 叶子硬检查 + 层级树生成）
================================================================================

用途：把 category_mapping.csv 从 12 个试点品类扩展到 CPI 全样本（143 候选 + 现有 12）。
单一信息源仍是本脚本生成的 category_mapping.csv（fetch/analyze 只读它，不读本脚本）。

盲分类声明（防「为结果好看而分类」）：
  本脚本的 N/R/中性 归类在 2026-09-02 完成并落盘，时间戳早于 h1_analyze.py 首次对
  这些新序列产出 δ̂（届时仓库尚未拉到新序列价格数据，归类者客观上不可能看到结果）。

书面规则（与 abundantics/H1_NR分类_书面规则_v0.1.md 一致）：
  主要成分 = 需现场提供、无法预先库存的人力劳动服务 → N；
  主要成分 = 可数字复制或全球贸易/离岸规模化生产的商品与服务 → R；
  两者混合、外生/管制驱动、或依据不明 → 中性（不强行二选一）；
  非「品类」的统计集合（大类/交叉聚合/含子项聚合层）→ 排除。

红线：
  · 老品类不动：既有 12 行 series_id/层级/状态/H1分组 原样保留（SAM2 聚合层保留 N，
    属历史口径锁定，嵌套 caveat 保留）。
  · 明细优先：新品类入 N/R 的前提 = 是 cu.item 树中的叶子（无子项），程序化强制。

用法：
  python h1_build_mapping.py            # 生成 category_mapping.csv + h1_item_hierarchy.csv + 校验报告
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES_CSV = os.path.join(HERE, "..", "abundantics", "bls_cu_item_candidates.csv")
CANDIDATES_CSV_ALT = os.path.join(HERE, "bls_cu_item_candidates.csv")
MAPPING_CSV = os.path.join(HERE, "category_mapping.csv")
HIERARCHY_CSV = os.path.join(HERE, "h1_item_hierarchy.csv")

BLIND_TS = "2026-09-02T23:30:00+08:00"  # 盲分类完成时间戳（早于任何 δ̂ 计算）

ALLOWED_GROUP = {"N", "R", "中性", "排除", "基准"}
LEVEL_MAJOR = "大类(level 0)"
LEVEL_L1 = "子类聚合(level 1)"
LEVEL_L2 = "商品组聚合(level 2)"
LEVEL_LEAF = "细项(level 3)"

# 老品类「非叶子却保留 N」的唯一例外（历史口径锁定，嵌套 caveat 保留）
LOCKED_NONLEAF = {"CUUR0000SAM2"}

# =========================================================================
# 新品类分类（137 项）：code -> (中文名, 层级, H1分组, 备注)
# =========================================================================
NEW = {
    # ---- 大类聚合（排除）----
    "SAH":   ("住房（整体）", LEVEL_MAJOR, "排除", "大类聚合，不入检验"),
    "SAM":   ("医疗保健（整体）", LEVEL_MAJOR, "排除", "大类聚合，不入检验"),
    "SAR":   ("娱乐（整体）", LEVEL_MAJOR, "排除", "大类聚合，不入检验"),
    "SAA":   ("服装（整体）", LEVEL_MAJOR, "排除", "大类聚合，不入检验"),
    "SAT":   ("交通（整体）", LEVEL_MAJOR, "排除", "大类聚合，不入检验"),
    "SAE":   ("教育与通信（整体）", LEVEL_MAJOR, "排除", "大类聚合，不入检验"),
    "SAG":   ("其他商品与服务（整体）", LEVEL_MAJOR, "排除", "大类聚合，不入检验"),
    # ---- 交叉集合（less X 类，排除）----
    "SA0E":   ("能源", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SA0L1":  ("总指数（除食品）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SA0L12": ("总指数（除食品与住房）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SA0L12E": ("总指数（除食品住房能源）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SA0L12E4": ("总指数（除食品住房能源二手车）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SA0L1E": ("总指数（除食品与能源）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SA0L2":  ("总指数（除住房）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SA0L5":  ("总指数（除医疗）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SA0LE":  ("总指数（除能源）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SAC":    ("商品（整体）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SACE":   ("能源商品", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SACL1":  ("商品（除食品）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SACL11": ("商品（除食品饮料）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SACL1E": ("商品（除食品能源）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SACL1E4": ("商品（除食品能源二手车）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SAD":    ("耐用消费品", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SAN":    ("非耐用消费品", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SAN1D":  ("国产农产食品", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SANL1":  ("非耐用消费品（除食品）", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SANL11": ("非耐用消费品（除食品饮料）", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SANL113": ("非耐用消费品（除食品饮料服装）", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SANL13": ("非耐用消费品（除食品服装）", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SAS":    ("服务（整体）", LEVEL_L1, "排除", "交叉集合，不入检验"),
    "SAS24":  ("公用事业与公共交通", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SAS2RS": ("住房租金（rent of shelter）", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SAS367": ("其他服务", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SAS4":   ("交通服务", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SASL2RS": ("服务（除住房租金）", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SASL5":  ("服务（除医疗服务）", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SASLE":  ("服务（除能源服务）", LEVEL_L2, "排除", "交叉集合，不入检验"),
    "SATCLTB": ("交通商品（除汽车燃油）", LEVEL_L2, "排除", "交叉集合，不入检验"),
    # ---- 子类聚合（排除）----
    "SA311": ("服装（除鞋类）", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SAA1":  ("男装及童男装", LEVEL_L1, "排除", "聚合层，不入检验"),
    "SAA2":  ("女装及童女装", LEVEL_L1, "排除", "聚合层，不入检验"),
    "SAE1":  ("教育", LEVEL_L1, "排除", "聚合层，不入检验"),
    "SAE2":  ("通信", LEVEL_L1, "排除", "聚合层，不入检验"),
    "SAEC":  ("教育与通信商品", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SAES":  ("教育与通信服务", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SAF1":  ("食品", LEVEL_L1, "排除", "聚合层，不入检验"),
    "SAG1":  ("个人护理", LEVEL_L1, "排除", "聚合层，不入检验"),
    "SAGC":  ("其他商品", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SAGS":  ("其他个人服务", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SAH1":  ("住所 Shelter", LEVEL_L1, "排除", "聚合层，不入检验"),
    "SAH2":  ("燃料与公用事业", LEVEL_L1, "排除", "聚合层，不入检验"),
    "SAH3":  ("家居陈设与运营", LEVEL_L1, "排除", "聚合层，不入检验"),
    "SAH31": ("家居陈设与用品", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SAM1":  ("医疗保健商品", LEVEL_L1, "排除", "聚合层，不入检验"),
    "SARC":  ("娱乐商品", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SARS":  ("娱乐服务", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SAT1":  ("私人交通", LEVEL_L1, "排除", "聚合层，不入检验"),
    "SAE21": ("信息与信息处理", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SAF11": ("居家食品", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SAH21": ("家庭能源", LEVEL_L2, "排除", "聚合层，不入检验"),
    # ---- 商品组聚合（含子项，排除）----
    "SEAE": ("鞋类", LEVEL_L2, "排除", "聚合层；含子项 SEAE01/02/03，不入检验"),
    "SEAG": ("珠宝与手表", LEVEL_L2, "排除", "聚合层；含子项 SEAG01/02，不入检验"),
    "SEEEC": ("信息技术商品", LEVEL_L2, "排除", "聚合层；含子项，不入检验"),
    "SERA": ("影音（整体）", LEVEL_L2, "排除", "聚合层；含子项 SERA01-06，不入检验"),
    "SERAC": ("影音产品", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SERAS": ("影音服务", LEVEL_L2, "排除", "聚合层，不入检验"),
    "SERB": ("宠物及相关（整体）", LEVEL_L2, "排除", "聚合层；含子项 SERB01/02，不入检验"),
    "SERC": ("体育用品（整体）", LEVEL_L2, "排除", "聚合层；含子项 SERC01/02，不入检验"),
    "SERD": ("摄影（整体）", LEVEL_L2, "排除", "聚合层；含子项 SERD01/02，不入检验"),
    "SERE": ("其他娱乐商品（整体）", LEVEL_L2, "排除", "聚合层；含子项 SERE01/02/03，不入检验"),
    "SERF": ("其他娱乐服务（整体）", LEVEL_L2, "排除", "聚合层；含子项 SERF01/02/03，不入检验"),
    "SERG": ("娱乐读物（整体）", LEVEL_L2, "排除", "聚合层；含子项 SERG01/02，不入检验"),
    "SETG": ("公共交通", LEVEL_L2, "排除", "聚合层；含子项 SETG01/02/03，不入检验"),
    "SEEB": ("学费/其他学杂费/托儿", LEVEL_L2, "排除", "聚合层；含子项 SEEB01/02/03，不入检验"),
    "SEEE": ("信息技术硬件与服务", LEVEL_L2, "排除", "聚合层；含子项 SEEE01/02/03，不入检验"),
    "SEHC": ("自有住房等价租金（整体）", LEVEL_L2, "排除", "聚合层；含子项 SEHC01/02，不入检验"),
    "SEMC": ("专业医疗服务", LEVEL_L2, "排除", "聚合层；含子项 SEMC01医生/SEMC02牙科，不入检验；诊断序列归档"),
    "SEMD": ("医院及相关服务", LEVEL_L2, "排除", "聚合层；含子项 SEMD01，不入检验；诊断序列归档"),
    "SEME": ("健康保险", LEVEL_L2, "排除", "聚合层（或含 SEME01）；诊断序列归档，供 ex-HI 口径"),
    "SEMF": ("药品", LEVEL_L2, "排除", "聚合层；含子项 SEMF01处方/SEMF02非处方，不入检验"),
    "SETA": ("新车与二手车", LEVEL_L2, "排除", "聚合层；含子项 SETA01/02，不入检验"),
    "SETB": ("汽车燃油", LEVEL_L2, "排除", "聚合层；含子项 SETB01汽油/SETB02其他燃油，不入检验"),
    "SEEC": ("邮政与快递服务", LEVEL_L2, "排除", "聚合层；含子项 SEEC01邮政/SEEC02快递，不入检验"),
    "SEFV": ("外食", LEVEL_L2, "排除", "聚合层；含子项 SEFV01-04（堂食/快餐等），不入检验"),
    "SEHB": ("外出住宿", LEVEL_L2, "排除", "聚合层；含子项 SEHB01/02，不入检验"),
    "SEHP": ("家庭运营服务", LEVEL_L2, "排除", "聚合层；含子项，不入检验"),
    # ---- 中性（不定向/外生驱动）----
    "SEGA":  ("烟草及吸烟用品", LEVEL_LEAF, "中性", "税驱动，外生；不定向"),
    "SAF116": ("酒精饮料", LEVEL_LEAF, "中性", "税驱动；⚠️ item_code 待 Action 核验 cu.item（可能为 Other food at home）"),
    "SEAG01": ("手表", LEVEL_LEAF, "中性", "⚠️ 可贸易制成品 vs 奢侈品位置性冲突，不定向"),
    "SEAG02": ("珠宝", LEVEL_LEAF, "中性", "⚠️ 可贸易 vs 奢侈品位置性冲突，不定向"),
    "SEGB": ("个人护理用品", LEVEL_LEAF, "中性", "可贸易制成品但品牌驱动、自动化降价信号弱，不定向"),
    "SEGE": ("杂项个人商品", LEVEL_LEAF, "中性", "⚠️ 文具/箱包等混合，不定向"),
    "SEHG": ("水、排污与垃圾处理服务", LEVEL_LEAF, "中性", "受管制公用事业，外生定价"),
    "SEHN": ("家居清洁用品", LEVEL_LEAF, "中性", "可贸易但属消费必需品、弱信号，不定向"),
    "SEMG": ("医疗设备与耗材", LEVEL_LEAF, "中性", "⚠️ 可贸易制成品 vs 专利稀缺冲突，不定向"),
    "SERA02": ("有线/卫星/流媒体电视服务", LEVEL_LEAF, "中性", "⚠️ 数字分发（偏R）但垄断定价、价格长期上行（偏N），不定向"),
    "SERB01": ("宠物及宠物用品", LEVEL_LEAF, "中性", "⚠️ 宠物食品/用品混合，不定向"),
    "SERD02": ("摄影师与照片冲洗", LEVEL_LEAF, "中性", "⚠️ 人力服务（偏N）与数字化（偏R）混合，不定向"),
    "SERG01": ("报纸与杂志", LEVEL_LEAF, "中性", "⚠️ 信息商品（偏R）但纸媒成本上行（偏N），不定向"),
    "SETF":  ("机动车税费", LEVEL_LEAF, "中性", "税/规费驱动，外生"),
    "SETG01": ("机票", LEVEL_LEAF, "中性", "⚠️ 自动化生产率高（偏R）但燃油主导且属服务（偏N），不定向"),
    "SETG03": ("市内交通", LEVEL_LEAF, "中性", "⚠️ 公交/地铁（偏N）与网约车平台（偏R）混合，不定向"),
    # ---- N（难自动化·现场人力服务）----
    "SEGC":  ("个人护理服务", LEVEL_LEAF, "N", "现场人力服务（理发/美容），无法库存；⚠️ 叶子待 cu.item 核验"),
    "SEGD":  ("杂项个人服务", LEVEL_LEAF, "N", "现场人力服务（法律/殡葬/金融中介等）"),
    "SEHA":  ("主要住所租金", LEVEL_LEAF, "N", "住房服务（租户侧），位置性；OER SEHC01 的姊妹口径"),
    "SEHD":  ("租户与家庭保险", LEVEL_LEAF, "N", "保险服务；⚠️ 叶子待 cu.item 核验"),
    "SERB02": ("宠物服务（含兽医）", LEVEL_LEAF, "N", "现场人力照护服务（兽医/寄养/美容）"),
    "SERF01": ("俱乐部会费/参与费", LEVEL_LEAF, "N", "现场人力/场地服务"),
    "SERF02": ("门票", LEVEL_LEAF, "N", "现场演出/赛事，人力与场地密集"),
    "SERF03": ("课程与指导费", LEVEL_LEAF, "N", "现场人力教学服务"),
    "SETD":  ("机动车维修保养", LEVEL_LEAF, "N", "现场人力维修服务"),
    "SETE":  ("机动车保险", LEVEL_LEAF, "N", "保险服务"),
    "SETG02": ("其他城际交通", LEVEL_LEAF, "N", "城际巴士/火车/船运，人力服务"),
    # ---- R（可复制·可贸易制成品）----
    "SEAF":  ("婴幼儿服装", LEVEL_LEAF, "R", "可贸易制成品（服装）"),
    "SEAA":  ("男装", LEVEL_LEAF, "R", "可贸易制成品（服装）"),
    "SEAB":  ("童男装", LEVEL_LEAF, "R", "可贸易制成品（服装）"),
    "SEAC":  ("女装", LEVEL_LEAF, "R", "可贸易制成品（服装）"),
    "SEAD":  ("童女装", LEVEL_LEAF, "R", "可贸易制成品（服装）"),
    "SEAE01": ("男鞋", LEVEL_LEAF, "R", "可贸易制成品（鞋类）"),
    "SEAE02": ("童鞋", LEVEL_LEAF, "R", "可贸易制成品（鞋类）"),
    "SEAE03": ("女鞋", LEVEL_LEAF, "R", "可贸易制成品（鞋类）"),
    "SEHH": ("窗饰与地面覆盖物", LEVEL_LEAF, "R", "可贸易制成品（家居耐用）"),
    "SEHJ": ("家具与寝具", LEVEL_LEAF, "R", "可贸易制成品（家居耐用）"),
    "SEHK": ("家电", LEVEL_LEAF, "R", "可贸易制成品（耐用电子）；⚠️ 叶子待 cu.item 核验"),
    "SEHL": ("其他家用设备与陈设", LEVEL_LEAF, "R", "可贸易制成品（家居耐用）"),
    "SEHM": ("工具/五金/户外装备", LEVEL_LEAF, "R", "可贸易制成品"),
    "SERA03": ("其他视频设备", LEVEL_LEAF, "R", "电子硬件，可贸易"),
    "SERA04": ("视频购买/订阅/租赁", LEVEL_LEAF, "R", "数字可复制"),
    "SERA05": ("音频设备", LEVEL_LEAF, "R", "电子硬件，可贸易"),
    "SERA06": ("录制音乐与订阅", LEVEL_LEAF, "R", "数字可复制"),
    "SERC01": ("运动车辆（含自行车）", LEVEL_LEAF, "R", "可贸易制成品"),
    "SERC02": ("运动装备", LEVEL_LEAF, "R", "可贸易制成品"),
    "SERD01": ("摄影器材", LEVEL_LEAF, "R", "电子硬件，可贸易"),
    "SERE02": ("缝纫机/布料/辅料", LEVEL_LEAF, "R", "可贸易制成品"),
    "SERE03": ("乐器及配件", LEVEL_LEAF, "R", "可贸易制成品"),
    "SERG02": ("娱乐书籍", LEVEL_LEAF, "R", "⚠️ 可复制信息商品（同软件逻辑），但定价偏版权，置信度中"),
    "SETC":  ("机动车零配件", LEVEL_LEAF, "R", "可贸易制成品"),
}

# =========================================================================
# 层级树（parent_code -> item_code）。v0 基于 BLS CPI 相对重要性结构，待 Action 拉取
# cu.item 权威核验。PARENT 仅作文档用途，叶子硬检查用 HAS_CHILDREN（下方）判定。
# =========================================================================
PARENT = {
    # 大类（无父）
    "SA0": "", "SAF": "", "SAH": "", "SAM": "", "SAR": "", "SAA": "", "SAT": "", "SAE": "", "SAG": "",
    # 交叉集合（顶层特殊集合，无父）
    "SA0E": "", "SA0L1": "", "SA0L12": "", "SA0L12E": "", "SA0L12E4": "", "SA0L1E": "",
    "SA0L2": "", "SA0L5": "", "SA0LE": "", "SAC": "", "SACE": "", "SACL1": "", "SACL11": "",
    "SACL1E": "", "SACL1E4": "", "SAD": "", "SAN": "", "SAN1D": "", "SANL1": "", "SANL11": "",
    "SANL113": "", "SANL13": "", "SAS": "", "SAS24": "", "SAS2RS": "", "SAS367": "", "SAS4": "",
    "SASL2RS": "", "SASL5": "", "SASLE": "", "SATCLTB": "",
    # 食品饮料
    "SAF1": "SAF", "SAF11": "SAF1", "SAF116": "SAF", "SEFV": "SAF1",
    # 住房
    "SAH1": "SAH", "SAH2": "SAH", "SAH3": "SAH", "SAH21": "SAH2", "SAH31": "SAH3",
    "SEHA": "SAH1", "SEHB": "SAH1", "SEHC": "SAH1", "SEHC01": "SEHC",
    "SEHD": "SAH1", "SEHG": "SAH2",
    "SEHH": "SAH31", "SEHJ": "SAH31", "SEHK": "SAH31", "SEHL": "SAH31", "SEHM": "SAH31",
    "SEHN": "SAH31", "SEHP": "SAH3",
    # 医疗
    "SAM1": "SAM", "SAM2": "SAM",
    "SEMC": "SAM2", "SEMD": "SAM2", "SEMD01": "SEMD", "SEME": "SAM2", "SEMF": "SAM1", "SEMG": "SAM1",
    # 娱乐
    "SARC": "SAR", "SARS": "SAR",
    "SERA": "SAR", "SERAC": "SAR", "SERAS": "SAR", "SERB": "SAR", "SERC": "SAR", "SERD": "SAR",
    "SERE": "SAR", "SERF": "SAR", "SERG": "SAR",
    "SERA01": "SERA", "SERA02": "SERA", "SERA03": "SERA", "SERA04": "SERA", "SERA05": "SERA", "SERA06": "SERA",
    "SERB01": "SERB", "SERB02": "SERB",
    "SERC01": "SERC", "SERC02": "SERC",
    "SERD01": "SERD", "SERD02": "SERD",
    "SERE01": "SERE", "SERE02": "SERE", "SERE03": "SERE",
    "SERF01": "SERF", "SERF02": "SERF", "SERF03": "SERF",
    "SERG01": "SERG", "SERG02": "SERG",
    # 服装
    "SAA1": "SAA", "SAA2": "SAA", "SA311": "SAA",
    "SEAA": "SAA1", "SEAB": "SAA1", "SEAC": "SAA2", "SEAD": "SAA2", "SEAF": "SAA",
    "SEAE": "SAA", "SEAE01": "SEAE", "SEAE02": "SEAE", "SEAE03": "SEAE",
    "SEAG": "SAA", "SEAG01": "SEAG", "SEAG02": "SEAG",
    # 交通
    "SAT1": "SAT", "SETG": "SAT",
    "SETA": "SAT1", "SETB": "SAT1", "SETC": "SAT1", "SETD": "SAT1", "SETE": "SAT1", "SETF": "SAT1",
    "SETG01": "SETG", "SETG02": "SETG", "SETG03": "SETG",
    # 教育与通信
    "SAE1": "SAE", "SAE2": "SAE", "SAEC": "SAE", "SAES": "SAE", "SAE21": "SAE2",
    "SEEA": "SAE1", "SEEB": "SAE1", "SEEB01": "SEEB", "SEEB03": "SEEB",
    "SEEC": "SAES", "SEEEC": "SAEC", "SEEE": "SAE21", "SEEE02": "SEEE", "SEED03": "SAE21",
    # 其他
    "SAG1": "SAG", "SAGC": "SAG", "SAGS": "SAG",
    "SEGA": "SAG", "SEGB": "SAG1", "SEGC": "SAG1", "SEGD": "SAGS", "SEGE": "SAGC",
}

# 有子项的品类集合（非叶子）。用于叶子硬检查：N/R 项不得在此集合内。
# 涵盖：全部排除聚合（含交叉集合）+ 基准 SA0 + 中性聚合 SAF + 老品类聚合 SAM2。
HAS_CHILDREN = {
    # 大类
    "SA0", "SAF", "SAH", "SAM", "SAR", "SAA", "SAT", "SAE", "SAG",
    # 交叉集合
    "SA0E", "SA0L1", "SA0L12", "SA0L12E", "SA0L12E4", "SA0L1E", "SA0L2", "SA0L5", "SA0LE",
    "SAC", "SACE", "SACL1", "SACL11", "SACL1E", "SACL1E4", "SAD", "SAN", "SAN1D", "SANL1",
    "SANL11", "SANL113", "SANL13", "SAS", "SAS24", "SAS2RS", "SAS367", "SAS4", "SASL2RS",
    "SASL5", "SASLE", "SATCLTB",
    # 子类聚合
    "SA311", "SAA1", "SAA2", "SAE1", "SAE2", "SAEC", "SAES", "SAF1", "SAG1", "SAGC", "SAGS",
    "SAH1", "SAH2", "SAH3", "SAH31", "SAM1", "SAM2", "SARC", "SARS", "SAT1", "SAE21", "SAF11", "SAH21",
    # 商品组聚合
    "SEAE", "SEAG", "SEEEC", "SERA", "SERAC", "SERAS", "SERB", "SERC", "SERD", "SERE", "SERF",
    "SERG", "SETG", "SEEB", "SEEE", "SEHC", "SEMC", "SEMD", "SEME", "SEMF", "SETA", "SETB",
    "SEEC", "SEFV", "SEHB", "SEHP",
}

# 老品类锁定清单：series_id -> 期望的 (状态, H1分组, 层级)。用于断言老品类不动。
LOCKED_EXPECT = {
    "CUUR0000SEMD01": ("已核实", "N", "细项(level 3)"),
    "CUUR0000SEEB01": ("已核实", "N", "细项(level 3)"),
    "CUUR0000SAM2":   ("已核实", "N", "子类聚合(level 1)"),
    "CUUR0000SEEB03": ("已核实", "N", "细项(level 3)"),
    "CUUR0000SEHC01": ("已核实", "N", "细项(level 3)"),
    "CUUR0000SAF":    ("已核实", "中性", "大类(level 0)"),
    "CUUR0000SEED03": ("已核实", "R", "细项(level 3)"),
    "CUUR0000SEEE02": ("已核实", "R", "细项(level 3)"),
    "CUUR0000SERE01": ("已核实", "R", "细项(level 3)"),
    "CUUR0000SERA01": ("已核实", "R", "细项(level 3)"),
    "CUUR0000SA0":    ("已核实", "基准", "总指数(level 0)"),
    "CUUR0000SEEA":   ("降级", "排除", "商品组聚合(level 2)"),
}


def load_candidates():
    path = CANDIDATES_CSV if os.path.exists(CANDIDATES_CSV) else CANDIDATES_CSV_ALT
    if not os.path.exists(path):
        raise FileNotFoundError(f"候选清单不存在：{CANDIDATES_CSV}")
    m = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            code = (r.get("item_code") or "").strip()
            name = (r.get("item_name") or "").strip()
            if code:
                m[code] = name
    return m


def load_existing():
    """读取现有 category_mapping.csv 的 12 行，原样保留（含 BOM/引用处理由写回时统一）。"""
    rows = []
    if os.path.exists(MAPPING_CSV):
        with open(MAPPING_CSV, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if not (r.get("series_id") or "").strip():
                    continue
                rows.append(r)
    return rows


def main():
    candidates = load_candidates()
    existing = load_existing()

    existing_codes = set()  # item_code（series_id 去掉 CUUR0000 前缀）
    for r in existing:
        sid = r["series_id"].strip()
        existing_codes.add(sid.replace("CUUR0000", ""))

    # ---- 校验 1：候选清单完整性（每个候选 code 要么在老品类，要么在 NEW）----
    new_codes = set(NEW.keys())
    missing = [c for c in candidates if c not in existing_codes and c not in new_codes]
    extra = [c for c in new_codes if c not in candidates]
    if missing:
        print(f"[FAIL] 候选清单中有 {len(missing)} 项未分类：{missing}", file=sys.stderr)
        return 1
    if extra:
        print(f"[WARN] NEW 中有 {len(extra)} 项不在候选清单（可能来自现有映射）：{extra}", file=sys.stderr)

    # ---- 校验 2：老品类锁定 ----
    locked_bad = []
    for r in existing:
        sid = r["series_id"].strip()
        if sid in LOCKED_EXPECT:
            exp = LOCKED_EXPECT[sid]
            got = ((r.get("状态") or "").strip(), (r.get("H1分组") or "").strip(), (r.get("层级") or "").strip())
            if got != exp:
                locked_bad.append((sid, exp, got))
    if locked_bad:
        print(f"[FAIL] 老品类被改动：{locked_bad}", file=sys.stderr)
        return 1

    # ---- 校验 3：叶子硬检查（N/R 项不得有子项；SAM2 为锁定例外）----
    leaf_bad = []
    for code, (zh, level, group, note) in NEW.items():
        if group in ("N", "R") and code in HAS_CHILDREN:
            leaf_bad.append((code, zh))
    for r in existing:
        sid = r["series_id"].strip()
        code = sid.replace("CUUR0000", "")
        grp = (r.get("H1分组") or "").strip()
        if grp in ("N", "R") and code in HAS_CHILDREN and sid not in LOCKED_NONLEAF:
            leaf_bad.append((sid, r.get("中文品类名")))
    if leaf_bad:
        print(f"[FAIL] N/R 项存在非叶子（嵌套）：{leaf_bad}", file=sys.stderr)
        return 1

    # ---- 校验 4：分组取值 + series_id 格式（item_code 为 3–8 位大写字母数字）----
    import re
    fmt_bad = []
    for code, (zh, level, group, note) in NEW.items():
        if group not in ALLOWED_GROUP:
            fmt_bad.append((code, group))
        if not re.fullmatch(r"[A-Z0-9]{3,8}", code):
            fmt_bad.append((code, "series_id 格式"))
    if fmt_bad:
        print(f"[FAIL] 分组/格式非法：{fmt_bad}", file=sys.stderr)
        return 1

    # ---- 写 category_mapping.csv（老 12 行原样在前，新行按候选顺序在后）----
    cols = ["中文品类名", "BLS_item_title", "series_id", "层级", "状态", "数据起始年份", "数据起始年份_口径", "备注", "H1分组"]
    out_rows = []
    for r in existing:
        # 老品类「数据起始年份」均为真实 BLS begin_year（历史口径锁定，与新版窗口回填口径不同）
        r["数据起始年份_口径"] = "真实begin_year"
        out_rows.append(r)
    for code in candidates:
        if code in existing_codes:
            continue
        zh, level, group, note = NEW[code]
        out_rows.append({
            "中文品类名": zh,
            "BLS_item_title": candidates[code],
            "series_id": "CUUR0000" + code,
            "层级": level,
            "状态": "待核实",
            "数据起始年份": "",
            "数据起始年份_口径": "",  # 待 h1_verify_series.py 回填（新品类必为「窗口最早观测年份」）
            "备注": note,
            "H1分组": group,
        })

    with open(MAPPING_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in out_rows:
            w.writerow({c: (r.get(c) or "") for c in cols})

    # ---- 写 h1_item_hierarchy.csv（v0，待 Action 核验）----
    with open(HIERARCHY_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["parent_code", "item_code", "item_name", "has_children", "display_level", "source_note"])
        all_codes = list(candidates.keys()) + [c for c in existing_codes if c not in candidates]
        for code in sorted(set(all_codes)):
            name = candidates.get(code, "")
            parent = PARENT.get(code, "?")
            has_children = "1" if code in HAS_CHILDREN else "0"
            lvl = "0" if parent == "" else ("1" if parent in ("SAF", "SAH", "SAM", "SAR", "SAA", "SAT", "SAE", "SAG") else "2/3")
            w.writerow([parent, code, name, has_children, lvl, "v0 基于BLS结构推断，待Action拉取cu.item核验"])

    # ---- 报告 ----
    def grp_count(g):
        return sum(1 for r in out_rows if (r.get("H1分组") or "").strip() == g)

    print("=" * 60)
    print("H1 品类映射扩展完成（盲分类 " + BLIND_TS + "）")
    print("=" * 60)
    print(f"总行数：{len(out_rows)}（老 {len(existing)} + 新 {len(out_rows) - len(existing)}）")
    print(f"  基准：{grp_count('基准')}   N：{grp_count('N')}   R：{grp_count('R')}   中性：{grp_count('中性')}   排除：{grp_count('排除')}")
    print(f"  检验集：N={grp_count('N')}  R={grp_count('R')}（合计 {grp_count('N') + grp_count('R')}）")
    amb = [(code, NEW[code][0], NEW[code][3]) for code in candidates
           if code in NEW and "⚠️" in NEW[code][3]]
    print(f"  模糊项（⚠️ 待复核，共 {len(amb)}）：")
    for code, zh, note in amb:
        print(f"    - {code} {zh}：{note}")
    print("  新品类状态均为「待核实」，待 Action 拉取 cu.series 验证 seriesID 存在性后翻「已核实」。")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
