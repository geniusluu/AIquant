#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK02 · 天齐锂业 A 股技术指标计算与可视化
- 数据源：TASK1-2/raw_data/tianqi_data.json（近一年日线 raw 行情）
- 指标：RSI(14) / MACD(12,26,9) / 布林带(20,2) / KDJ(9,3,3)
- 绘图：matplotlib，遵循中国股市惯例（红涨绿跌）
"""

import json
import math
import os

# ---- matplotlib 配置（必须在 import pyplot 前设置）----
os.environ["MPLCONFIGDIR"] = "/tmp/mpl_config"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.dates as mdates

# ---- 字体配置 ----
FONT_PATH = "/System/Library/Fonts/Supplemental/Songti.ttc"
font_manager.fontManager.addfont(FONT_PATH)
plt.rcParams["font.family"] = "Songti SC"
plt.rcParams["axes.unicode_minus"] = False

# ---- 路径 ----
# scripts/ → TASK02/ → 项目根
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT = os.path.join(BASE, "TASK1-2", "raw_data", "tianqi_data.json")
OUT_DIR = os.path.join(BASE, "TASK02", "charts")
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================
# 1. 读取数据
# ============================================================
with open(INPUT, encoding="utf-8") as f:
    records = json.load(f)

# 按日期升序
records.sort(key=lambda x: x["trade_date"])
dates_raw = [r["trade_date"] for r in records]
closes = [float(r["close"]) for r in records]
highs = [float(r["high"]) for r in records]
lows = [float(r["low"]) for r in records]
opens = [float(r["open"]) for r in records]
vols = [float(r["vol"]) for r in records]
pct_chgs = [float(r["pct_chg"]) if r["pct_chg"] is not None else 0.0 for r in records]

# 转换日期格式供 matplotlib 使用
from datetime import datetime
dates = [datetime.strptime(d, "%Y%m%d") for d in dates_raw]
n = len(closes)
print(f"数据加载完成：{n} 条记录，区间 {dates_raw[0]} ~ {dates_raw[-1]}")

# ============================================================
# 2. 指标计算（手写实现，不依赖 ta-lib）
# ============================================================

# ---------- RSI(14) ----------
def calc_rsi(prices, period=14):
    """
    RSI 计算步骤（Wilder 平滑法）：
    1. 计算每日价格变动 delta = close[t] - close[t-1]
    2. 分离 gain / loss
    3. 第一个 avg_gain / avg_loss 用简单平均
    4. 后续用 Wilder 平滑：avg = (prev_avg * (period-1) + curr) / period
    5. RS = avg_gain / avg_loss; RSI = 100 - 100/(1+RS)
    """
    rsi = [None] * len(prices)
    if len(prices) <= period:
        return rsi

    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]

    # 初始平均值（简单平均，对应第 period 个交易日）
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        rsi[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi[period] = 100 - 100 / (1 + rs)

    # Wilder 平滑
    for i in range(period + 1, len(prices)):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        if avg_loss == 0:
            rsi[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100 - 100 / (1 + rs)

    return rsi

rsi = calc_rsi(closes, 14)

# ---------- MACD(12, 26, 9) ----------
def calc_ema(values, period):
    """指数移动平均 EMA"""
    ema = [None] * len(values)
    if len(values) == 0:
        return ema
    multiplier = 2 / (period + 1)
    # 初始值用前 period 个的简单平均（对齐到 period-1 索引）
    if len(values) >= period:
        sma = sum(values[:period]) / period
        ema[period - 1] = sma
        for i in range(period, len(values)):
            ema[i] = values[i] * multiplier + ema[i - 1] * (1 - multiplier)
    return ema

def calc_macd(prices, fast=12, slow=26, signal=9):
    """
    MACD 计算步骤：
    1. EMA_fast = EMA(close, 12)
    2. EMA_slow = EMA(close, 26)
    3. DIF  = EMA_fast - EMA_slow        （快线-慢线）
    4. DEA  = EMA(DIF, 9)                 （DIF 的 9日 EMA）
    5. MACD = 2 * (DIF - DEA)            （柱状图）
    """
    ema_fast = calc_ema(prices, fast)
    ema_slow = calc_ema(prices, slow)

    dif = [None] * len(prices)
    for i in range(len(prices)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            dif[i] = ema_fast[i] - ema_slow[i]

    # DEA = EMA(DIF, 9)，需跳过前部的 None
    dif_valid_start = None
    for i, v in enumerate(dif):
        if v is not None:
            dif_valid_start = i
            break

    dea = [None] * len(prices)
    if dif_valid_start is not None:
        dif_for_ema = dif[dif_valid_start:]
        dea_valid = calc_ema(dif_for_ema, signal)
        for j, val in enumerate(dea_valid):
            if val is not None:
                dea[dif_valid_start + j] = val

    macd = [None] * len(prices)
    for i in range(len(prices)):
        if dif[i] is not None and dea[i] is not None:
            macd[i] = 2 * (dif[i] - dea[i])

    return dif, dea, macd

dif, dea, macd = calc_macd(closes, 12, 26, 9)

# ---------- 布林带(20, 2) ----------
def calc_boll(prices, period=20, nbdev=2):
    """
    布林带计算步骤：
    1. MA_mid = SMA(close, 20)            （中轨）
    2. std    = stddev(close, 20)          （20日标准差）
    3. MA_up  = MA_mid + 2 * std           （上轨）
    4. MA_dn  = MA_mid - 2 * std           （下轨）
    """
    mid = [None] * len(prices)
    up = [None] * len(prices)
    dn = [None] * len(prices)

    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1: i + 1]
        m = sum(window) / period
        variance = sum((p - m) ** 2 for p in window) / period
        std = math.sqrt(variance)
        mid[i] = m
        up[i] = m + nbdev * std
        dn[i] = m - nbdev * std

    return mid, up, dn

boll_mid, boll_up, boll_dn = calc_boll(closes, 20, 2)

# ---------- KDJ(9, 3, 3) ----------
def calc_kdj(highs, lows, closes, n_period=9, m1=3, m2=3):
    """
    KDJ 计算步骤（经典随机指标）：
    1. RSV = (close - LLV(low, N)) / (HHV(high, N) - LLV(low, N)) * 100
       — RSV 反映当日收盘价在过去 N 日价格区间的位置（0~100）
    2. K[t] = (2/3) * K[t-1] + (1/3) * RSV[t]     （对 RSV 做 3日平滑）
    3. D[t] = (2/3) * D[t-1] + (1/3) * K[t]       （对 K 做 3日平滑）
    4. J = 3 * K - 2 * D                           （J 为 K、D 的差值放大）
    初始 K = D = 50
    """
    length = len(closes)
    k = [50.0] * length
    d = [50.0] * length
    j = [50.0] * length
    rsv_list = [None] * length

    for i in range(n_period - 1, length):
        # N 日最高价 / 最低价
        hhv = max(highs[i - n_period + 1: i + 1])
        llv = min(lows[i - n_period + 1: i + 1])
        if hhv == llv:
            rsv = 50.0
        else:
            rsv = (closes[i] - llv) / (hhv - llv) * 100
        rsv_list[i] = rsv

        if i == n_period - 1:
            # 第一个有效值：K, D 初始为 50
            k[i] = (2 / 3) * 50 + (1 / 3) * rsv
            d[i] = (2 / 3) * 50 + (1 / 3) * k[i]
        else:
            k[i] = (2 / 3) * k[i - 1] + (1 / 3) * rsv
            d[i] = (2 / 3) * d[i - 1] + (1 / 3) * k[i]
        j[i] = 3 * k[i] - 2 * d[i]

    # 前 n_period-1 个标记为 None（数据不足）
    for i in range(n_period - 1):
        k[i] = None
        d[i] = None
        j[i] = None

    return k, d, j

k_vals, d_vals, j_vals = calc_kdj(highs, lows, closes, 9, 3, 3)

# ============================================================
# 3. 信号统计
# ============================================================
# RSI 信号
rsi_valid = [(d, v) for d, v in zip(dates, rsi) if v is not None]
rsi_overbought = sum(1 for _, v in rsi_valid if v > 70)
rsi_oversold = sum(1 for _, v in rsi_valid if v < 30)
rsi_latest = rsi_valid[-1][1] if rsi_valid else None

# MACD 信号
macd_valid = [(d, m, dd, ee) for d, m, dd, ee in zip(dates, macd, dif, dea)
              if m is not None and dd is not None and ee is not None]
gold_cross = 0
death_cross = 0
for i in range(1, len(macd_valid)):
    prev_dif, prev_dea = macd_valid[i-1][2], macd_valid[i-1][3]
    curr_dif, curr_dea = macd_valid[i][2], macd_valid[i][3]
    if prev_dif <= prev_dea and curr_dif > curr_dea:
        gold_cross += 1
    elif prev_dif >= prev_dea and curr_dif < curr_dea:
        death_cross += 1

# 布林带信号
boll_valid = [(d, c, u, m, l) for d, c, u, m, l in
              zip(dates, closes, boll_up, boll_mid, boll_dn)
              if u is not None]
touch_up = sum(1 for _, c, u, _, _ in boll_valid if c >= u * 0.99)
touch_dn = sum(1 for _, c, _, _, l in boll_valid if c <= l * 1.01)

# KDJ 信号
kdj_valid = [(d, k, dd, j) for d, k, dd, j in zip(dates, k_vals, d_vals, j_vals)
             if k is not None and dd is not None and j is not None]
kdj_gold = 0  # 金叉：K 由下穿 D
kdj_death = 0  # 死叉：K 由上穿 D
kdj_overbought = sum(1 for _, k, _, _ in kdj_valid if k > 80)  # K>80 超买
kdj_oversold = sum(1 for _, k, _, _ in kdj_valid if k < 20)   # K<20 超卖
kdj_j_over_100 = sum(1 for _, _, _, j in kdj_valid if j > 100)  # J>100 极度超买
kdj_j_below_0 = sum(1 for _, _, _, j in kdj_valid if j < 0)    # J<0 极度超卖
for i in range(1, len(kdj_valid)):
    prev_k, prev_d = kdj_valid[i-1][1], kdj_valid[i-1][2]
    curr_k, curr_d = kdj_valid[i][1], kdj_valid[i][2]
    if prev_k <= prev_d and curr_k > curr_d:
        kdj_gold += 1
    elif prev_k >= prev_d and curr_k < curr_d:
        kdj_death += 1

kdj_latest_k = kdj_valid[-1][1] if kdj_valid else None
kdj_latest_d = kdj_valid[-1][2] if kdj_valid else None
kdj_latest_j = kdj_valid[-1][3] if kdj_valid else None

print(f"\n=== 指标计算完成 ===")
print(f"RSI(14):  最新={rsi_latest:.2f} | 超买(>70)={rsi_overbought}天 | 超卖(<30)={rsi_oversold}天")
print(f"MACD:     金叉={gold_cross}次 | 死叉={death_cross}次")
print(f"BOLL(20,2): 触及上轨≈{touch_up}天 | 触及下轨≈{touch_dn}天")
print(f"KDJ(9,3,3): K={kdj_latest_k:.2f} D={kdj_latest_d:.2f} J={kdj_latest_j:.2f}")
print(f"          金叉={kdj_gold}次 | 死叉={kdj_death}次 | K>80={kdj_overbought}天 | K<20={kdj_oversold}天 | J>100={kdj_j_over_100}天 | J<0={kdj_j_below_0}天")

# ============================================================
# 4. 绘图
# ============================================================
# 中国股市惯例：红涨绿跌
RED = "#D32F2F"
GREEN = "#388E3C"
BLUE = "#1976D2"
ORANGE = "#F57C00"
PURPLE = "#7B1FA2"

# ---------- 图1：RSI ----------
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(dates, rsi, color=BLUE, linewidth=1.5, label="RSI(14)")
ax.fill_between(dates, 70, 100, alpha=0.08, color=RED, label="超买区(>70)")
ax.fill_between(dates, 0, 30, alpha=0.08, color=GREEN, label="超卖区(<30)")
ax.axhline(y=70, color=RED, linewidth=0.8, linestyle="--", alpha=0.6)
ax.axhline(y=30, color=GREEN, linewidth=0.8, linestyle="--", alpha=0.6)
ax.axhline(y=50, color="gray", linewidth=0.5, linestyle=":", alpha=0.4)

# 标注超买/超卖点
for d, v in rsi_valid:
    if v > 70:
        ax.scatter(d, v, color=RED, s=15, zorder=5, alpha=0.7)
    elif v < 30:
        ax.scatter(d, v, color=GREEN, s=15, zorder=5, alpha=0.7)

ax.set_ylim(0, 100)
ax.set_ylabel("RSI", fontsize=12)
ax.set_title(f"天齐锂业(002466.SZ) RSI(14) 指标 — 近一年", fontsize=14, fontweight="bold")
ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m月"))
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "rsi_tianqi.png"), dpi=150)
plt.close(fig)
print(f"\n图表保存：{os.path.join(OUT_DIR, 'rsi_tianqi.png')}")

# ---------- 图2：MACD ----------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [2, 1]}, sharex=True)

# 上图：收盘价
ax1.plot(dates, closes, color="#333", linewidth=1.2, label="收盘价")
ax1.set_ylabel("收盘价(元)", fontsize=12)
ax1.set_title("天齐锂业(002466.SZ) MACD(12,26,9) 指标 — 近一年", fontsize=14, fontweight="bold")
ax1.legend(loc="upper left", fontsize=10)
ax1.grid(True, alpha=0.3)

# 下图：MACD
# 柱状图（红涨绿跌）
macd_dates = [d for d, m in zip(dates, macd) if m is not None]
macd_vals = [m for m in macd if m is not None]
colors_bar = [RED if v >= 0 else GREEN for v in macd_vals]
ax2.bar(macd_dates, macd_vals, color=colors_bar, width=1.0, alpha=0.6, label="MACD柱")

# DIF / DEA 线
dif_dates = [d for d, v in zip(dates, dif) if v is not None]
dif_vals = [v for v in dif if v is not None]
dea_dates = [d for d, v in zip(dates, dea) if v is not None]
dea_vals = [v for v in dea if v is not None]

ax2.plot(dif_dates, dif_vals, color=ORANGE, linewidth=1.3, label="DIF(快线)")
ax2.plot(dea_dates, dea_vals, color=PURPLE, linewidth=1.3, label="DEA(慢线)")
ax2.axhline(y=0, color="gray", linewidth=0.6)

ax2.set_ylabel("MACD", fontsize=12)
ax2.legend(loc="upper left", fontsize=9, framealpha=0.9)
ax2.grid(True, alpha=0.3)
ax2.xaxis.set_major_locator(mdates.MonthLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m月"))
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "macd_tianqi.png"), dpi=150)
plt.close(fig)
print(f"图表保存：{os.path.join(OUT_DIR, 'macd_tianqi.png')}")

# ---------- 图3：布林带 ----------
fig, ax = plt.subplots(figsize=(14, 6))

# 填充上下轨之间区域
boll_dates = [d for d, v in zip(dates, boll_up) if v is not None]
up_vals = [v for v in boll_up if v is not None]
mid_vals = [v for v in boll_mid if v is not None]
dn_vals = [v for v in boll_dn if v is not None]

ax.fill_between(boll_dates, up_vals, dn_vals, alpha=0.1, color=BLUE, label="布林带通道")
ax.plot(boll_dates, up_vals, color=RED, linewidth=1.2, linestyle="--", label="上轨(+2σ)")
ax.plot(boll_dates, mid_vals, color=BLUE, linewidth=1.2, label="中轨(MA20)")
ax.plot(boll_dates, dn_vals, color=GREEN, linewidth=1.2, linestyle="--", label="下轨(-2σ)")

# 收盘价
ax.plot(dates, closes, color="#333", linewidth=1.3, label="收盘价")

# 标注触及上/下轨的点
for d, c, u, l in [(d, c, u, l) for d, c, u, m, l in boll_valid]:
    if c >= u * 0.99:
        ax.scatter(d, c, color=RED, s=20, zorder=5, alpha=0.8)
    elif c <= l * 1.01:
        ax.scatter(d, c, color=GREEN, s=20, zorder=5, alpha=0.8)

ax.set_ylabel("价格(元)", fontsize=12)
ax.set_title("天齐锂业(002466.SZ) 布林带(20,2) 指标 — 近一年", fontsize=14, fontweight="bold")
ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m月"))
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "boll_tianqi.png"), dpi=150)
plt.close(fig)
print(f"图表保存：{os.path.join(OUT_DIR, 'boll_tianqi.png')}")

# ---------- 图4：KDJ ----------
kdj_dates = [d for d, v in zip(dates, k_vals) if v is not None]
k_plot = [v for v in k_vals if v is not None]
d_plot = [v for v in d_vals if v is not None]
j_plot = [v for v in j_vals if v is not None]

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(kdj_dates, k_plot, color="#1565C0", linewidth=1.3, label="K线")
ax.plot(kdj_dates, d_plot, color="#E65100", linewidth=1.3, label="D线")
ax.plot(kdj_dates, j_plot, color="#6A1B9A", linewidth=1.1, alpha=0.8, label="J线")

ax.axhline(y=80, color=RED, linewidth=0.8, linestyle="--", alpha=0.5)
ax.axhline(y=20, color=GREEN, linewidth=0.8, linestyle="--", alpha=0.5)
ax.axhline(y=50, color="gray", linewidth=0.5, linestyle=":", alpha=0.3)
ax.fill_between(kdj_dates, 80, 120, alpha=0.06, color=RED, label="超买区(K>80)")
ax.fill_between(kdj_dates, -20, 20, alpha=0.06, color=GREEN, label="超卖区(K<20)")

for d, j in zip(kdj_dates, j_plot):
    if j > 100:
        ax.scatter(d, j, color=RED, s=18, zorder=5, alpha=0.8)
    elif j < 0:
        ax.scatter(d, j, color=GREEN, s=18, zorder=5, alpha=0.8)

for i in range(1, len(kdj_valid)):
    prev_k, prev_d = kdj_valid[i-1][1], kdj_valid[i-1][2]
    curr_k, curr_d = kdj_valid[i][1], kdj_valid[i][2]
    if prev_k <= prev_d and curr_k > curr_d:
        ax.annotate("金", (kdj_valid[i][0], curr_k), textcoords="offset points",
                    xytext=(0, 12), fontsize=7, color=RED, ha="center", fontweight="bold")
    elif prev_k >= prev_d and curr_k < curr_d:
        ax.annotate("死", (kdj_valid[i][0], curr_k), textcoords="offset points",
                    xytext=(0, -14), fontsize=7, color=GREEN, ha="center", fontweight="bold")

ax.set_ylim(-20, 120)
ax.set_ylabel("KDJ", fontsize=12)
ax.set_title("天齐锂业(002466.SZ) KDJ(9,3,3) 指标 — 近一年", fontsize=14, fontweight="bold")
ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m月"))
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "kdj_tianqi.png"), dpi=150)
plt.close(fig)
print(f"图表保存：{os.path.join(OUT_DIR, 'kdj_tianqi.png')}")

# ---------- 图5：综合对比（价格 + 布林带 + MACD + RSI + KDJ + 成交量）----------
fig, axes = plt.subplots(5, 1, figsize=(14, 17), sharex=True,
                          gridspec_kw={"height_ratios": [3, 1, 1.2, 1.2, 0.8]})

# 子图1：收盘价 + 布林带
ax = axes[0]
ax.fill_between(boll_dates, up_vals, dn_vals, alpha=0.08, color=BLUE)
ax.plot(boll_dates, up_vals, color=RED, linewidth=1, linestyle="--", alpha=0.7)
ax.plot(boll_dates, mid_vals, color=BLUE, linewidth=1, alpha=0.7)
ax.plot(boll_dates, dn_vals, color=GREEN, linewidth=1, linestyle="--", alpha=0.7)
ax.plot(dates, closes, color="#333", linewidth=1.2, label="收盘价")
ax.set_ylabel("价格(元)", fontsize=11)
ax.set_title("天齐锂业(002466.SZ) 技术指标综合视图 — 近一年", fontsize=14, fontweight="bold")
ax.legend(loc="upper left", fontsize=9)
ax.grid(True, alpha=0.3)

# 子图2：MACD 柱
ax = axes[1]
ax.bar(macd_dates, macd_vals, color=colors_bar, width=1.0, alpha=0.7)
ax.plot(dif_dates, dif_vals, color=ORANGE, linewidth=1, label="DIF")
ax.plot(dea_dates, dea_vals, color=PURPLE, linewidth=1, label="DEA")
ax.axhline(y=0, color="gray", linewidth=0.5)
ax.set_ylabel("MACD", fontsize=11)
ax.legend(loc="upper left", fontsize=8)
ax.grid(True, alpha=0.3)

# 子图3：RSI
ax = axes[2]
ax.plot(dates, rsi, color=BLUE, linewidth=1.2, label="RSI(14)")
ax.axhline(y=70, color=RED, linewidth=0.6, linestyle="--", alpha=0.5)
ax.axhline(y=30, color=GREEN, linewidth=0.6, linestyle="--", alpha=0.5)
ax.fill_between(dates, 70, 100, alpha=0.06, color=RED)
ax.fill_between(dates, 0, 30, alpha=0.06, color=GREEN)
ax.set_ylim(0, 100)
ax.set_ylabel("RSI", fontsize=11)
ax.legend(loc="upper left", fontsize=8)
ax.grid(True, alpha=0.3)

# 子图4：KDJ
ax = axes[3]
ax.plot(kdj_dates, k_plot, color="#1565C0", linewidth=1, label="K")
ax.plot(kdj_dates, d_plot, color="#E65100", linewidth=1, label="D")
ax.plot(kdj_dates, j_plot, color="#6A1B9A", linewidth=0.8, alpha=0.7, label="J")
ax.axhline(y=80, color=RED, linewidth=0.5, linestyle="--", alpha=0.4)
ax.axhline(y=20, color=GREEN, linewidth=0.5, linestyle="--", alpha=0.4)
ax.set_ylim(-20, 120)
ax.set_ylabel("KDJ", fontsize=11)
ax.legend(loc="upper left", fontsize=8)
ax.grid(True, alpha=0.3)

# 子图5：成交量
ax = axes[4]
vol_colors = [RED if closes[i] >= closes[i-1] else GREEN for i in range(1, n)]
ax.bar(dates[1:], vols[1:], color=vol_colors, width=1.0, alpha=0.6)
ax.set_ylabel("成交量(手)", fontsize=11)
ax.grid(True, alpha=0.3)

ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m月"))
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "combined_tianqi.png"), dpi=150)
plt.close(fig)
print(f"图表保存：{os.path.join(OUT_DIR, 'combined_tianqi.png')}")

print("\n=== 全部完成 ===")
