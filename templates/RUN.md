# <曲名> · 操作清单

> Phase 1 由老周汇总自 02/03/05（**04 由 Phase 3 抖叔补**）。
> **流程：Phase 2 跑 Suno + 导 SRT + 出封面 → 喊 `/finalize-shortvideo <曲名>` 触发 Phase 3 抖叔写 04 → Phase 4 上传 + `/done <曲名>`。**

## Phase 2. 用户前置准备（Suno + SRT + 封面）

### 2.1 跑 Suno
- prompt 源：[`02-suno-prompt.md`](./02-suno-prompt.md)（Style 段 + 01-lyrics.md 的 Suno 输入版歌词）
- 操作：粘贴到 https://suno.com，生成 ≥ 4 版选最稳
- 产出：下载选定 take 到 `assets/audio/<曲名>.mp3`
- 完成判据：`assets/audio/<曲名>.mp3` 存在
- 提醒：选 take 后回填 `02-suno-prompt.md` 的"生成日志"和"最终选定"

### 2.2 导出 Suno SRT（必走 — 抖叔 Phase 3 输入）
- 在 Chrome 装 [Suno Lyric Downloader](https://chrome-stats.com/d/hhplbhnaldbldkgfkcfjklfneggokijm) 扩展
- 在 Suno 选定 take 的页面点扩展按钮 → 导出 SRT 到 `assets/audio/<曲名>.srt`
- 完成判据：`assets/audio/<曲名>.srt` 存在（SRT 是抖叔 Phase 3 时间码 + 字幕的精确来源）

### 2.3 出封面 + 擦水印
- prompt 源：[`03-visual.md`](./03-visual.md)（封面图 Prompt 段）
- 操作：粘贴到 Midjourney / 即梦 / Gemini；MJ 默认 1024 → **必须 upscale 到 2048+ 再下载**（汽水音乐要求 ≥1440×1440）
- 产出：导出到 `assets/cover/`（cover.png 1:1 主封面 + poster-9x16.png 抖音海报版）
- **擦水印（Gemini 出图必走）**：
  - Gemini 右下角有 sparkle 合规水印，必须擦掉
  - ```bash
    python3 tools/remove-watermark.py assets/cover/cover.png assets/cover/cover-clean.png
    ```
  - **默认 GWR 引擎**（Reverse Alpha Blending 数学还原）—— **lossless 无痕迹**，不破坏背景纹理
  - 来源：https://github.com/GargantuaX/gemini-watermark-remover（开源 MIT）
- 完成判据：`assets/cover/cover.png`（或 `cover-clean.png`）存在

## Phase 3. 抖叔补 04-shortvideo（autopilot，喊一句）

```
/finalize-shortvideo <曲名>
```

老周接住 → 召唤抖叔 → 抖叔基于 `<曲名>.srt` 实际时间码 + 实际唱词写 `04-shortvideo.md` → 老周质量门 → INDEX status → `package_ready`。

完成判据：`04-shortvideo.md` 已含真实时间码 + SRT 实际字幕。

## Phase 4. 上传发布

### 4.1 剪短视频（可选 — 默认跳过）
> 汽水音乐发布时会**自动生成歌曲卡片视频**，比手剪稳。默认走平台自动卡片，本步跳过。
> 想自己出片：照 `04-shortvideo.md`（抖叔产出，**含精确 SRT 时间码 + 字幕**）在剪映/CapCut 按时间码剪 15s + 30s 两版，导出到 `assets/shorts/`。

### 4.2 上传发布
- 文案源：[`05-release.md`](./05-release.md)
- 抖音传视频 + 复制 05 的视频文案 + 置顶评论 1/2
- 汽水音乐传 mp3 + 封面 + 复制 05 的标题/简介/标签
- 完成判据：用户在汽水/抖音点击"发布"

---

## 收尾

完成 Phase 2 + 3 + 4 全部后回 Claude，执行：
```
/done <曲名>
```

老周会更新 INDEX.md（status → `released`），git commit，启动 T+7 复盘倒计时。
