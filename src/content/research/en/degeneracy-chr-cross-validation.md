---
title: "On the Degeneracy of Price-Derived Quality Weights, and an Independent Cross-Validation of an Energy-Parity Index for AI Inference and Bitcoin Mining"
date: 2026-09-04
lang: en
translation: "zh/degeneracy-chr-cross-validation"
description: "Quality-adjusting a price with a weight derived from that same price collapses the 'quality-adjusted parity deviation' algebraically into the raw price ratio. The fixed TEPI converges, to within an order of magnitude, with the entirely independent Compute Heat Rate project."
---

**Author**: Huidao Tang — Abundantics research program, Empirical Module 01 (TEPI)
**Data & code**: CC-BY 4.0. Methodology: abundantics.org/en/index/methodology/. Repository: github.com/tanghuidao/token-parity.

---

## Abstract

We report two findings from constructing TEPI (Token Energy Parity Index), a daily index comparing the gross revenue per kilowatt-hour earned by two energy-intensive digital activities: Bitcoin mining and large language model (LLM) inference. First, we show that quality-adjusting the price of a heterogeneous good using a weight derived from that good's own price produces a subtle but severe degeneracy: the resulting "quality-adjusted parity deviation" collapses algebraically into the raw price ratio, regardless of the underlying data — silently discarding the very adjustment it purports to make. We prove this result in general form and show that an early version of our index exhibited exactly this collapse in its first published snapshot. The fix — requiring the quality weight to come from a benchmark independent of price — restores the index's informativeness; we verify this using 2026-08 data. Second, using an entirely independent, concurrently published methodology — Compute Heat Rate (CHR), which prices AI workloads' electricity tolerance from vendor-direct pricing and hardware benchmarks — we find that TEPI's core quantities (gross inference revenue per kWh, and implied per-token energy consumption) converge with CHR's independent estimates to within the same order of magnitude, despite no shared data sources. We report both results with explicit attention to what they do, and do not, establish.

---

## 1. Introduction

Bitcoin mining and LLM inference are, at the level of physical inputs, the same activity: converting electrical energy into a digital token. In the framing we use throughout the Abundantics research program, the two differ in economic function rather than in physical mechanism — mining is a form of *defensive dissipation* (energy spent to defend an existing property claim, in the sense of Baumol's 1990 distinction between productive and unproductive uses of entrepreneurial effort), while inference is *productive dissipation* (energy spent to produce a cognitive output). This is an interpretive lens, not a normative claim, and nothing in the index depends on it.

TEPI asks a narrow, measurable question: at today's market prices, how much gross revenue does one kilowatt-hour earn in each of the two uses, and how large is the gap once model quality is accounted for? It does not measure profit, welfare, or energy allocation, and it is not investment advice. The construction follows the "physical common denominator" logic of purchasing-power-parity indices (Balassa, 1964; Samuelson, 1964), most familiar in its popularized form as *The Economist*'s Big Mac Index, but with joules rather than a single retail good as the common currency.

This note reports two things that emerged from building TEPI, both of which we believe are of interest beyond this specific index. Section 3 states and proves a degeneracy result: if a quality-adjustment weight for a heterogeneous good is itself derived from that good's price, the resulting "deviation from quality-adjusted parity" is mathematically forced to equal the unadjusted price ratio, for any data and any date. We are not aware of this exact result being stated elsewhere in the price-index literature, though it is almost certainly a special case of concerns already known in hedonic and quality-adjustment methodology; we do not claim priority, only that we have not seen it stated this explicitly, and that it cost us a released (if unannounced) version of our own index before we caught it. Section 5 reports an independent cross-validation: a methodologically unrelated project, Compute Heat Rate (CHR; Royal, 2026), arrives at figures of the same order of magnitude as TEPI's core outputs, using none of the same data sources.

---

## 2. TEPI in brief

TEPI publishes four daily quantities:

| Symbol | Name | Definition |
|---|---|---|
| $R_M$ | Mining gross revenue per kWh | Network-efficiency-weighted mining revenue per kilowatt-hour |
| $R_A$ | Inference gross revenue per kWh | Usage-weighted revenue per kilowatt-hour across a basket of LLMs |
| $\Lambda$ | Energy arbitrage ratio | $R_A$ / $R_M$ (published as a chain-linked series, $\Lambda_{\text{chained}}$) |
| $\Omega$ | Parity deviation index | Log ratio of a quality-adjusted, energy-denominated exchange rate to the market exchange rate |

Mining side: $R_M = \text{hashprice} / E_{\mathrm{PH}}$, where hashprice is the daily mining revenue per PH/s and $E_{\mathrm{PH}}$ is the daily energy consumption of one PH/s under an assumed network-wide mining efficiency $\eta$ (J/TH). This reduces to the identity $R_M = k \cdot P_{\mathrm{BTC}} / \varepsilon_{\mathrm{BTC}}$, where $P_{\mathrm{BTC}}$ is the BTC spot price, $\varepsilon_{\mathrm{BTC}}$ is the energy embodied in one bitcoin at the margin, and $k = 3.6 \times 10^6$ J/kWh.

Inference side: for a basket of models indexed by i, each with output-token price $p_i$ (USD/token) and per-token energy cost $j_i$ (J/token, including full-stack overhead), and usage weights $w_i$ summing to 1:

$$
R_A = k \sum_i w_i \, \frac{p_i}{j_i}
$$

A model's raw output tokens are converted to "standard tokens" using an external quality weight $q_i = s_i / s_{\text{ref}}$, where $s_i$ is a price-independent capability score (currently the Artificial Analysis Intelligence Index). This gives each model i a standard-token yield per joule, $t_i = q_i / j_i$, and a basket total $T = \sum_i w_i \, t_i$.

Two exchange rates are then compared: $\rho_{\text{parity}} = \varepsilon_{\mathrm{BTC}} \cdot T$ (how many standard tokens the energy in one bitcoin would buy if redirected to quality-adjusted inference) and $\rho_{\text{market}} = \varepsilon_{\mathrm{BTC}} / P_{\mathrm{BTC}} \cdot \ldots$ (how many standard tokens one bitcoin buys at market prices). $\Omega = \ln(\rho_{\text{parity}} / \rho_{\text{market}})$.

Full derivations and data sourcing are documented in the public methodology (Tang, 2026).

---

## 3. The degeneracy result

**Proposition.** Suppose the quality weight for model i is defined directly from its price, $q_i = p_i / p_{\text{ref}}$, for some reference price $p_{\text{ref}}$. Then, for any basket configuration, any weights $w_i$, and any date, $\Omega \equiv \ln \Lambda$.

**Proof.** Substituting $q_i = p_i / p_{\text{ref}}$ into $t_i = q_i / j_i$ gives $T = \sum_i w_i \, (p_i / p_{\text{ref}}) / j_i = (1/p_{\text{ref}}) \sum_i w_i \, p_i / j_i$. Then:


$$
\frac{\rho_{\text{parity}}}{\rho_{\text{market}}}
= \frac{\varepsilon_{\mathrm{BTC}} \cdot T \cdot p_{\text{ref}}}{P_{\mathrm{BTC}}}
= \frac{\varepsilon_{\mathrm{BTC}} \sum_i w_i \, p_i / j_i}{P_{\mathrm{BTC}}}
$$


Meanwhile $\Lambda = R_A/R_M = \bigl(k \sum_i w_i \, p_i / j_i\bigr) \big/ \bigl(k P_{\mathrm{BTC}} / \varepsilon_{\mathrm{BTC}}\bigr) = \varepsilon_{\mathrm{BTC}} \sum_i w_i \, p_i / j_i \big/ P_{\mathrm{BTC}}$ — the identical expression. Hence $\rho_{\text{parity}}/\rho_{\text{market}} \equiv \Lambda$, and $\Omega = \ln \Lambda$ for any configuration or date. ∎

The result is not an approximation or a coincidence under particular parameter values; it is an algebraic identity that holds regardless of the basket, the weights, or the date. Any index that (a) constructs a "quality" adjustment from price and (b) then reports whether price deviates from the quality-adjusted benchmark is, without knowing it, comparing a quantity to itself. The apparent second signal (the "quality-adjusted" one) carries zero information beyond the first.

**Empirical confirmation.** The initial internal release of TEPI (version 0) used exactly this construction, $q_i = p_i / p_{\text{ref}}$. On its first published snapshot, it reported $\Omega = 5.457 = \ln(234.4)$ — matching ln $\Lambda$ to the precision of the reported figures, exactly as the proposition predicts. This was not discovered by inspection of the formula alone; it was caught by the empirical coincidence of the two published numbers, which is itself a useful diagnostic for other practitioners: **if a "quality-adjusted" companion series to a price ratio is numerically indistinguishable from a monotonic transform of that ratio across every observation, the quality adjustment is very likely not doing any work.**

We are not aware of this specific degeneracy being named in the hedonic price-index literature, though we would not be surprised if it is a known failure mode under a different name; the broader caution that hedonic or quality weights must not be estimated from the same price data they are meant to adjust is consistent with standard concerns in that literature. We make no claim of priority — only that stating it in this explicit, provable form may be useful to other builders of cross-market or quality-adjusted indices, particularly outside contexts (like official CPI production) where this pitfall is already institutionally guarded against.

---

## 4. The fix, and its consequence

The current version of TEPI (v0.1) requires $q_i$ to come from a benchmark independent of price — currently the Artificial Analysis Intelligence Index, a third-party LLM evaluation that does not observe or use API pricing in its scoring. With this change, $\Omega$ is no longer identically equal to ln $\Lambda$. Using the verification run of 2026-08-16:

| Quantity | Value |
|---|---|
| $\Lambda$ (= $R_A / R_M$) | 233.93 |
| ln $\Lambda$ | 5.455 |
| $\Omega$ | 5.738 |
| Quality term ($\Omega - \ln \Lambda$) | 0.283 |
| Implied quality premium, $e^{\Omega - \ln \Lambda}$ | ≈ 1.33 |

The quality term is now genuinely informative and separable from the raw energy-arbitrage ratio: on this date, the four basket models were nearly quality-equivalent by the external benchmark (normalized weights 0.96–1.02) while spanning a 7.5× price range — meaning the market-implied premium for the higher-priced models exceeds what the independent capability measure can account for. This is a substantive, if narrow, empirical observation, and it is only visible because the quality signal is no longer definitionally tethered to the price it is meant to evaluate.

---

## 5. Independent cross-validation via Compute Heat Rate (CHR)

Compute Heat Rate (Royal, 2026) is an independently developed index that occupies the same conceptual space as TEPI — the intersection of energy and price for AI workloads — but approaches it from the opposite direction and with an entirely disjoint data pipeline. Where TEPI asks how much gross revenue one kWh earns in each use, CHR asks how high an electricity price a given AI workload tier can absorb before becoming unprofitable, net of non-electricity costs and a required return:


$$
\mathrm{CHR}_w = \frac{R_w - C_{\text{non-elec}}}{1 + m}
$$


CHR's inputs are vendor-direct API pricing (Anthropic, OpenAI, Google), GPU specifications and MLPerf inference benchmarks, and third-party data-center facility cost reports. None of these overlap with TEPI's inputs, which are OpenRouter's aggregated pricing and a working assumption for per-token energy consumption (1.0–3.0 J/token across the basket). CHR has been cited in a 2026 PJM (the largest U.S. grid operator) white paper on demand-response market design, indicating some degree of external, policy-facing traction independent of TEPI.

**Finding 1 — order-of-magnitude convergence in revenue per kWh.** Converting CHR's blended reference value (Q1 2026) to the same units as TEPI gives $R_w$ ≈ \$12.5/kWh, against TEPI's frontier-basket $R_A$ ≈ \$15.4/kWh — the same order of magnitude despite fully independent pricing sources. (We compare against CHR's underlying gross revenue, $R_w$, rather than CHR's headline net figure — the latter already nets out non-electricity costs and a required return, making it conceptually closer to a future profit-margin variant of TEPI, $\Lambda'$, than to the gross-revenue quantity $\Lambda$ is built from.) CHR's commodity-tier figure (\$1.85/kWh) implies a mining-to-inference ratio of roughly 28×, consistent with a commonly cited industry range of 20–25× for commodity-tier inference models — a range TEPI's own frontier-tier $\Lambda$ (234×) does not contradict, since it prices a different (higher-tier) basket. We note this explicitly: **the two figures are not measuring identical baskets**, and the appropriate reading is that both methods are internally consistent within their respective basket choices, not that either confirms the other's absolute level.

**Finding 2 — independent convergence on implied per-token energy.** Back-solving CHR's published tier revenues against vendor GPU specifications and MLPerf benchmarks implies a per-token energy cost of roughly 1.1–2.8 J/token for frontier and mid-tier inference. TEPI's independently chosen working assumption is 1.0–3.0 J/token. These two figures were arrived at through unrelated methods (CHR: hardware benchmarks and vendor-direct pricing; TEPI: a documented working assumption pending a formal sourcing appendix) and were not cross-checked during TEPI's initial specification. Their convergence is, in our judgment, meaningful evidence against the specific claim (which an earlier internal draft of this line of work had entertained) that TEPI's per-token energy assumption is systematically biased low by an order of magnitude.

**A note on the Q3 2026 update.** After this comparison was drafted, CHR published its Q3 2026 reference values (September 1, 2026). We flag this for two reasons rather than silently updating our numbers. First, the published blended CHR fell to ≈\$5,630/MWh, roughly 30% below Q2 — but CHR's own release attributes this primarily to a revised full-system power denominator (moving from a GPU-only power draw of 7.28 kW to a full-system facility-power reference of 13.26 kW) and a rebuilt workload taxonomy and weighting scheme, explicitly cautioning that the quarter-over-quarter change "should not be interpreted as a pure market-price movement." We deliberately did not re-run our comparison against the Q3 figures for this reason: doing so uncritically would risk exactly the error we caution against in Section 7 — conflating a methodology revision with a change in the underlying phenomenon. Second, CHR's Q3 release introduces a dispatch-focused companion metric, CHR-D, distinct from the long-run CHR used for build/siting decisions. This bifurcation parallels a limitation we flag in our own methodology (L3: TEPI's $R_A$ assumes 100% billable utilization and is therefore a long-run, upper-bound quantity, with no dispatch-level analogue yet published). We read this as a second, independent instance of two disjoint research efforts converging on the same structural distinction, and take it as further motivation for developing a utilization-adjusted variant of TEPI. We also note, approvingly, that CHR does not silently restate its Q1/Q2 figures under the new methodology — a discipline consistent with TEPI's own append-only, never-backfill practice.

We want to be precise about what these two findings do and do not establish. They are order-of-magnitude agreement between independent methods, which is a genuinely useful and comparatively rare form of early-stage validation for a class of index with essentially no formal peer review infrastructure. They are not a proof that both methods measure the same underlying economic quantity — utilization assumptions, cost bases (gross vs. net), and token accounting (input vs. output) differ between the two approaches in ways that could produce coincidental rather than structural agreement. We report this as a data point, not a confirmation.

---

## 6. Limitations

TEPI is explicit about its measurement boundaries, documented in full in the public methodology. In brief: it compares gross revenue, not profit (electricity is mining's dominant marginal cost but only a minor share of inference cost); it prices only output tokens, omitting input-token revenue and prefill energy; it assumes 100% billable utilization, making $R_A$ and $\Lambda$ upper bounds; network mining efficiency and per-token energy consumption are both hand-set, quarterly-reviewed parameters with quantified sensitivity; and the inference side currently relies on a single price aggregator, partially mitigated by a second, vendor-direct price source introduced in September 2026. A profit-margin variant ($\Lambda'$) is under active development; a preliminary trial using 2026 Q2 financial disclosures found a cash-cost-basis $\Lambda'$ substantially above the gross-revenue $\Lambda$, but a full-cost basis in which both mining and inference margins are negative — a result we consider important enough to warrant its own separate write-up before the variant is formally released.

---

## 7. Discussion

Two practical takeaways, offered to other builders of similarly novel, high-frequency, cross-market indices in fast-moving domains (AI economics, crypto-adjacent measurement) where formal peer review is slow or absent relative to the pace of the underlying phenomenon:

First, when constructing a quality or hedonic adjustment for a heterogeneous good, verify — algebraically, not just by inspection — that the adjustment weight cannot be reconstructed from the price series it is meant to evaluate. The failure mode is not always visible in the formula; it may only surface as an empirical coincidence between two supposedly independent published numbers, as it did here.

Second, independent cross-validation from a methodologically disjoint project, even an unreviewed one, is a meaningfully strong form of validation when it happens to be available — arguably more informative, at this stage, than the absence of a signal from formal peer review would suggest. We would encourage more explicit reporting of such comparisons, including negative results, as good practice for this class of real-time economic index.

All data and code underlying this note are public and versioned; we welcome scrutiny, replication, and disagreement.

---

## References

Balassa, B. (1964). The Purchasing-Power Parity Doctrine: A Reappraisal. *Journal of Political Economy*, 72(6), 584–596.

Baumol, W. J. (1990). Entrepreneurship: Productive, Unproductive, and Destructive. *Journal of Political Economy*, 98(5), 893–921.

ILO, IMF, OECD, Eurostat, UNECE, World Bank (2020). *Consumer Price Index Manual: Concepts and Methods.*

Royal, H. (2026). Compute Heat Rate. SSRN Working Paper (Abstract ID 6322318).

Samuelson, P. A. (1964). Theoretical Notes on Trade Problems. *Review of Economics and Statistics*, 46(2), 145–154.

Tang, H. (2026). TEPI — Token Energy Parity Index: Index Methodology v0.1. Abundantics Empirical Module 01. https://abundantics.org/en/index/methodology/
