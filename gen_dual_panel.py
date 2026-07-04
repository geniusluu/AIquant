#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成天齐锂业 A股+港股 双市场对比 HTML 面板"""

import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, "tianqi_data.json"), "r", encoding="utf-8") as f:
    a_records = json.load(f)
with open(os.path.join(BASE, "tianqi_hk_data.json"), "r", encoding="utf-8") as f:
    h_records = json.load(f)
with open(os.path.join(BASE, "analysis_result.json"), "r", encoding="utf-8") as f:
    analysis = json.load(f)

# A股数据
closes = [r["close"] for r in a_records]
def calc_ma(data, n):
    res = []
    for i in range(len(data)):
        if i < n - 1:
            res.append(None)
        else:
            res.append(round(sum(data[i-n+1:i+1]) / n, 2))
    return res

ma5_vals = calc_ma(closes, 5)
ma20_vals = calc_ma(closes, 20)

a_dates = [f"{r['trade_date'][:4]}-{r['trade_date'][4:6]}-{r['trade_date'][6:]}" for r in a_records]
a_ohlc = [[r["open"], r["close"], r["low"], r["high"]] for r in a_records]
a_vols = [round(r["vol"], 2) for r in a_records]
a_ma5 = ma5_vals
a_ma20 = ma20_vals
a_vol_colors = ["#E23A3A" if r["close"] >= r["open"] else "#2BA84A" for r in a_records]

# 港股数据
h_closes = [r["close"] for r in h_records]
h_ma5_vals = calc_ma(h_closes, 5)
h_ma20_vals = calc_ma(h_closes, 20)

h_dates = [f"{r['trade_date'][:4]}-{r['trade_date'][4:6]}-{r['trade_date'][6:]}" for r in h_records]
h_ohlc = [[r["open"], r["close"], r["low"], r["high"]] for r in h_records]
h_vols = [round(r["vol"], 2) for r in h_records]
h_ma5 = h_ma5_vals
h_ma20 = h_ma20_vals
h_vol_colors = ["#E23A3A" if r["close"] >= r["open"] else "#2BA84A" for r in h_records]

# 溢价率数据
a_by_date = {r["trade_date"]: r for r in a_records}
h_by_date = {r["trade_date"]: r for r in h_records}
common_dates = sorted(set(a_by_date.keys()) & set(h_by_date.keys()))
HKD_TO_CNY = 0.926

prem_dates = []
prem_values = []
a_close_norm = []
h_close_norm = []
for d in common_dates:
    a_p = a_by_date[d]["close"]
    h_p = h_by_date[d]["close"] * HKD_TO_CNY
    if h_p > 0:
        prem = round((a_p - h_p) / h_p * 100, 2)
        dfmt = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        prem_dates.append(dfmt)
        prem_values.append(prem)
        a_close_norm.append(round(a_by_date[d]["close"] / a_by_date[common_dates[0]]["close"] * 100, 2))
        h_close_norm.append(round(h_by_date[d]["close"] / h_by_date[common_dates[0]]["close"] * 100, 2))

chart_data = json.dumps({
    "a": {"dates": a_dates, "ohlc": a_ohlc, "vols": a_vols, "vol_colors": a_vol_colors, "ma5": a_ma5, "ma20": a_ma20},
    "h": {"dates": h_dates, "ohlc": h_ohlc, "vols": h_vols, "vol_colors": h_vol_colors, "ma5": h_ma5, "ma20": h_ma20},
    "premium": {"dates": prem_dates, "values": prem_values},
    "norm": {"dates": prem_dates, "a": a_close_norm, "h": h_close_norm},
}, ensure_ascii=False)

a = analysis
avg_prem = a['avg_premium']
a_dates_first = a_dates[0]
a_dates_last = a_dates[-1]
n_common = len(common_dates)
n_a = len(a_dates)
n_h = len(h_dates)

html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>天齐锂业 A股 vs 港股 · 双市场行情对比</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f0f2f5; color: #333;
  }
  .header {
    background: linear-gradient(135deg, #0f1923 0%, #1a2640 50%, #1a3a2e 100%);
    color: #fff; padding: 28px 40px;
  }
  .header h1 { font-size: 24px; font-weight: 600; display: flex; align-items: center; gap: 12px; }
  .header .codes { font-size: 15px; color: #6b7a90; font-weight: 400; }
  .header .subtitle { font-size: 13px; color: #6b7a90; margin-top: 6px; }
  .stats-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px; margin-top: 20px;
  }
  .stat-card {
    background: rgba(255,255,255,0.06); border-radius: 8px; padding: 14px 18px;
    border: 1px solid rgba(255,255,255,0.08);
  }
  .stat-label { font-size: 11px; color: #8e99ab; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
  .stat-value { font-size: 20px; font-weight: 600; }
  .stat-value.red { color: #ff6b6b; }
  .stat-value.green { color: #51cf66; }
  .stat-value.blue { color: #74c0fc; }
  .stat-value.yellow { color: #ffd43b; }
  .container { max-width: 1400px; margin: 24px auto; padding: 0 24px; }
  .chart-card {
    background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    padding: 24px; margin-bottom: 24px;
  }
  .chart-card h2 {
    font-size: 16px; font-weight: 600; margin-bottom: 4px; color: #1a1a2e;
    border-left: 4px solid; padding-left: 12px;
  }
  .chart-card.a-card h2 { border-color: #E23A3A; }
  .chart-card.h-card h2 { border-color: #1a73e8; }
  .chart-card.prem-card h2 { border-color: #FF9800; }
  .chart-card.corr-card h2 { border-color: #7B61FF; }
  .chart-desc { font-size: 12px; color: #999; margin-bottom: 16px; padding-left: 16px; }
  .chart { width: 100%; }
  .analysis-section {
    background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    padding: 32px; margin-bottom: 24px;
  }
  .analysis-section h2 {
    font-size: 18px; font-weight: 600; margin-bottom: 20px; color: #1a1a2e;
    border-left: 4px solid #1a73e8; padding-left: 12px;
  }
  .analysis-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
  @media (max-width: 900px) { .analysis-grid { grid-template-columns: 1fr; } }
  .analysis-block h3 {
    font-size: 15px; font-weight: 600; margin-bottom: 12px; color: #333;
    display: flex; align-items: center; gap: 8px;
  }
  .analysis-block.corr h3::before { content: ''; width: 8px; height: 8px; border-radius: 50%; display: inline-block; background: #7B61FF; }
  .analysis-block.prem h3::before { content: ''; width: 8px; height: 8px; border-radius: 50%; display: inline-block; background: #FF9800; }
  .analysis-block.active h3::before { content: ''; width: 8px; height: 8px; border-radius: 50%; display: inline-block; background: #E23A3A; }
  .analysis-block.band h3::before { content: ''; width: 8px; height: 8px; border-radius: 50%; display: inline-block; background: #1a73e8; }
  .analysis-block p { font-size: 14px; line-height: 1.8; color: #555; margin-bottom: 8px; }
  .analysis-block .highlight {
    background: #f0f4ff; padding: 2px 6px; border-radius: 4px; font-weight: 600; color: #1a73e8;
  }
  .band-table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 13px; }
  .band-table th { background: #f5f7fa; padding: 8px 12px; text-align: left; font-weight: 600; color: #666; }
  .band-table td { padding: 8px 12px; border-bottom: 1px solid #f0f0f0; }
  .band-table td.up { color: #E23A3A; font-weight: 600; }
  .band-table td.down { color: #2BA84A; font-weight: 600; }
  .footer { text-align: center; padding: 24px; font-size: 12px; color: #999; }
  .legend-note { font-size: 12px; color: #999; margin-top: 8px; display: flex; gap: 20px; flex-wrap: wrap; }
  .legend-note span { display: flex; align-items: center; gap: 6px; }
  .dot { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
  .company-intro {
    background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    padding: 32px; margin-bottom: 24px;
  }
  .company-intro h2 {
    font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1a1a2e;
    border-left: 4px solid #2BA84A; padding-left: 12px;
  }
  .company-intro p {
    font-size: 14px; line-height: 1.9; color: #555; margin-bottom: 12px; text-align: justify;
  }
  .company-intro .highlight {
    background: #e8f5e9; padding: 2px 6px; border-radius: 4px; font-weight: 600; color: #2e7d32;
  }
  .chart-insight {
    background: #f8f9fc; border-left: 3px solid #1a73e8; border-radius: 0 8px 8px 0;
    padding: 16px 20px; margin-top: 16px; font-size: 13px; line-height: 1.8; color: #444;
  }
  .chart-insight strong { color: #1a73e8; }
  .chart-card.a-card .chart-insight { border-left-color: #E23A3A; }
  .chart-card.a-card .chart-insight strong { color: #E23A3A; }
  .chart-card.h-card .chart-insight { border-left-color: #1a73e8; }
  .chart-card.h-card .chart-insight strong { color: #1a73e8; }
  .chart-card.prem-card .chart-insight { border-left-color: #FF9800; }
  .chart-card.prem-card .chart-insight strong { color: #FF9800; }
  .chart-card.corr-card .chart-insight { border-left-color: #7B61FF; }
  .chart-card.corr-card .chart-insight strong { color: #7B61FF; }
  .summary-section {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: #fff; border-radius: 12px; padding: 36px; margin-bottom: 24px;
  }
  .summary-section h2 {
    font-size: 20px; font-weight: 600; margin-bottom: 20px; color: #ffd43b;
    display: flex; align-items: center; gap: 10px;
  }
  .summary-section h2::before {
    content: ''; width: 4px; height: 24px; background: #ffd43b; border-radius: 2px; display: inline-block;
  }
  .summary-section p {
    font-size: 15px; line-height: 2; color: #c8d0e0; margin-bottom: 16px; text-align: justify;
  }
  .summary-section .key-point {
    background: rgba(255,212,59,0.1); padding: 2px 8px; border-radius: 4px;
    font-weight: 600; color: #ffd43b;
  }
</style>
</head>
<body>
<div class="header">
  <h1>天齐锂业 · A股 vs 港股 双市场行情对比</h1>
  <div class="codes">A股 002466.SZ · 深交所 ｜ 港股 09696.HK · 中国香港联交所</div>
  <div class="subtitle">__A_FIRST__ 至 __A_LAST__ ｜ 共同交易日 __N_COMMON__ 天 ｜ 汇率基准: 1 HKD ≈ 0.926 CNY</div>
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">A股区间涨幅</div>
      <div class="stat-value __A_CHG_CLASS__">__A_CHG__</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">港股区间涨幅</div>
      <div class="stat-value __H_CHG_CLASS__">__H_CHG__</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">日涨跌幅相关性</div>
      <div class="stat-value blue">__CORR__</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">平均AH溢价率</div>
      <div class="stat-value yellow">__AVG_PREM__%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">最新溢价率</div>
      <div class="stat-value yellow">__LATEST_PREM__%</div>
    </div>
  </div>
</div>

<div class="container">
  <div class="company-intro">
    <h2>公司简介 · 天齐锂业 (002466.SZ / 09696.HK)</h2>
    <p>天齐锂业是中国领先的锂新能源材料企业，主营业务涵盖<strong>硬岩型锂矿资源开发、锂精矿生产销售以及锂化工产品（碳酸锂、氢氧化锂等）的生产销售</strong>。公司控股全球最大、成本最低的硬岩锂矿——澳大利亚格林布什（Greenbushes）锂辉石矿（年产能214万吨锂精矿），同时参股智利SQM（全球最大盐湖锂资源商之一），形成了"矿石+盐湖"双轮驱动的资源布局，锂资源自给率行业领先。</p>
    <p>财务方面，2025年公司实现营业收入<span class="highlight">103.46亿元</span>（同比-20.8%），归母净利润<span class="highlight">4.63亿元</span>，成功扭亏为盈（2024年亏损79.05亿元）。2026年一季度业绩预告净利润<span class="highlight">17-20亿元</span>，同比增长<span class="highlight">1530%-1818%</span>，主要受益于锂价大幅上行与低成本矿产能释放。公司判断2026年全球锂行业供需将处于<span class="highlight">紧平衡</span>状态，上半年锂矿供应持续偏紧，新能源汽车与储能需求为核心增长引擎，中长期成长空间广阔。</p>
  </div>

  <div class="chart-card a-card">
    <h2>A股 002466.SZ · K线走势 & 成交量</h2>
    <div class="chart-desc">深交所 · 人民币计价 · 近一年 __N_A__ 个交易日</div>
    <div id="a-chart" class="chart" style="height:480px"></div>
    <div class="legend-note">
      <span><i class="dot" style="background:#E23A3A"></i> 阳线</span>
      <span><i class="dot" style="background:#2BA84A"></i> 阴线</span>
      <span><i class="dot" style="background:#FFB900"></i> MA5</span>
      <span><i class="dot" style="background:#7B61FF"></i> MA20</span>
    </div>
    <div class="chart-insight">
      <strong>图表解读：</strong>A股近一年走势可分为明显的五个阶段。7-8月受锂价见底预期催化，股价从¥32急涨至¥46（+44%），MA5快速上穿MA20形成金叉；随后8-9月获利回吐回调至¥42。9-11月走出一波主升浪，股价从¥42攀升至¥64（+52%），这是全年最大的趋势性上涨，对应碳酸锂期货价格反弹及三季报业绩改善预期。成交量方面，11月日均成交达100万手，为全年最活跃月份，量价齐升特征明显。11月至次年3月，股价从¥64深度回调至¥49（-23%），期间成交量逐步萎缩至日均41-43万手，市场进入缩量阴跌阶段。3月以来股价企稳反弹至¥59，MA20均线走平后再度向上，当前处于反弹趋势确认期。
    </div>
  </div>

  <div class="chart-card h-card">
    <h2>港股 09696.HK · K线走势 & 成交量</h2>
    <div class="chart-desc">中国香港联交所 · 港币计价 · 近一年 __N_H__ 个交易日</div>
    <div id="h-chart" class="chart" style="height:480px"></div>
    <div class="legend-note">
      <span><i class="dot" style="background:#E23A3A"></i> 阳线</span>
      <span><i class="dot" style="background:#2BA84A"></i> 阴线</span>
      <span><i class="dot" style="background:#FFB900"></i> MA5</span>
      <span><i class="dot" style="background:#7B61FF"></i> MA20</span>
    </div>
    <div class="chart-insight">
      <strong>图表解读：</strong>港股走势与A股高度同步，但波幅和绝对涨幅明显较小。港股从起始的HK$28.9涨至最新HK$40.3（+39.5%），远低于A股的+81%。几个关键差异值得关注：8月11日港股单日暴涨18.2%（A股当日+10%涨停未开），说明港股在极端行情中波动更剧烈；10月初港股一度冲至HK$50.8的阶段高点，彼时A股尚未创新高，港股领先约一周见顶。5月初港股触及全年最高HK$69.2，随后回调幅度（-42%）也大于A股同期回调（-28%），体现出港股对外资流动性更敏感、涨跌更高效的特征。成交量整体小于A股，但在关键转折点往往先于A股放量。
    </div>
  </div>

  <div class="chart-card prem-card">
    <h2>AH溢价率走势</h2>
    <div class="chart-desc">溢价率 = (A股价格 - 港股价格*汇率) / (港股价格*汇率) * 100% · 正值表示A股贵于港股</div>
    <div id="prem-chart" class="chart" style="height:360px"></div>
    <div class="chart-insight">
      <strong>图表解读：</strong>AH溢价率是衡量同一家公司在两个市场估值差异的核心指标。过去一年溢价率呈现"先收窄后急扩"的V型走势：起始时溢价约40%，8月初随着港股暴涨一度收窄至接近0%（即A股与港股几乎平价），这是外资集中看好锂业板块推高港股的结果。随后溢价率一路攀升，尤其进入2026年后加速上行，6月下旬触及全年最高的68.5%，当前维持在57%的高位。溢价率持续走扩意味着A股估值显著高于港股，背后的逻辑是：A股投资者更愿意为锂业成长性支付溢价，而港股受国际资金面和做空机制约束定价更为"理性"。高溢价状态下，需关注港股补涨或A股阶段性回调带来的均值回归风险。
    </div>
  </div>

  <div class="chart-card corr-card">
    <h2>标准化走势对比 (起始日 = 100)</h2>
    <div class="chart-desc">将两市场起始日收盘价标准化为100，直观对比涨跌幅度差异</div>
    <div id="corr-chart" class="chart" style="height:360px"></div>
    <div class="legend-note">
      <span><i class="dot" style="background:#E23A3A"></i> A股 (002466.SZ)</span>
      <span><i class="dot" style="background:#1a73e8"></i> 港股 (09696.HK)</span>
    </div>
    <div class="chart-insight">
      <strong>图表解读：</strong>将两市场起始日价格标准化为100后，可以清晰地看到A股（红线）的弹性显著大于港股（蓝线）。截至最新，A股指数升至约181，港股约139，差距超过40个百分点。两线在大部分时间内同涨同跌、方向一致，但斜率不同——A股上涨时涨得更快、下跌时也跌得更深。最典型的分化出现在2025年8月初和2026年5月：前者港股率先暴涨将两条线拉至接近重合，后者A股单边拉升将差距迅速拉开。这种"A强H弱"的格局，一方面源于A股散户和游资活跃度更高，另一方面也反映了内地资金对锂板块的偏好强于国际资金。当两条线差距过大时，往往预示着短期均值回归压力。
    </div>
  </div>

  <div class="analysis-section">
    <h2>分析摘要</h2>
    <div class="analysis-grid">
      <div class="analysis-block corr">
        <h3>相关性分析</h3>
        <p>过去一年中，天齐锂业A股与港股的<span class="highlight">日涨跌幅相关系数为 __CORR__</span>，属于<span class="highlight">高度正相关</span>。两个市场的日内涨跌方向高度一致，港股作为先行指标往往在盘前/盘中率先反应国际锂价和外围情绪，A股开盘后跟随。</p>
        <p>收盘价相关系数为 <span class="highlight">__CORR_PRICE__</span>，同样高度相关。整体走势趋同，但A股弹性更大——区间涨幅 __A_CHG__ 显著高于港股的 __H_CHG__，说明A股资金对锂业周期更敏感、投机性更强。</p>
      </div>
      <div class="analysis-block prem">
        <h3>AH溢价率</h3>
        <p>全年平均溢价率为 <span class="highlight">__AVG_PREM__%</span>，即A股整体比港股贵约四分之一。最高溢价出现在 <span class="highlight">__MAX_PREM_DATE__</span>（__MAX_PREM__%），最低接近折价水平在 <span class="highlight">__MIN_PREM_DATE__</span>（__MIN_PREM__%）。</p>
        <p>当前最新溢价率为 <span class="highlight">__LATEST_PREM__%</span>，处于历史较高区间。通常溢价率扩张发生在A股情绪亢奋、港股相对滞涨的阶段；溢价收窄则出现在港股补涨或A股回调时。</p>
      </div>
      <div class="analysis-block active">
        <h3>A股成交活跃度</h3>
        <p>全年日均成交量约 <span class="highlight">67.6万手</span>。最活跃的月份是 <span class="highlight">2025年11月</span>（日均约100万手），其次是 <span class="highlight">2026年4月</span>（80万手）和 <span class="highlight">2025年10月</span>（77万手）——这三段恰好对应锂价反弹预期和股价急涨急跌期。</p>
        <p>最冷清的是 <span class="highlight">2026年2-3月</span>（日均约41-43万手），属于横盘整理期。成交量峰值出现在 <span class="highlight">2025年10月30日</span>（181万手），当日大涨9%后放量。</p>
      </div>
      <div class="analysis-block band">
        <h3>A股主要波段区间</h3>
        <p>近一年A股经历了约 <span class="highlight">5个主要波段</span>：</p>
        <table class="band-table">
          <thead><tr><th>波段</th><th>时间</th><th>起点→终点</th><th>方向</th></tr></thead>
          <tbody>
            <tr><td>第1波段</td><td>2025.07-08</td><td>¥32 → ¥46</td><td class="up">↑ 急涨</td></tr>
            <tr><td>第2波段</td><td>2025.08-09</td><td>¥46 → ¥42</td><td class="down">↓ 回调</td></tr>
            <tr><td>第3波段</td><td>2025.09-11</td><td>¥42 → ¥64</td><td class="up">↑ 主升浪</td></tr>
            <tr><td>第4波段</td><td>2025.11-2026.03</td><td>¥64 → ¥49</td><td class="down">↓ 深度调整</td></tr>
            <tr><td>第5波段</td><td>2026.03-07</td><td>¥49 → ¥59</td><td class="up">↑ 反弹</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="summary-section">
    <h2>总结与后市展望</h2>
    <p><strong style="color:#fff">回顾：</strong>过去一年，天齐锂业A股和港股均录得显著涨幅（A股+81%、港股+39%），核心驱动来自锂价触底回升和公司业绩从巨亏到扭亏的拐点确认。2025年7月碳酸锂价格跌至周期底部后持续反弹，公司凭借格林布什低成本矿优势在价格底部依然盈利，2026年Q1净利润暴增15-18倍，基本面与股价形成正反馈。从市场结构看，A股弹性显著高于港股，AH溢价率从近0%扩大至57%，反映出国内资金对锂业成长性的更强偏好。</p>
    <p><strong style="color:#fff">展望：</strong>公司管理层判断2026年全球锂行业供需将维持<span class="key-point">紧平衡</span>格局，上半年锂矿供应持续偏紧。需求端，新能源汽车渗透率仍在提升、储能装机高速增长，叠加机器人、低空经济等新兴场景，中长期成长逻辑坚实。券商一致预期2026年公司净利润可达<span class="key-point">60.7亿元</span>（同比+1212%），每股收益3.57元，对应当前A股估值仍有下行保护。</p>
    <p><strong style="color:#fff">风险提示：</strong>需关注锂价短期波动风险（6月碳酸锂价格因淡季和库存担忧已有回调）、SQM股权处置的不确定性、以及当前AH溢价率处于历史高位可能带来的均值回归压力。从技术面看，A股经过3-7月的反弹后，MA20均线走平向上，中期趋势偏多，但短期在¥58-62区间存在获利盘压力，若放量突破则有望挑战前期高点¥82。</p>
    <p style="font-size:12px;color:#6b7a90;border-top:1px solid rgba(255,255,255,0.1);padding-top:16px;margin-top:8px;">以上分析基于公开市场数据，仅供学习研究参考，不构成任何投资建议。投资者应独立判断并自行承担投资风险。</p>
  </div>

  <div class="footer">数据来源：Tushare Pro (A股) / 东方财富 (港股) ｜ 生成时间：__A_LAST__ ｜ 仅供学习研究，不构成投资建议</div>
</div>

<script>
const D = __CHART_DATA__;
const upColor = '#E23A3A';
const downColor = '#2BA84A';

function makeKLine(elId, data, currency) {
  const chart = echarts.init(document.getElementById(elId));
  chart.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(15,25,35,0.92)', borderColor: '#333',
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: function(params) {
        let html = '<div style="font-weight:600;margin-bottom:4px">'+params[0].axisValue+'</div>';
        let kl = params.find(function(p){return p.seriesName==='K线'});
        if(kl){
          const r = data.ohlc[kl.dataIndex];
          const chg = ((r[1]-r[0])/r[0]*100).toFixed(2);
          const c = r[1]>=r[0]?upColor:downColor;
          html+='<div style="color:'+c+';font-size:13px;line-height:1.6">开 '+r[0]+' '+currency+'<br/>收 '+r[1]+' '+currency+'<br/>高 '+r[3]+'<br/>低 '+r[2]+'</div>';
        }
        let vol = params.find(function(p){return p.seriesName==='成交量'});
        if(vol) html+='<div style="color:#bbb;margin-top:2px">量 '+vol.data.toLocaleString()+'</div>';
        return html;
      }
    },
    axisPointer: { link: [{xAxisIndex:'all'}] },
    grid: [{left:'8%',right:'4%',top:'4%',height:'56%'},{left:'8%',right:'4%',top:'68%',height:'24%'}],
    xAxis: [
      {type:'category',data:data.dates,scale:true,boundaryGap:true,axisLine:{lineStyle:{color:'#ddd'}},axisLabel:{color:'#888',fontSize:11},min:'dataMin',max:'dataMax'},
      {type:'category',gridIndex:1,data:data.dates,scale:true,axisLabel:{show:false},axisTick:{show:false},axisLine:{lineStyle:{color:'#ddd'}}}
    ],
    yAxis: [
      {scale:true,splitLine:{lineStyle:{color:'#f0f0f0'}},axisLabel:{color:'#888',fontSize:11,formatter:function(v){return currency+v}}},
      {gridIndex:1,splitNumber:2,axisLabel:{color:'#888',fontSize:11},splitLine:{lineStyle:{color:'#f0f0f0'}}}
    ],
    dataZoom: [
      {type:'inside',xAxisIndex:[0,1],start:55,end:100},
      {show:true,type:'slider',xAxisIndex:[0,1],top:'94%',start:55,end:100,height:20,fillerColor:'rgba(26,115,232,0.1)',handleStyle:{color:'#1a73e8'}}
    ],
    series: [
      {name:'K线',type:'candlestick',data:data.ohlc,itemStyle:{color:upColor,color0:downColor,borderColor:upColor,borderColor0:downColor}},
      {name:'MA5',type:'line',data:data.ma5,smooth:true,showSymbol:false,lineStyle:{color:'#FFB900',width:1.5}},
      {name:'MA20',type:'line',data:data.ma20,smooth:true,showSymbol:false,lineStyle:{color:'#7B61FF',width:1.5}},
      {name:'成交量',type:'bar',xAxisIndex:1,yAxisIndex:1,data:data.vols.map(function(v,i){return {value:v,itemStyle:{color:data.vol_colors[i]}}})}
    ]
  });
  window.addEventListener('resize',function(){chart.resize()});
}

makeKLine('a-chart', D.a, '¥');
makeKLine('h-chart', D.h, 'HK$');

var premChart = echarts.init(document.getElementById('prem-chart'));
premChart.setOption({
  animation: false,
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(15,25,35,0.92)', borderColor: '#333',
    textStyle: {color:'#fff',fontSize:12},
    formatter: function(params){
      var p = params[0];
      var v = p.value;
      var color = v > 0 ? '#ff6b6b' : '#51cf66';
      return '<div style="font-weight:600">'+p.axisValue+'</div><div style="color:'+color+';font-size:14px;font-weight:600">溢价率 '+v+'%</div>';
    }
  },
  grid: {left:'8%',right:'4%',top:'8%',bottom:'18%'},
  xAxis: {type:'category',data:D.premium.dates,axisLine:{lineStyle:{color:'#ddd'}},axisLabel:{color:'#888',fontSize:11}},
  yAxis: {
    type:'value', name:'溢价率(%)',
    axisLabel:{color:'#888',fontSize:11,formatter:function(v){return v+'%'}},
    splitLine:{lineStyle:{color:'#f0f0f0'}},
    axisLine:{show:false}
  },
  dataZoom: [{type:'inside',start:55,end:100},{show:true,type:'slider',start:55,end:100,height:20,fillerColor:'rgba(255,152,0,0.1)',handleStyle:{color:'#FF9800'}}],
  series: [{
    name:'AH溢价率', type:'line', data:D.premium.values, smooth:true, showSymbol:false,
    lineStyle:{color:'#FF9800',width:2},
    areaStyle:{
      color:{type:'linear',x:0,y:0,x2:0,y2:1, colorStops:[{offset:0,color:'rgba(255,152,0,0.3)'},{offset:1,color:'rgba(255,152,0,0.02)'}]}
    },
    markLine:{
      symbol:'none',
      data:[
        {yAxis:0,lineStyle:{color:'#999',type:'dashed'},label:{formatter:'平价(0%)',color:'#999'}},
        {yAxis:__AVG_PREM__,lineStyle:{color:'#7B61FF',type:'dashed',width:1},label:{formatter:'均值 __AVG_PREM__%',color:'#7B61FF'}}
      ]
    }
  }]
});
window.addEventListener('resize',function(){premChart.resize()});

var corrChart = echarts.init(document.getElementById('corr-chart'));
corrChart.setOption({
  animation: false,
  tooltip: {
    trigger:'axis',
    backgroundColor:'rgba(15,25,35,0.92)',borderColor:'#333',
    textStyle:{color:'#fff',fontSize:12}
  },
  legend:{show:false},
  grid:{left:'8%',right:'4%',top:'8%',bottom:'18%'},
  xAxis:{type:'category',data:D.norm.dates,axisLine:{lineStyle:{color:'#ddd'}},axisLabel:{color:'#888',fontSize:11}},
  yAxis:{type:'value',name:'标准化指数(起始=100)',axisLabel:{color:'#888',fontSize:11},splitLine:{lineStyle:{color:'#f0f0f0'}},axisLine:{show:false}},
  dataZoom:[{type:'inside',start:0,end:100},{show:true,type:'slider',start:0,end:100,height:20}],
  series:[
    {name:'A股',type:'line',data:D.norm.a,smooth:true,showSymbol:false,lineStyle:{color:'#E23A3A',width:2},areaStyle:{color:'rgba(226,58,58,0.05)'}},
    {name:'港股',type:'line',data:D.norm.h,smooth:true,showSymbol:false,lineStyle:{color:'#1a73e8',width:2}}
  ]
});
window.addEventListener('resize',function(){corrChart.resize()});
</script>
</body>
</html>"""

# 替换占位符
a_chg_str = ("+" if a['a_period_change']>0 else "") + str(a['a_period_change']) + "%"
h_chg_str = ("+" if a['h_period_change']>0 else "") + str(a['h_period_change']) + "%"

replacements = {
    "__A_FIRST__": a_dates_first,
    "__A_LAST__": a_dates_last,
    "__N_COMMON__": str(n_common),
    "__N_A__": str(n_a),
    "__N_H__": str(n_h),
    "__A_CHG__": a_chg_str,
    "__H_CHG__": h_chg_str,
    "__A_CHG_CLASS__": "red" if a['a_period_change']>0 else "green",
    "__H_CHG_CLASS__": "red" if a['h_period_change']>0 else "green",
    "__CORR__": str(a['correlation_pct']),
    "__CORR_PRICE__": str(a['correlation_price']),
    "__AVG_PREM__": str(avg_prem),
    "__LATEST_PREM__": str(a['latest_premium']),
    "__MAX_PREM__": str(a['max_premium']),
    "__MIN_PREM__": str(a['min_premium']),
    "__MAX_PREM_DATE__": a['max_premium_date'],
    "__MIN_PREM_DATE__": a['min_premium_date'],
    "__CHART_DATA__": chart_data,
}

html = html_template
for key, val in replacements.items():
    html = html.replace(key, val)

out_path = os.path.join(BASE, "tianqi_dual_market.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"双市场对比面板已生成: {out_path}")
