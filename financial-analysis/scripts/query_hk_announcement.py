# -*- coding: utf-8 -*-
"""查询港股公告（标题 + PDF 原文链接）。数据源：HKEXnews。

两步：先把股票代码映射为内部 stockId，再按 stockId 查公告标题。

示例：
    python query_hk_announcement.py --code 00700
    python query_hk_announcement.py --code 00700 --start 20240101 --end 20241231 --lang zh --limit 20
"""
import json
import re
import _common


def resolve_stock_id(session, code):
    r = session.get("https://www1.hkexnews.hk/search/prefix.do",
                    params={"callback": "c", "lang": "EN", "type": "A",
                            "name": code, "market": "SEHK"}, timeout=20)
    r.raise_for_status()
    raw = re.sub(r"^[^(]*\(|\);?\s*$", "", r.text)  # 去掉 JSONP 包裹
    info = json.loads(raw).get("stockInfo", [])
    if not info:
        _common.fail(f"未找到港股代码 {code} 对应的 stockId")
    return info[0]["stockId"], info[0].get("name")


def main():
    p = _common.base_parser("港股公告查询（HKEXnews）")
    p.add_argument("--code", required=True, help="港股代码，如 00700")
    p.add_argument("--start", default="20240101", help="开始日期 YYYYMMDD")
    p.add_argument("--end", default="20241231", help="结束日期 YYYYMMDD")
    p.add_argument("--lang", choices=["en", "zh"], default="en")
    args = p.parse_args()

    lang = "EN" if args.lang == "en" else "ZH"
    page_size = args.limit or 25

    def fetch(session):
        stock_id, _ = resolve_stock_id(session, args.code)
        r = session.get("https://www1.hkexnews.hk/search/titleSearchServlet.do", params={
            "sortDir": "0", "sortByOptions": "DateTime", "category": "0", "market": "SEHK",
            "stockId": stock_id, "documentType": "-1", "fromDate": args.start, "toDate": args.end,
            "title": "", "searchType": "0", "t1code": "-2", "t2Gcode": "-2", "t2code": "-2",
            "lang": lang, "rowRange": str(page_size),
        }, timeout=20)
        r.raise_for_status()
        return json.loads(r.json()["result"])  # result 是被转义的 JSON 字符串

    try:
        records = _common.run_requests(
            fetch,
            headers={"Referer": f"https://www1.hkexnews.hk/search/titlesearch.xhtml?lang={args.lang}"},
            proxy=args.proxy, no_proxy=args.no_proxy, prefer="direct")
    except Exception as e:
        _common.fail(f"HKEXnews 查询失败: {e}")

    rows = []
    for it in records:
        stock_code = (it.get("STOCK_CODE") or args.code).split("<br/>")[0].strip()
        title = (it.get("TITLE") or "").strip()
        rows.append({
            "date": it.get("DATE_TIME"),
            "title": title,
            "code": stock_code,
            "pdf_url": ("https://www1.hkexnews.hk" + it["FILE_LINK"]) if it.get("FILE_LINK") else None,
        })
    if args.limit:
        rows = rows[:args.limit]
    _common.emit(rows, args.format, columns=["date", "title", "code", "pdf_url"])


if __name__ == "__main__":
    main()
