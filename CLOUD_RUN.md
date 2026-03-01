Cloud Run 部署与定时（简版）

前置条件
- 已安装并登录 gcloud
- 已设置默认项目与区域
- 已启用 Cloud Run 与 Cloud Scheduler API

部署（使用默认配置）
1) `./cloud_run_deploy.sh`
2) 运行一次验证：
   `gcloud run jobs execute binance-token-screener`

定时（北京时间 07:55）
1) 准备触发用服务账号，并授予 Cloud Run Invoker
2) 运行：
   `SERVICE_ACCOUNT_EMAIL=xxx@xxx.iam.gserviceaccount.com ./cloud_run_schedule.sh`

说明
- Cloud Run 任务入口为 `binance_token_screener_v3.0.py --auto`，参数保持默认值
- 定时区设置为 `Asia/Shanghai`，每天 07:55 触发
- 飞书配置通过 Secret 挂载到 `/secrets/feishu_config.json`，并设置 `FEISHU_CONFIG_PATH=/secrets/feishu_config.json`
- 历史数据与输出文件可选持久化到 GCS，需设置 `GCS_BUCKET`（必需）、`GCS_HISTORY_BLOB`（可选）、`GCS_OUTPUT_PREFIX`（可选）
