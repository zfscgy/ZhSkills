# -*- coding: utf-8 -*-
"""查询 A 股上市公司公告（标题 + PDF 原文链接）。

数据源按代码自动选择交易所接口：
    6/9 开头 -> 上交所 queryLatestBulletinNew.do
    0/2/3 开头 -> 深交所 annList
    8/4 开头（北交所）-> 无稳定公开接口，提示改用巨潮/AKShare

示例：
    python query_cn_announcement.py --code 600519
    python query_cn_announcement.py --code 000001 --start 2024-01-01 --end 2024-12-31 --limit 20 --format csv
"""
import json
import _common


def query_sse(session, code, start, end, page_size):
    url = "https://query.sse.com.cn/infodisplay/queryLatestBulletinNew.do"
    headers = {"Referer": "https://www.sse.com.cn/disclosure/listedinfo/announcement/"}
    params = {
        "isPagination": "true", "productId": code, "securityType": "0101",
        "reportType": "ALL", "beginDate": start, "endDate": end,
        "pageHelp.pageSize": str(page_size), "pageHelp.pageNo": "1",
        "pageHelp.beginPage": "1", "pageHelp.cacheSize": "1", "pageHelp.endPage": "1",
    }
    r = session.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    out = []
    for it in r.json()["pageHelp"]["data"]:
        out.append({
            "date": it.get("SSEDATE") or it.get("SSEDate"),
            "title": it.get("title"),
            "code": it.get("security_Code") or code,
            "pdf_url": ("https://www.sse.com.cn" + it["URL"]) if it.get("URL") else None,
        })
    return out


def query_szse(session, code, start, end, page_size):
    url = "https://www.szse.cn/api/disc/announcement/annList"
    headers = {"Content-Type": "application/json",
               "Referer": "https://www.szse.cn/disclosure/listed/notice/index.html"}
    payload = {"seDate": [start, end], "stock": [code],
               "channelCode": ["listedNotice_disc"], "pageSize": page_size, "pageNum": 1}
    r = session.post(url, headers=headers, data=json.dumps(payload), timeout=20)
    r.raise_for_status()
    out = []
    for it in r.json().get("data", []):
        sec_code = it.get("secCode")
        if isinstance(sec_code, list):
            sec_code = ",".join(sec_code)
        out.append({
            "date": it.get("publishTime"),
            "title": it.get("title"),
            "code": sec_code,
            "pdf_url": ("https://disc.szse.cn" + it["attachPath"]) if it.get("attachPath") else None,
        })
    return out


def main():
    p = _common.base_parser("A 股公告查询（交易所接口）")
    p.add_argument("--code", required=True, help="6 位股票代码，如 600519")
    p.add_argument("--start", default="2024-01-01", help="开始日期 YYYY-MM-DD")
    p.add_argument("--end", default="2024-12-31", help="结束日期 YYYY-MM-DD")
    args = p.parse_args()

    page_size = args.limit or 30
    head = args.code[0]

    if head in ("6", "9"):
        fetch = lambda s: query_sse(s, args.code, args.start, args.end, page_size)
    elif head in ("0", "2", "3"):
        fetch = lambda s: query_szse(s, args.code, args.start, args.end, page_size)
    elif head in ("8", "4"):
        _common.fail("北交所无稳定公开接口，请改用巨潮 hisAnnouncement/query 或 AKShare（见 reference-china.md）")
    else:
        _common.fail(f"无法识别交易所：code={args.code}")

    try:
        rows = _common.run_requests(fetch, proxy=args.proxy, no_proxy=args.no_proxy, prefer="direct")
    except Exception as e:
        _common.fail(f"公告查询失败: {e}")

    if args.limit:
        rows = rows[:args.limit]
    _common.emit(rows, args.format, columns=["date", "title", "code", "pdf_url"])


if __name__ == "__main__":
    main()
