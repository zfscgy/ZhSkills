# -*- coding: utf-8 -*-
"""查询 A 股历史行情（OHLCV）。

数据源：优先 AKShare（东方财富），失败时自动回退到 Baostock（免费、无 token、独立协议，
不受跨境代理影响）。A 股为境内数据，默认直连，不走跨境代理。

示例：
    python query_ashare_price.py --code 600519
    python query_ashare_price.py --code 000001 --start 20240101 --end 20240201 --adjust qfq --format csv
    python query_ashare_price.py --code 600519 --source baostock
"""
import _common

_ADJUST_TO_BS = {"qfq": "2", "hfq": "1", "": "3"}  # Baostock: 1后复权 2前复权 3不复权


def via_akshare(args):
    import akshare as ak
    df = _common.run_lib(
        lambda: ak.stock_zh_a_hist(symbol=args.code, period=args.period,
                                   start_date=args.start, end_date=args.end, adjust=args.adjust),
        proxy=args.proxy, no_proxy=args.no_proxy, prefer="direct")
    if df is None or df.empty:
        raise RuntimeError("AKShare 返回空")
    return df.to_dict(orient="records"), "akshare"


def via_baostock(args):
    import baostock as bs
    import pandas as pd

    prefix = "sh" if args.code[0] in ("6", "9") else "sz"
    bs_code = f"{prefix}.{args.code}"
    start = f"{args.start[:4]}-{args.start[4:6]}-{args.start[6:]}"
    end = f"{args.end[:4]}-{args.end[4:6]}-{args.end[6:]}"
    freq = {"daily": "d", "weekly": "w", "monthly": "m"}[args.period]

    def _query():
        lg = bs.login()
        if lg.error_code != "0":
            raise RuntimeError(f"Baostock 登录失败 {lg.error_code} {lg.error_msg}")
        rs = bs.query_history_k_data_plus(
            bs_code, "date,code,open,high,low,close,preclose,volume,amount,turn,pctChg",
            start_date=start, end_date=end, frequency=freq,
            adjustflag=_ADJUST_TO_BS.get(args.adjust, "2"))
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        bs.logout()
        df = pd.DataFrame(rows, columns=rs.fields)
        if df.empty:
            raise RuntimeError("Baostock 返回空")
        return df

    # Baostock 走自有协议，直连即可
    df = _common.run_lib(_query, no_proxy=True, prefer="direct")
    return df.to_dict(orient="records"), "baostock"


def main():
    p = _common.base_parser("A 股历史行情查询（AKShare，失败回退 Baostock）")
    p.add_argument("--code", required=True, help="6 位股票代码，如 600519")
    p.add_argument("--start", default="20200101", help="开始日期 YYYYMMDD")
    p.add_argument("--end", default="20261231", help="结束日期 YYYYMMDD")
    p.add_argument("--adjust", choices=["", "qfq", "hfq"], default="qfq",
                   help="复权方式：'' 不复权 / qfq 前复权 / hfq 后复权")
    p.add_argument("--period", choices=["daily", "weekly", "monthly"], default="daily")
    p.add_argument("--source", choices=["auto", "akshare", "baostock"], default="auto")
    args = p.parse_args()

    errors = []
    rows = source = None

    if args.source in ("auto", "akshare"):
        try:
            rows, source = via_akshare(args)
        except Exception as e:
            errors.append(f"akshare: {e}")

    if rows is None and args.source in ("auto", "baostock"):
        try:
            rows, source = via_baostock(args)
        except Exception as e:
            errors.append(f"baostock: {e}")

    if rows is None:
        _common.fail("A 股行情查询失败；" + " | ".join(errors))

    if args.limit:
        rows = rows[-args.limit:]
    # 把数据源标记放到 stderr，避免污染 stdout 的结构化输出
    print(f"[source={source}]", file=__import__("sys").stderr)
    _common.emit(rows, args.format)


if __name__ == "__main__":
    main()
