# -*- coding: utf-8 -*-
"""查询美股 / 全球股票历史行情（OHLCV）。数据源：yfinance（Yahoo Finance）。

示例：
    python query_us_price.py --ticker AAPL
    python query_us_price.py --ticker MSFT --start 2024-01-01 --end 2024-02-01 --format csv
"""
import _common


def main():
    p = _common.base_parser("美股历史行情查询（yfinance）")
    p.add_argument("--ticker", required=True, help="代码，如 AAPL、MSFT、0700.HK")
    p.add_argument("--start", default="2020-01-01", help="开始日期 YYYY-MM-DD")
    p.add_argument("--end", default="2026-12-31", help="结束日期 YYYY-MM-DD")
    p.add_argument("--interval", default="1d", help="K 线间隔：1d/1wk/1mo 等")
    p.add_argument("--raw", action="store_true", help="不复权（默认 auto_adjust 复权）")
    args = p.parse_args()

    import yfinance as yf

    try:
        hist = _common.run_lib(
            lambda: yf.Ticker(args.ticker).history(
                start=args.start, end=args.end, interval=args.interval,
                auto_adjust=not args.raw),
            proxy=args.proxy, no_proxy=args.no_proxy, prefer="proxy")
    except Exception as e:
        _common.fail(f"yfinance 查询失败: {e}")

    if hist is None or hist.empty:
        _common.fail(f"无数据：ticker={args.ticker}，检查代码或日期区间")

    hist = hist.reset_index()
    hist.columns = [str(c) for c in hist.columns]
    rows = hist.to_dict(orient="records")
    if args.limit:
        rows = rows[-args.limit:]
    _common.emit(rows, args.format)


if __name__ == "__main__":
    main()
