# Binance Token Screener 迁移 OpenClaw 里程碑文档

## 1. 目标与范围

### 总目标
把当前 `binance_token_screener` 从“单体脚本 + 本地/Google Cloud 调度”迁移为“OpenClaw 上多个可复用 skills + 定时工作流”。

### 本次明确要求
1. 停止依赖 Google Cloud（Cloud Run / Cloud Scheduler / GCS）。
2. 保留并强化每日日报能力，日报核心是“当日涨幅榜前 5”。
3. 对涨幅榜前 5（或前 N）补充 Binance K 线和 OI 数据。
4. 分析必须基于第一步产出的“全量基础数据”，不只看前 5。
5. 需要做整页（全量数据）异动分析，重点是“期货专注”页的异常。
6. 将流程拆成多个 skills，并在 OpenClaw 上定时运行。

### 非目标（当前阶段不做）
1. 不重做分析模型本身（先复用现有指标逻辑）。
2. 不先做复杂前端可视化（优先可运行、可定时、可告警）。

## 2. 现状盘点（基于当前仓库）

### 当前程序在做什么
1. 抓取 Binance 现货/期货行情并做多维分析（8 个标签页）。
2. 计算并写出“每日涨幅榜”历史（当前是前 20，14 天滚动）。
3. 已支持 K 线获取和 OI 获取/计算。
4. 输出到 Excel/CSV，并可上传飞书，发送 Telegram 日报。

### 与你目标直接相关的已有能力
1. OI 获取：`get_open_interest_data()`。
2. K 线获取：`get_historical_klines()`。
3. OI 历史与均值：`get_oi_history()`、`get_oi_market_value_history()`。
4. 每日涨幅榜历史：`create_daily_gainers_history()`（目前前 20）。

### 仍耦合 Google Cloud 的部分
1. GCS 读写（历史和输出落盘到 GCS）。
2. Cloud Run/Cloud Scheduler 部署脚本和文档。
3. `requirements.txt` 中仍保留 Google 相关依赖。

## 3. 目标架构（OpenClaw 版）

### Skill 分层
1. `skill_market_base_dataset`
   - 输入：时间窗口、现货/期货数量、过滤规则
   - 输出：基础全量数据（用于后续所有分析）

2. `skill_excel_ticker_extractor`
   - 输入：Excel 表格路径或表格数据
   - 输出：Ticker 列表（正则提取 + 规范化 + 去重）

3. `skill_market_top_gainers`
   - 输入：全量数据、topN（默认 5）
   - 输出：当日涨幅榜前 N（symbol、涨幅、价格、成交额）

4. `skill_binance_klines_oi_enrichment`
   - 输入：symbols（来自 topN）
   - 输出：每个 symbol 的 K 线摘要（1d/4h/1h 可配置）+ OI 当前值 + OI 变化

5. `skill_futures_focus_anomaly_scan`
   - 输入：全量数据（期货专注页相关字段）
   - 输出：期货专注页异动清单（如 OI 异动、资金费率异常、成交量异常）

6. `skill_llm_analyzer`
   - 输入：Ticker 列表 + 基础数据摘要 + 期货专注异动 + TopN 涨幅
   - 输出：LLM 结构化分析结果（风险位、异动原因、是否持续异常）

7. `skill_daily_report_builder`
   - 输入：topN 基础数据 + K 线/OI 增强数据 + 异动清单
   - 输出：标准化日报（Markdown/JSON/HTML）+ PDF 报告（本地落盘），可选推送飞书或 Telegram

8. `skill_pipeline_scheduler_adapter`
   - 输入：cron、时区、重试策略
   - 输出：在 OpenClaw 上注册并执行定时任务，串联前述 skills

### 数据流
1. 定时触发（OpenClaw Cron）
2. 产出全量基础数据（原始数据页）
3. 从 Excel 表格中正则提取 Ticker 列表
4. 基于全量数据计算涨幅榜前 N
5. 对应币种拉取 K 线 + OI
6. 基于全量数据做“期货专注”异动扫描
7. 使用 LLM 对 Ticker + 异动 + TopN 做结构化分析
8. 生成日报并发送
9. 结果与运行日志持久化到本地或对象存储（非 GCS）

## 4. 里程碑计划

## M0：现状冻结与基线验证（1-2 天）

### 交付物
1. 一次完整手工运行记录（含输出文件与日志）。
2. 关键数据口径文档（涨幅、K 线周期、OI 口径）。

### 验收标准
1. 能稳定产出当日涨幅榜。
2. 能拿到任意 symbol 的 K 线与 OI 数据。

## M1：去 Google Cloud 化（2-3 天）

### 工作项
1. 代码层：把 GCS 读写改为可插拔存储（先默认本地文件）。
2. 依赖层：移除 Google Cloud 非必要依赖。
3. 运维层：下线 Cloud Run / Scheduler 任务，归档脚本文档。

### 验收标准
1. 不设置任何 Google 环境变量也可完整运行。
2. 历史数据读写仍可用（本地或新存储后端）。
3. Google Cloud 账单相关资源可停用。

## M2：日报核心重构为“前 5”优先（2 天）

### 工作项
1. 将“每日涨幅榜”从固定前 20 改为可配置 `topN`（默认 5）。
2. 定义日报主模板：Top5 + 每个币的关键字段。
3. 增加“整页异动摘要”，重点覆盖期货专注页。
4. 输出机器可读 JSON + 人类可读 Markdown 两份。

### 验收标准
1. 每日报告必须包含“涨幅榜前 5”。
2. 支持切换前 5 / 前 10（参数化）。
3. HTML + PDF 均能稳定产出。

## M3：K 线 + OI 增强流水线（2-3 天）

### 工作项
1. 对 TopN symbols 拉取 K 线（建议 `1d, 4h, 1h` 三档可选）。
2. 对 TopN symbols 拉取 OI 当前值 + 最近 24h 变化。
3. 对期货专注页做异动扫描（如 OI/成交量/资金费率异常）。
4. 统一输出字段与异常处理（缺失数据、限频、超时重试）。

### 验收标准
1. TopN 每个币都返回 K 线摘要与 OI 信息（失败项有明确错误字段）。
2. 单次任务在目标时限内完成（例如 < 10 分钟，可后续调优）。

## M4：Skill 化封装（3-4 天）

### 工作项
1. 在 OpenClaw 中创建并落地 4 个 skills（见第 3 节）。
2. 每个 skill 提供统一输入输出 schema。
3. 提供最小回归测试用例（成功/失败各 1 组）。

### 验收标准
1. 任一 skill 可独立运行。
2. 组合运行时上下游字段能对齐。

## M5：OpenClaw 定时编排上线（1-2 天）

### 工作项
1. 配置每日定时触发（建议北京时间 `07:45`）。
2. 配置失败重试、告警和日志归档。
3. 进行连续 3 天试运行。

### 验收标准
1. 连续 3 天自动运行成功率达到目标（例如 >= 99%）。
2. 每天都能收到含 Top5 + K 线/OI 的日报。

## M6：Google Cloud 正式停运（半天）

### 工作项
1. 停止 Cloud Run Job。
2. 删除/停用 Cloud Scheduler。
3. 关闭或冻结不再使用的 GCS 路径与服务账号权限。
4. 更新仓库文档，明确“生产运行仅依赖 OpenClaw”。

### 验收标准
1. Google Cloud 资源停运后，OpenClaw 流程不受影响。
2. 成本面板确认无新增运行成本（按日核对）。

## 5. 落地改造清单（代码级）

1. `binance_token_screener_v3.0.py`
   - 新增 `TOP_N_GAINERS` 参数（默认 5）。
   - 拆分“数据抓取/分析/报告”函数，便于 skill 调用。
   - 增加“期货专注异动扫描”输出（可复用现有异常检测逻辑）。
   - 把 GCS 客户端逻辑替换为存储抽象层（local/file/object storage adapter）。

2. `simple_scheduler.py`
   - 仅保留本地调试用途；生产调度迁至 OpenClaw。

3. `requirements.txt`
   - 移除不再使用的 Google 依赖（在代码切换完成后）。

4. `cloud_run_deploy.sh`、`cloud_run_schedule.sh`、`CLOUD_RUN.md`
   - 标记为 deprecated 或移除到 `archive/`。

5. 新增 `excel_ticker_extractor.py`
   - 基于正则的 Ticker 提取逻辑（可配置正则、过滤列表）。

6. 新增 `llm_analyzer.py`
   - 封装 LLM 分析调用，统一输入/输出 schema。

## 6. 风险与应对

1. Binance API 限频导致数据不完整
   - 应对：批次请求 + 重试 + fallback 字段。

2. OI/K 线接口偶发超时
   - 应对：超时上限、指数退避、失败不阻塞主流程。

3. Skill 边界不清导致后续难维护
   - 应对：先冻结 I/O schema，再开发实现。

4. 停云后历史数据断档
   - 应对：先做历史数据迁移，再切生产流量。

## 7. 建议执行顺序（你可以直接按这个开工）

1. 先做 M1（去 Google Cloud 化）和 M2（Top5 日报），快速达成业务主目标。
2. 再做 M3（K 线 + OI 增强）保证日报质量。
3. 然后做 M4 + M5（Skill 化 + OpenClaw 定时）。
4. 最后做 M6（正式停云），并观察 3 天稳定性。

## 8. 关键代码定位（便于你后续改）

1. OI 获取：`binance_token_screener_v3.0.py` `get_open_interest_data()`。
2. K 线获取：`binance_token_screener_v3.0.py` `get_historical_klines()`。
3. 每日涨幅榜（当前前20）：`create_daily_gainers_history()` 中 `nlargest(20, '1d_return')`。
4. GCS 读写：`get_gcs_client()` / `read_json_from_gcs()` / `write_json_to_gcs()` / `persist_outputs_to_gcs()`。
5. 本地定时：`simple_scheduler.py`。
6. Cloud Run/Cloud Scheduler：`cloud_run_deploy.sh`、`cloud_run_schedule.sh`、`CLOUD_RUN.md`。
7. 异常检测逻辑（用于期货专注页）：`anomaly_info` 相关处理段（同文件内）。

---

文档状态：`v1.0`（可执行里程碑版）
更新时间：`2026-02-28`
## M7：Excel 正则提取 + LLM 分析落地（3-5 天）

### 工作项
1. 实现 Excel Ticker 正则提取（统一大小写、去重、过滤无效符号）。
2. 明确 Ticker 正则规则与排除词表（可配置）。
3. 构建 LLM 分析输入 schema（Ticker + TopN + 期货专注异动）。
4. 输出结构化 JSON + 人类可读总结。

### 验收标准
1. Excel -> Ticker 提取可复用且准确。
2. LLM 输出可用于日报生成，不丢关键字段。
3. 连续 3 天/4 天异常能在输出中标记。
