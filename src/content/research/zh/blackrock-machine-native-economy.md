---
title: "机器原生经济：叙事、证据与利益结构——评贝莱德《The Machine-Native Economy》白皮书"
date: 2026-09-24
lang: zh
description: "从货币与交易成本理论、市场微观结构与产业前沿三个参照系评述贝莱德《机器原生经济》白皮书：其贡献在于把“AI+Crypto”升格为机构级分析框架、并以运营支出（OpEx）视角重估 AI 基础设施的金融属性；局限在于核心类比存在范畴误置、关键数据口径混杂、对 x402 等协议的真实使用量避而不谈、且未充分披露自身商业利益。文章进而梳理贝莱德“敞口—储备—基础设施—实体算力”四层布局，指出其真正的战略落点是稳定币储备管理人与链上现金层，而非支付层本身。"
---

**作者**：汤汇道 —— 丰裕学（Abundantics）研究项目

---

## 摘要

2026年9月22日，贝莱德（BlackRock）数字资产研究团队发布11页白皮书《机器原生经济：数字资产如何连接智能、商业与算力》，提出“AI是机器原生的智能，数字资产是机器原生的货币”，并从LLM与区块链的“代币化同构”、代理商业（agentic commerce）对机器原生支付轨道的需求、算力作为新型数字资产市场三个维度论证AI普及将成为数字资产被低估的结构性需求来源。本文从货币与交易成本理论、市场微观结构与行业前沿三方面对报告进行述评：其主要贡献在于把“AI+Crypto”从市场叙事提升为机构级分析框架，清晰梳理了代理支付协议栈，并以运营支出（OpEx）视角重估算力的金融属性；主要不足在于核心类比存在范畴误置、关键数据口径混杂、对x402等协议真实使用量避而不谈、对原生代币价值捕获的内在张力分析不足、遗漏已上线或即将上线的算力期货与卡组织代理支付方案、几乎未讨论代理安全与责任分配，且未充分披露贝莱德在各论点中的直接商业利益。本文进一步梳理贝莱德“敞口—储备—基础设施—实体算力”四层布局，指出其真正的战略落点是“稳定币储备管理人与链上现金层”，而非支付层本身。

**关键词：机器原生经济；代理商业；x402；稳定币；代币化；算力期货；贝莱德**

> 说明：本文数据截至2026年9月23日。凡标注来源为行业媒体或第三方统计者，属二手数据，口径可能不一，仅供研究参考，不构成投资建议。

## 一、引言：一份“时点精准”的机构白皮书

贝莱德于2026年9月22日通过官方渠道发布该白皮书[1][2]。署名作者四人：数字资产研究主管Will Su、数字资产主管Robert Mitchnick、美国股票ETF主管Jay Jacobs、美国iShares产品创新主管William Helm。作者构成本身即是信号——两位来自数字资产条线，两位来自ETF产品条线——意味着这不是一份纯粹的学术研究，而是连接“研究观点”与“产品货架”的战略文件。

发布时点同样值得注意。此前半年，行业密集落地：Stripe与Paradigm孵化的支付链Tempo于3月18日上线主网并同步推出机器支付协议MPP[3]；x402基金会于4月在Linux基金会正式成立[4]；Stripe于8月19日宣布收购模型路由平台OpenRouter[5]；Circle的Arc公链于9月16日开放公共主网，贝莱德是其创始验证者之一[6]。此后，CME计划于10月5日上线首批GPU算力期货[7]，美国《GENIUS法案》最迟将于2027年1月18日生效[8]。白皮书恰好卡在“基础设施就位、真实需求尚待验证”的窗口期发布，其功能更接近为下一阶段资金配置提供叙事框架。

本文目标有二：其一，从经济学、货币金融理论与产业前沿三个参照系评估报告的新意与不足；其二，还原贝莱德自身在该领域的布局与地位，识别报告背后的利益结构。

## 二、报告要旨

报告的总论断是：AI负责理解信息与指挥行动，区块链提供机器可读的资产与可编程结算，两者结合将使数字资产成为日益自主的数字经济的核心基础设施[1]。其论证由三根支柱构成（表1）。

**表1  白皮书三大支柱及其证据性质**

| 支柱 | 核心主张 | 主要证据 | 证据性质 |
|---|---|---|---|
| 代币化同构 | LLM把语言切分为token并编码为数值；区块链把价值与权利表示为token用于机器可验证的转移与结算。二者都把现实输入翻译为机器原生表示，使代理与区块链的接口更直接 | 图1示意性流程；比特币政策研究所（BPI）的模型偏好模拟 | 概念类比＋模拟实验 |
| 代理商业需要机器原生支付轨道 | ACH与卡网络在开户授权、商户费率、结算终局性与可扩展性上不适配高频、极小额、全天候交易；x402、MPP、ACP、AP2、TAP构成新协议栈 | 稳定币流通市值超过3000亿美元；2025年调整后交易量超11万亿美元，2020–2025年CAGR约80%，ACH约8.5% | 行业统计（口径混合） |
| 算力成为数字资产新市场 | 算力是日益重要的经济资源，标准化算力合约可被代币化、转让、质押和可编程结算，交易所算力期货将改善价格发现 | AWS、微软智能云、谷歌云2030年合计收入一致预期约1.1万亿美元；McKinsey推理负载预测；Stripe收购OpenRouter | 卖方一致预期＋事件信号 |

*资料来源：根据BlackRock（2026）[1]整理。*

## 三、报告的新意与贡献

### 3.1 把“AI+Crypto”从市场叙事升格为机构级分析框架

过去两年，“AI代理需要加密货币”主要是加密原生机构与风投的叙事。全球最大资管机构以正式白皮书的形式将两大技术主题“并轨”，并给出“机器原生智能／机器原生货币”这一简洁的概念对，本身具有议程设定意义。报告对“代理式AI”的定义——能够在有限人类干预下，通过调用外部工具与基础设施规划并执行多步任务的系统——也较为规范，便于后续讨论统一口径。

### 3.2 协议栈的分层梳理与M2M/B2M/C2M三分法

报告区分了“基础层”（MCP负责代理访问外部工具与数据，A2A负责代理之间通信协调）与“金融层”（x402、MPP、ACP、AP2、TAP），并以订机票酒店的六步工作流（文中图2）展示二者如何协同。更重要的是，报告没有陷入“加密替代一切”的单一叙事，而是明确指出：高频、亚美分、全天候的M2M交易更适合加密原生轨道，而连接人类经营的商家与消费者的B2M、C2M场景，改造后的传统支付体系仍将重要。这一市场细分对产品设计与投资判断都有实际价值。

### 3.3 以OpEx视角重估AI基础设施的金融属性

市场讨论集中于AI资本开支的规模（报告引用高盛估计2025–2030年累计超过5万亿美元），报告则提醒应同等关注持续上升的运营支出，并把算力视为像能源、农产品那样需要定价、配置、融资与对冲的资源，援引基差市场、差价合约等大宗商品市场的成熟机制作为参照。这一“从资产到流量”的视角转换，是报告最具启发性的部分。

### 3.4 提出可检验的“AI原生货币分工”假说

报告借BPI的模拟研究，提出“稳定币作交易媒介、比特币作价值储藏”的AI原生货币架构假说。尽管证据力较弱（详见4.3），但它把一个经典的货币职能分工问题（参见Kiyotaki与Wright关于交易媒介内生化的搜寻模型[9]）搬到了“机器作为经济主体”的新情境中，为后续实证研究提供了可证伪的命题。

### 3.5 措辞相对克制

报告多处使用“示意性”“仍处早期”“取决于各网络的费用、质押与gas代付设计”等限定语，并在结论中承认代理支付活动与算力市场流动性“仍然有限”。相较一般行业宣传材料，这种自我限定是值得肯定的。

## 四、不足与商榷：与理论和产业前沿的对照

### 4.1 理论层：“代币化同构”是修辞性类比，存在范畴误置

LLM中的token是词表索引：它是非竞争性的、可无限复制的，其“意义”来自嵌入空间中的统计关系，且编码过程是有损的；数字资产token则是竞争性的权利凭证，其核心难题恰恰是防止双花，需要共识机制与法律确权来保证“同一单位不能同时属于两人”。二者共享的只是“离散化与编码”这一极其一般的计算特征，而非经济功能。换言之，同一个词“token”在两处是同名异义。

报告据此推出“LLM代理与区块链数据的接口比与碎片化遗留系统更直接”，这一推论也不够稳健。机器可读性并非区块链独有：ISO 20022报文、FIX协议、银行开放API同样是结构化的；代理访问区块链也需要经由RPC节点、索引服务或MCP服务器，与访问银行API并无本质差异。真正使公链对代理有吸引力的，是报告虽有提及但未作为主论证的几项属性：无需许可的接入（免开户与人工授信）、全天候原子结算、可组合性以及可编程托管（智能合约钱包的额度、白名单与时间锁）。

更坚实的理论基础在货币理论与区块链经济学中早已存在。Kocherlakota的“货币即记忆”[10]表明，货币的本质功能是替代一个记录所有历史交易的公共记忆；公共账本正是这种记忆的技术实现，而匿名、海量、无长期关系的代理恰恰是最需要“公共记忆”来建立信任的主体。Catalini与Gans[11]将区块链的经济价值归结为降低“验证成本”和“网络化成本”，代理经济同时放大了这两类成本。若以此为框架，报告的论证会比“token同构”更有说服力。

### 4.2 遗漏微支付经济学的关键文献——以及它本可提出的最强论据

微支付曾是互联网史上反复失败的构想。Szabo[12]与Odlyzko[13]的经典分析指出，微支付失败的主因并非技术成本，而是人类的“心理交易成本”：每次付费都要做一次微小的决策，用户因此强烈偏好包月、订阅等固定价格。这一文献对机器原生经济有双重含义。其一，它提供了报告本可提出的最强论据：AI代理的心理交易成本近乎为零，历史上阻碍按次付费的根本障碍在代理场景中被移除，这才是“按调用、按token、按任务”结算可能真正成立的理论依据。其二，它也提示了反面：企业作为代理的委托人，依然需要预算确定性，因此现实中更可能出现“预付余额＋额度会话＋流式扣费”的混合形态——MPP的会话（sessions）原语、OpenRouter的预付信用额度都是此类折中——这会显著减少链上交易笔数。

从Coase[14]的交易成本理论看，代理大幅降低了搜寻、议价与签约成本，企业与市场的边界将向“市场”一侧移动，更多原本内部化的服务会以API形式被外部采购；Hadfield与Koh[15]进一步指出，代理作为经济主体会重塑市场、组织与制度，并面临与不完全契约同构的“对齐问题”。这些理论本可帮助报告估算M2M支付的规模弹性，而不是仅以稳定币总量类比卡组织。

### 4.3 数据口径与证据强度

第一，稳定币交易量的可比性问题。报告引用的2025年逾11万亿美元“调整后”交易量，按其自身注释包含交易所、DeFi、借贷、铸造赎回与出入金活动，与Visa、Mastercard的消费支付量并不可比——报告图3注释承认了这一点，但正文仍以“同一数量级”作为修辞。可资对照的是，有研究引述McKinsey估算真实的稳定币支付规模每年约3900亿美元，而欧洲央行引用的估计显示，只有约0.5%的交易量属于零售规模的自然转账[16]。

第二，对x402真实使用量避而不谈。报告把x402描述为“正在浮现的高速M2M交易标准”，却未给出任何使用数据。独立数据呈现出明显落差：Coinbase在2026年4月下旬披露x402累计约1.65亿笔交易、约5000万美元交易额[4]；但Visa与Artemis于2026年7月发布的研究将约1.357亿美元原始交易额剔除刷量、测试与内部转账后，调整值仅约1500万美元，被剔除部分占美元交易额的89%[17]；CoinDesk在3月的报道估计真实日交易额约2.8万美元，且大量交易属“刷”出来的[18]；Chainalysis也指出2025年末的交易激增很大程度上来自PING迷因币而非代理采购服务[19]。换言之，报告所称的“结构性需求”目前仍是预测，而非观测事实。

第三，BPI研究的证据力有限。报告自己也承认该研究反映的是模拟中的模型回答而非代理实际行为。补充两点：该机构本身是比特币倡导型组织[20]；而关于LLM是否具有稳定、可操控的“偏好”，学界仍有较大争议（Hadfield与Koh援引的研究即对此提出质疑[15]；Horton[21]的“硅基经济人”方法也强调其作为模拟工具的边界）。以此作为“AI原生货币架构”的初步支持，严谨性不足。

第四，算力市场规模的代理变量偏宽。以AWS、微软智能云与谷歌云2030年约1.1万亿美元的合计收入作为算力市场的“宽口径代理”，其中大量是非AI负载与软件化服务，真正可能被标准化、代币化的只是可租赁GPU小时与容量合约的一部分。将其作为“算力数字资产”的潜在市场规模，存在高估风险。

### 4.4 原生加密资产价值捕获的内在张力

报告的关键传导链是：M2M交易增长→区块空间与验证者服务需求上升→ETH等原生加密资产获得使用性需求与价值捕获。然而，行业恰恰在工程上系统性地“去原生代币化”支付链路：Tempo主网以稳定币结算，没有价格波动的原生gas代币[3]；Arc以USDC作为原生gas[6]；x402的结算服务方普遍代付gas；MPP的会话原语则把多次交互压缩为少量链上交易。报告在Arc部分自己也承认，更多支付活动可能首先深化的是USDC作为结算与缴费资产的效用。

这意味着，M2M规模扩张的收益更可能流向稳定币发行方（储备浮存金收益）、储备资产管理人以及链的运营方，而不一定是公链原生代币持有人。值得玩味的是，据报道Arc在2026年5月仍进行了一轮代币预售[6]，说明即便是“稳定币即gas”的链，其治理与质押代币的价值捕获设计也远未定型。报告执行摘要对“原生加密资产”的乐观，与正文中的条件性限定之间缺少分析性衔接。

### 4.5 算力资产化：回避了“为何要上链”，也遗漏了既有的传统金融路径

其一，算力是不可储存商品。Working[22]的储存理论解释了可储存商品的期限结构，而算力像电力一样“当期不用即消失”，价格更易出现尖峰，远期曲线更多取决于产能投放与硬件代际折旧（H100到B200）。标准化算力凭证本质上更接近电力市场的“容量合约”，需要解决可交割性、服务等级协议、区域基差与代际折算问题。报告承认这些难点，但以“重要但终可解决”一笔带过。

其二，前沿已经越过报告的“预期”。报告称“我们预期”将出现交易所上市的算力期货，但事实上CME与Silicon Data已于8月11日宣布在10月5日于NYMEX上线H100与B200租赁指数期货（现金结算，每张合约代表一个月的GPU租赁）[7]；ICE与Ornn、以及Architect也在5月先后宣布了算力期货计划[23]。这些均是链下、受监管、现金结算的传统金融方案。价格数据也说明了对冲需求：据SemiAnalysis数据，H100一年期租赁价在2025年10月至2026年3月间由每小时1.70美元升至2.35美元[24]；单日内不同平台的H100报价区间可达0.72至15.14美元[25]。报告同样未提及Akash、Render、io.net等DePIN算力网络多年来的代币化尝试及其有限成效，而这恰是一个现成的“自然实验”。

其三，缺少“为何需要区块链”的论证。如果现金结算的CME期货已能满足对冲需求，代币化的增量价值应当被明确界定为：可实物交割的细颗粒度容量凭证、作为抵押品的跨平台流动性，以及面向代理的全天候程序化结算。报告若以此为主线，论证会更有力。

### 4.6 产业前沿的遗漏与表述瑕疵

报告对协议栈的梳理存在明显的“选择性”：未提及谷歌的通用商业协议（UCP）；完全未提及Mastercard——其Agent Pay以“代理令牌”限定额度与场景，并于2026年6月10日推出面向机器间持续支付的Agent Pay for Machines，且将代理凭证存放于公链之上[26]；未提及Visa于4月推出的Intelligent Commerce Connect，该产品同时支持TAP、MPP、ACP与UCP四种代理协议，而Visa的稳定币结算已覆盖包括Arc与Tempo在内的九条链[27]；未提及x402基金会的成员已包括Visa、Mastercard、Stripe、谷歌、AWS等[4]；也未提及ERC-8004等代理身份标准（据统计上线后数月内已有约2.4万个代理注册[28]）。这些事实共同指向一个与报告叙事方向相反的结论：卡组织与支付巨头正在“吸纳”而非“被替代”。

表述层面亦有若干瑕疵：谷歌AP2的正式名称是Agent Payments Protocol，正文写作“Agents Payment Protocol”、脚注写作“Agentic Payments Protocol”；Visa的TAP在正文与脚注中单复数不一致；第5页章节标题中“purpose-build”应为“purpose-built”；图5中“Continously”拼写有误。对一份旗舰白皮书而言，这些细节有损专业形象。

### 4.7 风险与制度维度几乎缺位

代理行为与安全。微软研究院的Magentic Marketplace实验显示，所有被测模型都表现出严重的“首个报价偏差”，响应速度相对质量获得10至30倍的优势；在操纵测试中，部分模型的付款被全部导向恶意代理[29]。当结算不可逆、金额由机器自主决定时，这类行为偏差与提示注入风险是“机器原生货币”必须首先回答的问题。

责任与授权。代理付错钱、被诱导付钱、超预算付钱，损失由谁承担？卡网络有成熟的拒付与争议解决机制，而稳定币转账不可逆——这在M2M场景是“特性”，在C2M场景却是“缺陷”。Chan等[30]提出的代理基础设施（身份、归因、交互记录、事后纠正）与Hammond等[31]对多代理风险的分类，都指向同一结论：瓶颈在授权与问责，而不在支付本身。

货币与金融稳定。国际清算银行（BIS）2025年年报认为稳定币难以同时满足“单一性、弹性与完整性”三项检验[32]；2026年年报进一步提出以代币化央行准备金、代币化商业银行货币及受监管私人货币构成的“统一账本”作为替代路径[33]。这是一种与报告截然不同的机构愿景（代币化存款而非稳定币），报告未作回应。

监管尚未落地。《GENIUS法案》的生效日为2027年1月18日与最终规则发布后120天二者中的较早者[8]；据报道各监管机构均未在2026年7月18日的法定期限前完成规则制定，OCC目标在11月发布最终规则[34][35]。报告所称“监管日益清晰”是前瞻性判断，而非既成事实。

隐私与地缘。公链透明性会暴露企业代理的采购与供应链信息；而在报告作为“战略信号”引用的OpenRouter上，有报道援引CNBC称中国来源模型占美国企业token使用量的46%[36]——模型路由与算力采购已与国家安全、出口管制深度缠绕，这一维度在报告中完全缺席。

### 4.8 利益相关性披露不足

报告的每一根支柱都能对应到贝莱德的具体业务（详见第五部分）：稳定币对应其为Circle管理的约600亿美元储备及新发行的储备型代币化基金；报告正面介绍的Arc，贝莱德是其创始验证者；代币化RWA对应BUIDL；原生加密资产对应IBIT与以太坊系列ETF；算力对应旗下GIP参与的400亿美元Aligned数据中心收购。报告末页仅有标准化免责声明，缺少学术规范意义上的利益冲突说明。本文并非暗示不当行为，而是建议读者将其定位为“战略论题与需求侧叙事”，而非中立研究。

## 五、贝莱德在该领域的布局与地位

### 5.1 总体图景：从“提供敞口”到“成为基础设施”

Larry Fink的2026年致股东信以代币化为核心，将其比作早期互联网级别的金融基础设施升级；据相关报道，贝莱德当时已有约1500亿美元资产与数字市场相关[37]。截至2026年二季度末，贝莱德数字资产基金规模为488亿美元，同比下降39%，主因是约458亿美元的市值损失抵消了151亿美元的净流入；公司重申了到2030年加密业务年收入5亿美元的目标[38]。这组数字说明：贝莱德的数字资产业务对币价高度敏感，而其战略重心正在从价格敞口转向对币价不敏感的“链上现金与储备”业务。

**表2  贝莱德机器原生经济相关布局（截至2026年9月）**

| 层级 | 代表产品/资产 | 规模与进展 | 与白皮书论点的对应 |
|---|---|---|---|
| 加密资产敞口层 | IBIT（比特币ETF）、以太坊ETF、质押以太坊ETF | IBIT净资产2025年末约674亿美元，2026年3月末约534亿美元[39] | “原生加密资产”价值捕获；BTC作价值储藏 |
| 链上现金与储备层 | BUIDL；BSTBL（既有货基的链上份额）；BRSRV（RSVXX）；Circle Reserve Fund | BUIDL于2026年7月中旬约28.7亿美元，覆盖六条公链[38][40]；BRSRV于8月3日上线，拟作为GENIUS合格储备资产[41]；为Circle管理约600亿美元储备，约占3000亿美元稳定币市场的四分之一[35] | 稳定币作交易货币；代币化RWA作抵押 |
| 基础设施参与层 | Securitize（转让代理与代币化平台）；Arc创始验证者；BNY托管 | Securitize于7月2日在纽交所上市[38]；Arc公共主网9月16日开放[6] | 结算网络与区块空间 |
| 实体算力层 | GIP；AI基础设施合作伙伴关系（AIP，与MGX、微软、英伟达）；Aligned Data Centers | 约400亿美元收购于7月21日交割，51个园区、6.4GW运营及规划容量[42] | 算力作为可金融化资源 |

*资料来源：根据公司公告、SEC文件及行业数据[6][35][37]–[42]整理；部分数值为媒体转述。*

### 5.2 战略定位：做“房东”而非“租客”

贝莱德首席财务官Martin Small在二季度业绩会上表示，希望成为稳定币行业的首选储备管理人[35]。结合表2可以看出，贝莱德在机器原生经济中的真正落点是资产负债表层：无论最终胜出的是x402还是MPP、是Base还是Tempo或Arc，只要为代理铸造的每一美元稳定币需要一美元合格储备，贝莱德的收入就会随稳定币浮存金增长。这是一种对协议之争保持中立的“卖铲人”策略。白皮书在此意义上扮演的是需求侧叙事：它论证代理经济会扩大稳定币与代币化资产的总量，而贝莱德在供给侧已为此备好了产品货架。

报告未明说、但本文认为最直接的一条变现渠道是：《GENIUS法案》禁止支付型稳定币发行方向持有人支付利息，因此代理钱包与企业代理“金库”中沉淀的闲置余额，有动力在不用时自动扫入BUIDL、BRSRV一类收益型代币化货基，在需要支付时再赎回为稳定币。若代理具备全天候的资金管理能力，“代理营运资本的收益化”可能成为代币化货基的新增需求来源。这是本文的推论，有待监管口径（尤其是对“收益”与“关联方安排”的解释）进一步明确。

### 5.3 竞争格局与相对地位

在机构级代币化现金领域，贝莱德处于领先地位：BUIDL是最大的代币化美债基金之一，但面临Circle USYC、富兰克林邓普顿BENJI、Ondo、富达、WisdomTree等的直接竞争[40]。在代理支付层，贝莱德并无直接产品，真正的整合者是Stripe——其拥有Bridge、Tempo、MPP，并以媒体报道约70亿至80亿美元的价格收购OpenRouter（官方未披露金额）[5][43]，据报道还在寻求收购PayPal[43]；Coinbase则掌握x402、Base与机构托管（且是IBIT的托管人）。在卡组织层，Visa与Mastercard正在把代理支付纳入既有网络并主动接入稳定币结算[26][27]。在银行代币化存款方向，BIS支持的统一账本路径构成潜在的制度性替代[33]。

综合判断：贝莱德在“代币化现金与储备管理”和“加密资产ETF敞口”两项上具有规模与信用优势，在实体算力层通过GIP获得了少有的“算力资产端”位置；但在代理本身、支付协议与开发者生态上处于外围。其优势（品牌、监管关系、分销、储备规模）与劣势（非技术平台、对币价敏感、利益冲突可见度高）都相当清晰。

## 六、结论与启示

贝莱德的这份白皮书是迄今分量最重的机构级“AI×数字资产”论述。它的价值在于提供了一个清晰、可传播的框架，并以OpEx视角把算力纳入金融化议程；它的局限在于以修辞性类比替代机制论证、以口径混合的总量数据替代真实使用数据，对原生代币价值捕获的张力、已在推进的传统金融方案以及代理安全与责任问题着墨不足，且未对自身的深度利益关联作出充分说明。它更适合被理解为贝莱德“链上现金与储备管理人”战略的需求侧叙事。

对投资者，应区分叙事与现金流：与稳定币浮存金、储备管理和合规基础设施挂钩的收益更确定，公链原生代币的受益取决于具体的费用与质押机制。对建设者，真正的瓶颈是身份、授权、风控与争议解决，而非“能否付款”。对监管者，需要尽早界定代理的法律地位与责任链、KYA标准及基于风险的微支付合规阈值。对学界，值得展开的研究包括：代理支付的需求弹性与心理交易成本消失的实证检验、代理市场的机制设计与操纵防范、不可储存算力的价格形成，以及代理经济中的价值分配与货币分工。

## 参考文献

[1] BlackRock (2026). The Machine-Native Economy: How Digital Assets Connect Intelligence, Commerce, and Compute. White paper, September 2026. https://www.blackrock.com/us/individual/literature/whitepaper/the-machine-native-economy.pdf

[2] The Crypto Times (2026-09-22). BlackRock Examines AI Payments, Tokenized Assets and Compute. https://www.cryptotimes.io/2026/09/22/blackrock-examines-ai-payments-tokenized-assets-and-compute/

[3] Tempo (2026-03-18). Tempo Mainnet Is Live. https://tempo.xyz/blog/mainnet/ ; OurCryptoTalk (2026-03-19). Tempo Goes Live With Stripe’s Machine Payments Protocol.

[4] Eco (2026). x402 Protocol Explained (x402 Foundation membership; Coinbase-reported metrics). https://eco.com/support/en/articles/14839402-x402-protocol-explained

[5] Stripe (2026-08-19). Stripe Agrees to Acquire OpenRouter to Help Businesses Optimize Token Routing and Usage; OpenRouter (2026-08-19). OpenRouter Is Joining Stripe.

[6] CoinMarketCap Academy (2026-09). What Is Circle’s Arc? The Blockchain That Charges Gas in USDC.

[7] CME Group (2026-08-11). CME Group and Silicon Data to Launch Compute Futures on October 5. Press release.

[8] Office of the Comptroller of the Currency (2026). Implementing the GENIUS Act for the Issuance of Stablecoins, Notice of Proposed Rulemaking. Federal Register, 2 March 2026; Mayer Brown (2026-03-27) legal update.

[9] Kiyotaki, N., & Wright, R. (1989). On Money as a Medium of Exchange. Journal of Political Economy, 97(4), 927–954.

[10] Kocherlakota, N. R. (1998). Money Is Memory. Journal of Economic Theory, 81(2), 232–251.

[11] Catalini, C., & Gans, J. S. (2020). Some Simple Economics of the Blockchain. Communications of the ACM, 63(7), 80–90.

[12] Szabo, N. (1999). The Mental Accounting Barrier to Micropayments. Essay.

[13] Odlyzko, A. (2003). The Case Against Micropayments. In Financial Cryptography 2003, LNCS 2742, Springer, 77–83.

[14] Coase, R. H. (1937). The Nature of the Firm. Economica, 4(16), 386–405.

[15] Hadfield, G. K., & Koh, A. (2025). An Economy of AI Agents. arXiv:2509.01063; prepared for the NBER Handbook on the Economics of Transformative AI.

[16] Stablecoin Insider (2026-02-24). AI Agents for Stablecoins in 2026 (citing McKinsey and ECB estimates).

[17] Visa & Artemis (2026-07-14). Agentic Payments from the Ground Up; as summarized in “TRM Labs x402 Report” (Spotedcrypto, 2026-09).

[18] CoinDesk (2026-03-11). Coinbase-backed AI Payments Protocol Wants to Fix Micropayment but Demand Is Just Not There Yet.

[19] Concordium (2026). x402 Explained: The HTTP Payment Protocol for AI Agents (citing Chainalysis on-chain analysis).

[20] Bitcoin Policy Institute (2026). Which Money Do AI Agents Prefer? https://www.btcpolicy.org/

[21] Horton, J. J. (2023). Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus? NBER Working Paper 31122.

[22] Working, H. (1949). The Theory of Price of Storage. American Economic Review, 39(6), 1254–1262.

[23] Friedman, D. (2026-06). Compute Derivatives Market Primer. Substack.

[24] Spheron (2026-08-27). Compute Futures: What CME’s GPU Contracts Mean for AI Buyers (citing SemiAnalysis rental price data).

[25] FinStrat Management (2026). GPU Compute Futures: Price Discovery or a New Layer of Risk.

[26] UniversalCommerceProtocol.fr (2026-06-21). Visa Intelligent Commerce and Mastercard Agent Pay; Digital Applied (2026-06-13). Visa + OpenAI: Tokenized Payments for Shopping Agents.

[27] TechInformed (2026-04-09). Visa Opens One Integration for AI Agent Payments; Eco (2026). Visa Intelligent Commerce Explained.

[28] Nevermined (2026-05-08). 40 Stablecoin Payments for AI Agents Statistics.

[29] Bansal, G., et al. (2025). Magentic Marketplace: An Open-Source Environment for Studying Agentic Markets. Microsoft Research, arXiv:2510.25779.

[30] Chan, A., et al. (2025). Infrastructure for AI Agents. arXiv:2501.10114.

[31] Hammond, L., et al. (2025). Multi-Agent Risks from Advanced AI. arXiv:2502.14143.

[32] Bank for International Settlements (2025). Annual Economic Report 2025, Chapter III: The Next-Generation Monetary and Financial System. https://www.bis.org/publ/arpdf/ar2025e3.htm

[33] Bank for International Settlements (2026). Annual Economic Report 2026, Chapter III: Anchoring Trust in Money: Innovation Beyond Stablecoins; Press release, 23 June 2026. https://www.bis.org/publ/arpdf/ar2026e3.htm

[34] PYMNTS (2026-08-20). OCC Races the Clock to Finish GENIUS Act Stablecoin Rules.

[35] CoinInsider (2026-08-04). BlackRock Launches Two Tokenized Money Market Funds for Stablecoin Reserves; Forkast (2026-08-03). BlackRock’s New Stablecoin Reserve Vehicles Aren’t Competition — They’re the Foundation.

[36] Yahoo Finance (2026-08-17). Stripe Acquires OpenRouter for \$7B+ (citing CNBC investigation of 2026-07-07).

[37] Wyde (2026). Larry Fink Says Tokenization Is the Internet in 1996. The Law Says Not Yet. (on BlackRock 2026 Chairman’s Letter).

[38] Messari (2026). BlackRock USD Institutional Digital Liquidity Fund: Research & News (incl. BlackRock Q2 2026 digital asset AUM).

[39] iShares Bitcoin Trust ETF (2026). Form 10-Q for the Quarter Ended March 31, 2026. U.S. SEC EDGAR.

[40] Securitize (2026). Introducing the BlackRock BUIDL Fund. https://securitize.io/blackrock/buidl ; RWA.xyz BUIDL page.

[41] BlackRock (2026). BlackRock Daily Reinvestment Stablecoin Reserve Vehicle (RSVXX) Product Page and Prospectus (31 July 2026).

[42] Aligned Data Centers (2026-07-21). AIP, MGX and BlackRock’s GIP Close Acquisition of Aligned Data Centers. Press release.

[43] Bloomberg (2026-08-16). Stripe Finalizes Deal to Acquire AI Startup OpenRouter for Over \$7 Billion; Axios (2026-08-17). Stripe Strikes Mega-Deal for OpenRouter; CNBC (2026-08-19).
