#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读取 tianqi_data.json，生成内嵌数据的 HTML K线面板"""

import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "tianqi_data.json"), "r", encoding="utf-8") as f:
    records = json.load(f)

# 构造 ECharts 所需数据
dates = []
ohlc = []   # [open, close, low, high]  (echarts candlestick 顺序)
vols = []
ma5 = []
ma20 = []
vol_colors = []

closes = [r["close"] for r in records]

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

for i, r in enumerate(records):
    # 日期格式化为 YYYY-MM-DD
    d = r["trade_date"]
    d_fmt = f"{d[:4]}-{d[4:6]}-{d[6:]}"
    dates.append(d_fmt)
    ohlc.append([r["open"], r["close"], r["low"], r["high"]])
    vols.append(round(r["vol"], 2))
    ma5.append(ma5_vals[i])
    ma20.append(ma20_vals[i])
    # 涨红跌绿（中国惯例）
    if r["close"] >= r["open"]:
        vol_colors.append("#E23A3A")  # 红
    else:
        vol_colors.append("#2BA84A")  # 绿

# 统计摘要
first_close = closes[0]
last_close = closes[-1]
period_change = round((last_close - first_close) / first_close * 100, 2)
high_idx = closes.index(max(closes))
low_idx = closes.index(min(closes))
avg_vol = round(sum(vols) / len(vols))

data_json = json.dumps({
    "dates": dates,
    "ohlc": ohlc,
    "vols": vols,
    "vol_colors": vol_colors,
    "ma5": ma5,
    "ma20": ma20,
}, ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>天齐锂业 002466.SZ · K线行情面板</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f0f2f5;
    color: #333;
    min-height: 100vh;
  }}
  .header {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: #fff;
    padding: 24px 40px;
  }}
  .header h1 {{
    font-size: 24px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .header .stock-code {{
    font-size: 16px;
    color: #8e99ab;
    font-weight: 400;
  }}
  .header .subtitle {{
    font-size: 13px;
    color: #8e99ab;
    margin-top: 6px;
  }}
  .stats {{
    display: flex;
    gap: 48px;
    margin-top: 20px;
    flex-wrap: wrap;
  }}
  .stat-item {{
    display: flex;
    flex-direction: column;
  }}
  .stat-label {{
    font-size: 12px;
    color: #8e99ab;
    margin-bottom: 4px;
  }}
  .stat-value {{
    font-size: 22px;
    font-weight: 600;
  }}
  .stat-value.up {{ color: #ff4d4f; }}
  .stat-value.down {{ color: #2BA84A; }}
  .stat-value.neutral {{ color: #fff; }}
  .container {{
    max-width: 1200px;
    margin: 24px auto;
    padding: 0 24px;
  }}
  .chart-card {{
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    padding: 24px;
    margin-bottom: 24px;
  }}
  .chart-card h2 {{
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    color: #1a1a2e;
    border-left: 4px solid #1a73e8;
    padding-left: 12px;
  }}
  #kline-chart {{
    width: 100%;
    height: 520px;
  }}
  .footer {{
    text-align: center;
    padding: 24px;
    font-size: 12px;
    color: #999;
  }}
  .legend-note {{
    font-size: 12px;
    color: #999;
    margin-top: 8px;
    display: flex;
    gap: 24px;
    justify-content: center;
  }}
  .legend-note span {{
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .dot {{
    width: 10px;
    height: 10px;
    border-radius: 2px;
    display: inline-block;
  }}
</style>
</head>
<body>
<div class="header">
  <h1>天齐锂业 <span class="stock-code">002466.SZ · 深圳证券交易所</span></h1>
  <div class="subtitle">近一年日线行情 · {dates[0]} 至 {dates[-1]} · 共 {len(dates)} 个交易日</div>
  <div class="stats">
    <div class="stat-item">
      <span class="stat-label">最新收盘价</span>
      <span class="stat-value neutral">¥{last_close}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">区间涨跌幅</span>
      <span class="stat-value {'up' if period_change > 0 else 'down' if period_change < 0 else 'neutral'}">
        {'+' if period_change > 0 else ''}{period_change}%
      </span>
    </div>
    <div class="stat-item">
      <span class="stat-label">期间最高价</span>
      <span class="stat-value neutral">¥{records[high_idx]['high']} <small style="font-size:13px;color:#8e99ab;font-weight:400">({dates[high_idx]})</small></span>
    </div>
    <div class="stat-item">
      <span class="stat-label">期间最低价</span>
      <span class="stat-value neutral">¥{records[low_idx]['low']} <small style="font-size:13px;color:#8e99ab;font-weight:400">({dates[low_idx]})</small></span>
    </div>
    <div class="stat-item">
      <span class="stat-label">日均成交量</span>
      <span class="stat-value neutral">{avg_vol:,} 手</span>
    </div>
  </div>
</div>

<div class="container">
  <div class="chart-card">
    <h2>K线走势 & 交易量</h2>
    <div id="kline-chart"></div>
    <div class="legend-note">
      <span><i class="dot" style="background:#E23A3A"></i> 阳线（收盘 ≥ 开盘）</span>
      <span><i class="dot" style="background:#2BA84A"></i> 阴线（收盘 &lt; 开盘）</span>
      <span><i class="dot" style="background:#FFB900"></i> MA5 均线</span>
      <span><i class="dot" style="background:#7B61FF"></i> MA20 均线</span>
    </div>
  </div>
  <div class="footer">数据来源：Tushare Pro · 生成时间：{dates[-1]} · 仅供学习研究，不构成投资建议</div>
</div>

<script>
const rawData = {data_json};

const chart = echarts.init(document.getElementById('kline-chart'));

const upColor = '#E23A3A';
const downColor = '#2BA84A';

chart.setOption({{
  animation: false,
  tooltip: {{
    trigger: 'axis',
    axisPointer: {{ type: 'cross' }},
    backgroundColor: 'rgba(26,26,46,0.92)',
    borderColor: '#333',
    textStyle: {{ color: '#fff', fontSize: 12 }},
    formatter: function(params) {{
      let html = '<div style="font-weight:600;margin-bottom:6px">' + params[0].axisValue + '</div>';
      let price = params.find(p => p.seriesName === '日K');
      if (price) {{
        const d = price.data;
        const raw = rawData.ohlc[price.dataIndex];
        const chg = ((raw[1] - raw[0]) / raw[0] * 100).toFixed(2);
        const color = raw[1] >= raw[0] ? upColor : downColor;
        html += '<div style="color:'+color+';font-size:13px;line-height:1.7">';
        html += '开盘 ' + raw[0] + '<br/>';
        html += '收盘 ' + raw[1] + '<br/>';
        html += '最高 ' + raw[3] + '<br/>';
        html += '最低 ' + raw[2] + '<br/>';
        html += '涨跌 <b>' + ('+' + chg).replace('+-','-') + '%</b>';
        html += '</div>';
      }}
      let vol = params.find(p => p.seriesName === '成交量');
      if (vol) {{
        html += '<div style="color:#bbb;margin-top:4px">成交量 ' + vol.data.toLocaleString() + ' 手</div>';
      }}
      return html;
    }}
  }},
  axisPointer: {{
    link: [{{ xAxisIndex: 'all' }}]
  }},
  grid: [
    {{ left: '8%', right: '4%', top: '4%', height: '58%' }},
    {{ left: '8%', right: '4%', top: '70%', height: '22%' }}
  ],
  xAxis: [
    {{
      type: 'category',
      data: rawData.dates,
      scale: true,
      boundaryGap: true,
      splitLine: {{ show: false }},
      axisLabel: {{ color: '#888', fontSize: 11 }},
      min: 'dataMin',
      max: 'dataMax',
      axisLine: {{ lineStyle: {{ color: '#ddd' }} }}
    }},
    {{
      type: 'category',
      gridIndex: 1,
      data: rawData.dates,
      scale: true,
      boundaryGap: true,
      splitLine: {{ show: false }},
      axisLabel: {{ show: false }},
      axisTick: {{ show: false }},
      min: 'dataMin',
      max: 'dataMax',
      axisLine: {{ lineStyle: {{ color: '#ddd' }} }}
    }}
  ],
  yAxis: [
    {{
      scale: true,
      splitLine: {{ lineStyle: {{ color: '#f0f0f0' }} }},
      axisLabel: {{ color: '#888', fontSize: 11, formatter: function(v) {{ return '¥' + v; }} }},
    }},
    {{
      gridIndex: 1,
      splitNumber: 2,
      axisLabel: {{ color: '#888', fontSize: 11, formatter: function(v) {{ return (v/10000).toFixed(1)+'万'; }} }},
      splitLine: {{ lineStyle: {{ color: '#f0f0f0' }} }},
    }}
  ],
  dataZoom: [
    {{
      type: 'inside',
      xAxisIndex: [0, 1],
      start: 60,
      end: 100
    }},
    {{
      show: true,
      type: 'slider',
      xAxisIndex: [0, 1],
      top: '94%',
      start: 60,
      end: 100,
      height: 20,
      borderColor: '#e0e0e0',
      fillerColor: 'rgba(26,115,232,0.1)',
      handleStyle: {{ color: '#1a73e8' }}
    }}
  ],
  series: [
    {{
      name: '日K',
      type: 'candlestick',
      data: rawData.ohlc,
      itemStyle: {{
        color: upColor,
        color0: downColor,
        borderColor: upColor,
        borderColor0: downColor
      }}
    }},
    {{
      name: 'MA5',
      type: 'line',
      data: rawData.ma5,
      smooth: true,
      showSymbol: false,
      lineStyle: {{ color: '#FFB900', width: 1.5 }},
      z: 5
    }},
    {{
      name: 'MA20',
      type: 'line',
      data: rawData.ma20,
      smooth: true,
      showSymbol: false,
      lineStyle: {{ color: '#7B61FF', width: 1.5 }},
      z: 5
    }},
    {{
      name: '成交量',
      type: 'bar',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: rawData.vols.map((v, i) => ({{
        value: v,
        itemStyle: {{ color: rawData.vol_colors[i] }}
      }})),
    }}
  ]
}});

window.addEventListener('resize', () => chart.resize());
</script>
</body>
</html>"""

out_path = os.path.join(BASE, "tianqi_dashboard.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML 面板已生成: {out_path}")
