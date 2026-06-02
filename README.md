# 基础中文场景技能库

| 技能 | 简介 | Python 依赖 |
|------|------|------------|
| `create-pptx` | 使用 python-pptx 程序化生成专业 PPT，支持卡片布局、流程图、箭头连接线等，内置设计规范与 API 参考。 | `python-pptx>=1.0.2` |
| `create-docx` | 使用 python-docx 程序化生成 Word 文档，支持多级标题、中文字体、段落格式、表格、列表、页眉页脚，内置完整示例脚本与 API 手册。 | `python-docx>=1.2.0` |
| `internet-trending` | 获取微博、知乎、B站、GitHub 等平台实时热榜，优先 WebFetch 抓取聚合榜单，失败自动降级为 WebSearch。 | 无 |
| `news-reader` | 国内外 50+ 新闻媒体网址与特性速查，覆盖官方媒体、财经、科技、英文国际媒体，附场景推荐。 | 无 |
| `read-documents` | 读取并解析常见文档：大 PDF 用 pymupdf 快速取正文；小型 pdf / ppt / doc / xlsx / html / 图片 / 音频 等用 MarkItDown 转 Markdown（注意大文件慢）；docx / pptx 专用脚本可额外提取标题层级、表格、演讲者备注与元数据，支持 Markdown 和 JSON 输出。 | `pymupdf`, `markitdown[all]`, `python-docx>=1.2.0`, `python-pptx>=1.0.2` |
| `financial-analysis` | 获取中国及海外股票/金融数据：A 股、港股、美股行情，上市公司公告与财报（巨潮、沪深北交所、HKEXnews、SEC EDGAR），金融新闻、研报、宏观数据。提供 5 个命令行脚本（行情/公告/SEC filing，境内直连+境外代理自动回退、东财失败回退 Baostock），中国/海外明细分两个引用文件。 | `akshare`, `baostock`, `tushare`, `yfinance`, `requests`, `pandas`（解析 PDF 另需 `pymupdf`, `pdfplumber`） |
