#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取天齐锂业近一年日线行情数据并存储为 CSV"""

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
TS_CODE = "002466.SZ"  # 天齐锂业

# 计算近一年的日期范围
end_date = datetime.now().strftime("%Y%m%d")
start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
print(f"获取 {TS_CODE} 天齐锂业 {start_date} ~ {end_date} 的日线行情...")

url = "https://api.tushare.pro"
payload = {
    "api_name": "daily",
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

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    print(f"请求失败: {e}")
    raise SystemExit(1)

if result.get("code") != 0:
    print(f"Tushare 返回错误: {result}")
    raise SystemExit(1)

data = result["data"]
fields = data["fields"]
items = data["items"]
print(f"成功获取 {len(items)} 条记录，字段: {fields}")

# 转为字典列表并按日期升序排列
records = [dict(zip(fields, row)) for row in items]
records.sort(key=lambda x: x["trade_date"])

# 写入 JSON（供 HTML 面板读取）
json_path = os.path.join(os.path.dirname(__file__), "tianqi_data.json")
json_data = []
for r in records:
    # 处理 NaN / None
    row_data = {}
    for k, v in r.items():
        if isinstance(v, float) and math.isnan(v):
            row_data[k] = None
        else:
            row_data[k] = v
    json_data.append(row_data)

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)
print(f"JSON 数据已保存至: {json_path}")

# 写入 CSV
csv_path = os.path.join(os.path.dirname(__file__), "tianqi_data.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)
print(f"CSV 数据已保存至: {csv_path}")

# 打印前几行预览
print("\n数据预览（前5行）:")
for r in records[:5]:
    print(
        f"  {r['trade_date']} | 开:{r['open']} 高:{r['high']} 低:{r['low']} "
        f"收:{r['close']} 量:{r['vol']}手 额:{r['amount']}千"
    )
print("...")
print("\n数据预览（后5行）:")
for r in records[-5:]:
    print(
        f"  {r['trade_date']} | 开:{r['open']} 高:{r['high']} 低:{r['low']} "
        f"收:{r['close']} 量:{r['vol']}手 额:{r['amount']}千"
    )
