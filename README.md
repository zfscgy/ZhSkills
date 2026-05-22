# 基础中文场景技能库

| 技能 | 简介 | Python 依赖 |
|------|------|------------|
| `create-pptx` | 使用 python-pptx 程序化生成专业 PPT，支持卡片布局、流程图、箭头连接线等，内置设计规范与 API 参考。 | `python-pptx>=1.0.2` |
| `create-docx` | 使用 python-docx 程序化生成 Word 文档，支持多级标题、中文字体、段落格式、表格、列表、页眉页脚，内置完整示例脚本与 API 手册。 | `python-docx>=1.2.0` |
| `internet-trending` | 获取微博、知乎、B站、GitHub 等平台实时热榜，优先 WebFetch 抓取聚合榜单，失败自动降级为 WebSearch。 | 无 |
| `news-reader` | 国内外 50+ 新闻媒体网址与特性速查，覆盖官方媒体、财经、科技、英文国际媒体，附场景推荐。 | 无 |
| `read-documents` | 读取并解析常见文档：大 PDF 用 pymupdf 快速取正文；小型 pdf / ppt / doc / xlsx / html / 图片 / 音频 等用 MarkItDown 转 Markdown（注意大文件慢）；docx / pptx 专用脚本可额外提取标题层级、表格、演讲者备注与元数据，支持 Markdown 和 JSON 输出。 | `pymupdf`, `markitdown[all]`, `python-docx>=1.2.0`, `python-pptx>=1.0.2` |
