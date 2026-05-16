# /make-mv

完整 MV pipeline 触发器：把一首已发布 / 待发布的歌做成 ~60-90s 抖音长视频 MV。

**用户输入**：`$ARGUMENTS`（曲名，例：「盼长大」）

> 完整 MV 5 步设计见 `docs/superpowers/specs/2026-05-16-mv-pipeline.md` 与 `knowledge/video-pipeline.md`「完整 MV pipeline」节。
> 流程中间有用户手动断点（跑 Gemini + 即梦），故 `/make-mv` 分两阶段，**同一命令重复跑**：
> - **断点前**：选段切音频 + 出关键帧 prompt + 生成即梦交接文档
> - **断点后**：拼接 + 烧字幕（检测到 `assets/mv/mv*.mp4` 已齐时自动进此阶段）

## 你的执行步骤

> 以**老周**身份执行。先 Read `personas/00-laozhou-producer.md` 加载行为准则。

### 1. 参数检查
- 若 `$ARGUMENTS` 为空：
  - Read `songs/INDEX.md`
  - 列出 `status == released` 或 `package_ready` 且 `assets/audio/*.srt` 存在的曲目
  - 回复："你想给哪首做完整 MV？" + 列表，终止

### 2. 在 INDEX 查找曲名
- Read `songs/INDEX.md`，精确匹配 `title`（或模糊匹配 slug），定位项目目录 `songs/<日期-曲名>/`

### 3. 检查前置文件 + 判定阶段
项目目录下：
- `assets/audio/<曲名>.mp3` 必须存在（用户已跑 Suno）
- `assets/audio/*.srt` 必须存在（用户已导出 Suno SRT）
- `assets/cover/cover-clean.png` 必须存在（即梦全段风格锚；缺则提示用户先出干净封面）
- 缺任一 → 回复缺什么 + 操作指引，终止

**判定阶段**：
- 若 `assets/mv/mv1.mp4` 起的分段 mp4 **都存在** → 跳到 **断点后阶段（步骤 B）**
- 否则 → **断点前阶段（步骤 A）**

---

## 步骤 A · 断点前（选段 + 关键帧 + 即梦交接文档）

### A1. 召唤抖叔选段
> 切换到抖叔身份。Read `personas/05-doushu-shortvideo.md`，按「完整 MV 模式」行事。

抖叔输入契约（必读）：
- `<项目>/assets/audio/<曲名>.srt`（选段定位核心输入）
- `<项目>/00-brief.md`「画像」字段、`<项目>/03-visual.md`（视觉语言 / 风格锚）
- `knowledge/video-pipeline.md`「完整 MV pipeline」节、`templates/mv-jimeng-handoff.md`

抖叔产出：
- 选 ~60-90s 连续段落（典型 Verse → Pre-Chorus → Chorus），从 SRT 取毫秒时间码
- 切成 N 段，每段 ≤15s（末段为余数），给分段定位表
- 向用户播报选段范围 + 分段方案（用户保留一票否决；无异议即继续）

### A2. 切音频
按抖叔的分段方案，用 ffmpeg 切音频（毫秒时间码）：
- 每段 → `assets/audio/cuts/<曲名>-mv-0N.mp3`
- 选段整段（同范围）→ `assets/audio/cuts/<曲名>-mv-full.mp3`（作最终干净音轨）
```bash
ffmpeg -y -i <曲名>.mp3 -ss <段起> -to <段止> -c:a libmp3lame -q:a 2 <曲名>-mv-0N.mp3
ffmpeg -y -i <曲名>.mp3 -ss <选段起> -to <选段止> -c:a libmp3lame -q:a 2 <曲名>-mv-full.mp3
```

### A3. 抖叔出每段即梦 prompt
抖叔为每段写即梦 prompt（氛围 / 主体清单 / 风格锚 / 镜头线索 / 禁忌），并为每段写一句**画面叙事简述**交青衫。

### A4. 召唤青衫出分段关键帧
> 切换到青衫身份。Read `personas/04-qingshan-visual.md`，按「MV 分段关键帧模式」行事。

青衫据每段画面叙事简述 + `03-visual.md` 视觉语言，出 N 个 Gemini 9:16 关键帧 prompt：
- 走完整防呆规则（NO TEXT / NO BORDER / 人物锚 East Asian）
- **画风必须显式写明**（即梦只跟关键帧画风，不自己转）

### A5. 抖叔填充即梦交接文档
抖叔把选段表 + 青衫关键帧 prompt + 每段即梦 prompt 填进 `<项目>/mv-jimeng-handoff.md`（用 `templates/mv-jimeng-handoff.md` 模板）。

### A6. 老周质量门 + 播报
审核（抖叔 §6 完整 MV + 青衫 §6）：
- [ ] 选段连续、时间码取自 SRT
- [ ] 分段定位表完整（时长加总 = 选段总长）
- [ ] 每段即梦 prompt 五要素齐
- [ ] N 个关键帧 prompt 已回填，画风显式
- [ ] 音频已切到 `assets/audio/cuts/`

播报（温和教练风）+ RUN 指引：
- "🎬 `<曲名>` MV 即梦素材包已就绪（`mv-jimeng-handoff.md`）"
- 用户行动：① 跑 Gemini 出 N 张关键帧 → 每张跑 `python3 tools/remove-watermark.py` 擦水印 → 存 `assets/mv/mv-kf-0N.png`　② 即梦逐段（全能参考，会员最新模型，每段 ≥4 版选最稳）→ 下载到 `assets/mv/mv1.mp4` … `mvN.mp4`　③ 回来重跑 `/make-mv <曲名>` 进断点后阶段
- 握手（抖叔 §7 完整 MV · 断点前）

---

## 步骤 B · 断点后（拼接 + 烧字幕）

> 切换到抖叔身份执行拼接。

### B1. 核对分段 mp4
`assets/mv/` 下 `mv1.mp4` … `mvN.mp4` 齐（N = 即梦段数）。缺段则提示用户补齐，终止。

### B2. 取精确时长
- `ffprobe` 每段对应音频 `assets/audio/cuts/<曲名>-mv-0N.mp3` 取时长
- 前 N-1 段 trim 到 15.0s（或其音频实长，取较小值）；末段 trim 到末段音频实长

### B3. ffmpeg 拼接
filter_complex：每段 `trim` 到精确时长 + `setpts` 重置 + `concat`，map 干净音轨（`<曲名>-mv-full.mp3`，丢弃即梦自带音轨）：
```bash
ffmpeg -y -i mv1.mp4 … -i mvN.mp4 -i <曲名>-mv-full.mp3 \
  -filter_complex "[0:v]trim=0:<t1>,setpts=PTS-STARTPTS[v0]; … ;
                   [v0]…[vN-1]concat=n=N:v=1:a=0[outv]" \
  -map "[outv]" -map N:a -c:v libx264 -preset medium -crf 18 \
  -pix_fmt yuv420p -c:a aac -b:a 192k -shortest assets/mv/mv-assembled.mp4
```

### B4. 烧字幕
```bash
python3 tools/align-lyrics.py \
  --input-video <项目>/assets/mv/mv-assembled.mp4 \
  --lyrics-srt <项目>/assets/audio/<曲名>.srt \
  --hook "<MV 选段首句>" --lead-in 0 --font-size 104 \
  --output <项目>/assets/mv/final-mv.mp4
```
`--hook` 取选段第一句唱词，`--font-size 104`（完整 MV 必须，默认 64 在 720×1280 上偏小）。

### B5. 老周验收 + 播报
- 抽 2-3 帧自查（字幕大小 / 音画位置）
- 播报：`final-mv.mp4` 路径 + 时长，提示用户播放验收（风格 / 跨段一致 / 音画同步）
- 握手（抖叔 §7 完整 MV · 断点后）
- 提醒：完整 MV pipeline 仍 🧪，本首达标后是第 2 首验证样本（≥2 首升 ✅）

## 错误处理
- **抖叔 / 青衫连续失败 3 次**：终止，上报具体卡点
- **SRT / mp3 / cover-clean 缺失**：终止，给操作指引
- **断点后分段 mp4 不齐**：终止，提示补齐即梦分段
- **即梦视频带水印**：`remove-watermark.py` 是 Gemini 图水印工具，不适用即梦视频水印；若即梦会员导出仍带水印，需另搜即梦专用方案（别用通用 delogo / inpaint）
