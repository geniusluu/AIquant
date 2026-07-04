#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成天齐锂业技术指标综合 HTML 面板（含 KDJ）
- 嵌入 RSI / MACD / 布林带 / KDJ / 综合视图 五张 PNG
- 自包含，无需联网
"""

import base64
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHART_DIR = os.path.join(BASE, "TASK02", "charts")

def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

charts = {
    "rsi": os.path.join(CHART_DIR, "rsi_tianqi.png"),
    "macd": os.path.join(CHART_DIR, "macd_tianqi.png"),
    "boll": os.path.join(CHART_DIR, "boll_tianqi.png"),
    "kdj": os.path.join(CHART_DIR, "kdj_tianqi.png"),
    "combined": os.path.join(CHART_DIR, "combined_tianqi.png"),
}

imgs = {k: img_to_base64(v) for k, v in charts.items()}

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>天齐锂业(002466.SZ) · 技术指标分析面板（四指标版）</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #f0f2f5;
    color: #333;
  }}
  .header {{
    background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
    color: #fff;
    padding: 28px 40px 22px;
  }}
  .header h1 {{ font-size: 22px; font-weight: 700; letter-spacing: 1px; }}
  .header .sub {{ font-size: 13px; opacity: 0.75; margin-top: 6px; }}
  .badge-row {{ display: flex; gap: 10px; margin-top: 16px; flex-wrap: wrap; }}
  .badge {{
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 13px;
    line-height: 1.5;
  }}
  .badge .val {{ font-size: 16px; font-weight: 700; color: #FFD54F; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 28px 24px 60px; }}
  .card {{
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 28px;
    overflow: hidden;
  }}
  .card-hd {{
    padding: 16px 24px 12px;
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .card-hd .icon {{
    width: 32px; height: 32px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; color: #fff; font-weight: 700;
  }}
  .card-hd h2 {{ font-size: 15px; font-weight: 600; }}
  .card-hd .tag {{ margin-left: auto; font-size: 11px; color: #999; background: #f5f5f5; padding: 3px 10px; border-radius: 4px; }}
  .card-bd {{ padding: 16px 20px; }}
  .chart-img {{ width: 100%; border-radius: 6px; display: block; }}
  .insight {{
    margin-top: 14px;
    background: #f8f9fa;
    border-left: 3px solid #1a73e8;
    border-radius: 0 6px 6px 0;
    padding: 12px 18px;
    font-size: 13px;
    line-height: 1.8;
    color: #444;
  }}
  .insight strong {{ color: #1a73e8; }}
  .insight .red {{ color: #D32F2F; font-weight: 600; }}
  .insight .green {{ color: #388E3C; font-weight: 600; }}
  /* 指标配合逻辑专用样式 */
  .combo-section {{
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 28px;
    overflow: hidden;
  }}
  .combo-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    padding: 20px 24px;
  }}
  .combo-item {{
    border: 1px solid #e8eaf0;
    border-radius: 8px;
    padding: 16px 18px;
    background: #fafbfc;
  }}
  .combo-item h3 {{
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .combo-item h3 .pill {{
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 500;
  }}
  .combo-item .buy {{ background: #FFEBEE; color: #C62828; }}
  .combo-item .sell {{ background: #E8F5E9; color: #2E7D32; }}
  .combo-item p {{ font-size: 12.5px; line-height: 1.7; color: #555; }}
  @media (max-width: 800px) {{
    .combo-grid {{ grid-template-columns: 1fr; }}
    .header {{ padding: 20px 20px 16px; }}
    .container {{ padding: 16px 12px 40px; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>📊 天齐锂业 (002466.SZ) · 四指标技术分析</h1>
  <div class="sub">数据区间：2025-07-04 ~ 2026-07-03（近一年，242个交易日）</div>
  <div class="badge-row">
    <div class="badge">RSI(14) <span class="val">42.16</span></div>
    <div class="badge">MACD 金/死叉 <span class="val">8 / 8</span></div>
    <div class="badge">布林带上/下轨 <span class="val">33 / 9</span></div>
    <div class="badge">KDJ K/D/J <span class="val">32.95 / 42.49 / 13.89</span></div>
    <div class="badge">KDJ 金/死叉 <span class="val">24 / 24</span></div>
    <div class="badge">KDJ K&lt;20 <span class="val">26</span> 天</div>
  </div>
</div>

<div class="container">

  <!-- ===== RSI ===== -->
  <div class="card">
    <div class="card-hd">
      <div class="icon" style="background:#1976D2;">R</div>
      <h2>RSI 相对强弱指标 (14日)</h2>
      <span class="tag">超买线70 / 超卖线30</span>
    </div>
    <div class="card-bd">
      <img class="chart-img" src="data:image/png;base64,{imgs['rsi']}" alt="RSI图表">
      <div class="insight">
        <strong>📌 原理与解读：</strong><br>
        RSI 衡量一段时期内<span class="red">上涨幅度</span>占<span class="green">涨跌总幅度</span>的比例，值域 0~100。<br>
        • RSI &gt; 70 为<strong>超买</strong>（短期涨幅过大，回调风险增加）；RSI &lt; 30 为<strong>超卖</strong>（短期跌幅过大，反弹概率增大）。<br>
        • 最新值 <strong>42.16</strong>，中性偏弱。近一年 23 天超买、仅 1 天超卖，说明整体偏强但近期动能减弱。
      </div>
    </div>
  </div>

  <!-- ===== MACD ===== -->
  <div class="card">
    <div class="card-hd">
      <div class="icon" style="background:#F57C00;">M</div>
      <h2>MACD 指标 (12,26,9)</h2>
      <span class="tag">DIF快线 / DEA慢线 / MACD柱</span>
    </div>
    <div class="card-bd">
      <img class="chart-img" src="data:image/png;base64,{imgs['macd']}" alt="MACD图表">
      <div class="insight">
        <strong>📌 原理与解读：</strong><br>
        MACD = 快慢均线差离值。DIF（快线）上穿 DEA（慢线）为<span class="red">金叉（买入信号）</span>，下穿为<span class="green">死叉（卖出信号）</span>。<br>
        • 近一年 <strong>8 次金叉 / 8 次死叉</strong>，多空交替频繁，呈震荡格局。<br>
        • MACD 柱由红转绿通常领先价格见顶；由绿转红领先价格见底。
      </div>
    </div>
  </div>

  <!-- ===== 布林带 ===== -->
  <div class="card">
    <div class="card-hd">
      <div class="icon" style="background:#388E3C;">B</div>
      <h2>布林带 (20日, 2倍标准差)</h2>
      <span class="tag">上轨+2σ / 中轨MA20 / 下轨-2σ</span>
    </div>
    <div class="card-bd">
      <img class="chart-img" src="data:image/png;base64,{imgs['boll']}" alt="布林带图表">
      <div class="insight">
        <strong>📌 原理与解读：</strong><br>
        布林带用统计标准差衡量价格波动的边界。<strong>收窄</strong>＝波动率压缩（变盘前兆）；<strong>张口</strong>＝趋势启动。<br>
        • 近一年 <strong>33 天</strong>触及上轨 vs <strong>9 天</strong>触及下轨，整体偏强。<br>
        • 股价沿上轨运行为强势特征；跌破中轨（MA20）需警惕中期走弱。
      </div>
    </div>
  </div>

  <!-- ===== KDJ ===== -->
  <div class="card">
    <div class="card-hd">
      <div class="icon" style="background:#7B1FA2;">K</div>
      <h2>KDJ 随机指标 (9,3,3)</h2>
      <span class="tag">K线 / D线 / J线</span>
    </div>
    <div class="card-bd">
      <img class="chart-img" src="data:image/png;base64,{imgs['kdj']}" alt="KDJ图表">
      <div class="insight">
        <strong>📌 KDJ 原理：</strong><br>
        KDJ 是一种<strong>随机震荡指标</strong>，核心思想是衡量"当前收盘价在近期价格区间中的位置"。<br><br>
        <strong>计算步骤：</strong><br>
        ① <code>RSV = (收盘价 − 9日最低价) / (9日最高价 − 9日最低价) × 100</code><br>
        &nbsp;&nbsp;&nbsp;RSV 越接近 100，说明收盘价越接近近期高点（多头占优）<br>
        ② <code>K = 2/3 × 昨日K + 1/3 × 今日RSV</code>（对 RSV 做 3 日平滑）<br>
        ③ <code>D = 2/3 × 昨日D + 1/3 × 今日K</code>（再对 K 做一次平滑）<br>
        ④ <code>J = 3K − 2D</code>（J 是 K、D 的放大差值，灵敏度最高）<br><br>
        <strong>信号规则：</strong><br>
        • <span class="red">K &gt; 80 为超买区</span>（短期过热，回调风险）；<span class="green">K &lt; 20 为超卖区</span>（短期超跌，反弹概率大）<br>
        • K 上穿 D = <span class="red">金叉（买入）</span>；K 下穿 D = <span class="green">死叉（卖出）</span><br>
        • <strong>J &gt; 100</strong>：极度超买（K、D 差距被放大到极端，见顶信号）<br>
        • <strong>J &lt; 0</strong>：极度超卖（见底信号，J 的负值越大反弹动能越强）<br><br>
        <strong>📌 本股数据解读：</strong><br>
        • 最新 K=32.95 / D=42.49 / J=13.89，K&lt;D 且 J 偏低，短期偏弱但尚未进入超卖区。<br>
        • 近一年 <strong>24 次金叉 / 24 次死叉</strong>，信号频繁——KDJ 灵敏度高，适合捕捉短期转折，但<strong>单独使用容易产生虚假信号</strong>，需配合其他指标过滤。<br>
        • K&lt;20 共 <strong>26 天</strong>（超卖），J&gt;100 共 <strong>19 天</strong>（极度超买），J&lt;0 共 <strong>13 天</strong>（极度超卖），说明股价波动幅度较大。
      </div>
    </div>
  </div>

  <!-- ===== 指标配合逻辑 ===== -->
  <div class="combo-section">
    <div class="card-hd" style="padding:16px 24px 12px;">
      <div class="icon" style="background:#00695C;">★</div>
      <h2>四指标配合逻辑 — 多指标共振策略</h2>
      <span class="tag">交叉验证</span>
    </div>
    <div class="combo-grid">

      <div class="combo-item">
        <h3>① KDJ + MACD 共振 <span class="pill buy">买入共振</span></h3>
        <p>
          <strong>逻辑</strong>：KDJ 灵敏度高（捕捉短期转折），MACD 更稳定（确认中期趋势）。<br>
          <strong>买入</strong>：KDJ 金叉 <em>且</em> MACD 同步金叉（或 MACD 柱由绿转红）→ 短期与中期动能同时转正，信号可靠度高。<br>
          <strong>过滤</strong>：若 KDJ 金叉但 MACD 仍死叉，则为"弱信号"，可能是熊市反弹，需谨慎。
        </p>
      </div>

      <div class="combo-item">
        <h3>② KDJ + RSI 双确认 <span class="pill sell">卖出共振</span></h3>
        <p>
          <strong>逻辑</strong>：两者都是震荡指标（0~100），但 KDJ 对价格高低敏感，RSI 对涨跌幅度敏感。<br>
          <strong>超买共振</strong>：K &gt; 80 <em>且</em> RSI &gt; 70 → 双重超买，见顶概率大幅提升。<br>
          <strong>超卖共振</strong>：K &lt; 20 <em>且</em> RSI &lt; 30 → 双重超卖，反弹概率增大。<br>
          两者同时极端比单一指标更可信。
        </p>
      </div>

      <div class="combo-item">
        <h3>③ KDJ + 布林带 位置确认 <span class="pill buy">轨道过滤</span></h3>
        <p>
          <strong>逻辑</strong>：布林带提供价格运行的"轨道边界"，KDJ 提供拐点信号。<br>
          <strong>有效买入</strong>：KDJ 金叉发生在<strong>布林带下轨附近</strong>（股价超跌反弹）→ 信号有效。<br>
          <strong>有效卖出</strong>：KDJ 死叉发生在<strong>布林带上轨附近</strong>（股价超买回落）→ 信号有效。<br>
          <strong>过滤</strong>：KDJ 金叉但股价在中轨上方远离下轨 → 可能是趋势中继而非底部反转。
        </p>
      </div>

      <div class="combo-item">
        <h3>④ MACD + 布林带 趋势确认 <span class="pill buy">趋势共振</span></h3>
        <p>
          <strong>逻辑</strong>：MACD 判断趋势方向，布林带判断波动率状态。<br>
          <strong>趋势启动</strong>：布林带由<strong>收窄转为张口</strong>（波动率扩张）<em>且</em> MACD 金叉 → 新趋势确认，可追涨。<br>
          <strong>趋势衰竭</strong>：股价触及上轨 <em>且</em> MACD 死叉 → 上涨动能衰竭，逢高减仓。<br>
          这组配合能过滤掉震荡期的虚假 MACD 信号。
        </p>
      </div>

      <div class="combo-item">
        <h3>⑤ 全指标共振（最强信号） <span class="pill buy">四指标共振</span></h3>
        <p>
          <strong>买入共振</strong>：KDJ 金叉 + MACD 金叉 + RSI 从超卖回升 + 股价触及布林带下轨<br>
          → 四个指标从不同维度（价格位置/动量/波动率/震荡）同时给出买入信号，<strong>可靠度最高</strong>。<br>
          <strong>卖出共振</strong>：KDJ 死叉 + MACD 死叉 + RSI 超买回落 + 股价触及上轨<br>
          → 多维卖出共振，减仓/离场优先级最高。
        </p>
      </div>

      <div class="combo-item">
        <h3>⑥ J 值极端反转（KDJ 独有） <span class="pill sell">J 值信号</span></h3>
        <p>
          <strong>逻辑</strong>：J = 3K − 2D，当 K、D 差距极端放大时，J 会突破 0~100 边界。<br>
          <strong>J &gt; 100</strong>：短期极度超买，通常在 1~3 日内见顶回落（天齐近一年出现 19 次）。<br>
          <strong>J &lt; 0</strong>：短期极度超卖，通常在 1~3 日内见底反弹（天齐近一年出现 13 次）。<br>
          <strong>配合</strong>：J 值极端 <em>且</em> 布林带触及对应轨道 → 反转概率极高。
        </p>
      </div>

    </div>
    <div style="padding:0 24px 20px;">
      <div class="insight" style="border-left-color:#00695C;">
        <strong>⚠️ 重要提示：</strong>多指标共振可以提高信号可靠度，但<strong>没有任何指标组合是完美的</strong>。
        技术指标本质是对历史价格的统计总结，在强势趋势中可能出现持续超买（指标钝化），在低波动横盘中可能出现频繁假信号。
        实际交易中需结合<strong>成交量确认、基本面分析、仓位管理</strong>综合决策。以上分析不构成投资建议。
      </div>
    </div>
  </div>

  <!-- ===== 综合视图 ===== -->
  <div class="card">
    <div class="card-hd">
      <div class="icon" style="background:#37474F;">★</div>
      <h2>综合视图（价格 + 布林带 + MACD + RSI + KDJ + 成交量）</h2>
      <span class="tag">全指标叠加</span>
    </div>
    <div class="card-bd">
      <img class="chart-img" src="data:image/png;base64,{imgs['combined']}" alt="综合视图">
    </div>
  </div>

  <div style="text-align:center;color:#aaa;font-size:12px;margin-top:20px;">
    数据来源：Tushare Pro · 计算与绘图：Python/Matplotlib · 四指标版（RSI + MACD + 布林带 + KDJ）· 2026-07-04
  </div>

</div>
</body>
</html>"""

OUT = os.path.join(BASE, "TASK02", "tianqi_indicators.html")
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"HTML 面板已生成：{OUT}")
