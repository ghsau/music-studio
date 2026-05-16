# 完整 MV pipeline 固化 — 设计文档

> 日期：2026-05-16
> 状态：设计已批准，待实现
> 设计者：老白（工作室总设计师）

## 1. 背景与问题

工作室原有视频能力只覆盖 **15s/30s 切片**（`/finalize-shortvideo` → 抖叔 → `04-shortvideo.md`，工具链 `cut-chorus.py` / `align-lyrics.py`）。

2026-05-15 因主理人办了即梦会员，试跑了一条 **完整 MV**（盼长大，72s 抖音长视频）：用户从全曲选 ~1 分钟连续段落 → 切成 5 段 → 每段一张 Gemini 关键帧 → 即梦全能参考模式逐段生成 → ffmpeg 拼接 → 烧字幕。端到端跑通，主理人确认「这个跑通了」。

问题：这条流程目前只活在一次性的临时记忆和盼长大歌曲目录里的 `mv-jimeng-handoff.md` 中，不可复用。下次做 MV 要人肉重记 5 步。主理人要求固化成正式 pipeline。

## 2. 设计决策记录

| # | 决策点 | 结论 | 理由 |
|---|---|---|---|
| D1 | 固化 = 升 ✅？ | 否 | `video-pipeline.md` 升 ✅ 标准是「≥2 首达标」，完整 MV 只跑通 1 首（盼长大）。本轮只固化「流程可复用」，pipeline 保持 🧪，第 2 首完整 MV 跑通后由算子复盘升 ✅ |
| D2 | 切片 vs 完整 MV 关系 | 同一 knowledge 文件下的两条平行 pipeline | 共用基础（Suno SRT 真相数据 / 工具链 / 即梦全能参考），但选段策略、时长上限、段数不同。拆成两节，不混写 |
| D3 | 涉及哪些 persona | 抖叔（导演侧）+ 青衫（关键帧出图侧） | MV 5 步：选段/即梦交接/拼接/字幕属抖叔（短视频导演）；分段关键帧出图属青衫（视觉总监）。改动涉及 2 persona → 重大改造，落本 spec |
| D4 | 加 `/make-mv` 命令？ | 加 | MV 5 步中间有用户手动断点（Gemini 出图 + 即梦逐段是用户跑的）。命令负责断点前（选段切音频 + 生成即梦交接文档）和断点后（拼接 + 烧字幕），跟 `/finalize-shortvideo` 同构。主理人 2026-05-16 拍板 |
| D5 | 即梦交接文档归属 | 提成工作室级模板 `templates/mv-jimeng-handoff.md` | 盼长大那份是具体实例，结构可复用。模板化后 `/make-mv` 填充即可 |

## 3. 完整 MV pipeline（5 步）

```
[1 选段切音频]  抖叔从全曲 SRT 选 ~60-90s 连续段落 → ffmpeg 切成 N 段（每段 ≤15s）
                  + 同范围整段导出作最终音轨
                       ↓
[2 分段关键帧]  青衫出 N 张 Gemini 9:16 关键帧 prompt（推进画面叙事）
                  用户跑 Gemini → remove-watermark.py 擦水印
                       ↓  ← 用户手动断点
[3 即梦逐段]    即梦全能参考模式：@图片1=cover-clean（风格锚）+ @图片2=该段关键帧
                  + @音频1=该段音频；会员 15s/段 + 最新模型；每段 ≥4 版选最稳
                       ↓  ← 用户手动断点
[4 拼接]        ffmpeg filter_complex：每段 trim 到精确时长 + concat
                  + map 干净音轨（丢弃即梦自带音轨）
                       ↓
[5 烧字幕]      align-lyrics.py（--font-size 104）→ final-mv.mp4
```

### 3.1 与切片 pipeline 的关键差异

| 维度 | 切片 (15s/30s) | 完整 MV (~60-90s) |
|---|---|---|
| 段数 | 1 段 | N 段（盼长大 5 段） |
| 单段时长 | ≤13s（即梦免费档 UI 上限）| ≤15s（即梦会员档） |
| 跨段一致性 | 不涉及 | 关键——靠一张 cover 作全段风格锚 |
| 关键帧 | 1 张（青衫海报版可复用） | N 张分段关键帧（青衫专出，跨年龄/跨场景叙事必须） |
| 字幕字号 | `--font-size 64`（默认） | `--font-size 104`（72s 全长，64 缩放后偏小） |
| 触发命令 | `/finalize-shortvideo` | `/make-mv` |

### 3.2 关键坑（实现时写进 knowledge）

- **关键帧画风 = 即梦输出画风**。即梦忠实跟关键帧的画风，不会自己转。想要水墨，关键帧 Gemini prompt 必须显式出成水墨。
- **字幕字号**：`align-lyrics.py` 默认 `--font-size 64` 是按 1080×1920 ASS 画布算的；MV 实际 720×1280，缩放后只剩 ~43px（占画面高 3.3%）偏小。完整 MV 用 `--font-size 104`（缩放后 ~69px / 占高 5.4%）。
- **即梦实际出 ~15.07s/段**：拼接时每段要 trim 回精确时长。

## 4. 改动清单（before → after）

| 文件 | 动作 |
|---|---|
| `docs/superpowers/specs/2026-05-16-mv-pipeline.md` | 本 spec（新建） |
| `knowledge/video-pipeline.md` | 拆成「切片 pipeline」+「完整 MV pipeline」两节，整体保持 🧪 |
| `personas/05-doushu-shortvideo.md` | 抖叔职责 / 输入输出契约加「完整 MV 导演」 |
| `personas/04-qingshan-visual.md` | 青衫职责加「MV 分段关键帧出图」 |
| `templates/mv-jimeng-handoff.md` | 工作室级即梦交接模板（新建，从盼长大那份提炼） |
| `.claude/commands/make-mv.md` | `/make-mv` 命令（新建） |
| `CLAUDE.md` | Slash Commands 表登记 `/make-mv` |

## 5. 升级 ✅ 条件

完整 MV pipeline 跑通 **第 2 首**且效果达发布标准后，由算子在 T+7 复盘时升 ✅，归因记录到 `notes/video-pipeline-notes.md`。在此之前保持 🧪。
