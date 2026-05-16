# 视频制作 Pipeline 🧪

> 工作室有两条平行视频 pipeline，共用同一套上游真相数据和工具链：
> - **切片 pipeline** —— 15s/30s 抖音切片（`/finalize-shortvideo` → 抖叔）
> - **完整 MV pipeline** —— ~60-90s 抖音长视频 MV（`/make-mv` → 抖叔 + 青衫）
>
> **个人实战记录**（具体歌名 + 接续点 + 待优化点）记录在 `notes/video-pipeline-notes.md`，不入 git。

## 状态

🧪 **实验中** — 工具链已就位。AI 视频生成（即梦 / 可灵 / Runway）输出质量因题材而异，复用时建议先小规模实测。
- **切片 pipeline**：升级 ✅ 标准见文末。
- **完整 MV pipeline**：2026-05-15 盼长大端到端跑通 1 首（设计见 `docs/superpowers/specs/2026-05-16-mv-pipeline.md`），需第 2 首达标才升 ✅。

---

## 共用基础

### ✅ 1. Suno SRT 是上游真相数据

**问题**：本以为要自建 stable-ts / WhisperX 做歌词对齐。

**真相**：Suno 内部 endpoint `/api/gen/{songId}/aligned_lyrics/v2/` 已存有 word-level 时间码（毫秒精度，是创作的"地面真相"）。Chrome 扩展 [Suno Lyric Downloader](https://chrome-stats.com/d/hhplbhnaldbldkgfkcfjklfneggokijm) 一键导出 LRC + SRT。

**收益**：pipeline 从 1-3 分钟（stable-ts 推理）降到 < 1 秒；精度从 ±2s 升到毫秒级。

**普世教训**：自动化方案先查上游原始数据，别默认自建 ML 推理。

### ✅ 2. 即梦全能参考模式

**核心创新**：四模态混合输入（图 + 视频 + 音频 + 文本），**音频驱动镜头切换**——重音→切镜，弱拍→留白，是首次声音作为视频生成参考素材。

**最佳素材组合**（参 [官方教程](https://zhuanlan.zhihu.com/p/2023700533832065608)）：
- @图片1 美术风格锚（封面）
- @图片2 关键帧锚（海报 / 分段关键帧）
- @音频1 节奏锚
- 文字 prompt 含氛围 + 主体 + 风格 + 镜头线索 + 禁忌

**禁忌**：
- 不要超 3 张图（5 件素材最佳，9 张是上限非推荐）
- 不要分镜驱动（违背模型自由调度的设计）

### 工具清单

#### `tools/cut-chorus.py`
找 hook 句首次（或第 N 次）出现的时间，ffmpeg 切片（**切片 pipeline 用**）。

**双路径设计**：
- 优先：`--lyrics-srt PATH` 走 Suno 导出的 SRT（毫秒精度，零模型推理）✅
- Fallback：`--full-lyrics PATH` 走 stable-ts 强制对齐（中文歌曲偏差 ±2s，不推荐）

**关键参数**：
- `--occurrence N` ：hook 句第几次出现（默认 1=Chorus 1；Final Chorus 通常 = 3）
- `--lead-in SECONDS`：起点提前几秒（默认 0.2，赶 13s 上限时设 0）
- `--duration SECONDS`：切片时长（默认 15，即梦免费档 UI 实测 13s 上限）

#### `tools/align-lyrics.py`
SRT → .ass → ffmpeg 烧字幕。**两条 pipeline 都用**。

**双路径**同 cut-chorus。

**关键参数**：
- `--hook + --occurrence + --lead-in`：定位视频在原曲中的位置（与切片严格同步）
- `--audio-tempo`：如果切片做了 atempo 压缩（如 1.0758），字幕时间同步压缩
- `--font-size`：字号。默认 64 是按 1080×1920 ASS 画布算的，**切片用默认，完整 MV 用 104**（见下方完整 MV pipeline 第 5 步）

#### `tools/cut-audio.sh`
最朴素的 ffmpeg 切片包装（手指定起始时间），无智能。fallback / 完整 MV 分段切音频用。

#### `tools/remove-watermark.py`
GWR 引擎擦 Gemini sparkle 水印（关键帧 / 封面出图后必走）。详见 `personas/04-qingshan-visual.md` §5 防呆规则 5。

---

## 切片 pipeline（15s / 30s）

```
[L1 素材层]  完整 mp3 + SRT（Suno 毫秒时间码） + 风格图
                  ↓
[L2 切片层]  cut-chorus.py（找 hook + 切音频段）
                  ↓
[L3 生成层]  即梦 / 可灵 / Runway 全能参考模式（4 件素材 + 文字 prompt）
                  ↓
[L4 合成层]  align-lyrics.py（SRT 转 .ass + ffmpeg 烧字幕）
                  ↓
            final-XXs.mp4
```

### ✅ 3. atempo 加速突破时长上限

**问题**：即梦免费档音频 ≤ 13s，但完整 Pre-Chorus 段常超 13s。

**解法**：ffmpeg `atempo=1.0758` 微加速（3.5-7% 范围内人耳几乎不察），把超长段压缩到 ≤ 12.99s。

**模板**：
```bash
# Step 1: 切完整源段（含 0.5s buffer 留尾音）
ffmpeg -i full.mp3 -ss <start> -t <duration+0.5> -c:a libmp3lame -q:a 2 /tmp/full.mp3

# Step 2: atempo 压缩到 ≤ 12.99s（< 13s 严格）
ffmpeg -i /tmp/full.mp3 -af "atempo=<ratio>" -t 12.99 -c:a libmp3lame -q:a 2 final.mp3
```

`ratio = source_duration / target_duration`（保 < 13s 时把 target 设 12.99）。

字幕时间同步压缩：align-lyrics.py 加 `--audio-tempo <ratio>`。

> 注：即梦**会员档**单段可到 15s，无需 atempo。atempo 仅免费档 / 13s 卡线时用。

### ✅ 4. 选段策略（切片）

15s 切片可选 4 类切法（13s 时类似但要更挑剔）：

| 选段 | 内容 | 适用 |
|---|---|---|
| Chorus 1 起拍 | hook + 反差 punch 内容 | 反差直白题材 |
| Final Chorus 起拍 | hook + 觉悟句 + 终章前奏 | 觉悟终结题材 |
| **Pre-Chorus 反转弧** ⭐ | 设定 → 画面 → 前提 → 反转 4 句完整 | **社交媒体黄金"觉悟反转"结构** |
| 手指定其他段 | 用 cut-audio.sh | 兜底 |

**判断**：Pre-Chorus 反转弧最戳——设定→画面→前提→反转，4 句完整呈现是抖音爆款结构。

### 切片 AI 视频生成的待优化方向

复用时可能遇到 AI 视频效果不达发布标准（一镜到底 / 风格漂移 / 切镜不跟节奏 / 出脸 / 速度感不对）。可调优方向：

1. **改图组合**：试 cover + 1 张分镜关键帧 + 1 张运镜参考视频 + 音频
2. **prompt 精简**：镜头线索写太细会限制模型；试纯氛围 + 风格 + 主体三段
3. **时长试 14-15s**：UI 实测 13s 但官方说 15s
4. **换其他工具**：可灵 AI / Runway Gen-4 / Pika 2.x 对比
5. **手剪兜底**：用封面 / 海报作背景 + Ken Burns 运动 + ffmpeg 字幕，保 95% 质量

---

## 完整 MV pipeline（~60-90s）

> 抖音 / 视频号长视频 MV。2026-05-15 盼长大端到端跑通。设计见 `docs/superpowers/specs/2026-05-16-mv-pipeline.md`。
> 触发：`/make-mv <曲名>`（断点前选段+关键帧，断点后拼接+字幕）。

```
[1 选段切音频]  抖叔从全曲 SRT 选 ~60-90s 连续段落 → ffmpeg 切成 N 段（每段 ≤15s）
                  + 同范围整段导出作最终音轨（full-Xmin.mp3）
                       ↓
[2 分段关键帧]  青衫出 N 张 Gemini 9:16 关键帧 prompt（推进画面叙事）
                  用户跑 Gemini → remove-watermark.py 擦水印 → assets/mv/mv-kf-0N.png
                       ↓  ← 用户手动断点
[3 即梦逐段]    全能参考模式：@图片1=cover-clean（风格锚，全段共用）
                  + @图片2=该段关键帧 + @音频1=该段音频
                  会员 15s/段 + 最新模型；每段 ≥4 版选最稳 → assets/mv/mvN.mp4
                       ↓  ← 用户手动断点
[4 拼接]        ffmpeg filter_complex：每段 trim 到精确时长 + concat
                  + map 干净音轨（full-Xmin.mp3，丢弃即梦自带音轨）
                       ↓
[5 烧字幕]      align-lyrics.py --font-size 104 → final-mv.mp4
```

### 完整 MV 与切片的关键差异

| 维度 | 切片 (15s/30s) | 完整 MV (~60-90s) |
|---|---|---|
| 段数 | 1 段 | N 段（盼长大 5 段） |
| 单段时长 | ≤13s（即梦免费档）| ≤15s（即梦会员档） |
| 跨段一致性 | 不涉及 | 关键——靠一张 cover 作全段风格锚 |
| 关键帧 | 1 张 | N 张分段关键帧（青衫专出） |
| 字幕字号 | `--font-size 64`（默认） | `--font-size 104` |
| 触发命令 | `/finalize-shortvideo` | `/make-mv` |

### 关键坑

**1. 关键帧画风 = 即梦输出画风。** 即梦忠实跟关键帧的画风，不会自己转。盼长大关键帧出成写实电影感 → 即梦跟成写实，偏离了 `03-visual.md` 的「古风水墨融合」。**想要水墨，关键帧 Gemini prompt 必须显式出成水墨。**

**2. 字幕字号。** `align-lyrics.py` 默认 `--font-size 64` 按 1080×1920 ASS 画布算；MV 实际 720×1280，缩放后只剩 ~43px（占画面高 3.3%）偏小。**完整 MV 用 `--font-size 104`**（缩放后 ~69px / 占高 5.4%，落在 MV 常规 5-6% 区间）。

**3. 即梦实际出 ~15.07s/段。** 拼接时每段要 `trim` 回精确时长（盼长大：前 4 段 trim 0:15，末段 trim 到音频实长）。

**4. 跨段一致性靠 cover 风格锚。** N 段只用一张 cover 作 @图片1 风格锚，即梦会员最新模型成片仍像同一部片（盼长大 5 段验证 PASS）。

### 拼接命令模板

```bash
ffmpeg -y -i mv1.mp4 ... -i mvN.mp4 -i full-Xmin.mp3 \
  -filter_complex "[0:v]trim=0:15,setpts=PTS-STARTPTS[v0]; ... ;
                   [vN-1]...[concat=n=N:v=1:a=0[outv]" \
  -map "[outv]" -map N:a \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest mv-assembled.mp4
```

### 烧字幕命令

**静态字幕**（空镜 MV）：
```bash
python3 tools/align-lyrics.py \
  --input-video <拼好的MV> --lyrics-srt <全曲SRT> \
  --hook "<MV首句>" --lead-in 0 --font-size 104 \
  --output final-mv.mp4
```

**卡拉OK字幕**（演唱版 MV，加 `--karaoke`）：
```bash
python3 tools/align-lyrics.py --karaoke \
  --input-video <拼好的MV> --lyrics-srt <全曲SRT> \
  --hook "<MV首句>" --lead-in 0 \
  --output final-mv.mp4
```
`--karaoke` 模式：逐字扫光填充（`\kf`）+ 入场淡入弹出 + 位置上移（避开抖音底部描述区）。PlayRes 自动跟随视频实际宽高（非 9:16 不变形）；字号默认按视频高 5.5% 自适应。逐字时间码按行级时长在行内均分插值。无关键词高亮（2026-05-16 主理人确认先不做）。

`align-lyrics.py` 对全长 MV 一样适用（按 hook 定位 + 自动提取时间窗内字幕 + 过滤结构标签）。

### 即梦失败模式记录

复用时记录失败模式（一镜到底 / 风格漂移 / 跨段割裂 / 内容错 / 出脸 / 不跟节奏），跑完一起复盘。即梦会员最新模型 2026-05-15 verdict：跨段一致性 PASS，质量明显优于旧版，平替（Kling / Vidu）暂不需要。

---

## 字幕烧入注意

`align-lyrics.py` 默认用 `PingFang SC`（macOS 默认 CJK 字体），但 ffmpeg ass filter 在某些环境可能找不到字体。**首次使用时实测一次**，必要时配 `--fonts-dir`。

---

## 升级 ✅ 标准

- **切片 pipeline**：待跑通 ≥ 2 首歌且视频效果均达发布标准，升级 ✅。
- **完整 MV pipeline**：盼长大已跑通 1 首，待第 2 首完整 MV 达标后升级 ✅。

**升级时归因记录到 `notes/video-pipeline-notes.md`。**
