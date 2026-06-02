# 海外市场数据获取参考（美股 / SEC / 海外行情 API / 海外宏观 / 海外新闻研报）

本文件是 `SKILL.md` 的海外部分明细，按需阅读。中国部分（A 股 / 港股 / 巨潮 / 交易所接口 / 中国宏观）见 `reference-china.md`。

优先用 `scripts/` 下的命令行脚本（`query_us_price.py`、`query_sec_filing.py`）；脚本不覆盖的场景再用下面的原始接口。多数海外 API 需要自己的 API key。

---

## 1. 海外数据源地图

### 1.1 SEC 报表与公告

```text
SEC EDGAR Search                 https://www.sec.gov/search-filings
SEC Developer Resources          https://www.sec.gov/about/developer-resources
SEC EDGAR APIs                   https://www.sec.gov/search-filings/edgar-application-programming-interfaces

SEC EDGAR 全文检索接口（GET，见 2.6）
https://efts.sec.gov/LATEST/search-index

SEC ticker-CIK 映射
https://www.sec.gov/files/company_tickers.json

SEC submissions API 示例（Apple）
https://data.sec.gov/submissions/CIK0000320193.json

SEC companyfacts API 示例（Apple）
https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json

SEC companyconcept API 示例（Apple Assets）
https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/Assets.json

SEC bulk companyfacts            https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip
SEC bulk submissions             https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip
```

### 1.2 海外行情 / 财务 API

```text
Alpha Vantage            https://www.alphavantage.co/documentation/
Nasdaq Data Link         https://docs.data.nasdaq.com/
Financial Modeling Prep  https://site.financialmodelingprep.com/developer/docs
Finnhub                  https://finnhub.io/docs/api
Polygon.io               https://polygon.io/docs
Twelve Data              https://twelvedata.com/docs
Yahoo Finance / yfinance（非官方稳定 API）  https://finance.yahoo.com/
```

### 1.3 海外宏观

```text
FRED API           https://fred.stlouisfed.org/docs/api/fred/
World Bank API     https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information
IMF Data           https://www.imf.org/en/Data
OECD Data Explorer https://data-explorer.oecd.org/
```

---

## 2. 美国 SEC 报表与公告获取

SEC API 访问建议：请求头写清楚应用名和联系邮箱，否则会被限流。

```python
HEADERS = {"User-Agent": "financial-data-skill your-email@example.com"}
```

### 2.1 ticker 到 CIK

```python
import requests
import pandas as pd

r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=HEADERS, timeout=20)
r.raise_for_status()
tickers = pd.DataFrame(r.json()).T
tickers["cik_str"] = tickers["cik_str"].astype(int).astype(str).str.zfill(10)
print(tickers[tickers["ticker"].str.upper() == "AAPL"])
```

### 2.2 submissions API：filing 列表

```python
import requests
import pandas as pd

cik = "0000320193"
r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=HEADERS, timeout=20)
r.raise_for_status()
filings = pd.DataFrame(r.json()["filings"]["recent"])
forms = filings[filings["form"].isin(["10-K", "10-Q", "8-K", "20-F", "6-K"])]

row = forms.iloc[0]
acc_no = row["accessionNumber"].replace("-", "")
filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no}/{row['primaryDocument']}"
print(filing_url)
```

### 2.3 companyfacts API：XBRL 财务数据

```python
import requests
import pandas as pd

cik = "0000320193"
r = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", headers=HEADERS, timeout=30)
r.raise_for_status()
us_gaap = r.json()["facts"].get("us-gaap", {})

concept = "Revenues"
if concept in us_gaap:
    df = pd.DataFrame(us_gaap[concept]["units"].get("USD", []))
    print(df[["fy", "fp", "form", "filed", "start", "end", "val"]].tail(20))
```

常用 XBRL 概念候选：

```text
Revenues / SalesRevenueNet / RevenueFromContractWithCustomerExcludingAssessedTax
CostOfRevenue / GrossProfit / OperatingIncomeLoss / NetIncomeLoss
Assets / AssetsCurrent / Liabilities / LiabilitiesCurrent / StockholdersEquity
EarningsPerShareBasic / EarningsPerShareDiluted
NetCashProvidedByUsedInOperatingActivities
```

不同公司、行业、会计准则使用的 XBRL 标签可能不同；自动化三表时要做标签映射并抽样核验原始 filing。

### 2.4 companyconcept API：只取一个概念

```python
import requests
import pandas as pd

url = "https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/Assets.json"
r = requests.get(url, headers=HEADERS, timeout=20)
r.raise_for_status()
df = pd.DataFrame(r.json()["units"]["USD"])
print(df[["fy", "fp", "form", "filed", "end", "val"]].tail())
```

### 2.5 SEC RSS：跟踪最新 filing

```bash
pip install feedparser
```

```python
import feedparser

url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AAPL&type=8-K&dateb=&owner=exclude&count=40&output=atom"
feed = feedparser.parse(url)
for entry in feed.entries[:5]:
    print(entry.published, entry.title, entry.link)
```

### 2.6 EDGAR 全文检索 API

按关键词、表单类型、日期、公司跨所有 filing 做全文检索。

```text
GET https://efts.sec.gov/LATEST/search-index
```

```python
import requests

url = "https://efts.sec.gov/LATEST/search-index"
params = {
    "q": "artificial intelligence",   # 加引号可做精确短语
    "forms": "10-K",                  # 表单类型，可逗号分隔
    "dateRange": "custom",
    "startdt": "2024-01-01",
    "enddt": "2024-12-31",
    # "ciks": "0000320193",           # 可选：限定公司 CIK
}
r = requests.get(url, headers=HEADERS, params=params, timeout=30)
r.raise_for_status()
js = r.json()
print("命中总数：", js["hits"]["total"]["value"])
for hit in js["hits"]["hits"][:10]:
    src = hit["_source"]
    accession, _, doc = hit["_id"].partition(":")   # _id = "accessionNo:文件名"
    cik = int(src["ciks"][0])
    filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}/{doc}"
    print(src["file_date"], src["form"], src["display_names"], filing_url)
```

---

## 3. 海外股票行情和财务 API

### 3.1 Alpha Vantage

```python
import requests
import pandas as pd

API_KEY = "你的 Alpha Vantage API Key"
params = {"function": "TIME_SERIES_DAILY_ADJUSTED", "symbol": "IBM",
          "outputsize": "full", "datatype": "json", "apikey": API_KEY}
r = requests.get("https://www.alphavantage.co/query", params=params, timeout=30)
r.raise_for_status()
df = pd.DataFrame(r.json()["Time Series (Daily)"]).T
```

新闻情绪：`function=NEWS_SENTIMENT&tickers=AAPL,MSFT&topics=earnings,financial_markets`。

### 3.2 Financial Modeling Prep (FMP)

```python
import requests
import pandas as pd

API_KEY = "你的 FMP API Key"
hist = requests.get("https://financialmodelingprep.com/stable/historical-price-eod/full",
                    params={"symbol": "AAPL", "apikey": API_KEY}, timeout=30).json()
income = requests.get("https://financialmodelingprep.com/stable/income-statement",
                      params={"symbol": "AAPL", "period": "annual", "apikey": API_KEY}, timeout=30).json()
```

### 3.3 Finnhub

```python
import requests
import pandas as pd
from datetime import datetime, timezone

API_KEY = "你的 Finnhub API Key"
def to_ts(d):
    return int(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())

params = {"symbol": "AAPL", "resolution": "D",
          "from": to_ts("2020-01-01"), "to": to_ts("2026-12-31"), "token": API_KEY}
js = requests.get("https://finnhub.io/api/v1/stock/candle", params=params, timeout=30).json()
if js.get("s") == "ok":
    df = pd.DataFrame({"date": pd.to_datetime(js["t"], unit="s"), "open": js["o"],
                       "high": js["h"], "low": js["l"], "close": js["c"], "volume": js["v"]})
```

公司新闻：`GET https://finnhub.io/api/v1/company-news?symbol=AAPL&from=2025-01-01&to=2025-12-31&token=...`。

### 3.4 Nasdaq Data Link

```bash
pip install nasdaq-data-link
```

```python
import nasdaqdatalink
nasdaqdatalink.ApiConfig.api_key = "你的 Nasdaq Data Link API Key"
# data = nasdaqdatalink.get("DATASET/CODE")   # 不同数据产品有不同代码，使用前在官网确认
```

依赖具体数据产品代码；许多高质量数据需要订阅。旧的 `WIKI/*` 美股数据已不适合作为最新来源。

### 3.5 yfinance / Yahoo Finance

```bash
pip install yfinance pandas
```

```python
import yfinance as yf

t = yf.Ticker("AAPL")
hist = t.history(start="2020-01-01", end="2026-12-31", auto_adjust=True)
print(t.income_stmt.head(), t.balance_sheet.head(), t.cashflow.head())
```

Yahoo chart endpoint 示例：

```text
https://query1.finance.yahoo.com/v8/finance/chart/AAPL?period1=1577836800&period2=1798675200&interval=1d
```

Yahoo/yfinance 不是官方交易所数据源，适合快速探索。

---

## 4. 海外金融新闻

### 4.1 一手来源

```text
公司 IR 页面 / SEC 8-K / 6-K
PR Newswire / Business Wire / GlobeNewswire
```

### 4.2 GDELT

```python
import requests

params = {"query": "Apple earnings", "mode": "ArtList", "format": "json",
          "maxrecords": 20, "sort": "HybridRel"}
r = requests.get("https://api.gdeltproject.org/api/v2/doc/doc", params=params, timeout=30)
r.raise_for_status()
for art in r.json().get("articles", [])[:5]:
    print(art.get("seendate"), art.get("title"), art.get("url"))
```

注意：GDELT 限流较频繁（429），需退避重试。

### 4.3 NewsAPI

```python
import requests

API_KEY = "你的 NewsAPI Key"
params = {"q": "AAPL OR Apple", "language": "en", "sortBy": "publishedAt",
          "pageSize": 20, "apiKey": API_KEY}
r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=30)
r.raise_for_status()
for art in r.json().get("articles", [])[:5]:
    print(art.get("publishedAt"), art.get("title"), art.get("url"))
```

### 4.4 商业新闻源（需授权）

```text
Bloomberg News / Terminal、Reuters / LSEG Workspace、Dow Jones Newswires
FactSet StreetAccount、MT Newswires
```

不要复制大段付费新闻全文。

---

## 5. 海外研报

```text
Bloomberg Research Portal / LSEG Workspace / FactSet Research
S&P Capital IQ / Morningstar / Visible Alpha / I/B/E/S Estimates
券商/投行官网、公司 IR earnings presentation / investor day
```

无商业终端时的替代路径：

1. 公司 IR 下载 earnings presentation、transcript、investor day。
2. SEC 8-K 附件查 exhibit 99.1 / 99.2，常见为 earnings release 或 presentation。
3. 搜索：`{ticker} investor presentation pdf`、`{company} earnings presentation`。
4. 公开财经媒体只作为二次线索。

---

## 6. 海外宏观数据

### 6.1 FRED

```python
import requests
import pandas as pd

API_KEY = "你的 FRED API Key"
params = {"series_id": "CPIAUCSL", "api_key": API_KEY, "file_type": "json",
          "observation_start": "2020-01-01"}
r = requests.get("https://api.stlouisfed.org/fred/series/observations", params=params, timeout=30)
r.raise_for_status()
df = pd.DataFrame(r.json()["observations"])
df["value"] = pd.to_numeric(df["value"], errors="coerce")
```

常用 series：

```text
CPIAUCSL 美国 CPI / UNRATE 失业率 / FEDFUNDS 联邦基金利率
DGS10 10年期国债 / DGS2 2年期国债 / GDP / PCE
```

### 6.2 World Bank

```python
import requests
import pandas as pd

url = "https://api.worldbank.org/v2/country/CHN/indicator/NY.GDP.MKTP.CD?format=json&per_page=200"
js = requests.get(url, timeout=30).json()
df = pd.DataFrame(js[1])
print(df[["date", "value"]].head())
```
