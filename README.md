# AI Coding 工程化

> **从 Prompt 到 Harness 的团队实战手册**  
> Prompt · Context · Harness

**作者**：Austin  
**版本**：2026 春  
**语言**：简体中文  
**输出**：`dist/全书.md` / `dist/全书.html` / `dist/全书.pdf` / `dist/全书.epub`

---

## 这是什么

一本关于**如何正确使用 AI**（而非"AI 原理"）的实战手册。围绕**三代杠杆**的演进展开：

- **Prompt Engineering**（第一代）：怎么写好一条指令。
- **Context Engineering**（第二代）：怎么组织一次对话里模型看到的所有信息。
- **Harness Engineering**（第三代）：怎么让 AI 的输入输出都有制度保障。

加上**能力边界（02）、模型篇（11-12）、Token 篇（13-14）、评测（10）** 4 个横向专题。

全书围绕虚构项目 `mini-library`（Java 17 + Spring Boot 3）展开，所有示例、反例、Prompt 模板、Harness 配置都可以复用到你自己的项目里。

**配套实验仓库**：[ai-coding-mini-library](https://github.com/AustinCao/ai-coding-mini-library)（含所有可跑代码、三代对照、黄金用例集与夜跑管线）。

## 目录

```
meta/                     # 元信息：不会进入最终成书
  CASESPEC.md            # 贯穿案例 mini-library 的规范与 seed 数据
  STYLE.md               # 写作与排版规范
  OUTLINE.md             # 全书大纲、字数预算、对照分布
  GLOSSARY.md            # 术语表

chapters/                 # 正文 16 章
  00-前言.md
  01-地图-三代杠杆.md
  02-能力边界-任务分类.md
  03-prompt-骨架模板.md
  04-prompt-反模式与资产化.md
  05-context-包裹顺序.md
  06-context-rag纪律.md
  07-context-代码场景.md
  08-harness-最小五要素.md
  09-harness-团队规范即缰绳.md
  10-harness-评测与黄金用例集.md
  11-模型-能力地图.md
  12-模型-组合使用.md
  13-token-花在哪与省钱矩阵.md
  14-token-风险边界与总成本.md
  15-结语.md

appendix/                 # 附录 A / B / C
  A-检查清单.md
  B-延伸阅读.md
  C-术语扩展.md

assets/                   # 图片与静态资源
  images/
    opus-token-breakdown.png   # 13 章引用的真实 Opus token 账单截图

scripts/
  build_book.py           # 构建脚本（合并 / HTML / PDF / ePub）

dist/                     # 构建产物
  全书.md
  全书.html
  全书.pdf
  全书.epub
```

## 快速开始

### 依赖

```bash
pip install -r requirements.txt
```

`requirements.txt` 只需要 3 个 Python 包：

- `markdown` — 合并与 HTML 渲染
- `Pygments` — 代码高亮
- `EbookLib` — ePub 生成

**PDF 生成**额外依赖本机安装 Chrome / Chromium / Edge 任一（构建脚本自动探测）。

### 构建全书

```bash
python scripts/build_book.py
```

产物：

- `dist/全书.md` —— 合并后的单文件 Markdown，可直接在任何 Markdown 阅读器打开
- `dist/全书.html` —— PDF 向的 HTML（对齐「花叔 Claude Code 橙皮书」风格）
- `dist/全书.pdf` —— 印刷/屏幕双用 PDF
- `dist/全书.epub` —— 针对**微信读书**排版优化的 ePub

### 可选参数

```bash
# 仅生成 Markdown + HTML，不生成 PDF / ePub
python scripts/build_book.py --html-only

# 生成 Markdown + HTML + PDF，但不生成 ePub
python scripts/build_book.py --no-epub

# 生成 Markdown + HTML + ePub，但不生成 PDF
python scripts/build_book.py --no-pdf
```

## 输出格式说明

### PDF 版（对齐「花叔橙皮书」）

- 主色 `#E67E22` 橙，与 Anthropic/Claude 的品牌延展色一致；
- 正文宋体、标题黑体，双字体增强对比；
- 每章 `# ` 强制分页；表格、代码块 `page-break-inside: avoid`；
- 引用块以橙色左边条 + 橙色底衬出"作者旁白"；
- 代码块橙色左边条 + 等宽字，避免在 PDF 里被吞。

### ePub 版（微信读书优化）

- 每章独立 xhtml，便于微信读书的章节切换与进度记忆；
- 内嵌 CSS 精简到 ~30 行，避免平台 CSS 冲突；
- `pre { white-space: pre-wrap }`，保证长代码在手机上能换行；
- 图片用 `file_name="assets/images/..."` 精确打包，不走网络引用；
- 元信息 `title / author / language / description` 完整，便于上架。

## 写作纪律（给后续贡献者）

本书所有章节遵循 `meta/STYLE.md` 的硬约束，核心几条：

1. **核心术语** Prompt / Context / Harness 正文保留英文，只在首次出现时给一次括注中文；
2. 每章有 **一句话交付** + **章前小片段** + **行动清单（3~5 条）**；
3. 每章**至少一次前后对照**（除模型/Token 两篇用表格替代）；
4. **六段固定 Context 顺序**：System → Project → Task → Shots → Code → Output；
5. 所有代码示例引用 `CASESPEC §5` 的 6 条硬约束，不自造规范。

字数预算：全书 **5~7 万汉字**（不含代码、表格）。

## 配套实验仓库（ai-coding-mini-library）

书中所有可运行代码、Prompt 资产、Harness 脚本均已整理到独立仓库：

```
ai-coding-mini-library/
  app/            Java 17 + Spring Boot 全量实现（5 个用例，21 个单测）
  generations/    三代工作方式同题对照
    gen1-prompt-only/          一句话提问产出——功能能跑，7 条 BAD-xx 齐踩
    gen2-context-engineering/  6 段 Context 产出——合规、可直接上线
    gen3-harness/              工作台视角——说明 Harness 如何取代手工组装
  prompts/        可复用 Prompt 资产（system / project / shots / 模板）
  harness/        第八章"最小五要素"可运行实现
    memory/         ContextBuilder（自动组装 6 段）+ SessionStore
    tools/          语义断言工具（调 eval/scripts/assertions.py）
    planner/        TaskPlanner（扫描 golden cases）
    review/         ReviewAgent（断言结果 → 中文反馈）
    runtime/        runner.py 主循环（生成→检查→重试→报告）
  eval/           黄金用例集 + 评测脚本
  scripts/        nightly.sh（本地 cron 夜跑）+ crontab.example
  .github/        nightly.yml（GitHub Actions 每晚自动触发）
```

**5 分钟上手（完全离线）**：

```bash
cd ai-coding-mini-library
cd app && mvn test && cd ..                              # 21 个单测全绿
pip install -r eval/scripts/requirements.txt
python harness/runtime/runner.py --all --provider mock  # Harness mock 全通过
bash scripts/nightly.sh                                 # 夜跑 = Java + 语义断言 + 报告
```

## 版权与致谢

本书为个人作品。部分数据、价格、模型能力对照截至 **2026 年 4 月**，具体数值可能随厂商更新浮动。如发现过时，欢迎 PR。

—— Austin, 2026 春
