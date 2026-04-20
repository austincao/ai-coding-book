# AI Coding 工程化

> Austin 与团队在 AI 辅助开发实践中的一些总结与思考  
> Prompt · Context · Harness

**作者**：Austin 与团队  
**版本**：2026 春  
**语言**：简体中文  
**可下载格式**：PDF · ePub（见 `dist/` 目录）

---

## 这是什么

这本书记录的是我们团队在实际项目里把 AI 引入开发流程时踩过的坑、摸索出的做法，以及对一些问题的不成熟思考。不是权威指南，只是在某个阶段的真实记录——如果你有更好的做法或不同的看法，非常欢迎交流和指正。

内容分三个阶段展开：

- **Prompt Engineering**（第一阶段）：怎么写好一条指令。
- **Context Engineering**（第二阶段）：怎么组织一次对话里模型看到的所有信息。
- **Harness Engineering**（第三阶段）：怎么让 AI 的输入输出有更稳定的工程保障。

加上**能力边界（02）、模型篇（11-12）、Token 篇（13-14）、评测（10）** 4 个横向专题。

全书围绕虚构项目 `mini-library`（Java 17 + Spring Boot 3）展开，所有示例、反例、Prompt 模板都在配套代码仓库里可以直接跑。

**配套实验仓库**：[ai-coding-mini-library](https://github.com/austincao/ai-coding-mini-library)（含所有可跑代码、三阶段对照、黄金用例集与夜跑管线）。

---

## 获取书籍

`dist/` 目录下提供 PDF 和 ePub 两种格式，可直接下载：

| 格式 | 适合场景 |
| --- | --- |
| `dist/AI Coding工程化.pdf` | 电脑阅读、打印 |
| `dist/AI Coding工程化.epub` | 微信读书、手机 / 平板 |

---

## 仓库结构

```
meta/                     # 规格与写作约定（公开）
  CASESPEC.md            # 贯穿案例 mini-library 的规范与 seed 数据
  STYLE.md               # 写作与排版规范
  OUTLINE.md             # 全书大纲
  GLOSSARY.md            # 术语表

assets/                   # 书中图片

scripts/
  build_book.py           # 构建脚本（需要本地章节源文件）

dist/                     # 可下载的书籍文件
  AI Coding工程化.pdf
  AI Coding工程化.epub

chapters/                 # 章节源稿（不在此仓库开放）
appendix/                 # 附录源稿（不在此仓库开放）
```

---

## 写作约定（供参考）

`meta/STYLE.md` 里有全部细节，核心几条：

1. **核心术语** Prompt / Context / Harness 正文保留英文，只在首次出现时括注中文；
2. 每章有一句话交付 + 章前片段 + 行动清单（3～5 条）；
3. 每章至少一次前后对照；
4. 六段 Context 固定顺序：System → Project → Task → Shots → Code → Output；
5. 所有代码示例遵循 `CASESPEC §5` 的 6 条约束，不自造规范。

---

## 配套实验仓库（ai-coding-mini-library）

书中所有可运行代码、Prompt 资产、Harness 脚本均已整理到独立仓库：

```
ai-coding-mini-library/
  app/            Java 17 + Spring Boot 完整实现（5 个用例，21 个单测）
  generations/    三阶段写法同题对照
    gen1-prompt-only/          一句话提问的典型产出（含违规点标注）
    gen2-context-engineering/  6 段 Context 产出（合规对照）
    gen3-harness/              Harness 工作台视角说明
  prompts/        可复用 Prompt 资产（system / project / shots / 模板）
  harness/        最小五要素可运行实现
  eval/           黄金用例集 + 评测脚本
  scripts/        nightly.sh 夜跑管线
  .github/        GitHub Actions nightly workflow
```

**5 分钟上手（完全离线）**：

```bash
git clone https://github.com/austincao/ai-coding-mini-library.git
cd ai-coding-mini-library
cd app && mvn test && cd ..                              # Java 单测
pip install -r eval/scripts/requirements.txt
python harness/runtime/runner.py --all --provider mock  # Harness 循环
bash scripts/nightly.sh                                 # 一键夜跑
```

---

## 反馈与交流

书里的结论和做法都还在迭代，很多地方可能理解得不够深，或者受我们团队特定场景影响。如果你有不同的看法、发现了错误、或者有更好的实践方式，欢迎通过 Issue 或 PR 告诉我们。

—— Austin 与团队，2026 春
