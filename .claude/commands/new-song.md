# /new-song

启动 autopilot 流水线，从一句话主题端到端产出一首歌的完整发布工作包。

**用户输入：** `$ARGUMENTS`（一句话主题，例：「暮春，等不到信」）

## 你的执行步骤

> 你现在以**老周**身份执行。先 Read `personas/00-laozhou-producer.md` 加载行为准则。

### 1. 参数检查
- 若 `$ARGUMENTS` 为空：不创建任何文件，回复用户："给我一句话主题，比如'暮春，等不到信'"。终止。

### 2. 读 INDEX 决定模式
- Read `songs/INDEX.md`
- 解析 `## 全局状态` 段的 `published_count`、`current_mode`
- 若 `published_count >= 5` 且 `current_mode == explore`：
  - 改 INDEX：`current_mode = converge`，`mode_switched_at = <今天 YYYY-MM-DD>`
  - 在最终播报中告诉用户切换了模式

### 2.5 Bootstrap：确保 `songs/INDEX.md` 存在
- 若 `songs/INDEX.md` **不存在**（fork 后第一次跑）：
  - `cp songs/INDEX.template.md songs/INDEX.md`
  - 在最终播报中告诉用户："首次使用，已从 template 初始化 `songs/INDEX.md`"
- 若已存在：跳过此步

### 3. 创建项目骨架
- 由观山先在心里出 2-4 字曲名（暂存即可，文件夹用此曲名）
- 路径：`songs/<今天 YYYY-MM-DD>-<曲名>/`
- 处理重名：若该 slug 已存在，依次追加 `-2`、`-3` ……
- 拷贝 `templates/` 下 per-song 文件（00-brief / 01-lyrics / 02-suno-prompt / 03-visual / 05-release / 06-review）+ `templates/RUN.md` 到该目录（**04 槽位已退役** — 视频走发布后可选的 `/make-video`）
- 建子目录：`assets/audio/`、`assets/cover/`、`assets/mv/`

### 4. 在 INDEX 登记占位
在 `songs/INDEX.md` 的 `## 作品` 表添加一行。**`mode_at_creation` 用步骤 2 计算后的 `current_mode`**（即若 5→6 切换刚发生，本首应记为 `converge`）：

| slug | title | theme | status | created_at | released_at | next_review_due | mode_at_creation | metrics |
|---|---|---|---|---|---|---|---|---|
| `<日期-曲名>` | `<曲名>` | `$ARGUMENTS` | `draft` | `<今天>` | | | `<步骤 2 后的 current_mode>` | |

### ⭐ 4.3 模式选择（2026-05-14 加，必走 — 双模式分流）

按老周 §7「步骤 0 起心动念判断」**第一步问用户**：

> **「你这次是模式 A 个人 IP（真实锚点）还是模式 B 商业爆款（纯学市场）？」**

用户拍板写到 brief 顶部「模式」字段。**整首歌不允许中途切换**。

### 4.4 题材气质解析（必走）

按老周 §7「步骤 1.4」做题材 attitude 解析：

1. 1-2 句话解析题材内在 attitude
2. 列 2-3 个 attitude 方向候选
3. **给用户拍板**（≤30 秒），选定 attitude 写到 brief「气质」字段

### 4.45 外部参照系研究（必走 — 双模式做法不同）

**模式 A 个人 IP**：WebSearch **≥1 首**同类题材+attitude 榜单歌，抓 BPM/编曲/flow/hook motif，写到 brief「参照系」字段
**模式 B 商业爆款**：WebSearch **≥3 首**爆款深度拆解（BPM + 副歌 5-7-5 结构 + 押韵 + Hook 黄金 15s 位置 + 编曲层次时间线 + 和声进行），写到 brief「参照系」字段。**A0 强制 — 缺拆解数据不允许下放到 brief**

**BPM / 风格 决策必须有外部数据支撑，禁止凭推论**。

### 4.5 选风格画像（顶层路由）

- Read `knowledge/styles.md`
- 按老周 §7「画像选择规则」判断主画像（+ 可选副画像）
- **基于步骤 4.4 attitude + 4.45 参照系数据**确定画像参数（BPM 范围 / 编曲 / 人声 / hook 模式），不凭抽象
- 写到 `<项目>/00-brief.md` 的「画像」字段（替换占位骨架）
- 在最终播报中告诉用户："这首走 `<画像名>` 画像，气质 `<attitude>`，参照系 `<参照歌>`"

不允许跳过这一步——画像是所有下游角色的执行对象。

### 5. 顺序调度（按 SPEC §2.4）
**严格按顺序**，每个角色：
1. Read 该 persona 的完整文件
2. **传入当前模式**：明确告诉新角色 `current_mode = explore` 还是 `converge`，按该角色 §5 行为准则中对应模式条目执行（converge 时优先采纳 `knowledge/` 中带 ✅ 标记的项 + 20% 探索新方向）
3. 切换扮演该角色，读它要求的输入契约文件
4. **填充**产出文件（templates 已拷贝到项目里，用 Edit/Write 直接把占位骨架替换为真实内容；末尾的握手行模板已有，确保保留单一一份并替换为最终版）
5. 你（老周）读产出文件末尾的"握手"行，按 §2.5 走质量门
6. 不通过则同角色重做（最多 2 次）；2 次都不过，**中断 autopilot**，向用户上报具体问题

调度顺序：
- 观山 → `00-brief.md`
- 墨九 → `01-lyrics.md`
- 阿声 → `02-suno-prompt.md`
- 并行（2 角色，**不含抖叔**）：
  - 青衫 → `03-visual.md`
  - 小汽 → `05-release.md`

**重要**：抖叔**不在做歌主线**。视频是**发布后的可选步骤**——用户跑完 Suno 后想做视频，跑 `/make-video <曲名>` 触发抖叔（视频子系统设计见 `docs/superpowers/specs/2026-05-17-video-subsystem.md`）。

### 6. 老周汇总 RUN.md
基于已存在的 `templates/RUN.md` 内容（已拷贝），替换 `<曲名>` 为实际曲名，确认步骤指向的 0X 文件路径正确。RUN.md 标注 Phase 2 用户操作流（跑 Suno → 出封面 → 上传发布）。

### 7. 更新 INDEX
**Phase 1 完成后 status 设 `package_ready`**（工作包文档已齐；视频是发布后可选，不卡此状态）。
若步骤 2 切到了 converge，更新 `## 全局状态` 段（`current_mode` 与 `mode_switched_at`）。

### 8. 向用户播报
温和教练风格的简短消息：
- 一行总结："`<曲名>` 工作包已就绪（含 brief / 词 / Suno prompt / 视觉 / 发布包 5 份），status = package_ready"
- 2~3 行亮点（来自 00-brief 概念句、01-lyrics 副歌 hook）
- 一行行动："照 `songs/<日期-曲名>/RUN.md` 走 Phase 2（跑 Suno + 出封面），上传发布后 `/done <曲名>`。想做视频跑 `/make-video <曲名>`"
- 若切到了 converge：附一句"从这首开始进入收敛模式"

## 错误处理
- **任意 persona 连续失败 3 次**：终止，向用户报告"卡在 <角色> 的 <环节>，缺 <什么>，要继续还是改方向？"
- **拷贝模板失败 / 写文件失败**：终止，报告具体错误
