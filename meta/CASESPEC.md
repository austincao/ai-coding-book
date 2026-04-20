# CASESPEC：贯穿案例规格（mini-library）

> 本文件是全书的**单一事实源**。任何章节的示例默认都在这个设定里发生。
> 如果某章确实需要另起一个例子，必须在该例子标题处加「**平行例子**」四字，并与本规格显式区分。
>
> 全书正文以**业务说法**叙述用例；**UC-01～UC-05** 用于与本文件章节、评测用例目录名对齐（见 `chapters/00-前言.md` §五）。

---

## 1. 项目概述

- **项目名**：`mini-library`
- **一句话定位**：一个供校园 / 小型社区使用的**简易图书馆系统**，核心功能是**借书**与**还书**。
- **目标用户**：图书管理员（后台）+ 读者（前台，本书主要演示后台 API）。
- **规模设定**：SKU 约 1 万本、读者约 5 千人、日借还峰值 ~2000 次。
  （用这个规模来决定"要不要引缓存、要不要分库"等取舍讨论。）

## 2. 固定技术栈（全书不换）

| 层 | 选型 |
| --- | --- |
| 语言 | Java 17 |
| 框架 | Spring Boot 3.x |
| Web | Spring MVC |
| ORM | MyBatis（XML mapper，不用 MyBatis-Plus，避免"魔法"） |
| 数据库 | MySQL 8.x |
| 构建 | Maven |
| 单元测试 | JUnit 5 + Mockito |
| 集成测试 | Spring Boot Test + Testcontainers（MySQL） |
| 日志 | SLF4J + Logback |
| 规范基线 | 《阿里巴巴 Java 开发手册》(泰山版) |

> 书里出现的所有代码片段都应能**编译通过**（或明确标注为"示意伪代码，略去 import"）。

## 3. 核心领域模型

```
Book        (id, isbn, title, author, total_copies, available_copies, status, gmt_create, gmt_modified)
Reader      (id, card_no, name, phone, status, gmt_create, gmt_modified)
BorrowRecord(id, book_id, reader_id, borrow_time, due_time, return_time, status, gmt_create, gmt_modified)
```

状态机：

- `Book.status` ∈ {`ON_SHELF`, `OFF_SHELF`}
- `Reader.status` ∈ {`ACTIVE`, `FROZEN`}
- `BorrowRecord.status` ∈ {`BORROWED`, `RETURNED`, `OVERDUE`}

## 4. 核心用例（全书演示都围绕它们）

| 用例 ID | 名称 | 一句话规则 |
| --- | --- | --- |
| UC-01 | 借书 | 读者 ACTIVE + 书有余量 → 生成 BORROWED 记录，available_copies - 1，due_time = now + 30d |
| UC-02 | 还书 | 记录状态置为 RETURNED，available_copies + 1；超期则写 OVERDUE 事件日志 |
| UC-03 | 续借 | BORROWED 且未超期才允许；最多续 1 次，续 15 天 |
| UC-04 | 按书名 / ISBN 检索 | 模糊 + 分页 |
| UC-05 | 读者冻结 | 3 本以上超期未还 → 自动 FROZEN，禁止借书 |

> 本书里 **Prompt 篇** 主要用 UC-01 / UC-02；
> **Context 篇** 主要用 UC-05（需要跨多个已有模块阅读代码）；
> **Harness 篇** 主要用 UC-01 + UC-05 的回归测试集；
> **模型篇** 的"组合使用"用 UC-01 的完整迭代（需求→设计→编码→测试→review）。

## 5. 团队硬约束（共 6 条，全书所有示例优先引用）

> 命名/结构对齐阿里《Java 开发手册》。违反任意一条都算"坏例子"。

1. **分层约束**：`controller` / `service` / `manager` / `dao`，**禁止跨层调用**；`controller` 不允许直接调用 `dao`。
2. **命名规范**：
   - 类名 `UpperCamelCase`，方法/变量 `lowerCamelCase`，常量 `UPPER_SNAKE_CASE`；
   - DO（数据库对象）以 `DO` 结尾，如 `BookDO`；VO 以 `VO` 结尾；对外 DTO 以 `DTO` 结尾；
   - **禁止缩写不规范**：`cnt` / `res` / `tmp` 一律禁用，写 `count` / `result` / `temp`。
3. **响应格式**：所有 HTTP 接口统一返回：

   ```json
   { "success": true, "code": "0", "message": "ok", "data": { } }
   ```

   失败时 `success=false`，`code` 使用枚举 `ResultCode`（如 `LIB_BOOK_NOT_FOUND`）。
4. **异常与日志规范**（合并口径）：
   - 业务异常一律抛 `BizException(ResultCode, message)`；
   - 全局 `@RestControllerAdvice` 捕获并转为统一响应体；
   - **禁止在 controller 里 `try-catch` 吞异常**；
   - 关键链路打 `INFO`，异常打 `ERROR` 并带 `traceId`；
   - **禁止 `e.printStackTrace()`**；日志**禁止 `+` 拼串**，用 `{}` 占位符。
5. **数据访问规范**（合并事务 + SQL）：
   - 写操作必须 `@Transactional`，**只读查询禁止加事务**；
   - 事务内**禁止远程调用 / 发消息 / 读外部文件**；
   - **禁用 `SELECT *`**；所有 DML 必须带 `WHERE`；
   - 分页必须用 `LIMIT offset, size`，且 `offset` 做上限保护。
6. **测试要求**：
   - `service` 层单测覆盖率 ≥ 80%；
   - 每个公开 API 至少 1 个 happy path + 1 个异常路径集成测试；
   - **禁止写"只 assert 不报错"的空测试**。

## 6. 固定"坏例子"锚点（供全书反模式引用）

这些片段在正文中会反复出现，写的时候**原文复用**，不要改造：

- **BAD-01**：controller 直接调 `BookMapper`，跳过 service。
- **BAD-02**：接口返回裸 `Book` 对象，没有统一响应体。
- **BAD-03**：`try { ... } catch (Exception e) { e.printStackTrace(); return null; }`。
- **BAD-04**：`service` 方法名 `doIt()` / `process()` 之类无意义命名。
- **BAD-05**：在 `@Transactional` 方法里调用 HTTP 查外部信用分。
- **BAD-06**：`LIKE '%' + keyword + '%'` 拼接 SQL。

## 7. 固定"好例子"锚点

- **GOOD-01**：`BookService.borrow(Long readerId, Long bookId)` 的完整实现（入参校验 / 查库 / 扣减 / 写记录 / 事务）。
- **GOOD-02**：`@RestControllerAdvice` 的全局异常处理器。
- **GOOD-03**：`BorrowRecordMapper.xml` 的分页查询（带总数、不 `SELECT *`）。
- **GOOD-04**：针对 UC-01 的 JUnit5 + Mockito 单测（含异常分支）。

## 8. 数据样例（固定 seed，便于全书引用）

```sql
-- 3 本书
INSERT INTO book(id, isbn, title, author, total_copies, available_copies, status)
VALUES
 (1001, '9787111213826', '深入理解Java虚拟机', '周志明', 3, 3, 'ON_SHELF'),
 (1002, '9787121362729', '代码整洁之道',       'Robert C. Martin', 2, 1, 'ON_SHELF'),
 (1003, '9787115428028', 'Effective Java',     'Joshua Bloch',     1, 0, 'OFF_SHELF');

-- 2 名读者
INSERT INTO reader(id, card_no, name, status)
VALUES
 (2001, 'R0001', '张三', 'ACTIVE'),
 (2002, 'R0002', '李四', 'FROZEN');
```

> 任何章节若出现 `bookId=1001`、`readerId=2001` 等数字，读者必须能回到本节对齐。

## 9. 约束合规检查清单（每章自检）

每章收尾前请逐项打勾：

- [ ] 所有代码片段没有违反第 5 节任何一条硬约束（除非是 BAD-xx 故意违反用于对照）。
- [ ] 出现的 `bookId` / `readerId` 与第 8 节 seed 一致。
- [ ] 如果换了新例子，是否在段首标注「**平行例子**」？
- [ ] 如果改了领域模型字段，是否回到本文件同步修订？

---

*本规格一经全书引用，原则上只增不删；若必须调整，需同步更新所有已写章节并在 `CONTINUITY.md` 留下变更记录。*
