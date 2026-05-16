# <曲名> · 操作清单

> Phase 1 由老周汇总自 02/03/05。Phase 1 完成后 status = `package_ready`。
> **流程：Phase 2 跑 Suno + 出封面 → 上传发布 → `/done <曲名>`。视频是发布后的可选步骤。**

## Phase 2. 用户前置准备（Suno + 封面）

### 2.1 跑 Suno
- prompt 源：[`02-suno-prompt.md`](./02-suno-prompt.md)（Style 段 + 01-lyrics.md 的 Suno 输入版歌词）
- 操作：粘贴到 https://suno.com，生成 ≥ 4 版选最稳
- 产出：下载选定 take 到 `assets/audio/<曲名>.mp3`
- 提醒：选 take 后回填 `02-suno-prompt.md` 的"生成日志"和"最终选定"

### 2.2 出封面 + 擦水印
- prompt 源：[`03-visual.md`](./03-visual.md)（封面图 Prompt 段）
- 操作：粘贴到 Midjourney / 即梦 / Gemini；MJ 默认 1024 → **必须 upscale 到 2048+ 再下载**（汽水音乐要求 ≥1440×1440）
- 产出：导出到 `assets/cover/`（cover.png 1:1 主封面 + poster-9x16.png 抖音海报版）
- **擦水印（Gemini 出图必走）**：
  ```bash
  python3 tools/remove-watermark.py assets/cover/cover.png assets/cover/cover-clean.png
  ```
  默认 GWR 引擎（Reverse Alpha Blending 数学还原，lossless）。来源：https://github.com/GargantuaX/gemini-watermark-remover
- 完成判据：`assets/cover/cover.png`（或 `cover-clean.png`）存在

## Phase 3. 上传发布

- 文案源：[`05-release.md`](./05-release.md)
- 汽水音乐传 mp3 + 封面 + 复制 05 的标题/简介/标签
- 抖音传视频（汽水会自动生成卡片视频）+ 复制 05 的视频文案 + 置顶评论 1/2
- 完成判据：用户在汽水/抖音点击"发布"

收尾回 Claude 执行 `/done <曲名>`：老周更新 INDEX（status → `released`），启动 T+7 复盘倒计时。

---

## 可选 · 做抖音视频

视频**不是必做**——汽水发布会自动生成卡片视频。想做更好的抖音视频（生成画面 MV / 数字人演唱 MV / 检索素材拼接），发布前后任意时间跑：

```
/make-video <曲名>
```

抖叔会带你选路径 + 长度。**视频需要 Suno SRT**——做视频前在 Suno 选定 take 页面用 [Suno Lyric Downloader](https://chrome-stats.com/d/hhplbhnaldbldkgfkcfjklfneggokijm) 扩展导出 `assets/audio/<曲名>.srt`。
