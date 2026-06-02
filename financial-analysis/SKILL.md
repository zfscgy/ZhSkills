---
name: financial-data-acquisition
aliases:
  - 股票金融数据获取
  - 股票行情与财报数据
  - 金融新闻与研报检索
  - A股港股美股数据采集
version: 3.0.0
language: zh-CN
description: >
  面向中国及海外股票、金融数据的获取型 Skill。覆盖股票走势、上市公司报表、金融新闻、投资研报与宏观数据。
  提供可直接调用的命令行脚本（A股/港股/美股行情、A股/港股公告、SEC filing），以及官网入口、API endpoint、
  Python 示例和数据源选择方法。中国明细见 reference-china.md，海外明细见 reference-overseas.md。
---

# 股票与金融数据获取 Skill

## 0. 使用目标与原则

需要以下数据时启用本 Skill：

- 股票走势：A 股、港股、美股、ETF、指数的 OHLCV、成交额、分红拆股、复权价格。
- 上市公司报表：年报、季报、10-K/10-Q/20-F/6-K/8-K、招股书、公告、XBRL 财务数据。
- 金融新闻 / 投资研报 / 宏观金融数据（利率、通胀、GDP、就业、央行、汇率、债券等）。

原则：

1. **官方入口用于核验，API/SDK 用于批量采集**。
2. **报表和公告优先监管机构、交易所、法定披露平台、公司 IR 原文**。
3. **行情区分实时/延迟/盘后、复权/不复权、授权/非授权**。
4. **免费库和网页接口适合研究原型，正式生产用授权数据源或回到原始披露核验**。
5. **不要绕过登录、验证码、付费墙或商业数据库授权限制**。

---

## 1. 优先用命令行脚本

`scripts/` 下是已实测、内置容错的 CLI 工具。能用脚本就别手写请求代码——脚本已固化几个易错点：**境内数据默认直连、境外数据默认走系统代理并自动回退**（本地 `https://` 代理 scheme 会被修正为 `http://`）、对限流/连接重置做退避重试、A 股行情在东方财富失败时自动回退 Baostock、UTF-8 输出、统一 JSON/CSV 格式。

依赖（建议用一个干净的 Python 环境）：

```bash
pip install akshare baostock tushare yfinance requests pandas
```

| 脚本 | 用途 | 数据源 |
|---|---|---|
| `query_ashare_price.py` | A 股历史行情 OHLCV | AKShare/东方财富，失败回退 Baostock |
| `query_cn_announcement.py` | A 股公告（自动按代码选沪深交易所） | 上交所 / 深交所 |
| `query_hk_announcement.py` | 港股公告 | HKEXnews |
| `query_us_price.py` | 美股/全球股票行情 | yfinance |
| `query_sec_filing.py` | 美股 SEC filing 列表（含原文 URL） | SEC EDGAR |

公共参数：`--format json|csv`（默认 json）、`--limit N`、`--proxy URL`（强制指定代理）、`--no-proxy`（强制直连）。默认无需指定：境内脚本先直连，境外脚本先走系统代理，失败自动切换另一种。

```bash
# A 股行情（前复权日线）
python scripts/query_ashare_price.py --code 600519 --start 20240101 --end 20241231 --adjust qfq

# A 股公告（沪市 6 开头自动走上交所，深市 0/3 开头自动走深交所）
python scripts/query_cn_announcement.py --code 600519 --start 2024-01-01 --end 2024-12-31 --limit 20

# 港股公告
python scripts/query_hk_announcement.py --code 00700 --start 20240101 --end 20241231

# 美股行情（CSV）
python scripts/query_us_price.py --ticker AAPL --start 2024-01-01 --end 2024-12-31 --format csv

# 美股 SEC filing（只看 10-K/10-Q）
python scripts/query_sec_filing.py --ticker AAPL --forms 10-K,10-Q --limit 10
```

输出均带原文/PDF 链接，可据此回到官方披露核验。

> 注：东方财富 push2his 接口会间歇性丢弃连接（直连/代理都可能 RemoteDisconnected），所以 `query_ashare_price.py` 在 AKShare 失败时自动回退到 Baostock（免费、无 token、独立协议），数据源会打到 stderr 的 `[source=...]`。需要东财字段时重跑或加 `--source akshare`。

---

## 2. 数据源快速地图

只列入口；具体调用参数、Python 示例见下面两个引用文件。

### 中国（A 股 / 港股 / 基金 / 债券 / 中国宏观）→ 见 [reference-china.md](reference-china.md)

```text
巨潮 CNINFO   https://www.cninfo.com.cn/   公告查询接口 /new/hisAnnouncement/query
上交所        https://www.sse.com.cn/      公告接口 query.sse.com.cn/infodisplay/queryLatestBulletinNew.do
深交所        https://www.szse.cn/         公告接口 www.szse.cn/api/disc/announcement/annList
北交所        https://www.bse.cn/          无稳定公开接口，改用巨潮/AKShare
HKEXnews     https://www1.hkexnews.hk/    prefix.do + titleSearchServlet.do
程序化库      Tushare / AKShare / Baostock / 东方财富 push2his
商业库        Wind / iFinD / Choice / 聚源 / CSMAR / RESSET / Bloomberg / LSEG / FactSet
官方宏观      国家统计局 / 央行 / 外管局 / 财政部 / 海关总署
```

### 海外（美股 / SEC / 海外行情 API / 海外宏观 / 海外新闻研报）→ 见 [reference-overseas.md](reference-overseas.md)

```text
SEC EDGAR     submissions / companyfacts / companyconcept / 全文检索 efts.sec.gov/LATEST/search-index
行情/财务 API  Alpha Vantage / FMP / Finnhub / Nasdaq Data Link / Polygon / Twelve Data / yfinance
宏观           FRED / World Bank / IMF / OECD
新闻           GDELT / NewsAPI / Bloomberg / Reuters-LSEG / Dow Jones
研报           Bloomberg / LSEG / FactSet / Capital IQ / Morningstar / 公司 IR
```

---

## 3. 常见任务路径

- **某 A 股最近 N 年走势**：`query_ashare_price.py`（或 Tushare `daily`+`adj_factor`）→ 标注复权方式 → 必要时回授权源核验。
- **某 A 股年报 PDF**：`query_cn_announcement.py` 拿公告列表与 PDF 链接（或巨潮 `hisAnnouncement/query`）→ 下载 → PyMuPDF/pdfplumber 抽取 → 关键数字回看原文页码。见 reference-china.md。
- **港股公告**：`query_hk_announcement.py` → PDF 链接回 HKEXnews 核验。
- **美股最近 N 年财务**：`query_sec_filing.py` 找 10-K/10-Q → companyfacts 取 XBRL → 关键年份回 filing 原文核验。见 reference-overseas.md。
- **公司最新新闻**：官方公告（SEC 8-K / 巨潮 / HKEXnews / 公司 IR）优先 → 新闻 API（GDELT/NewsAPI/Alpha Vantage/Finnhub）→ 正式投研终端。
- **投资研报**：授权终端（Wind/iFinD/Choice/Bloomberg/LSEG/FactSet）→ 券商官网/研究所 → 公司 IR 演示材料；公开搜索只作补充，不绕过付费墙。

---

## 4. 数据可靠性分级

```text
最高可信：监管机构（SEC、证监会、央行、统计局）、交易所/法定披露平台（巨潮、沪深北交所、HKEXnews）、公司官网 IR
正式投研（通常需授权）：Wind、iFinD、Choice、Bloomberg、LSEG、FactSet、S&P Capital IQ、Morningstar、CSMAR、RESSET、聚源
快速探索/补充：Tushare、AKShare、Baostock、Alpha Vantage、FMP、Finnhub、Nasdaq Data Link、yfinance、GDELT、NewsAPI
```

---

## 5. 采集工程要点

- **API Key 管理**：用 `.env` + `python-dotenv`，不要把 key/token/cookie 写进代码或日志。
- **限速与重试**：对 GET/POST 配 `urllib3` `Retry`（`429/500/502/503/504` + backoff）；`scripts/_common.py` 已内置可参考。
- **缓存原始数据**：把 JSON/PDF 原文落盘（如 `data_raw/`），分析层只读缓存，便于复算与核验。
- **代理**：Windows 系统代理常把本地 HTTP 代理写成 `https://` scheme，触发 `check_hostname requires server_hostname`；把 https 代理 scheme 改成 `http://` 即可（脚本已自动处理）。

参考目录结构：

```text
financial_data_project/
  data_raw/{cninfo_pdf,sec_json,prices,news,research}/
  data_processed/  notebooks/  scripts/  config/  .env
```

---

## 6. 注意事项

- 不要把第三方结构化字段当作原始披露原文。
- 不要把免费接口当作交易所授权实时行情。
- 不要泄露 API key、Cookie、Token；不要复制商业研报或付费新闻全文。
- 不要忽略复权、币种、时区、交易日历、财报修订和 XBRL 标签差异。
- 网页/非官方接口（巨潮、东方财富、交易所公告、HKEXnews）参数与字段可能随改版变化；遇到字段缺失、限流、403/429、PDF 扫描件、表格错位时，保留原始文件并记录失败原因。
