# 视频子系统重构 — 设计文档

> 日期：2026-05-17
> 状态：设计已批准（主理人确认主线位置 + 命令合一），待实现
> 设计者：老白（工作室总设计师）
> 取代：`2026-05-16-mv-pipeline.md`（其内容并入本 spec 的路径 A / B）

## 1. 背景与问题

视频能力是一块一块长出来的，现在乱：

- **`04-shortvideo`（切片脚本）和 `/make-mv`（完整 MV）概念重叠**——都是"视频产出"，却两套模型、两个命令、抖叔挂两种模式
- **演唱模式半成品**挂在 `2026-05-16-mv-pipeline.md` §6
- `knowledge/video-pipeline.md` 已塞「切片 + 完整 MV」两节，再加新路径会更挤
- 切片是 Phase 3 主线必经（卡 `package_ready`），但不是每首歌都值得做视频

主理人 2026-05-17 要求：按 3 条生产路径重构视频，整合成一个子系统。

## 2. 决策记录

| # | 决策点 | 结论 | 理由 |
|---|---|---|---|
| D1 | 整体结构 | 一个「视频子系统」= 共用底座 + 3 条生成路径 | 三条路径只是"画面从哪来"不同，底座（切音频/字幕/发布规格）完全共用 |
| D2 | 视频在主线的位置 | **发布后可选**，不再是 Phase 3 门槛 | 主理人拍板。歌做完（词/曲/封面/发布包）即 `package_ready`；视频是发布后按需做。不是每首歌都值得做视频，强制拖节奏 |
| D3 | 命令结构 | 合并为一个 `/make-video <曲名>` | 主理人拍板。`/finalize-shortvideo` + `/make-mv` 废弃。防命令膨胀 |
| D4 | 切片（15/30s）怎么归置 | 切片 = **长度选项**，不是独立路径 | 任一路径都可出「短版」或「完整版」。原 `04-shortvideo` 手剪脚本退役 |
| D5 | 3 条路径 | A 生成画面 / B 数字人演唱 / C 检索素材拼接 | 见 §3 |
| D6 | 谁统管 | 抖叔（"短视频导演"→"视频导演"）统管 3 路径；青衫供图（关键帧 / 歌手形象）；算子复盘 | 不新增 persona，抖叔职责扩展 |
| D7 | per-song 文件编号 | `04` 槽位退役，不重编号 | 重编号 05/06→04/05 churn 巨大；留空槽，`/make-video` 产出走 `assets/` + handoff 文档 |

## 3. 架构

```
视频子系统（抖叔统管 · 青衫供图 · 算子复盘）
│
├─ 共用底座（3 路径都用）
│   选段切音频（cut-chorus.py / 手切）
│   字幕烧入（align-lyrics.py，含 --karaoke 卡拉OK模式）
│   抖音发布规格（9:16 / 时长 / 编码）
│
├─ 路径 A · 生成画面 MV               🧪 待优化
│   歌词 → Gemini 关键帧 → 即梦全能参考逐段生成 → 拼接
│   = 现盼长大 final-mv。主理人评：当前视觉普通、没发挥即梦优势 → 标「待优化」，本轮不深做
│   交接模板：templates/mv-jimeng-handoff.md
│
├─ 路径 B · 数字人演唱 MV             🧪 进行中
│   歌手形象图 → 即梦数字人对口型逐段 → 拼接
│   当前角色：沧桑叙事型男歌手（singer-portrait）
│   字幕：align-lyrics.py --karaoke（卡拉OK扫光，整体提前 ~0.3s）
│   待解决：形象图出 9:16；即梦视频水印去除
│
└─ 路径 C · 检索素材拼接 MV           🧪 待调研落地
    歌词意象 → 检索现成素材 → 剪辑拼接
    定位：A/B 之外的低成本快速路径
```

### 3.1 路径 C 调研结论（2026-05-17 WebSearch）

- **中文素材源**：爱给网（中国风背景视频专区，水墨/古风）、摄图网、潮点视频、包图网、制片帮。⚠️ 版权——"免费"≠"可商用"，商业发布须确认授权并留凭证。
- **自动拼接工具**：FluxNote（beat-sync stock footage，基于 Pexels）、Pictory（按歌词主题匹配素材）、Revid。但多为英文 / Pexels 库，对国风中文题材适配差。
- **诚实判断**：2026 评测共识——"检索拼接（loop stock footage）"质量天花板**明显低于** AI 生成画面。**路径 C 定位为「低成本快速兜底版」**，不是主力。落地方式倾向：抖叔按意象从中文素材站人工/半自动检索 + ffmpeg 拼接，不强求全自动工具。

## 4. 工作流变化

**改造前**：Phase 3（`/finalize-shortvideo` → 抖叔 04-shortvideo）是主线必经，`package_ready` 等它。

**改造后**：
- Phase 1（`/new-song`）产出词/曲/视觉/发布包 → Phase 2 用户跑 Suno → **直接 `package_ready`**（不再等视频）
- 视频是 `package_ready` / `released` 之后的**可选**步骤：`/make-video <曲名>` 按需做
- `04` per-song 槽位退役；`/make-video` 产出走 `assets/` + handoff 文档

## 5. 文件改动清单（before → after）

| 文件 | 动作 |
|---|---|
| `docs/.../specs/2026-05-17-video-subsystem.md` | 本 spec（新建）|
| `docs/.../specs/2026-05-16-mv-pipeline.md` | 顶部标注「已并入 2026-05-17-video-subsystem.md」 |
| `knowledge/video-pipeline.md` | 重写为「共用底座 + 路径 A/B/C」 |
| `personas/05-doushu-shortvideo.md` | 抖叔 "短视频导演"→"视频导演"，统管 3 路径（文件名保留，省 churn）|
| `personas/04-qingshan-visual.md` | 青衫供图涵盖：路径 A 分段关键帧 + 路径 B 歌手形象 |
| `.claude/commands/make-video.md` | 新建（路径选择 A/B/C + 长度选择 短/完整）|
| `.claude/commands/finalize-shortvideo.md` | 删除 |
| `.claude/commands/make-mv.md` | 删除 |
| `.claude/commands/new-song.md` | 移除 Phase 3；Phase 1 完成即 `package_ready` |
| `personas/00-laozhou-producer.md` | Phase 3 段重写：视频移出主线 |
| `CLAUDE.md` | 命令表（去 finalize-shortvideo/make-mv，加 make-video）；工作流概览（视频改发布后可选）|
| `templates/04-shortvideo.md` | 退役（`/new-song` 不再拷贝）|

## 6. 升级 ✅ 条件

视频子系统整体保持 🧪。各路径独立按 `knowledge/video-pipeline.md` 升级标准（≥2 首达标 + 算子归因）升 ✅。
