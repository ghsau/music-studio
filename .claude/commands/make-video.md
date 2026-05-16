# /make-video

视频子系统触发器：给一首歌做抖音视频。**视频是发布后的可选步骤**，不是做歌主线。

**用户输入**：`$ARGUMENTS`（曲名，例：「盼长大」）

> 视频子系统设计见 `docs/superpowers/specs/2026-05-17-video-subsystem.md`，路径细节见 `knowledge/video-pipeline.md`。
> 3 条生成路径 + 长度选项，流程中间有用户手动断点（出图 / 跑即梦 / 检素材），故 `/make-video` 分两阶段，**同一命令重复跑**：
> - **断点前**：选路径 + 选段切音频 + 出交接文档（即梦 prompt / 关键帧需求）
> - **断点后**：拼接 + 烧字幕（检测到 `assets/mv/` 分段 mp4 已齐时自动进此阶段）

## 你的执行步骤

> 以**老周**身份执行。先 Read `personas/00-laozhou-producer.md`。

### 1. 参数检查
- 若 `$ARGUMENTS` 为空：Read `songs/INDEX.md`，列出 `package_ready` / `released` 且有 `assets/audio/*.srt` 的曲目，回复"给哪首做视频？" + 列表，终止。

### 2. 在 INDEX 查找曲名 + 检查前置
- Read `songs/INDEX.md`，匹配 `title`，定位项目目录
- 前置文件：`assets/audio/<曲名>.mp3` + `assets/audio/*.srt` 必须存在；缺则提示用户补，终止
- 路径 A 还需 `assets/cover/cover-clean.png`（即梦风格锚）

### 3. 判定阶段
- `assets/mv/` 下分段 mp4（`mv1.mp4` 起）**都存在** → 跳到 **断点后（步骤 B）**
- 否则 → **断点前（步骤 A）**

---

## 步骤 A · 断点前

### A1. 老周帮选路径 + 长度
向用户确认（老周据题材给建议，用户可改）：
- **路径**：A 生成画面 MV / B 数字人演唱 MV / C 检索素材拼接 MV
- **长度**：短版（15-30s）/ 完整版（60-90s）

### A2. 召唤抖叔选段
> 切换到抖叔身份。Read `personas/05-doushu-shortvideo.md`。

抖叔读 `<曲名>.srt` + `00-brief.md`「画像」+ `03-visual.md` + `knowledge/video-pipeline.md` 对应路径节，选连续段落、切 N 段（每段 ≤15s），向用户播报选段方案。
- ffmpeg 切音频 → `assets/audio/cuts/<曲名>-mv-0N.mp3` + 整段 `<曲名>-mv-full.mp3`

### A3. 按路径出交接文档
- **路径 A**：抖叔出每段即梦 prompt + 画面叙事简述 → 召唤青衫（Read `personas/04-qingshan-visual.md`）出 N 张 Gemini 9:16 关键帧 prompt → 抖叔填 `<项目>/mv-jimeng-handoff.md`（`templates/mv-jimeng-handoff.md` 模板）
- **路径 B**：抖叔出每段即梦数字人对口型动作 prompt → 召唤青衫出 9:16 歌手形象图 prompt（带环境，嘴部不遮挡）→ 抖叔汇总到 handoff 文档
- **路径 C**：抖叔按歌词意象列素材检索清单（中文素材站，标注须确认可商用授权）

### A4. 老周质量门 + 播报
审核（抖叔 §6 + 青衫 §6）。播报 + RUN 指引：用户跑 Gemini 出图（擦水印）/ 即梦逐段 / 检索素材 → 下载到 `assets/mv/mv1.mp4 …` → 回来重跑 `/make-video <曲名>` 进断点后。握手（抖叔 §7 断点前）。

---

## 步骤 B · 断点后（拼接 + 烧字幕）

> 切换到抖叔身份执行。

### B1. 核对分段 mp4
`assets/mv/` 下分段 mp4 齐。缺则提示补齐，终止。

### B2. 拼接
`ffprobe` 取每段对应音频精确时长 → ffmpeg `filter_complex`：每段 `trim` 到精确时长 + `concat` + map 干净音轨（`<曲名>-mv-full.mp3`，丢弃即梦自带音轨）→ `assets/mv/mv-assembled.mp4`（libx264 crf18）

### B3. 烧字幕
```bash
python3 tools/align-lyrics.py [--karaoke] \
  --input-video <项目>/assets/mv/mv-assembled.mp4 \
  --lyrics-srt <项目>/assets/audio/<曲名>.srt \
  --hook "<MV 选段首句>" --lead-in 0 \
  --output <项目>/assets/mv/final-mv.mp4
```
- 路径 A（生成画面）：静态字幕，加 `--font-size 104`
- 路径 B（数字人演唱）：加 `--karaoke`（卡拉OK扫光）

### B4. 老周验收 + 播报
抽 2-3 帧自查（字幕大小 / 音画位置）→ 播报 `final-mv.mp4` 路径 + 时长，提示用户播放验收 → 握手（抖叔 §7 断点后）。

## 错误处理
- 抖叔 / 青衫连续失败 3 次：终止，上报具体卡点
- SRT / mp3 / cover-clean 缺失：终止，给操作指引
- 断点后分段 mp4 不齐：终止，提示补齐
- **即梦视频水印**：`remove-watermark.py` 只擦 Gemini 图水印，不适用即梦视频水印；即梦会员若仍带水印需另搜方案
