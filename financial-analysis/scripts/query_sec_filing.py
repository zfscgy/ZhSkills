# -*- coding: utf-8 -*-
"""查询美股公司 SEC filing 列表（10-K/10-Q/8-K 等，含原文 URL）。数据源：SEC EDGAR。

示例：
    python query_sec_filing.py --ticker AAPL
    python query_sec_filing.py --ticker MSFT --forms 10-K,10-Q --limit 10 --format csv

注意：SEC 要求 User-Agent 写明应用名 + 邮箱，可用 --email 覆盖。
"""
import _common


def ticker_to_cik(session, ticker):
    r = session.get("https://www.sec.gov/files/company_tickers.json", timeout=20)
    r.raise_for_status()
    for row in r.json().values():
        if row["ticker"].upper() == ticker.upper():
            return str(row["cik_str"]).zfill(10), row.get("title")
    _common.fail(f"未找到 ticker={ticker} 对应的 CIK")


def main():
    p = _common.base_parser("SEC filing 查询（EDGAR submissions）")
    p.add_argument("--ticker", required=True, help="美股代码，如 AAPL")
    p.add_argument("--forms", default="10-K,10-Q,8-K,20-F,6-K",
                   help="表单类型，逗号分隔；传 ALL 不过滤")
    p.add_argument("--email", default="financial-data-skill@example.com",
                   help="SEC User-Agent 联系邮箱")
    args = p.parse_args()

    want = None if args.forms.strip().upper() == "ALL" else set(args.forms.split(","))

    def fetch(session):
        cik, _ = ticker_to_cik(session, args.ticker)
        r = session.get(f"https://data.sec.gov/submissions/CIK{cik}.json", timeout=20)
        r.raise_for_status()
        recent = r.json()["filings"]["recent"]
        cik_int = int(cik)
        out = []
        for i in range(len(recent["form"])):
            form = recent["form"][i]
            if want and form not in want:
                continue
            accession = recent["accessionNumber"][i]
            doc = recent["primaryDocument"][i]
            acc_no = accession.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_no}/{doc}" if doc else None
            out.append({
                "filingDate": recent["filingDate"][i],
                "form": form,
                "reportDate": recent["reportDate"][i],
                "accession": accession,
                "filing_url": url,
            })
            if args.limit and len(out) >= args.limit:
                break
        return out

    try:
        rows = _common.run_requests(
            fetch, headers={"User-Agent": f"financial-data-skill {args.email}"},
            proxy=args.proxy, no_proxy=args.no_proxy, prefer="proxy")
    except Exception as e:
        _common.fail(f"SEC 查询失败: {e}")

    _common.emit(rows, args.format,
                 columns=["filingDate", "form", "reportDate", "accession", "filing_url"])


if __name__ == "__main__":
    main()
