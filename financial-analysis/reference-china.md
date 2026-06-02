# 中国市场数据获取参考（A 股 / 港股 / 基金 / 债券 / 中国宏观）

本文件是 `SKILL.md` 的中国部分明细，按需阅读。海外（美股 / SEC / 海外宏观）见 `reference-overseas.md`。

优先用 `scripts/` 下的命令行脚本（已内置代理 scheme 修正、限速重试、UTF-8 输出）；脚本不覆盖的场景再用下面的原始接口。

---

## 1. 中国数据源地图

### 1.1 A 股 / 北交所 / 基金 / 债券

官方与法定披露入口：

```text
巨潮资讯网 - 最新公告
https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice

巨潮资讯网 - 公告查询
https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/search
公告查询接口（POST，见 2.1.2）
https://www.cninfo.com.cn/new/hisAnnouncement/query

上交所 - 上市公司公告
https://www.sse.com.cn/disclosure/listedinfo/announcement/
公告查询接口（GET，见 2.6.1）
https://query.sse.com.cn/infodisplay/queryLatestBulletinNew.do

科创板公告
https://star.sse.com.cn/star/disclosure/listannouncement/

深交所 - 上市公司公告
https://www.szse.cn/disclosure/notice/company/index.html
公告查询接口（POST JSON，见 2.6.2）
https://www.szse.cn/api/disc/announcement/annList

北交所 - 上市公司公告
https://www.bse.cn/disclosure/announcement.html
注：北交所无稳定公开查询接口，建议改用巨潮（覆盖北交所）或 AKShare，见 2.6.3

证监会
https://www.csrc.gov.cn/

中国人民银行
https://www.pbc.gov.cn/

国家统计局
https://www.stats.gov.cn/
https://data.stats.gov.cn/
```

结构化/程序化数据源：

```text
Tushare Pro
https://tushare.pro/
https://tushare.pro/document/2

AKShare
https://akshare.akfamily.xyz/
https://akshare.akfamily.xyz/data/stock/stock.html
https://github.com/akfamily/akshare

Baostock
http://baostock.com/

东方财富行情接口：非官方稳定 API，适合原型，不应作为唯一权威来源
https://push2his.eastmoney.com/api/qt/stock/kline/get
```

商业库：

```text
Wind / 同花顺 iFinD / 东方财富 Choice / 聚源 / CSMAR / RESSET
Bloomberg / LSEG Workspace / Refinitiv / FactSet / S&P Capital IQ
```

### 1.2 港股

```text
HKEXnews - 公告标题高级搜索，英文
https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en

HKEXnews - 公告标题高级搜索，中文
https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=zh

HKEXnews - 内容全文搜索
https://www3.hkexnews.hk/search/eps/EPSSearch.html

HKEXnews - 股票代码到 stockId 映射接口（GET，见 2.6.4）
https://www1.hkexnews.hk/search/prefix.do

HKEXnews - 公告标题查询接口（GET，见 2.6.4）
https://www1.hkexnews.hk/search/titleSearchServlet.do

港交所
https://www.hkex.com.hk/
```

港股行情可选：港交所授权行情、Bloomberg/LSEG/FactSet/Wind/iFinD/Choice、AKShare、yfinance。

---

## 2.1 巨潮资讯网 CNINFO

适合获取 A 股公司公告、年报、季报、问询函、监管函、分红、回购、基金/债券公告。

### 2.1.1 手工检索入口

```text
https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/search
```

输入股票代码或简称，选择日期区间和公告分类，下载 PDF 原文。

### 2.1.2 POST 查询接口

```text
POST https://www.cninfo.com.cn/new/hisAnnouncement/query
```

示例：查询贵州茅台 `600519` 年报类公告（注意 `column` 要与交易所匹配：沪市 `sse`、深市 `szse`）。

```python
import requests

url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/search",
}
data = {
    "pageNum": 1,
    "pageSize": 30,
    "column": "sse",                   # 沪市 sse / 深市 szse；与股票代码匹配，否则返回空
    "tabName": "fulltext",
    "plate": "sh",                     # sh / sz
    "stock": "600519,gssh0600519",     # 代码,orgId（orgId 可在网页 Network 请求中拿到）
    "searchkey": "",
    "secid": "",
    "category": "category_ndbg_szsh",  # 年报；分类代码可能变化
    "trade": "",
    "seDate": "2020-01-01~2024-12-31",
    "sortName": "",
    "sortType": "",
    "isHLtitle": "true",
}

resp = requests.post(url, headers=headers, data=data, timeout=20)
resp.raise_for_status()
for item in resp.json().get("announcements", []) or []:
    title = item.get("announcementTitle")
    date = item.get("announcementTime")
    adjunct = item.get("adjunctUrl")
    pdf_url = "https://static.cninfo.com.cn/" + adjunct if adjunct else None
    print(date, title, pdf_url)
```

注意：

- 这是网页接口，不是长期承诺的开放 API；`category`、`column`、`plate` 可能变化，必要时用浏览器开发者工具复制最新请求。
- `column` 与股票代码不匹配（如沪市 `600519` 配 `szse`）会返回 0 条。
- PDF 下载通常是 `https://static.cninfo.com.cn/` + `adjunctUrl`。

### 2.1.3 下载 PDF

```python
from pathlib import Path
import time
import requests

save_dir = Path("data_raw/cninfo_pdf")
save_dir.mkdir(parents=True, exist_ok=True)
headers = {"User-Agent": "Mozilla/5.0"}

pdf_urls = [
    # "https://static.cninfo.com.cn/finalpage/...pdf",
]
for url in pdf_urls:
    path = save_dir / url.split("/")[-1]
    if path.exists():
        continue
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    path.write_bytes(r.content)
    time.sleep(1.0)
```

### 2.1.4 解析 PDF 文本和表格

```bash
pip install pymupdf pdfplumber pandas openpyxl
```

```python
import fitz  # PyMuPDF

doc = fitz.open("annual_report.pdf")
for page_no, page in enumerate(doc, start=1):
    text = page.get_text("text")
    if "合并资产负债表" in text or "利润表" in text or "现金流量表" in text:
        print("可能财务表页码：", page_no)
```

```python
import pdfplumber
import pandas as pd

with pdfplumber.open("annual_report.pdf") as pdf:
    for page_no, page in enumerate(pdf.pages, start=1):
        for table in page.extract_tables():
            df = pd.DataFrame(table)
            print("page", page_no, df.head())
```

---

## 2.2 Tushare Pro：A 股行情、财务、指数

```bash
pip install tushare pandas
```

```python
import tushare as ts

ts.set_token("你的 Tushare Token")
pro = ts.pro_api()

stocks = pro.stock_basic(exchange="", list_status="L",
                         fields="ts_code,symbol,name,area,industry,market,list_date")
daily = pro.daily(ts_code="600519.SH", start_date="20200101", end_date="20261231")
income = pro.income(ts_code="600519.SH", start_date="20200101", end_date="20261231")
balance = pro.balancesheet(ts_code="600519.SH", start_date="20200101", end_date="20261231")
cashflow = pro.cashflow(ts_code="600519.SH", start_date="20200101", end_date="20261231")
fina = pro.fina_indicator(ts_code="600519.SH", start_date="20200101", end_date="20261231")
index_daily = pro.index_daily(ts_code="000300.SH", start_date="20200101", end_date="20261231")
```

前复权价格：

```python
price = pro.daily(ts_code="600519.SH", start_date="20200101", end_date="20261231")
adj = pro.adj_factor(ts_code="600519.SH", start_date="20200101", end_date="20261231")
df = price.merge(adj, on=["ts_code", "trade_date"], how="left")
latest_factor = df["adj_factor"].iloc[0]
for col in ["open", "high", "low", "close"]:
    df[col + "_qfq"] = df[col] * df["adj_factor"] / latest_factor
```

---

## 2.3 AKShare：A 股 / 港股 / 美股 / 指数

```bash
pip install akshare --upgrade
```

```python
import akshare as ak

# A 股历史行情，adjust="" 不复权 / "qfq" 前复权 / "hfq" 后复权
df = ak.stock_zh_a_hist(symbol="600519", period="daily",
                        start_date="20200101", end_date="20261231", adjust="qfq")

spot = ak.stock_zh_a_spot_em()                       # A 股实时快照
idx = ak.stock_zh_index_daily_em(symbol="sh000300")  # 指数
hk = ak.stock_hk_hist(symbol="00700", period="daily",
                      start_date="20200101", end_date="20261231", adjust="qfq")
us = ak.stock_us_hist(symbol="105.AAPL", period="daily",
                      start_date="20200101", end_date="20261231", adjust="qfq")
```

注意：AKShare 封装大量第三方网页接口，字段可能变化，且部分接口（如东方财富 push2his）经代理时偶发连接重置，需重试。正式结论回到官方披露或授权数据源核验。

---

## 2.4 Baostock：免费 A 股历史行情与基础财务

```bash
pip install baostock pandas
```

```python
import baostock as bs
import pandas as pd

bs.login()
rs = bs.query_history_k_data_plus(
    "sh.600519", "date,code,open,high,low,close,preclose,volume,amount,adjustflag",
    start_date="2020-01-01", end_date="2026-12-31", frequency="d",
    adjustflag="2")  # 1 后复权，2 前复权，3 不复权
rows = []
while rs.next():
    rows.append(rs.get_row_data())
df = pd.DataFrame(rows, columns=rs.fields)
bs.logout()
```

财务数据：`bs.query_profit_data` / `query_balance_data` / `query_cash_flow_data`（参数 `code`、`year`、`quarter`）。

---

## 2.5 东方财富 K 线接口

```text
https://push2his.eastmoney.com/api/qt/stock/kline/get
```

```python
import requests
import pandas as pd

params = {
    "secid": "1.600519",  # 1 沪市，0 深市
    "fields1": "f1,f2,f3,f4,f5,f6",
    "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    "klt": "101",         # 101 日线，102 周线，103 月线
    "fqt": "1",           # 0 不复权，1 前复权，2 后复权
    "beg": "20200101", "end": "20261231",
}
r = requests.get("https://push2his.eastmoney.com/api/qt/stock/kline/get",
                 params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
r.raise_for_status()
rows = [x.split(",") for x in r.json()["data"]["klines"]]
cols = ["date", "open", "close", "high", "low", "volume", "amount",
        "amplitude", "pct_chg", "change", "turnover"]
df = pd.DataFrame(rows, columns=cols)
```

---

## 2.6 交易所公告检索接口（上交所 / 深交所 / 港交所 / 北交所）

这些是各交易所网页前端使用的非官方查询接口，参数和字段可能随改版变化。优先用 `scripts/query_cn_announcement.py` 和 `scripts/query_hk_announcement.py`；下面是底层细节。

### 2.6.1 上交所 SSE 公告查询

endpoint（注意是 `infodisplay` 路径，`security/stock` 路径返回空）：

```text
GET https://query.sse.com.cn/infodisplay/queryLatestBulletinNew.do
```

```python
import requests

url = "https://query.sse.com.cn/infodisplay/queryLatestBulletinNew.do"
headers = {"User-Agent": "Mozilla/5.0",
           "Referer": "https://www.sse.com.cn/disclosure/listedinfo/announcement/"}  # 必需
params = {
    "isPagination": "true", "productId": "600519", "securityType": "0101",
    "reportType": "ALL", "beginDate": "2024-01-01", "endDate": "2024-12-31",
    "pageHelp.pageSize": "25", "pageHelp.pageNo": "1", "pageHelp.beginPage": "1",
    "pageHelp.cacheSize": "1", "pageHelp.endPage": "1",
}
r = requests.get(url, headers=headers, params=params, timeout=20)
r.raise_for_status()
for it in r.json()["pageHelp"]["data"]:
    title = it.get("title")  # 标题用小写 title，TITLE 常为空
    pdf_url = "https://www.sse.com.cn" + it["URL"] if it.get("URL") else None
    print(it.get("SSEDATE"), title, pdf_url)
```

### 2.6.2 深交所 SZSE 公告查询

```text
POST https://www.szse.cn/api/disc/announcement/annList
```

```python
import json
import requests

url = "https://www.szse.cn/api/disc/announcement/annList"
headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json",
           "Referer": "https://www.szse.cn/disclosure/listed/notice/index.html"}
payload = {"seDate": ["2024-01-01", "2024-12-31"], "stock": ["000001"],
           "channelCode": ["listedNotice_disc"], "pageSize": 30, "pageNum": 1}
r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
r.raise_for_status()
for it in r.json().get("data", []):
    pdf_url = "https://disc.szse.cn" + it["attachPath"] if it.get("attachPath") else None
    print(it.get("publishTime"), it.get("title"), pdf_url)
```

### 2.6.3 北交所 BSE

北交所没有稳定、公开、可直接调用的公告查询接口。推荐：

1. 巨潮资讯网同时覆盖北交所公告，复用 2.1.2 的 `hisAnnouncement/query`。
2. AKShare 的公告/信息披露相关接口（以最新文档为准）。

不要硬抓 `bse.cn` 内部 `disclosureInfoController` 类接口，实测参数校验严格且易变，返回“查询参数异常”。

### 2.6.4 港交所 HKEXnews 公告标题查询

两步：先用 `prefix.do` 把股票代码映射为内部 `stockId`，再用 `titleSearchServlet.do` 查询。

```python
import json
import re
import requests

S = requests.Session()
headers = {"User-Agent": "Mozilla/5.0",
           "Referer": "https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en"}

pre = S.get("https://www1.hkexnews.hk/search/prefix.do", headers=headers,
            params={"callback": "c", "lang": "EN", "type": "A",
                    "name": "00700", "market": "SEHK"}, timeout=20)
raw = re.sub(r"^[^(]*\(|\);?\s*$", "", pre.text)        # 去掉 JSONP 包裹
stock_id = json.loads(raw)["stockInfo"][0]["stockId"]   # 腾讯 00700 -> 7609

r = S.get("https://www1.hkexnews.hk/search/titleSearchServlet.do", headers=headers, params={
    "sortDir": "0", "sortByOptions": "DateTime", "category": "0", "market": "SEHK",
    "stockId": stock_id, "documentType": "-1",
    "fromDate": "20240101", "toDate": "20241231", "title": "",
    "searchType": "0", "t1code": "-2", "t2Gcode": "-2", "t2code": "-2",
    "lang": "EN", "rowRange": "25"}, timeout=20)
records = json.loads(r.json()["result"])                # result 是被转义的 JSON 字符串
for it in records:
    pdf_url = "https://www1.hkexnews.hk" + it["FILE_LINK"] if it.get("FILE_LINK") else None
    print(it.get("DATE_TIME"), it.get("TITLE"), pdf_url)
```

---

## 3. 中国金融新闻与研报

### 3.1 一手来源（公告优先）

```text
公司 IR 页面
巨潮 / 上交所 / 深交所 / 北交所公告
HKEXnews 公告
交易所互动易、业绩说明会材料
```

### 3.2 商业新闻源（需授权）

```text
财联社 / Wind 新闻 / 同花顺 iFinD 新闻 / 东方财富 Choice 新闻
```

不要复制大段付费新闻全文。

### 3.3 中国研报来源

```text
Wind 研报 / 同花顺 iFinD 研报 / 东方财富 Choice 研报
慧博投研资讯 / 朝阳永续
各券商研究所官网/公众号/小程序
公司官网 IR 演示材料
```

检索关键词：

```text
{公司名} 研报 评级 目标价
{股票代码} 深度报告 PDF
{行业名} 行业研究报告 券商 PDF
{公司名} 业绩点评 证券研究报告
```

---

## 4. 中国宏观数据

官方入口：

```text
国家统计局
https://www.stats.gov.cn/
https://data.stats.gov.cn/

中国人民银行       https://www.pbc.gov.cn/
国家外汇管理局     https://www.safe.gov.cn/
财政部             https://www.mof.gov.cn/
海关总署           https://www.customs.gov.cn/
中国债券信息网     https://www.chinabond.com.cn/
中国货币网         https://www.chinamoney.com.cn/
```

优先使用官方 CSV/Excel 下载；若无 API，可使用 AKShare 宏观接口（如 `ak.macro_china_gdp`、`ak.macro_china_cpi` 等，以最新文档为准）做补充，正式结论回到官方核验。
