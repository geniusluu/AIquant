#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天齐锂业 A股(002466.SZ) vs 港股(09696.HK) 对比分析 + 可视化面板"""

import json
import math
import os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))

# 加载数据
with open(os.path.join(BASE, "tianqi_data.json"), "r", encoding="utf-8") as f:
    a_records = json.load(f)
with open(os.path.join(BASE, "tianqi_hk_data.json"), "r", encoding="utf-8") as f:
    h_records = json.load(f)

# 建立日期索引
a_by_date = {r["trade_date"]: r for r in a_records}
h_by_date = {r["trade_date"]: r for r in h_records}

# 找共同交易日
common_dates = sorted(set(a_by_date.keys()) & set(h_by_date.keys()))
print(f"A股交易日: {len(a_records)}, 港股交易日: {len(h_records)}, 共同交易日: {len(common_dates)}")

# === 相关性分析（基于共同交易日的收盘价涨跌幅）===
a_pct = [a_by_date[d]["pct_chg"] for d in common_dates]
h_pct = [h_by_date[d]["pct_chg"] for d in common_dates]

def pearson(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((x[i]-mx)*(y[i]-my) for i in range(n))
    sx = math.sqrt(sum((xi-mx)**2 for xi in x))
    sy = math.sqrt(sum((yi-my)**2 for yi in y))
    if sx == 0 or sy == 0:
        return 0
    return cov / (sx * sy)

corr_pct = pearson(a_pct, h_pct)

# 收盘价相关（标准化对比走势）
a_close = [a_by_date[d]["close"] for d in common_dates]
h_close = [h_by_date[d]["close"] for d in common_dates]
corr_price = pearson(a_close, h_close)

print(f"\n=== 相关性分析 ===")
print(f"日涨跌幅相关系数: {corr_pct:.4f}")
print(f"收盘价相关系数: {corr_price:.4f}")

# === AH溢价率 ===
# AH溢价率 = (A股价格 - 港股价格×汇率) / (港股价格×汇率) × 100%
# 假设汇率约 1 CNY ≈ 1.08 HKD (即 1 HKD ≈ 0.926 CNY)
HKD_TO_CNY = 0.926

premiums = []
premium_dates = []
for d in common_dates:
    a_price = a_by_date[d]["close"]
    h_price_hkd = h_by_date[d]["close"]
    h_price_cny = h_price_hkd * HKD_TO_CNY
    if h_price_cny > 0:
        premium = (a_price - h_price_cny) / h_price_cny * 100
        premiums.append(round(premium, 2))
        premium_dates.append(d)

avg_premium = round(sum(premiums) / len(premiums), 2)
max_premium = max(premiums)
min_premium = min(premiums)
max_premium_date = premium_dates[premiums.index(max_premium)]
min_premium_date = premium_dates[premiums.index(min_premium)]
latest_premium = premiums[-1]

print(f"\n=== AH溢价率分析 (汇率: 1 HKD ≈ {HKD_TO_CNY} CNY) ===")
print(f"平均溢价率: {avg_premium}%")
print(f"最高溢价率: {max_premium}% ({max_premium_date})")
print(f"最低溢价率: {min_premium}% ({min_premium_date})")
print(f"最新溢价率: {latest_premium}% ({premium_dates[-1]})")

# === A股成交活跃度分析 ===
# 按月统计平均成交量
from collections import defaultdict
monthly_vol = defaultdict(list)
for r in a_records:
    month = r["trade_date"][:6]
    monthly_vol[month].append(r["vol"])

avg_vol = sum(r["vol"] for r in a_records) / len(a_records)
print(f"\n=== A股成交活跃度 ===")
print(f"全年日均成交量: {avg_vol:,.0f} 手")
print(f"\n月度平均成交量:")
for month in sorted(monthly_vol.keys()):
    mv = sum(monthly_vol[month]) / len(monthly_vol[month])
    bars = "█" * int(mv / avg_vol * 20)
    print(f"  {month}: {mv:>12,.0f} 手  {bars}")

# 找成交量最高的10天
vol_sorted = sorted(a_records, key=lambda x: -x["vol"])[:10]
print(f"\n成交量最高的10天:")
for r in vol_sorted:
    print(f"  {r['trade_date']}: {r['vol']:>12,.0f} 手  收:{r['close']}元")

# === A股波段识别 ===
# 简单波段识别：找局部极值（窗口=10天的前后比较）
WINDOW = 10
highs = []
lows = []
for i in range(WINDOW, len(a_records) - WINDOW):
    is_high = all(a_records[i]["close"] >= a_records[j]["close"] for j in range(i-WINDOW, i+WINDOW+1) if j != i)
    is_low = all(a_records[i]["close"] <= a_records[j]["close"] for j in range(i-WINDOW, i+WINDOW+1) if j != i)
    if is_high:
        highs.append(i)
    if is_low:
        lows.append(i)

print(f"\n=== A股主要波段（局部极值，窗口={WINDOW}天）===")
print(f"局部高点: {len(highs)} 个")
for idx in highs:
    print(f"  {a_records[idx]['trade_date']}: ¥{a_records[idx]['close']} (量:{a_records[idx]['vol']:,.0f})")
print(f"局部低点: {len(lows)} 个")
for idx in lows:
    print(f"  {a_records[idx]['trade_date']}: ¥{a_records[idx]['close']} (量:{a_records[idx]['vol']:,.0f})")

# === 输出统计摘要供HTML使用 ===
# A股关键统计
a_first_close = a_records[0]["close"]
a_last_close = a_records[-1]["close"]
a_period_change = round((a_last_close - a_first_close) / a_first_close * 100, 2)
a_high_idx = max(range(len(a_records)), key=lambda i: a_records[i]["high"])
a_low_idx = min(range(len(a_records)), key=lambda i: a_records[i]["low"])

# 港股关键统计
h_first_close = h_records[0]["close"]
h_last_close = h_records[-1]["close"]
h_period_change = round((h_last_close - h_first_close) / h_first_close * 100, 2)
h_high_idx = max(range(len(h_records)), key=lambda i: h_records[i]["high"])
h_low_idx = min(range(len(h_records)), key=lambda i: h_records[i]["low"])

# 波段标注（取主要波段：显著高点和低点交替）
# 识别主要趋势波段 - 手动标注基于数据分析
bands = []

# 将分析结果输出供后续HTML生成
analysis = {
    "correlation_pct": round(corr_pct, 4),
    "correlation_price": round(corr_price, 4),
    "avg_premium": avg_premium,
    "max_premium": max_premium,
    "min_premium": min_premium,
    "max_premium_date": max_premium_date,
    "min_premium_date": min_premium_date,
    "latest_premium": latest_premium,
    "a_period_change": a_period_change,
    "h_period_change": h_period_change,
    "a_high": {"date": a_records[a_high_idx]["trade_date"], "price": a_records[a_high_idx]["high"]},
    "a_low": {"date": a_records[a_low_idx]["trade_date"], "price": a_records[a_low_idx]["low"]},
    "h_high": {"date": h_records[h_high_idx]["trade_date"], "price": h_records[h_high_idx]["high"]},
    "h_low": {"date": h_records[h_low_idx]["trade_date"], "price": h_records[h_low_idx]["low"]},
}

with open(os.path.join(BASE, "analysis_result.json"), "w", encoding="utf-8") as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)

print(f"\n分析结果已保存至 analysis_result.json")
print(json.dumps(analysis, ensure_ascii=False, indent=2))
