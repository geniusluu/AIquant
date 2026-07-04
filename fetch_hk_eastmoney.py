#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过东方财富接口获取天齐锂业港股(09696.HK)近一年日线行情"""

import csv
import json
import os
import socket
import urllib.request

socket.setdefaulttimeout(30)

# secid=116.09696 是东方财富对港股09696的标识
url = (
    "https://push2his.eastmoney.com/api/qt/stock/kline/get?"
    "secid=116.09696&fields1=f1,f2,f3,f4,f5,f6&"
    "fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&"
    "klt=101&fqt=1&beg=20250704&end=20260704&cb="
)

print("获取天齐锂业港股 09696.HK 近一年日线行情(东方财富)...")
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read().decode("utf-8"))

klines = result.get("data", {}).get("klines", [])
print(f"成功获取 {len(klines)} 条记录")

# 解析: date,open,close,high,low,volume,amount,amplitude,pct_chg,change,turnover
records = []
for line in klines:
    parts = line.split(",")
    d = parts[0].replace("-", "")  # 20250704 格式
    records.append({
        "ts_code": "09696.HK",
        "trade_date": d,
        "open": float(parts[1]),
        "close": float(parts[2]),
        "high": float(parts[3]),
        "low": float(parts[4]),
        "vol": float(parts[5]) / 100,  # 东方财富单位是股，转为手(100股=1手)
        "amount": float(parts[6]) / 1000,  # 转为千元
        "pct_chg": float(parts[8]),
        "change": float(parts[9]),
    })

# 升序
records.sort(key=lambda x: x["trade_date"])

fields = list(records[0].keys())
BASE = os.path.dirname(os.path.abspath(__file__))

# JSON
json_path = os.path.join(BASE, "tianqi_hk_data.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
print(f"JSON: {json_path}")

# CSV
csv_path = os.path.join(BASE, "tianqi_hk_data.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)
print(f"CSV: {csv_path}")

print(f"\n最早: {records[0]['trade_date']} 收:{records[0]['close']} 港元")
print(f"最新: {records[-1]['trade_date']} 收:{records[-1]['close']} 港元")
