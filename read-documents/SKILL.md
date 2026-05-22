---
name: read-documents
description: 读取并解析常见文档文件，输出 Markdown 或结构化 JSON。可以阅读 pdf / ppt / pptx / doc / docx / xlsx / html / csv / epub / 图片 / 音频 / zip 等几乎所有常见格式。当用户需要读取、提取、浏览、摘要任意文档内容时使用——小文件优先用 MarkItDown 通用读取转 Markdown；大体积 PDF 改用 pymupdf 快速取正文；需要标题层级、表格、演讲者备注、元数据等结构化信息时再用 python-docx / python-pptx 专用脚本。
---

# 读取文档（pdf / ppt / doc / xlsx / 图片 …）

> **选择哪种读取方式？**
>
> - **大体积 PDF（几十 MB / 上百页）** → **首选 [一、快速 PDF 读取 pymupdf](#一快速-pdf-读取-pymupdf大-pdf-首选)**
>   pymupdf 解析速度远快于 markitdown，仅需正文时几乎"瞬开"。
> - **小型 pdf / pptx / docx / xlsx / html / 图片 / 音频 …，只关心内容不关心精确格式** → **[二、通用读取 MarkItDown](#二通用读取-markitdown小文件首选)**
>   一行命令把几乎所有常见文件转成 Markdown。**注意：大文件转换会比较慢，请改用 pymupdf 或专用脚本。**
> - **需要标题层级、表格单元、演讲者备注、元数据等结构化字段** → [三、读取 DOCX](#三读取-docx) / [四、读取 PPTX](#四读取-pptx)。

## 工具脚本

| 脚本 | 用途 |
|------|------|
| [scripts/read-pdf.py](scripts/read-pdf.py)   | **大 PDF 首选**：pymupdf 提取 PDF 纯文本，速度快，支持页码范围 |
| [scripts/read-any.py](scripts/read-any.py)   | **小文件通用**：任意文件 → Markdown（基于 `markitdown`），覆盖 pdf/ppt/doc/xlsx/html/图片/音频 等 |
| [scripts/read-docx.py](scripts/read-docx.py) | **专用**：.docx 段落、标题层级、表格、元数据 |
| [scripts/read-pptx.py](scripts/read-pptx.py) | **专用**：.pptx 逐张幻灯片标题/正文、表格、备注、元数据 |

---

## 一、快速 PDF 读取 pymupdf（大 PDF 首选）

**依赖：`pymupdf`**

```bash
pip install pymupdf
```

> 当 PDF 文件较大（几十 MB / 上百页），用 markitdown 会明显变慢——它内部走 pdfminer。
> pymupdf 基于 MuPDF C 引擎，对同样体量的 PDF 通常**快一个数量级**，几乎是瞬开。
>
> 仅需正文文字时，**大 PDF 一律先用这个脚本**。

### 命令行快速使用

```bash
# 读取整份 PDF 的正文（默认截断到 20000 字符）
python scripts/read-pdf.py big-report.pdf

# 只读第 1–10 页（强烈建议给大文件指定范围）
python scripts/read-pdf.py big-report.pdf --pages 1-10

# 离散页 + 范围混用
python scripts/read-pdf.py big-report.pdf --pages "1,3,5-8,20-"

# 完整输出（不截断）
python scripts/read-pdf.py big-report.pdf --no-truncate
```

### 在脚本中调用

```python
import pymupdf

doc = pymupdf.open("big-report.pdf")
try:
    for i, page in enumerate(doc, 1):
        text = page.get_text("text")   # 纯文本，最常用
        print(f"--- Page {i} ---\n{text}")
finally:
    doc.close()
```

> `get_text()` 还支持 `"blocks"` / `"words"` / `"dict"` / `"html"` 等模式，
> 需要坐标、字体或布局信息时再切换；常规摘要用默认 `"text"` 就够了。
>
> 局限：对扫描件 / 纯图片 PDF 无法直接取字，需 `page.get_textpage_ocr()` 走 OCR。

---

## 二、通用读取 MarkItDown（小文件首选）

**依赖：`markitdown[all]`**

```bash
pip install "markitdown[all]"
```

> 由 Microsoft 维护，把几乎所有常见文件读成 Markdown 纯文本。支持：
> **PDF、PowerPoint (ppt/pptx)、Word (doc/docx)、Excel (xls/xlsx)、HTML、CSV、JSON、XML、EPUB、ZIP、图片（OCR + EXIF）、音频（转录）、YouTube URL** 等。
>
> 在"只需要看清文件里写了什么"的场景下，是**小文件**的首选方法。
>
> ⚠️ **性能提醒**：MarkItDown 对**大文件转换会比较慢**（尤其是大 PDF，内部用 pdfminer）。
> 遇到几十 MB 的 PDF 请改用上面的 [pymupdf 脚本](#一快速-pdf-读取-pymupdf大-pdf-首选)；
> 大 docx / pptx 则直接用下面的专用脚本。

### 命令行快速使用

```bash
# 直接把 Markdown 内容打印到 stdout（默认截断到 20000 字符，避免塞爆上下文）
python scripts/read-any.py report.pdf

# 自定义截断阈值
python scripts/read-any.py report.pdf --max-chars 50000

# 关闭截断，输出完整内容（慎用，可能很长）
python scripts/read-any.py report.pdf --no-truncate
```

> 脚本**不会**生成中间文件，结果直接打到 stdout。需要落盘时自行重定向：
> `python scripts/read-any.py report.pdf --no-truncate > report.md`

### 在脚本中调用

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("any-file.pdf")   # 也支持 .pptx / .docx / .xlsx / .html / 图片 等
print(result.text_content)            # str：Markdown 纯文本
```

### 适用场景

- 给 LLM 喂文档做摘要、问答、检索（RAG 入库）
- 快速预览 PDF / PPT / Word 内容，不在意是否还原排版
- 一份脚本统一处理"用户随便丢过来的文件"

> 如果你需要**保留表格结构**、**判断标题级别**、**提取演讲者备注**、**读取元数据**，请改用下方专用脚本。

---

## 三、读取 DOCX

**依赖：`python-docx>=1.0.0`**

```bash
pip install python-docx
```

### 命令行快速使用

```bash
# 基础：输出 Markdown 格式文本
python scripts/read-docx.py input.docx

# 同时提取表格 + 元数据
python scripts/read-docx.py input.docx --tables --meta

# JSON 格式（供程序处理）
python scripts/read-docx.py input.docx --json --tables --meta
```

### 在脚本中调用

```python
from docx import Document

doc = Document("input.docx")

for para in doc.paragraphs:
    print(para.style.name, para.text)   # e.g. "Heading 1", "第一章"

for table in doc.tables:
    for row in table.rows:
        cells = [cell.text for cell in row.cells]
        print(cells)

cp = doc.core_properties
print(cp.title, cp.author, cp.created)
```

### 判断标题层级

```python
def heading_level(para) -> int | None:
    name = para.style.name          # "Heading 1" / "Heading 2" / "Normal" ...
    for lvl in (1, 2, 3, 4):
        if name == f"Heading {lvl}":
            return lvl
    return None
```

---

## 四、读取 PPTX

**依赖：`python-pptx>=1.0.2`**

```bash
pip install python-pptx
```

### 命令行快速使用

```bash
# 基础：逐张输出幻灯片标题 + 正文
python scripts/read-pptx.py input.pptx

# 同时提取表格、备注、元数据
python scripts/read-pptx.py input.pptx --tables --notes --meta

# JSON 格式
python scripts/read-pptx.py input.pptx --json --tables --notes --meta
```

### 在脚本中调用

```python
from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

prs = Presentation("input.pptx")

for i, slide in enumerate(prs.slides, 1):
    title = ""
    body_lines = []

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        if shape.is_placeholder:
            ph_type = shape.placeholder_format.type
            if ph_type in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
                title = shape.text_frame.text.strip()
                continue
        for para in shape.text_frame.paragraphs:
            text = para.text.strip()
            if text:
                body_lines.append(text)

    print(f"Slide {i}: {title}")
    for line in body_lines:
        print(f"  - {line}")
```

### 提取演讲者备注

```python
for slide in prs.slides:
    if slide.has_notes_slide:
        notes = slide.notes_slide.notes_text_frame.text.strip()
        if notes:
            print(notes)
```

### 提取幻灯片中的表格

```python
for shape in slide.shapes:
    if shape.has_table:
        for row in shape.table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            print(cells)
```

---

## 五、JSON 输出格式参考

**DOCX JSON 结构：**

```json
{
  "meta": { "title": "...", "author": "...", "created": "..." },
  "paragraphs": [
    { "type": "heading", "level": 1, "text": "第一章" },
    { "type": "paragraph", "level": null, "text": "正文内容..." }
  ],
  "tables": [
    [["列A", "列B"], ["值1", "值2"]]
  ]
}
```

**PPTX JSON 结构：**

```json
{
  "meta": { "title": "...", "author": "...", "slides": 10 },
  "slides": [
    {
      "slide": 1,
      "title": "幻灯片标题",
      "body": ["要点一", "要点二"],
      "tables": [[ ["列A", "列B"], ["值1", "值2"] ]],
      "notes": "演讲者备注文本"
    }
  ]
}
```

---

## 六、工作流程（决策树）

```
拿到一个文件
   │
   ├─ 是大体积 PDF（几十 MB / 上百页）？
   │     → read-pdf.py（pymupdf），必要时加 --pages 限定范围
   │
   ├─ 只想"看看里面写了什么" / 给 LLM 做摘要、问答（且文件不大）
   │     → read-any.py（MarkItDown），一行搞定
   │     ⚠️ 大文件会很慢，请先回到上一步用 pymupdf / 走专用脚本
   │
   └─ 需要结构化字段（标题级别 / 表格 / 备注 / 元数据 / JSON 管道）
         ├─ .docx → read-docx.py [--tables --meta --json]
         └─ .pptx → read-pptx.py [--tables --notes --meta --json]
```

简单规则：
- **大 PDF → pymupdf**（`read-pdf.py`）
- **小型混合格式 → MarkItDown**（`read-any.py`，注意大文件慢）
- **需要结构化字段 → 专用脚本**（`read-docx.py` / `read-pptx.py`）
