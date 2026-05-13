# /done

标记一首歌"已发布"。用户在汽水音乐 + 抖音点击"发布"后回 Claude 执行此命令。

**用户输入：** `$ARGUMENTS`（曲名，例：「青鸟不至」）

## 你的执行步骤

> 以**老周**身份执行。

### 1. 参数检查
- 若 `$ARGUMENTS` 为空：
  - Read `songs/INDEX.md`
  - 列出当前 `status` 为 `draft` 或 `package_ready` 的曲目
  - 回复："你想标哪首发布？" + 列表
  - 终止

### 2. 在 INDEX 中查找曲名
- Read `songs/INDEX.md`
- 精确匹配 `title` 字段
- 若无精确匹配：
  - 模糊匹配（包含主要字符）找最接近的 1~3 个
  - 回复："没找到精确匹配，是这几个吗：<候选>？"
  - 终止
- 若匹配到的项 `status == released` 或 `status == reviewed`：
  - 回复："`<曲名>` 已经标记发布过了，要不要直接 `/review <曲名>`？"
  - 终止

### 3. 资产体积检查
- 跑 `du -sh songs/<日期-曲名>/assets/`
- 若 > 50MB：在最终播报中追加一次性提示："这首资产 `<体积>`，建议把原始素材移到外部存储只留终版（或之后启用 git LFS）。"

### 3.5 资产规格自检（封面分辨率兜底）
- 跑 `python3 tools/check-assets.py songs/<日期-曲名>`
- 解析 stdout：
  - 退出码 0 且无 ✗：通过，继续
  - 输出含「自动修复 N 个封面」：在最终播报追加 "封面已自动放大到达标尺寸（备份保留为 `*-original.*`）"
  - 退出码非 0 或有未自动修复的 ✗ 项：在播报中提示用户手动处理（不阻断 /done）
- 若 `tools/check-assets.py` 不存在或报错：跳过这一步，不阻断 /done

### 4. 更新 INDEX
对该项目行做以下修改：
- `status` → `released`
- `released_at` → `<今天 YYYY-MM-DD>`
- `next_review_due` → `<今天 + 7 天>`

更新全局状态：
- `published_count` += 1

### 5. 模式切换检查（如果还没切）
- 若 `published_count` 改后 **正好等于 5** 且 `current_mode == explore`（只在第 5 首 /done 时触发一次）：
  - **不在此处切换**（切换发生在下一次 `/new-song` 启动时，按 SPEC §4.4）
  - 但提醒用户："这是第 5 首发布。下一次 `/new-song` 时会切到收敛模式"

### 6. 提交 git
```
git add songs/
git commit -m "release: <曲名>"
```

### 7. 播报
温和教练风格：
- "🎉 `<曲名>` 已发布。T+7 (`<next_review_due>`) 我让算子来复盘。"
- 若资产偏大：附体积提示
- 若是第 5 首：附模式切换提醒
