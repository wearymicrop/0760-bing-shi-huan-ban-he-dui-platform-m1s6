# 冰时换班核对台

冰场夜班交接使用这本账簿核对包场分钟、时券折抵和待复核占用。换班前经营方会收到乱序的订场、改单和撤销记录。结账员需要按截至时刻恢复有效订单，然后把每单拆到实际营业日和当时有效的权益版本。

## 启动与演示

1. 执行 `docker compose up --build -d`，访问 `http://localhost:18454`。
2. 首页加载「周末夜场」。点 `0042` 的时段票签，核对午夜前 20 分钟扣旧券、午夜后 10 分钟扣新券，另有 10 分钟自付。
3. 进入「时券对账」。样例有效预订 340 分钟，扣券 70 分钟、自付 155 分钟、豁免 30 分钟、争议 85 分钟，两项差额均为 0。
4. 导入文件可使用 `sample_data/clean.json`。也可在工具条选择「例行早场」，其 60 分钟有效占用无争议。
5. 到「值班归档」复算并下载凭证。相同规则包和输入内容使用原批次号。

| 模块 | 页面 |
|---|---|
| 冰场日历 | `/desk/calendar` |
| 包场权益 | `/desk/passes` |
| 冰面占用 | `/desk/bookings` |
| 换班结转 | `/desk/changes` |
| 有效折抵 | `/desk/debit` |
| 时券对账 | `/desk/balance` |
| 值班归档 | `/desk/archive` |

`POST /api/runs` 接受 `{"sample":"night"}`、`{"sample":"clean"}` 或 multipart `source`。保存后可通过 `/api/modules/{模块}/{运行号}` 查看各阶段结论。归档与证据格式见 [字段与计算方式](docs/DATA-DICTIONARY.md)。[边界与回归](docs/DEPTH.md) 列出样例触发的冲突。

时券归档保存在本地 SQLite 命名卷中。`docker compose down` 关闭服务并保留封存记录。以 `docker compose exec -T app pytest -q` 运行回归。
