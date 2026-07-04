#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取天齐锂业港股(09696.HK)近一年日线行情数据"""

import csv
import json
import math
import os
import socket
import urllib.request
from datetime import datetime, timedelta

socket.setdefaulttimeout(60)

TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "")
if not TUSHARE_TOKEN:
    print("错误: 请先设置环境变量 TUSHARE_TOKEN")
    print("  export TUSHARE_TOKEN='你的token'")
    raise SystemExit(1)
TS_CODE = "09696.HK"

end_date = datetime.now().strftime("%Y%m%d")
start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
print(f"获取 {TS_CODE} 天齐锂业(港股) {start_date} ~ {end_date} 的日线行情...")

url = "https://api.tushare.pro"
payload = {
    "api_name": "hk_daily",
    "token": TUSHARE_TOKEN,
    "params": {
        "ts_code": TS_CODE,
        "start_date": start_date,
        "end_date": end_date,
    },
    "fields": "ts_code,trade_date,open,high,low,close,vol,amount,pre_close,change,pct_chg",
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req, timeout=60) as resp:
    result = json.loads(resp.read().decode("utf-8"))

if result.get("code") != 0:
    print(f"Tushare 返回错误: {result}")
    raise SystemExit(1)

data = result["data"]
fields = data["fields"]
items = data["items"]
print(f"成功获取 {len(items)} 条记录")

# 按日期升序
records = [dict(zip(fields, row)) for row in items]
records.sort(key=lambda x: x["trade_date"])

# JSON
json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tianqi_hk_data.json")
json_data = []
for r in records:
    row_data = {}
    for k, v in r.items():
        if isinstance(v, float) and math.isnan(v):
            row_data[k] = None
        else:
            row_data[k] = v
    json_data.append(row_data)

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)
print(f"JSON: {json_path}")

# CSV
csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tianqi_hk_data.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)
print(f"CSV: {csv_path}")

print(f"\n最新: {records[-1]['trade_date']} 收:{records[-1]['close']} 港元")
print(f"最早: {records[0]['trade_date']} 收:{records[0]['close']} 港元")
