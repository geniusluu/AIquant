# 天齐锂业 A股 vs 港股 行情分析

使用 Tushare Pro 和东方财富数据接口，获取天齐锂业近一年 A股（002466.SZ）与港股（09696.HK）的日线行情数据，进行双市场对比分析并可视化。

## 项目结构

| 文件 | 说明 |
|------|------|
| `tianqi_dual_market.html` | **双市场对比面板**（A股K线 + 港股K线 + AH溢价率 + 标准化走势对比） |
| `tianqi_dashboard.html` | A股单市场 K线面板 |
| `fetch_tianqi_data.py` | 获取A股行情数据（Tushare） |
| `fetch_hk_data.py` | 获取港股行情数据（Tushare hk_daily） |
| `fetch_hk_eastmoney.py` | 获取港股行情数据（东方财富，备选源） |
| `save_hk_data.py` | 港股数据格式化存储 |
| `analyze_dual_market.py` | 双市场相关性、溢价率、波段分析 |
| `gen_panel.py` | 生成A股单市场HTML面板 |
| `gen_dual_panel.py` | 生成双市场对比HTML面板 |
| `tianqi_data.json/csv` | A股行情数据 |
| `tianqi_hk_data.json/csv` | 港股行情数据 |
| `analysis_result.json` | 分析结果摘要 |

## 快速开始

### 1. 安装依赖

无需额外安装，仅使用 Python 标准库 + ECharts CDN（浏览器打开 HTML 即可渲染图表）。

### 2. 配置 Tushare Token

```bash
export TUSHARE_TOKEN='你的tushare_token'
```

Token 获取：登录 [Tushare Pro](https://tushare.pro) → 个人中心 → 复制 token。

### 3. 获取数据

```bash
# A股数据
python3 fetch_tianqi_data.py

# 港股数据（注意 Tushare hk_daily 有频率限制）
python3 fetch_hk_data.py
```

### 4. 生成分析

```bash
# 双市场对比分析
python3 analyze_dual_market.py

# 生成可视化面板
python3 gen_dual_panel.py
```

### 5. 查看结果

浏览器打开 `tianqi_dual_market.html` 即可。

## 分析结论摘要

- **相关性**：A股与港股日涨跌幅相关系数 **0.86**（高度正相关）
- **AH溢价率**：全年均值 **24.26%**，最新 **57.19%**
- **A股波段**：近一年经历 5 个主要波段，主升浪出现在 2025年9-11月

## 技术栈

- Python 3.9+（标准库 urllib/json）
- [ECharts 5.5](https://echarts.apache.org/) 前端图表渲染
- [Tushare Pro](https://tushare.pro/) A股数据
- 东方财富港股数据接口

## 声明

本项目仅供学习研究，不构成任何投资建议。
