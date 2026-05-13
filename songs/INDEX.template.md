# 作品总台账

> 这是工作室的核心状态文件。老周在每次启动时扫这里。
>
> **fork 后第一次使用**：`/new-song` 会自动从 `INDEX.template.md` 复制此文件为 `INDEX.md`。也可以手动 `cp songs/INDEX.template.md songs/INDEX.md`。

## 主题 backlog（待启动）

> 由榜单调研 + 节令窗口对位产出。老周在节令前 5-7 天主动提醒。
> （初始为空，由 `/songbook` 或榜单分析填充）

| 优先级 | 主题 | 节令窗口 | 真实锚点 | 推荐画像 |
|---|---|---|---|---|

## 全局状态

- published_count: 0
- current_mode: explore
- mode_switched_at: null

## 作品

| slug | title | theme | status | created_at | released_at | next_review_due | mode_at_creation | metrics |
|---|---|---|---|---|---|---|---|---|

## 状态字段说明

- **status**：`draft`（已立项，工作包未齐）/ `package_ready`（工作包齐，待发布）/ `released`（用户已 /done）/ `reviewed`（算子已复盘）
- **mode_at_creation**：立项时的全局 `current_mode`，便于事后追溯哪批是探索期、哪批是收敛期产出
- **next_review_due**：`released_at + 7d`。空 = 未发布或已复盘
- **metrics**：复盘时由算子填入摘要（详细数据在 `06-review.md`）
