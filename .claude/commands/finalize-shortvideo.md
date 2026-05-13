# /finalize-shortvideo

Phase 3 触发器：用户跑完 Suno + 导出 SRT 后，激活抖叔基于真实音频时间码 + 实际唱词写 `04-shortvideo.md`。

**用户输入**：`$ARGUMENTS`（曲名，例：「这不公平」）

## 你的执行步骤

> 以**老周**身份执行。先 Read `personas/00-laozhou-producer.md` 加载行为准则。

### 1. 参数检查
- 若 `$ARGUMENTS` 为空：
  - Read `songs/INDEX.md`
  - 列出当前 `status == draft` 且 `assets/audio/*.srt` 存在的曲目（候选 Phase 3 项）
  - 回复："你想为哪首跑 Phase 3？" + 列表
  - 终止

### 2. 在 INDEX 中查找曲名
- Read `songs/INDEX.md`
- 精确匹配 `title` 字段（或模糊匹配 slug）
- 若 `status == released` 或 `package_ready` 已含 04：
  - 回复："`<曲名>` 已含 04，要重写？回 `--force` 重跑"（暂不支持 --force，让用户手动改）
  - 终止
- 若 `status != draft`：
  - 回复："`<曲名>` status 是 `<status>`，Phase 3 仅适用 draft 阶段。"
  - 终止

### 3. 检查前置文件
项目目录 `songs/<日期-曲名>/`：
- `assets/audio/<曲名>.mp3` 必须存在（用户已跑 Suno）
- `assets/audio/*.srt` 必须存在（用户已用 Chrome 扩展导出 Suno SRT）
- 都不存在则回复缺什么 + 操作指引（跑 Suno / 装 [Suno Lyric Downloader 扩展](https://chrome-stats.com/d/hhplbhnaldbldkgfkcfjklfneggokijm) 导出 SRT）+ 终止

### 4. 召唤抖叔（Phase 3 核心）

> 切换到抖叔身份。读 `personas/05-doushu-shortvideo.md` 加载行为准则。

抖叔输入契约（必读）：
- `<项目>/assets/audio/<曲名>.srt`（真实时间码 + 真实唱词，**核心输入**）
- `<项目>/00-brief.md` 的「画像」字段
- `<项目>/01-lyrics.md`（创作版本对照）
- `<项目>/02-suno-prompt.md`（BPM 参考）
- `knowledge/styles.md` 中本曲画像的「抖音 hook 模式」
- `knowledge/douyin-hooks.md`

抖叔产出：填充 `<项目>/04-shortvideo.md`（替换 templates 占位骨架）
- 15s + 30s 两版切片，**时间码从 SRT 取（毫秒精度）**
- 字幕用 **SRT 实际唱词**，跟 01-lyrics 稿子有差异时以 SRT 为准
- 含逐秒脚本（字幕 + 画面建议）+ 卡点位置 + 创作笔记

### 5. 老周质量门
读 `04-shortvideo.md` 末尾握手行。审核（按抖叔 §6 + 老周 §6）：
- [ ] SRT 文件已读 + 时间码取自 SRT
- [ ] 字幕用 SRT 实际唱词（核对 SRT vs 字幕）
- [ ] 15s 切片入点出点明确（精确到 0.01 秒）
- [ ] 15s 逐秒脚本 ≥ 5 行
- [ ] 30s 切片完整且与 15s 不重复
- [ ] 字幕每行 ≤ 12 字
- [ ] 至少 1 个明确卡点

不通过同抖叔重做（最多 2 次）。2 次都不过中断 + 上报。

### 6. 更新 INDEX
将该项目 `status` 从 `draft` 升 **`package_ready`**。

### 7. 向用户播报
温和教练风格：
- "🎬 `<曲名>` 04-shortvideo 已就绪（基于 Suno SRT 实际时间码 + 实际唱词）"
- 列亮点：15s 切片入点 `<XX:XX>` + 字幕第一句 + 切段理由
- 行动："出封面（擦水印）+ 上传抖音/汽水 + `/done <曲名>` 收尾"

## 错误处理
- **抖叔连续失败 3 次**：终止，上报"卡在 SRT 解析 / 切片选段 / 字幕节奏"等具体问题
- **SRT 缺失**：终止，提示用户先用 Chrome 扩展导出
- **mp3 缺失**：终止，提示用户先跑 Suno
