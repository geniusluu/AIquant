# 股票数据取数规范（Data Spec v2.0）

> **文件作用**：本文档是锂业三股取数工作的规范化说明，对应机器可读版本为同目录 `stock_data_spec.json`。未来任何取数脚本、新增标的、数据更新都应遵循本规范，保证数据格式、命名、质量的一致性。
>
> **v2.0 相比 v1.0 的主要变化**：引入复权处理策略、除权除息事件日志、交易日历校验、增量更新模式、数据血缘元数据，并将频率限制细化到每个接口。

---

## 1. 适用范围

本规范适用于 **锂业板块三只典型标的** 的日线行情（OHLCV）取数：

| 标的 | A股代码 | 港股代码 | 取数范围 |
|:---|:---|:---|:---|
| 天齐锂业 | 002466.SZ | 09696.HK | A + H |
| 赣锋锂业 | 002460.SZ | 01772.HK | A + H |
| 盐湖股份 | 000792.SZ | — | 仅 A |

---

## 2. 数据源

| 优先级 | 数据源 | A股接口 | 港股接口 | 认证 |
|:---:|:---|:---|:---|:---|
| 主 | Tushare Pro | `daily` / `adj_factor` / `dividend` | `hk_daily` / `hk_adjfactor` | MCP 配置优先，环境变量 fallback |
| 备 | 东方财富 | `f41` | `f26` | 免登录 |

### 2.1 认证加载策略

```
token = 读取 ~/.workbuddy/mcp.json → mcpServers.tushareMcp.url → 截取 token= 后的值
if token 为空:
    token = 读取环境变量 TUSHARE_TOKEN
if 仍为空:
    报错退出
```

### 2.2 失败切换策略

- Tushare 连续超时/报错 **3 次**后，自动切换东方财富备选源。
- 东方财富无复权因子接口，仅提供 raw 行情，切换后需人工补取复权数据。

### 2.3 频率限制（按接口细化）

| 接口 | 用途 | 间隔 | 说明 |
|:---|:---|:---|:---|
| `daily` | A股日线 | 200ms | 限制宽松 |
| `adj_factor` | A股复权因子 | **65秒** | ⚠️ 严格限制 1次/分钟 |
| `dividend` | 除权除息事件 | 30秒 | 建议间隔 |
| `hk_daily` | 港股日线 | 1秒 | 中等限制 |
| `hk_adjfactor` | 港股复权因子 | 1秒 | 限制宽松 |

> **关键提醒**：三只 A股取复权因子需间隔 65s，全程约 4 分钟。脚本必须自动 sleep，不能并行。

---

## 3. 字段定义（Schema）

所有标的共用同一套字段，保证横向可比。

| 字段 | 类型 | 单位 | 说明 | 是否必需 |
|:---|:---|:---|:---|:---:|
| `ts_code` | string | — | 股票代码 | ✓ |
| `trade_date` | string | YYYYMMDD | 交易日期 | ✓ |
| `open` | float | 元 / 港元 | 开盘价 | ✓ |
| `high` | float | 元 / 港元 | 最高价 | ✓ |
| `low` | float | 元 / 港元 | 最低价 | ✓ |
| `close` | float | 元 / 港元 | 收盘价 | ✓ |
| `vol` | float | 手 | 成交量（1手=100股） | ✓ |
| `amount` | float | 千元 / 千港元 | 成交额 | |
| `pre_close` | float | 元 / 港元 | 前收盘价 | |
| `change` | float | 元 / 港元 | 涨跌额 | |
| `pct_chg` | float | % | 涨跌幅（保留4位小数） | ✓ |

> **币种注意**：A股字段单位为人民币（CNY），港股字段单位为港元（HKD）。横向比较时需标注或做汇率换算。

---

## 4. 复权处理（v2.0 新增）

### 4.1 三种复权策略

| 策略 | 说明 | 适用场景 |
|:---|:---|:---|
| `raw` | 不复权，交易所原始挂牌价 | 数据核对、审计 |
| `qfq` | 前复权，以最新交易日为基准向前调整 | **技术分析、横向比较（默认）** |
| `hfq` | 后复权，以最早交易日为基准向后调整 | 长期收益率计算 |

### 4.2 存储策略

默认同时存储 **raw + qfq** 两套数据：

```
raw_data/
  ganfeng_a_data_raw.json   ← 不复权
  ganfeng_a_data_raw.csv
  ganfeng_a_data_qfq.json   ← 前复权（分析用）
  ganfeng_a_data_qfq.csv
  ganfeng_a_adj.json        ← 复权因子序列
```

### 4.3 复权计算公式

```
前复权：price_qfq = price_raw × (adj_factor / latest_adj_factor)
后复权：price_hfq = price_raw × adj_factor
```

- 复权仅应用于价格字段：`open, high, low, close, pre_close`
- **成交量和成交额不做复权处理**（保持原始值）

### 4.4 横向比较规则

> ⚠️ 三股横向比较、技术指标计算、收益率对比时，**必须统一使用 qfq 数据**，否则除权日会产生虚假价格跳变。

---

## 5. 除权除息事件日志（v2.0 新增）

| 项目 | 说明 |
|:---|:---|
| 接口 | Tushare `dividend` |
| 范围 | A股标的（港股分红事件暂不纳入） |
| 产出文件 | `除权除息事件日志.json` |
| 记录字段 | `ts_code, end_date, ann_date, div_proc, stk_div, cash_div, ex_date` |
| 用途 | 解释复权因子跳变 + 排除除权导致的涨跌异常误报 |

---

## 6. 时间范围与更新模式

### 6.1 时间范围

| 配置项 | 默认值 | 说明 |
|:---|:---|:---|
| 模式 | `rolling` | 滚动窗口，自动取近 365 天 |
| 窗口 | 365 天 | 可按需调整 |
| 固定模式 | `fixed` | 指定 `start_date` / `end_date`（YYYYMMDD） |

### 6.2 更新模式（v2.0 新增）

| 模式 | 说明 | 适用场景 |
|:---|:---|:---|
| `full` | 全量重取所有数据 | 首次取数、数据校准 |
| `incremental` | 仅取上次截止日之后的新数据 | 日常增量更新，减少 API 调用 |

---

## 7. 存储规范

### 7.1 格式

每只标的 × 每种复权方式输出 **两份** 文件：

- **JSON**：结构化，供下游 Python/前端读取，`NaN → null`。
- **CSV**：UTF-8 with BOM（`utf-8-sig`），Excel 可直接打开。

### 7.2 命名规则

```
{instrument_id}_data_{adjust}.{ext}
{instrument_id}_adj.json
```

| instrument_id | adjust | 示例文件 |
|:---|:---|:---|
| tianqi_a | raw | `tianqi_a_data_raw.json` / `.csv` |
| tianqi_a | qfq | `tianqi_a_data_qfq.json` / `.csv` |
| ganfeng_hk | raw | `ganfeng_hk_data_raw.json` / `.csv` |
| yanhu_a | qfq | `yanhu_a_data_qfq.json` / `.csv` |

### 7.3 排序与 NaN

- 所有记录按 `trade_date` **升序**（ASC）排列。
- JSON 中 `NaN → null`；CSV 中 `NaN → 空字符串`。

### 7.4 存储位置

`TASK02/raw_data/`

---

## 8. 数据质量校验

| 校验项 | 规则 | 处置 |
|:---|:---|:---|
| **行数** | A股 230~252 行；港股 235~252 行 | 超出范围则告警 |
| **缺失值** | `open/high/low/close/vol` 不允许为空 | 记录告警，人工复核 |
| **涨跌异常** | `pct_chg` 超 ±20% | 标记复核；若当日有除权除息事件，归因为公司行动 |
| **日期连续性** | 按交易日历（`trade_cal`）检查断档 | 停牌日期单独记录 |
| **复权一致性**（v2.0） | qfq 数据中除权日前后价格比例与复权因子跳变一致（容差 0.001） | 不一致则告警 |

---

## 9. 数据血缘报告（v2.0 新增）

每次取数完成后自动生成 `数据血缘报告.json`，记录：

| 字段 | 说明 |
|:---|:---|
| `fetch_timestamp_utc8` | 取数完成时间戳（UTC+8） |
| `spec_version` | 使用的 spec 版本 |
| `data_source` | 实际使用的数据源（Tushare / 东方财富） |
| `instruments_summary` | 每只标的的行数、日期范围 |
| `quality_check_results` | 校验通过/告警/失败的汇总 |
| `adj_changes_count` | 复权因子跳变次数 |
| `corporate_actions_count` | 除权除息事件数 |
| `errors` | 执行过程中的错误记录 |

用途：数据审计、版本追溯、问题排查。

---

## 10. 横向对齐输出

取数完成后，以三只 A 股的**交易日交集**为基准，使用 **qfq** 收盘价生成对齐数据集：

- 文件：`三股对齐数据.csv`
- 列：`trade_date, tianqi_close, ganfeng_close, yanhu_close, tianqi_pct, ganfeng_pct, yanhu_pct`
- 用途：三股收益率对比、相关性分析、标准化走势叠图

---

## 11. 执行参数

| 参数 | 值 |
|:---|:---|
| 频率限制 | 自动按接口配置（见 §2.3） |
| 重试次数 | 3 次 |
| 退避策略 | 指数退避，基础 2 秒 |
| 超时 | 30 秒 |
| 备选源触发 | 连续失败 3 次 |
| 自动备份 | 开启，备份至 `TASK02/raw_data/` |

---

## 12. 扩展指南

新增标的时，只需在 `stock_data_spec.json` 的 `instruments` 数组中追加一项：

```json
{
  "id": "your_id",
  "name_cn": "股票简称",
  "ts_code": "XXXXXX.SZ",
  "market": "A",
  "exchange": "SZSE",
  "currency": "CNY",
  "has_hk": false,
  "status": "active"
}
```

脚本自动识别 `.SZ/.SH → daily`、`.HK → hk_daily`，无需修改取数逻辑。

新增市场时，在 `data_source.primary.interface_map` 中新增市场映射，并在 `rate_limits` 配置对应频率限制。

---

## 13. 版本记录

| 版本 | 日期 | 变更 |
|:---|:---|:---|
| 1.0.0 | 2026-07-04 | TASK1-2 初始版本，定义三股 OHLCV 日线取数基本规范 |
| 2.0.0 | 2026-07-04 | 新增复权策略、除权除息事件、交易日历校验、增量更新、数据血缘、接口级频率限制 |
