# -*- coding: utf-8 -*-
"""
说明书D 腿二：构建 ce_ucc_crosswalk.csv（65 CPI品类 -> CE UCC码）

编码依据（权威、非拍脑袋）：
  BLS《CPI Handbook of Methods》附录5 —— CE UCC to CPI ELI Concordance
  URL: https://www.bls.gov/cpi/additional-resources/ce-cpi-concordance.htm
  口径：2024 年度支出权重、自 2026-01 起用于指数计算的 CPI 项目结构。
  （原文注：SEME02/SEME03 系列不在该表，通过插值创建权重——与本 65 品类无关。）

层级桥接：CPI item strata（本表 series_id）--(1对多)--> CPI ELI --(1对多)--> CE UCC
  - ELI 码前缀即 CPI item strata 前缀（如 SEAA->AA, SEHJ->HJ, SERA->RA...）
  - 每个 UCC 标注 CE 来源：I=Interview Survey(MTBI 文件), D=Diary Survey(EXPD 文件)
  - 标注 (1) 的 UCC 为"CPI 调整因子拆分码"（一个 CE UCC 被 CPI 分配到多个 ELI）

本脚本只产出映射表，不下载 Diary 数据、不跑恩格尔回归。
"""
import csv
from collections import Counter

# ---------------------------------------------------------------------------
# 一、ELI -> UCC 对照（自 BLS concordance 固化，逐条可溯源）
#    格式：ELI码 -> (ELI标题, [(UCC, 来源I/D), ...])
# ---------------------------------------------------------------------------
ELI_UCC = {
    # ---- 男装 AA ----
    'AA011': ('Mens Suits', [('360110', 'I')]),
    'AA012': ('Mens Sportcoats/Tailored Jackets', [('360120', 'D')]),
    'AA013': ('Mens Coats And Jackets', [('360210', 'D')]),
    'AA021': ('Mens Underwear,Hosiery,Nightwear', [('360319', 'D')]),
    'AA022': ('Mens Accessories', [('360330', 'D')]),
    'AA033': ('Mens Sweaters/Shirts/Vests', [('360420', 'D')]),
    'AA041': ('Mens Pants And Shorts', [('360513', 'D')]),
    'AA090': ('Unsampled Mens Apparel', [('360901', 'D'), ('360902', 'D')]),
    # ---- 女装 AC ----
    'AC011': ('Womens Coats And Jackets', [('380110', 'D')]),
    'AC021': ('Womens Dresses', [('380210', 'D')]),
    'AC031': ('Womens Tops', [('380319', 'D')]),
    'AC032': ('Womens Skirts/Pants/Shorts', [('380339', 'D')]),
    'AC033': ('Womens Suits', [('380510', 'D')]),
    'AC041': ('Womens Undergarments/Nightwear', [('380429', 'D')]),
    'AC042': ('Womens Hosiery And Accessories', [('380430', 'D'), ('380901', 'D')]),
    'AC090': ('Unsampled Womens Apparel', [('380909', 'D')]),
    # ---- 童男装 AB ----
    'AB011': ('Boys Coats And Jackets', [('370110', 'D')]),
    'AB012': ('Boys Sweaters/Shirts/Vests', [('370125', 'D')]),
    'AB013': ('Boys Underwear/Nightwear/Hosiery', [('370219', 'D'), ('370220', 'D')]),
    'AB014': ('Boys Suits/Sport Coats/Pants', [('370319', 'D')]),
    'AB090': ('Unsampled Boys Apparel', [('370902', 'D'), ('370903', 'D')]),
    # ---- 童女装 AD ----
    'AD011': ('Girls Coats And Jackets', [('390110', 'D')]),
    'AD012': ('Girls Dresses/Suits', [('390120', 'D')]),
    'AD013': ('Girls Shirts/Blouses/Sweaters', [('390210', 'D')]),
    'AD014': ('Girls Skirts/Pants/Shorts', [('390223', 'D')]),
    'AD016': ('Girls Underwear/Nightwear/Hosiery', [('390319', 'D'), ('390322', 'D')]),
    'AD090': ('Unsampled Girls Apparel', [('390901', 'D'), ('390902', 'D')]),
    # ---- 婴幼儿服装 AF ----
    'AF011': ('Infants/Toddlers Outer/Play/Dress/Sleep', [('410119', 'D')]),
    'AF012': ('Infants Underwear/Diapers', [('410130', 'D')]),
    # ---- 鞋 AE ----
    'AE011': ('Mens Footwear', [('400110', 'D')]),
    'AE021': ('Boys Footwear', [('400210', 'D')]),
    'AE022': ('Girls Footwear', [('400220', 'D')]),
    'AE031': ('Womens Footwear', [('400310', 'D')]),
    # ---- 家纺 HH ----
    'HH011': ('Floor Coverings', [('320111', 'I'), ('320624', 'I'), ('320625', 'I')]),
    'HH021': ('Curtains And Drapes', [('280210', 'I')]),
    'HH022': ('Shades And Blinds', [('320120', 'I')]),
    'HH031': ('Bathroom Linens', [('280110', 'D')]),
    'HH032': ('Bedroom Linens', [('280120', 'D')]),
    'HH033': ('Kitchen/Dining Linens', [('280140', 'D')]),
    # ---- 家具 HJ ----
    'HJ011': ('Mattresses/Foundations', [('290110', 'I')]),
    'HJ012': ('Other Bedroom Furniture', [('290120', 'I')]),
    'HJ021': ('Sofas/Slipcovers', [('290210', 'I'), ('280220', 'I')]),
    'HJ022': ('Living Room Chairs', [('290310', 'I')]),
    'HJ023': ('Living Room Tables', [('290320', 'I')]),
    'HJ024': ('Kitchen/Dining Room Furniture', [('290410', 'I')]),
    'HJ031': ('Infants Furniture', [('290420', 'I')]),
    'HJ032': ('Outdoor Furniture', [('290430', 'I')]),
    'HJ033': ('Occasional Furniture', [('290440', 'I')]),
    # ---- 家电 HK ----
    'HK011': ('Refrigerators/Freezers', [('300111', 'I'), ('300112', 'I')]),
    'HK012': ('Washers/Dryers', [('300216', 'I'), ('300217', 'I')]),
    'HK013': ('Ranges/Cooktops', [('300311', 'I'), ('300312', 'I')]),
    'HK014': ('Microwave Ovens', [('300321', 'I'), ('300322', 'I')]),
    'HK021': ('Floor Cleaning Equipment', [('320511', 'I')]),
    'HK022': ('Small Electric Kitchen Appliances', [('320521', 'I')]),
    'HK023': ('Other Electric Appliances', [('300411', 'I'), ('300412', 'I'), ('320522', 'I'), ('690244', 'I'), ('690245', 'I')]),
    # ---- 灯具/餐具 HL ----
    'HL011': ('Lamps/Lighting Fixtures', [('320221', 'D')]),
    'HL012': ('Clocks/Decor Items', [('320233', 'D')]),
    'HL031': ('Dishes', [('320345', 'D')]),
    'HL032': ('Flatware', [('320330', 'D')]),
    'HL041': ('Nonelectric Cookingware', [('320370', 'D')]),
    'HL042': ('Tableware/Non-Elec Kitware', [('320380', 'D')]),
    # ---- 工具/户外 HM ----
    'HM012': ('Power Tools', [('320420', 'I')]),
    'HM013': ('Other Hardware', [('320430', 'D'), ('320611', 'I'), ('320612', 'I')]),
    'HM014': ('Hand Tools', [('320902', 'D')]),
    'HM021': ('Lawn/Garden/Outdoor Equip', [('320150', 'D'), ('320410', 'D')]),
    'HM022': ('Lawn/Garden Materials', [('330511', 'I'), ('330610', 'D')]),
    # ---- 通信/电子 ----
    'ED031': ('Wireless Phone Service', [('270102', 'I')]),  # (1) 拆分
    'EE021': ('Computer Software', [('310400', 'I'), ('690117', 'I'), ('690119', 'I')]),
    'RA011': ('Televisions', [('310140', 'I'), ('690320', 'I')]),
    'RA031': ('Other Video Equipment', [('310210', 'I'), ('310315', 'D'), ('310334', 'I'), ('310335', 'D'), ('690330', 'I'), ('690350', 'I')]),
    'RA041': ('Prerecorded Video', [('310220', 'D'), ('310242', 'D')]),
    'RA042': ('Rental Of Video', [('310241', 'D'), ('620912', 'D'), ('620918', 'I')]),
    'RA051': ('Audio Equipment', [('310312', 'D'), ('310314', 'I'), ('310316', 'I'), ('310331', 'D'), ('310332', 'D'), ('690340', 'I')]),
    'RA061': ('Music Media/Audio Content', [('270311', 'I'), ('310340', 'I'), ('310350', 'I')]),
    # ---- 娱乐 ----
    'RE011': ('Toys/Games/Hobbies', [('610110', 'D'), ('610120', 'I')]),
    'RC011': ('Outboard Motors/Powered Sports Vehicles', [('600110', 'I'), ('600132', 'I'), ('600133', 'I'), ('600142', 'I'), ('860701', 'I')]),
    # 注：600151(Purch Motor Home/Camper) 主体属机动车 TA090(房车/露营车)，已剔除，
    #     不纳入运动车辆 SERC01 —— 见 ce_ucc_crosswalk_说明.md 边界处理
    'RC012': ('Unpowered Boats/Trailers', [('600121', 'I'), ('600122', 'I'), ('600133', 'I')]),
    'RC013': ('Bicycles', [('600310', 'I')]),
    'RC021': ('General Sports Equipment', [('600210', 'I'), ('600430', 'I'), ('600902', 'I')]),
    'RC022': ('Water Sports Equipment', [('600901', 'I')]),
    'RC023': ('Hunting/Fishing/Camping Gear', [('600410', 'D'), ('600420', 'D')]),
    'RD011': ('Film/Photographic Supplies', [('610210', 'I'), ('610220', 'D')]),
    'RD012': ('Photographic Equipment', [('610230', 'I')]),
    'RE021': ('Sewing Items', [('320512', 'I'), ('420115', 'I')]),
    'RE031': ('Music Instruments/Accessories', [('610130', 'I')]),
    'RG022': ('Books', [('590230', 'I')]),
    # ---- 服务 ----
    'MD011': ('Hospital Rooms/Services', [('570111', 'I'), ('570230', 'D')]),
    'EB011': ('College Tuition', [('670110', 'I')]),
    'EB031': ('Day Care/Preschool', [('670320', 'I')]),
    'MC011': ('Physicians Services', [('560110', 'I')]),
    'MC021': ('Dental Services', [('560210', 'I')]),
    'MC031': ('Eyecare', [('550110', 'I'), ('560310', 'I')]),
    'MC041': ('Other Medical Professionals', [('550340', 'I'), ('560330', 'I'), ('560420', 'I')]),
    'HC011': ('Owners Equivalent Rent', [('910104', 'I')]),
    'HA011': ('Rent Of Dwelling', [('210110', 'I'), ('800710', 'I')]),
    'HD011': ('Tenants/Household Insurance', [('220121', 'I'), ('350110', 'I')]),
    'RB021': ('Pet Services', [('620410', 'I')]),
    'RB022': ('Vet Services', [('620420', 'D')]),
    'RF011': ('Club Dues/Fees', [('620111', 'I'), ('620115', 'I'), ('620121', 'D'), ('620122', 'I'), ('620930', 'D'), ('680905', 'I')]),
    'RF021': ('Admissions Movies/Theater', [('620212', 'I'), ('620213', 'I'), ('620215', 'I'), ('620216', 'I'), ('620510', 'D')]),
    'RF022': ('Admissions Sporting Events', [('620221', 'I'), ('620222', 'I')]),
    'RF031': ('Fees For Lessons', [('620310', 'I')]),
    'TE011': ('Motor Vehicle Insurance', [('500110', 'I')]),
    'TG021': ('Intercity Bus', [('530210', 'I')]),
    'TG022': ('Intercity Train', [('530510', 'I')]),
    'TG023': ('Ship/Cruise', [('530901', 'I')]),
    'GC011': ('Personal Care Services', [('650310', 'I')]),
    'GD011': ('Legal Fees', [('680110', 'I')]),
    'GD021': ('Funeral', [('680140', 'I'), ('680901', 'I')]),
    'GD031': ('Laundry/Dry Cleaning', [('340520', 'D'), ('340530', 'D'), ('440120', 'I'), ('440210', 'I'), ('440900', 'I')]),
    'GD041': ('Shoe Repair', [('440110', 'I')]),
    'GD042': ('Clothing Alterations', [('440130', 'I'), ('440140', 'I')]),
    'GD043': ('Jewelry/Watch Repair', [('440150', 'I')]),
    'GD051': ('Checking/Bank Services', [('620112', 'I'), ('680210', 'I'), ('680220', 'I')]),
    'GD052': ('Accounting Fees', [('680902', 'I')]),
    # ---- 车辆 ----
    'TC011': ('Tires', [('480110', 'I')]),
    'TC021': ('Vehicle Parts', [('480100', 'I'), ('480213', 'I')]),  # 480100 拆分
    'TC022': ('Motor Oil/Fluids', [('480100', 'I'), ('470211', 'I'), ('470212', 'I'), ('470220', 'I')]),  # 480100 拆分
    'TD011': ('Motor Vehicle Body Work', [('490100', 'I')]),  # 490100 拆分
    'TD021': ('Motor Vehicle Maintenance', [('490100', 'I'), ('520410', 'I'), ('520550', 'I')]),  # 490100 拆分
    'TD031': ('Motor Vehicle Repair', [('490100', 'I')]),  # 490100 拆分
}

# ---------------------------------------------------------------------------
# 二、65 CPI 品类 -> ELI 映射（series_id 来自 category_mapping.csv，勿改）
# ---------------------------------------------------------------------------
CATEGORY_ELI = {
    # ===== R 组（43）=====
    'CUUR0000SEAA01': ('男西装与外套', "Men's suits, sport coats, and outerwear", 'R', ['AA011', 'AA012', 'AA013'], ''),
    'CUUR0000SEAA02': ('男内衣/睡衣/泳装及配饰', "Men's underwear, nightwear, swimwear and accessories", 'R', ['AA021', 'AA022'], ''),
    'CUUR0000SEAA03': ('男衬衫与毛衣', "Men's shirts and sweaters", 'R', ['AA033'], ''),
    'CUUR0000SEAA04': ('男裤与短裤', "Men's pants and shorts", 'R', ['AA041'], ''),
    'CUUR0000SEAC01': ('女外套', "Women's outerwear", 'R', ['AC011'], ''),
    'CUUR0000SEAC02': ('女连衣裙', "Women's dresses", 'R', ['AC021'], ''),
    'CUUR0000SEAC03': ('女套装与单件', "Women's suits and separates", 'R', ['AC033', 'AC031', 'AC032'], ''),
    'CUUR0000SEAC04': ('女内衣/睡衣/泳装及配饰', "Women's underwear, nightwear, swimwear and accessories", 'R', ['AC041', 'AC042'], ''),
    'CUUR0000SEAF': ('婴幼儿服装', "Infants' and toddlers' apparel", 'R', ['AF011', 'AF012'], ''),
    'CUUR0000SEAB': ('童男装', "Boys' apparel", 'R', ['AB011', 'AB012', 'AB013', 'AB014'], ''),
    'CUUR0000SEAD': ('童女装', "Girls' apparel", 'R', ['AD011', 'AD012', 'AD013', 'AD014', 'AD016'], ''),
    'CUUR0000SEAE01': ('男鞋', "Men's footwear", 'R', ['AE011'], ''),
    'CUUR0000SEAE02': ('童鞋', "Boys' and girls' footwear", 'R', ['AE021', 'AE022'], ''),
    'CUUR0000SEAE03': ('女鞋', "Women's footwear", 'R', ['AE031'], ''),
    'CUUR0000SEHH01': ('地面覆盖物', 'Floor coverings', 'R', ['HH011'], ''),
    'CUUR0000SEHH02': ('窗帘与窗饰', 'Window coverings', 'R', ['HH021', 'HH022'], ''),
    'CUUR0000SEHH03': ('其他家纺布艺', 'Other linens', 'R', ['HH031', 'HH032', 'HH033'], ''),
    'CUUR0000SEHJ01': ('卧室家具', 'Bedroom furniture', 'R', ['HJ011', 'HJ012'], ''),
    'CUUR0000SEHJ02': ('客厅/厨房/餐厅家具', 'Living room, kitchen, and dining room furniture', 'R', ['HJ021', 'HJ022', 'HJ023', 'HJ024'], ''),
    'CUUR0000SEHJ03': ('其他家具', 'Other furniture', 'R', ['HJ031', 'HJ032', 'HJ033'], ''),
    'CUUR0000SEHK01': ('大家电', 'Major appliances', 'R', ['HK011', 'HK012', 'HK013', 'HK014'], ''),
    'CUUR0000SEHK02': ('其他家电', 'Other appliances', 'R', ['HK021', 'HK022', 'HK023'], ''),
    'CUUR0000SEHL01': ('钟表灯具装饰品', 'Clocks, lamps, and decorator items', 'R', ['HL011', 'HL012'], ''),
    'CUUR0000SEHL03': ('餐具', 'Dishes and flatware', 'R', ['HL031', 'HL032'], ''),
    'CUUR0000SEHL04': ('非电炊具与餐具', 'Nonelectric cookware and tableware', 'R', ['HL041', 'HL042'], ''),
    'CUUR0000SEHM01': ('工具五金耗材', 'Tools, hardware and supplies', 'R', ['HM012', 'HM013', 'HM014'], ''),
    'CUUR0000SEHM02': ('户外装备与耗材', 'Outdoor equipment and supplies', 'R', ['HM021', 'HM022'], ''),
    'CUUR0000SEED03': ('手机通信服务', 'Wireless telephone services', 'R', ['ED031'], '270102 为CPI调整因子拆分码：部分权重归手机硬件 ELI EE041（不在65品类），恩格尔回归取CE全额账单口径并备注'),
    'CUUR0000SEEE02': ('电脑软件', 'Computer software and accessories', 'R', ['EE021'], ''),
    'CUUR0000SERA01': ('电视机', 'Televisions', 'R', ['RA011'], ''),
    'CUUR0000SERA03': ('其他视频设备', 'Other video equipment', 'R', ['RA031'], ''),
    'CUUR0000SERA04': ('视频购买/订阅/租赁', 'Purchase subscription and rental of video', 'R', ['RA041', 'RA042'], ''),
    'CUUR0000SERA05': ('音频设备', 'Audio equipment', 'R', ['RA051'], ''),
    'CUUR0000SERA06': ('录制音乐与订阅', 'Recorded music and music subscriptions', 'R', ['RA061'], ''),
    'CUUR0000SERE01': ('玩具', 'Toys', 'R', ['RE011'], ''),
    'CUUR0000SERC01': ('运动车辆（含自行车）', 'Sports vehicles including bicycles', 'R', ['RC011', 'RC012', 'RC013'], '600133 为CPI拆分码(跨RC011/RC012)；已剔除房车/露营车 600151(主体属机动车TA090)；860701 为处置船/拖车的负向码'),
    'CUUR0000SERC02': ('运动装备', 'Sports equipment', 'R', ['RC021', 'RC022', 'RC023'], ''),
    'CUUR0000SERD01': ('摄影器材', 'Photographic equipment and supplies', 'R', ['RD011', 'RD012'], ''),
    'CUUR0000SERE02': ('缝纫机/布料/辅料', 'Sewing machines fabric and supplies', 'R', ['RE021'], ''),
    'CUUR0000SERE03': ('乐器及配件', 'Music instruments and accessories', 'R', ['RE031'], ''),
    'CUUR0000SERG02': ('娱乐书籍', 'Recreational books', 'R', ['RG022'], '报纸/杂志(ELI RG011/RG012)属 SERG01 不在65品类，本行仅取书籍 UCC 590230'),
    'CUUR0000SETC01': ('轮胎', 'Tires', 'R', ['TC011'], ''),
    'CUUR0000SETC02': ('汽车配件（除轮胎）', 'Vehicle accessories other than tires', 'R', ['TC021', 'TC022'], '480100 为CPI拆分码（跨 ELI TC021/TC022，均在本品类内）'),
    # ===== N 组（22）=====
    'CUUR0000SEMD01': ('医院服务', 'Hospital services', 'N', ['MD011'], '不含健康保险 UCC(580xxx)——保险保费属 CPI SEME 健康保险，不在65品类'),
    'CUUR0000SEEB01': ('大学学费', 'College tuition and fees', 'N', ['EB011'], ''),
    'CUUR0000SAM2': ('医疗护理服务', 'Medical care services', 'N', ['MC011', 'MC021', 'MC031', 'MC041'], '门诊医生/牙医/眼/其他专业人士服务；不含保险(580xxx)、不含医院(570xxx 属SEMD01)、不含家庭健康/疗养院(560410/570220)'),
    'CUUR0000SEEB03': ('托儿照护', 'Day care and preschool', 'N', ['EB031'], ''),
    'CUUR0000SEHC01': ('住房（位置性）', "Owners' equivalent rent of primary residence", 'N', ['HC011'], 'OER为归算租金，CE用 UCC 910104（Rental Equivalence of Owned Home）计，非实际现金支出'),
    'CUUR0000SEHA': ('主要住所租金', 'Rent of primary residence', 'N', ['HA011'], ''),
    'CUUR0000SEHD': ('租户与家庭保险', "Tenants' and household insurance", 'N', ['HD011'], ''),
    'CUUR0000SERB02': ('宠物服务（含兽医）', 'Pet services including veterinary', 'N', ['RB021', 'RB022'], ''),
    'CUUR0000SERF01': ('俱乐部会费/参与费', 'Club membership for shopping clubs fraternal or other organizations or participant sports fees', 'N', ['RF011'], ''),
    'CUUR0000SERF02': ('门票', 'Admissions', 'N', ['RF021', 'RF022'], ''),
    'CUUR0000SERF03': ('课程与指导费', 'Fees for lessons or instructions', 'N', ['RF031'], ''),
    'CUUR0000SETE': ('机动车保险', 'Motor vehicle insurance', 'N', ['TE011'], ''),
    'CUUR0000SETG02': ('其他城际交通', 'Other intercity transportation', 'N', ['TG021', 'TG022', 'TG023'], '城际公交/火车/船；不含航空(TG011 属SETG01)与市内公交(TG031 属SETG03)'),
    'CUUR0000SEGC01': ('理发及其他个人护理服务', 'Haircuts and other personal care services', 'N', ['GC011'], ''),
    'CUUR0000SEGD01': ('法律服务', 'Legal services', 'N', ['GD011'], ''),
    'CUUR0000SEGD02': ('殡葬服务', 'Funeral expenses', 'N', ['GD021'], ''),
    'CUUR0000SEGD03': ('洗衣与干洗服务', 'Laundry and dry cleaning services', 'N', ['GD031'], ''),
    'CUUR0000SEGD04': ('服装修补与其他服装服务', 'Apparel services other than laundry and dry cleaning', 'N', ['GD041', 'GD042', 'GD043'], '鞋修+服装改修/租赁+珠宝钟表维修'),
    'CUUR0000SEGD05': ('金融服务', 'Financial services', 'N', ['GD051', 'GD052'], '银行/支票账户服务+税务准备/会计费'),
    'CUUR0000SETD01': ('机动车车身修理', 'Motor vehicle body work', 'N', ['TD011'], '490100 为CPI拆分码：CE单一UCC无法拆 TD011/TD021/TD031，恩格尔回归需注明测量限制'),
    'CUUR0000SETD02': ('机动车维护保养', 'Motor vehicle maintenance and servicing', 'N', ['TD021'], '490100 拆分码 + 520410(年检)/520550(拖车)'),
    'CUUR0000SETD03': ('机动车维修', 'Motor vehicle repair', 'N', ['TD031'], '490100 拆分码'),
}

CONCORDANCE_URL = 'https://www.bls.gov/cpi/additional-resources/ce-cpi-concordance.htm'
CONCORDANCE_DESC = 'BLS CPI Handbook of Methods Appendix 5: CE UCC to CPI ELI Concordance（2024年度支出权重，2026-01起生效）'


def build_rows():
    rows = []
    for sid, (cn, title, grp, elis, note) in CATEGORY_ELI.items():
        uccs, srcs = [], []
        eli_titles = []
        for e in elis:
            et, pairs = ELI_UCC[e]
            eli_titles.append(f'{e}={et}')
            for ucc, s in pairs:
                if ucc not in uccs:
                    uccs.append(ucc)
                    srcs.append(s)
        rows.append({
            'series_id': sid,
            '中文品类名': cn,
            'BLS_item_title': title,
            'H1分组': grp,
            'ELI代码': ';'.join(elis),
            'ELI标题': ' | '.join(eli_titles),
            'UCC码': ';'.join(uccs),
            'UCC数': len(uccs),
            'CE来源': ';'.join(srcs),
            '映射依据': CONCORDANCE_DESC,
            '备注': note,
        })
    return rows


def main():
    rows = build_rows()
    # 校验：series_id 与 category_mapping 65 品类一致
    cm = list(csv.DictReader(open('research/h1-cpi/category_mapping.csv', encoding='utf-8-sig')))
    cm65 = [r['series_id'] for r in cm if r.get('H1分组') in ('N', 'R')]
    got = [r['series_id'] for r in rows]
    assert set(cm65) == set(got), f"series_id 不一致：缺 {set(cm65)-set(got)} 多 {set(got)-set(cm65)}"
    assert len(rows) == 65, f"应65行，实{len(rows)}"

    fields = ['series_id', '中文品类名', 'BLS_item_title', 'H1分组', 'ELI代码', 'ELI标题',
              'UCC码', 'UCC数', 'CE来源', '映射依据', '备注']
    with open('research/h1-cpi/ce_ucc_crosswalk.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # 统计
    print('总品类:', len(rows))
    print('H1分组:', dict(Counter(r['H1分组'] for r in rows)))
    allucc = [u for r in rows for u in r['UCC码'].split(';')]
    print('UCC 出现总次数(含跨品类重复):', len(allucc))
    print('UCC 去重后数量:', len(set(allucc)))
    # 跨品类重复的 UCC（拆分码）
    c = Counter(allucc)
    dup = {k: v for k, v in c.items() if v > 1}
    print('跨品类重复 UCC(拆分码):', dup)
    # I/D 来源统计
    src_count = Counter()
    for r in rows:
        for s in r['CE来源'].split(';'):
            src_count[s] += 1
    print('UCC 来源分布(I=Interview/D=Diary):', dict(src_count))
    # 与 Interview UCC 清单交叉核对
    intv = set(open('research/h1-cpi/ce_pumd_raw/ucc_codes_interview.txt').read().split())
    i_ucc = {u for r in rows for u, s in zip(r['UCC码'].split(';'), r['CE来源'].split(';')) if s == 'I'}
    matched = i_ucc & intv
    print(f'I来源UCC {len(i_ucc)} 个，其中 {len(matched)} 个在 mtbi 实测清单中；缺失: {sorted(i_ucc-intv)}')


if __name__ == '__main__':
    main()
