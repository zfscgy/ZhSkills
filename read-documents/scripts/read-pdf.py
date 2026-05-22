"""
read-pdf.py  —  快速读取 PDF 纯文本（基于 pymupdf / MuPDF）

为什么用这个脚本：
    针对**大体积 PDF**（几十 MB / 几百页），pymupdf 的解析速度比 markitdown
    （内部走 pdfminer）快一个数量级，几乎"瞬开"。仅需正文文字时强烈推荐。

用法:
    python read-pdf.py <file.pdf> [--pages 1-10] [--max-chars N] [--no-truncate]

选项:
    --pages SPEC     页码范围，如 "1-10" / "1,3,5" / "5-"（从第 5 页到末页）。
                     默认读取全部页。页码从 1 开始。
    --max-chars N    最大输出字符数（默认 20000），超出截断并提示。
    --no-truncate    关闭截断，完整输出。

依赖:
    pip install pymupdf
"""

import sys
import argparse
from pathlib import Path

try:
    import pymupdf
except ImportError:
    print(
        "[错误] 未安装 pymupdf，请运行：pip install pymupdf",
        file=sys.stderr,
    )
    sys.exit(2)


DEFAULT_MAX_CHARS = 20000


def parse_pages(spec: str, total: int) -> list[int]:
    """把 '1-10' / '1,3,5' / '5-' 这种描述解析为 0-based 页码列表。"""
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a) if a else 1
            end = int(b) if b else total
            for p in range(start, end + 1):
                if 1 <= p <= total:
                    pages.add(p - 1)
        else:
            p = int(part)
            if 1 <= p <= total:
                pages.add(p - 1)
    return sorted(pages)


def extract_text(path: Path, pages_spec: str | None) -> str:
    doc = pymupdf.open(str(path))
    try:
        total = doc.page_count
        idxs = parse_pages(pages_spec, total) if pages_spec else range(total)
        chunks = []
        for i in idxs:
            page = doc[i]
            text = page.get_text("text")
            chunks.append(f"\n\n--- Page {i + 1} ---\n\n{text}")
        return "".join(chunks).lstrip()
    finally:
        doc.close()


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    omitted = len(text) - max_chars
    notice = (
        f"\n\n... [已截断 {omitted} 字符 / 共 {len(text)} 字符，"
        f"如需完整内容请加 --no-truncate 或调高 --max-chars，"
        f"或用 --pages 指定页码范围] ..."
    )
    return text[:max_chars] + notice


def main():
    parser = argparse.ArgumentParser(
        description="用 pymupdf 快速提取 PDF 纯文本（适合大 PDF）"
    )
    parser.add_argument("file", help="PDF 文件路径")
    parser.add_argument(
        "--pages",
        help='页码范围，如 "1-10" / "1,3,5" / "5-"（1-based）',
    )
    parser.add_argument(
        "--max-chars", type=int, default=DEFAULT_MAX_CHARS,
        help=f"最大输出字符数，默认 {DEFAULT_MAX_CHARS}",
    )
    parser.add_argument(
        "--no-truncate", action="store_true",
        help="关闭截断，完整输出",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"[错误] 文件不存在：{path}", file=sys.stderr)
        sys.exit(1)

    text = extract_text(path, args.pages)
    if not args.no_truncate:
        text = truncate(text, args.max_chars)

    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
