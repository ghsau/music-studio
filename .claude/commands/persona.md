# /persona

强制单独召唤某角色绕过 autopilot。

**用户输入：** `$ARGUMENTS`（格式：`<花名> <任务>`，例：「墨九 这段副歌再来 3 个版本」）

## 你的执行步骤

### 1. 解析参数
- 拆分 `$ARGUMENTS`：第一个空格之前 = `<花名>`，之后 = `<任务>`
- 若 `$ARGUMENTS` 为空：列出 8 位花名让用户选，终止

### 2. 校验花名
- 合法花名：老周 / 观山 / 墨九 / 阿声 / 青衫 / 抖叔 / 小汽 / 算子
- 若不在列表：回复"没有这个花名，团队是：<8 位>"，终止

### 3. 加载 persona
- 按花名找对应文件：`personas/00-laozhou-producer.md` ~ `personas/07-suanzi-analyst.md`
- Read 该文件

### 4. 切换扮演 + 执行任务
- 严格按 persona 的七段（或老周的特殊版）行事
- 任务可能在某个项目上下文中（用户可能先 `cd` 或提到曲名），也可能脱离项目（如"老周帮我整理 knowledge/"）
- 不在项目上下文 + 任务需要项目数据 → 主动问用户哪个项目

### 5. 特殊任务：老周专属命令
若花名是"老周"且任务是以下之一，按规定执行：
- "切换模式 explore" → 改 INDEX `current_mode = explore`，写 `mode_switched_at = 今天`
- "切换模式 converge" → 改 INDEX `current_mode = converge`，写 `mode_switched_at = 今天`
- "改名 <新曲名>"（须在某 song 项目上下文）→ 重命名文件夹 + INDEX 中的 slug/title

### 6. 完成后
- 不强制写"握手"行（这是脱离 autopilot 的单点召唤）
- 简短播报做了什么
