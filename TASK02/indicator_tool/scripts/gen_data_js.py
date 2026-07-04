#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并五股 JSON 数据为 data.js（供前端嵌入）"""

import json
import math
import os

_SCRIPT = os.path.dirname(os.path.abspath(__file__))
INDICATOR_TOOL = os.path.dirname(_SCRIPT)          # .../TASK02/indicator_tool
BASE = os.path.join(os.path.dirname(os.path.dirname(INDICATOR_TOOL)), "TASK1-2", "raw_data")
OUT = os.path.join(INDICATOR_TOOL, "js", "data.js")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

FILES = {
    "tianqi_a": ("tianqi_data.json", "天齐锂业", "002466.SZ", "A", "CNY"),
    "tianqi_hk": ("tianqi_hk_data.json", "天齐锂业(港)", "09696.HK", "HK", "HKD"),
    "ganfeng_a": ("ganfeng_a_data.json", "赣锋锂业", "002460.SZ", "A", "CNY"),
    "ganfeng_hk": ("ganfeng_hk_data.json", "赣锋锂业(港)", "01772.HK", "HK", "HKD"),
    "yanhu_a": ("yanhu_a_data.json", "盐湖股份", "000792.SZ", "A", "CNY"),
}

stocks = {}
for key, (fname, name, code, market, currency) in FILES.items():
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f"  MISSING: {fname}")
        continue
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    records.sort(key=lambda x: x["trade_date"])
    # 清理 NaN
    clean = []
    for r in records:
        row = {}
        for k, v in r.items():
            if isinstance(v, float) and math.isnan(v):
                row[k] = None
            else:
                row[k] = v
        clean.append(row)
    stocks[key] = {"name": name, "code": code, "market": market, "currency": currency, "records": clean}
    print(f"  {key}: {name} {code} | {len(clean)} 条")

# 写 data.js
with open(OUT, "w", encoding="utf-8") as f:
    f.write("// 自动生成：五股日线行情数据（近一年）\n")
    f.write("// 生成时间：2026-07-04\n\n")
    f.write("const STOCK_DATA = ")
    f.write(json.dumps(stocks, ensure_ascii=False, indent=2))
    f.write(";\n")

size_kb = os.path.getsize(OUT) / 1024
print(f"\ndata.js 已生成：{OUT}")
print(f"文件大小：{size_kb:.0f} KB")
