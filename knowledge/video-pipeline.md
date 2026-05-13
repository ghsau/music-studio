# 视频制作 Pipeline 🧪

> 抖音切片视频自动化工作流。工具链已就位，AI 视频生成质量待持续验证。
>
> **个人实战记录**（具体歌名 + 接续点 + 待优化点）记录在 `notes/video-pipeline-notes.md`，不入 git。

## 状态

🧪 **实验中** — 工具链已就位。AI 视频生成（即梦 Seedance 2.0 / 可灵 / Runway）输出质量因题材而异，复用本 pipeline 时建议先小规模实测。

---

## 架构（三层）

```
[L1 素材层]  完整 mp3 + SRT（Suno 自带毫秒精度时间码） + 风格图
                  ↓
[L2 切片层]  cut-chorus.py (找 hook + 切音频段)
                  ↓
[L3 生成层]  即梦 Seedance / 可灵 / Runway 全能参考模式（4 件素材 + 文字 prompt）
                  ↓
[L4 合成层]  align-lyrics.py (SRT 转 .ass + ffmpeg 烧字幕)
                  ↓
            final-XXs.mp4
```

---

## 工具清单

### `tools/cut-chorus.py`
找 hook 句首次（或第 N 次）出现的时间，ffmpeg 切片。

**双路径设计**：
- 优先：`--lyrics-srt PATH` 走 Suno 导出的 SRT（毫秒精度，零模型推理）✅
- Fallback：`--full-lyrics PATH` 走 stable-ts 强制对齐（中文歌曲偏差 ±2s，不推荐）

**关键参数**：
- `--occurrence N` ：hook 句第几次出现（默认 1=Chorus 1；Final Chorus 通常 = 3）
- `--lead-in SECONDS`：起点提前几秒（默认 0.2，赶 13s 上限时设 0）
- `--duration SECONDS`：切片时长（默认 15，即梦 UI 实测 13s 上限）

### `tools/align-lyrics.py`
SRT → .ass → ffmpeg 烧字幕。

**双路径**同 cut-chorus。

**关键参数**（与 cut-chorus 切片严格同步）：
- `--hook + --occurrence + --lead-in`：定位视频在原曲中的位置
- `--audio-tempo`：如果切片做了 atempo 压缩（如 1.0758），字幕时间同步压缩

### `tools/cut-audio.sh`
最朴素的 ffmpeg 切片包装（手指定起始时间），无智能。完全 fallback 用。

---

## 关键发现（通用技巧）

### ✅ 1. Suno SRT 是上游真相数据

**问题**：本以为要自建 stable-ts / WhisperX 做歌词对齐。

**真相**：Suno 内部 endpoint `/api/gen/{songId}/aligned_lyrics/v2/` 已存有 word-level 时间码（毫秒精度，是创作的"地面真相"）。Chrome 扩展 [Suno Lyric Downloader](https://chrome-stats.com/d/hhplbhnaldbldkgfkcfjklfneggokijm) 一键导出 LRC + SRT。

**收益**：pipeline 从 1-3 分钟（stable-ts 推理）降到 < 1 秒；精度从 ±2s 升到毫秒级。

**普世教训**：自动化方案先查上游原始数据，别默认自建 ML 推理。

### ✅ 2. 即梦 Seedance 2.0 全能参考模式

**核心创新**：四模态混合输入（图 + 视频 + 音频 + 文本），**音频驱动镜头切换**——重音→切镜，弱拍→留白，是首次声音作为视频生成参考素材。

**最佳素材组合**（参 [官方教程](https://zhuanlan.zhihu.com/p/2023700533832065608)）：
- @图片1 美术风格锚（封面）
- @图片2 关键帧锚（海报）
- @音频1 节奏锚（≤ 13s 上限）
- 文字 prompt 含氛围 + 主体 + 风格 + 镜头线索 + 禁忌

**禁忌**：
- 不要超 3 张图（5 件素材最佳，9 张是上限非推荐）
- 不要分镜驱动（违背模型自由调度的设计）
- 不要超 13s 音频（实测 UI 上限，官方文档说 15s 但 UI 卡 13s）

### ✅ 3. atempo 加速突破时长上限

**问题**：即梦音频 ≤ 13s，但完整 Pre-Chorus 段常超 13s。

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

### ✅ 4. 选段策略（通用）

15s 切片可选 4 类切法（13s 时类似但要更挑剔）：

| 选段 | 内容 | 适用 |
|---|---|---|
| Chorus 1 起拍 | hook + 反差 punch 内容 | 反差直白题材 |
| Final Chorus 起拍 | hook + 觉悟句 + 终章前奏 | 觉悟终结题材 |
| **Pre-Chorus 反转弧** ⭐ | 设定 → 画面 → 前提 → 反转 4 句完整 | **社交媒体黄金"觉悟反转"结构** |
| 手指定其他段 | 用 cut-audio.sh | 兜底 |

**判断**：Pre-Chorus 反转弧最戳——设定→画面→前提→反转，4 句完整呈现是抖音爆款结构。

---

## AI 视频生成的待优化方向

复用此 pipeline 时可能遇到 AI 视频效果不达发布标准（一镜到底 / 风格漂移 / 切镜不跟节奏 / 出脸 / 速度感不对）。可调优方向：

1. **改图组合**：试 cover + 1 张分镜关键帧 + 1 张运镜参考视频 + 音频
2. **prompt 精简**：镜头线索写太细会限制模型；试纯氛围 + 风格 + 主体三段
3. **时长试 14-15s**：UI 实测 13s 但官方说 15s，试 14s 看是否真接受
4. **换其他工具**：可灵 AI / Runway Gen-4 / Pika 2.x 实拍对比
5. **手剪兜底**：用封面/海报作背景 + Ken Burns 运动 + ffmpeg 字幕，保 95% 质量

---

## 字幕烧入注意

`align-lyrics.py` 默认用 `PingFang SC`（macOS 默认 CJK 字体），但 ffmpeg ass filter 在某些环境可能找不到字体。**首次使用时实测一次**，必要时配 `--fonts-dir`。

---

## 升级 ✅ 标准

待跑通 ≥ 2 首歌且视频效果均达发布标准，本 pipeline 升级 ✅。**升级时归因记录到 `notes/video-pipeline-notes.md`**。
