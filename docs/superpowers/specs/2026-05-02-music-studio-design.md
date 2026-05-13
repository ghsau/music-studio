---
title: AI 独立音乐制作工作室 · 设计规格
date: 2026-05-02
status: approved
owner: didi
---

# AI 独立音乐制作工作室 · 设计规格

## 1. 背景与目标

### 1.1 用户画像
- 独立音乐人，目标：以 AI 工具高效产出并发布作品
- 主要生成方式：全 AI（Suno / Udio 类）
- 风格：国风为主，其他不限制
- 语言：中文为主
- 节奏：高产流水线，1~3 首/周，后续可能扩展到概念专辑
- 主发布平台：汽水音乐（绑定抖音生态）

### 1.2 设计目标
1. **AI 端到端自治**：把用户工作压缩到 4 个不可避免的"按钮级"动作（跑 Suno、出封面、剪短视频、上传发布）
2. **全流程覆盖**：概念 → 作词 → Suno prompt → 视觉 → 抖音切片 → 汽水发布 → 数据复盘
3. **越用越聪明**：每首歌发布后自动沉淀经验回知识库，下首歌的产出质量持续提升
4. **高产流水线**：`/new-song` 触发到 `RUN.md` 就绪 ≤ 5 分钟（不含外部生成时间）。"5 分钟"贯穿全文，§8 验收标准与本目标一致。

### 1.3 非目标（YAGNI）
- 不接入 Suno / Midjourney / 即梦的 API（先手动衔接，后续视情况扩展）
- 不做自动剪映 / 自动上传汽水（外部服务无公开 API）
- 不做多人协作（单人工作室）
- 第一版不做灵感速记入口（`inbox/`），后续按需迭代
- 不内置 MV 制作流程（短视频切片足够覆盖抖音生态）

## 2. 团队角色（8 位 Persona）

每个角色 = 一个 markdown 文件存于 `personas/`，主 Claude 按场景加载并扮演。

| 花名 | 角色 | 职责 | 主要产出文件 |
|---|---|---|---|
| 老周 | 制作人 / 总监（温和教练型） | 默认主持人，调度全队，质量监理 | 决策意见、最终质检 |
| 观山 | 概念策划 | 主题、意境、世界观 | `00-brief.md` |
| 墨九 | 作词人 | 国风歌词、副歌钩子 | `01-lyrics.md` |
| 阿声 | Suno Prompt 工程师 + 声乐指导 | Suno style/structure/vocal prompt | `02-suno-prompt.md` |
| 青衫 | 视觉总监 | 封面、海报画面 prompt | `03-visual.md` |
| 抖叔 | 短视频导演 | 抖音切片脚本（逐秒时间码 + 字幕） | `04-shortvideo.md` |
| 小汽 | 汽水音乐运营 | 标题、简介、标签、置顶评论 | `05-release.md` |
| 算子 | 数据分析师 | 发布后复盘 + 知识库回填 | `06-review.md` |

### 2.1 老周的"温和教练"行为准则
- 阶段开始：一两句话点明"现在做什么、为什么"
- 给反馈：先肯定，再建议改进，不直接否定
- 卡住时：主动给二选一方向，不干等
- 质量门：每节点轻量 check，不达标自己回炉，达标才往下走
- 决策：autopilot 模式下自己拍板，不再让用户 3 选 1

### 2.2 角色协作流（默认 autopilot）
```
观山 → 墨九 → 阿声 → [用户跑 Suno + 选 take]
                         ↓
        ┌────────────────┼────────────────┐
       青衫            抖叔            小汽
        └────────────────┼────────────────┘
                         ↓
                    [用户出图/剪片/上传]
                         ↓
                  T+7 天 → 算子复盘
                         ↓
                    沉淀回 knowledge/
```

### 2.3 Persona 文件规范模板（必须）

所有 8 个 persona 文件结构必须一致，包含以下 7 段（顺序固定）：

```markdown
# <花名> · <角色>

## 1. 身份
一句话身份描述 + 性格基调（2~3 句）

## 2. 职责
- 这个角色负责的 3~5 件具体事

## 3. 输入契约
- 必读：从哪些上游文件/知识库吸收信息（列出路径）
- 选读：可参考的 knowledge/ 文件
- 用户输入：用户可能直接传入什么

## 4. 输出契约
- 产出文件路径
- 必含字段（用 markdown 章节标题列出）
- 格式硬约束（如：歌词必须含 [Verse 1] / [Chorus] 标签；prompt 必须 < 200 词）

## 5. 行为准则
- 风格/语气
- 决策原则（例：墨九"宁可素不可俗"）
- 与"探索/收敛模式"的交互（见 §4.4）

## 6. 质量门（老周会 check 的项）
- 3~5 条可勾选的判据，每条一句话

## 7. 握手
- 完成后输出一行 handoff 给老周："已完成 X，建议下一步交给 Y"
- 失败/卡住时的上报格式
```

老周自己的 persona 文件结构略有不同（多一个"调度规则"段，少一个"握手"段），实施时单独说明。

### 2.4 角色握手契约（autopilot 三阶段）

**2026-05-11 重构**：抖叔从 Phase 1 挪到 Phase 3（Suno 跑完后）。原因：抖叔输出依赖**实际音频时间码 + 实际唱词**，跑 Suno 前写 04 等于估值"先射箭后画靶"。详 `memory/feedback_external_first.md` 同期反思。

#### Phase 1 — autopilot 一次跑完（Suno 跑前）

| 步骤 | 角色 | 输入 | 输出 | 老周质量门 |
|---|---|---|---|---|
| 1 | 老周 | 用户的 `<一句话主题>` | 项目骨架（拷贝 templates/）+ 占位 INDEX 条目 | 主题非空、目录创建成功 |
| 2 | 观山 | `主题` + `knowledge/guofeng-imagery.md` | `00-brief.md`（含：核心概念句、3 关键词、意境描述、目标听众） | 概念句 ≤ 30 字、3 关键词具体不空泛 |
| 3 | 墨九 | `00-brief.md` + `knowledge/guofeng-imagery.md` + `knowledge/guofeng-rhyme.md` + `knowledge/douyin-hooks.md` | `01-lyrics.md`（含：完整歌词带 [Verse]/[Chorus] 标签、副歌 hook 句、押韵脚） | 副歌 hook 句 ≤ 14 字、整首韵脚一致、含至少 2 个意象词 |
| 4 | 阿声 | `00-brief.md` + `01-lyrics.md` + `knowledge/suno-style-cn.md` + `knowledge/suno-vocal.md` | `02-suno-prompt.md`（含：style 描述、人声指示、结构标签如 [Intro]/[Outro]、BPM 建议） | style 关键词 ≥ 5 个、人声明确、结构标签齐全 |
| 5 | 青衫 | `00-brief.md` + `01-lyrics.md` | `03-visual.md`（含：封面图 prompt、配色方案、字体方向、海报画面） | prompt 可直接粘贴到 Midjourney/即梦/Gemini |
| 6 | 小汽 | `00-brief.md` + `01-lyrics.md` + `knowledge/qishui-playbook.md` | `05-release.md`（含：标题 ≤ 30 字、简介 ≤ 200 字、3~5 个标签、抖音文案、置顶评论 2 条） | 标题/简介符合字数限制、标签贴合 |
| 7 | 老周 | 步骤 2~6 全部产出 | `RUN.md`（操作清单 + 各步骤指向源文件） | 6 个文档齐全（00-03 + 05）、INDEX 已登记 status=draft |

Phase 1 结束 INDEX status = **draft（待 Suno 后补 04）**

#### Phase 2 — 用户操作（autopilot 暂停）

| 步骤 | 谁做 | 动作 |
|---|---|---|
| 8 | 👤 用户 | 跑 Suno → 选 take → mp3 落到 `assets/audio/<曲名>.mp3` |
| 9 | 👤 用户 | Chrome 扩展 [Suno Lyric Downloader] 导出实际唱词的 SRT 到 `assets/audio/<曲名>.srt` |
| 10 | 👤 用户 | 喊 `/finalize-shortvideo <曲名>` 触发 Phase 3 |

#### Phase 3 — 抖叔基于 Suno SRT 写 04（autopilot 续跑）

| 步骤 | 角色 | 输入 | 输出 | 老周质量门 |
|---|---|---|---|---|
| 11 | 抖叔 | `<曲名>.srt`（Suno 真实时间码 + 真实唱词）+ `02-suno-prompt.md`（BPM）+ `00-brief.md`（画像）+ `knowledge/douyin-hooks.md` | `04-shortvideo.md`（含：15s 与 30s 两版切片脚本、**精确时间码**、**SRT 实际字幕**、画面建议、卡点位置） | 切片含明确入点出点（毫秒级）、字幕用 SRT 实际唱词、字幕 ≤ 12 字/行 |
| 12 | 老周 | step 11 产出 | INDEX status → **package_ready** | 04 齐全 + 时间码精确 |

#### Phase 4 — 用户上传 + /done + T+7 复盘

| 步骤 | 谁做 | 动作 |
|---|---|---|
| 13 | 👤 用户 | 出封面 + 擦水印（tools/remove-watermark.py 默认 GWR） |
| 14 | 👤 用户 | 抖音传 final-XXs.mp4 + 汽水传 mp3 + 封面 + 复制 05 文案 |
| 15 | 👤 用户 | `/done <曲名>` → 老周更新 INDEX → git commit → T+7 倒计时 |
| 16（T+7 后） | 算子 | 用户贴入数据 + 全部 0X 文件 | `06-review.md` + 回填 `knowledge/` |

**握手机制**：每个角色完成后，在自己的产出文件末尾追加：
```markdown
---
**握手**：已完成 <文件名>，建议下一步交给 <下一角色>。
```
老周读到这一行后判断质量门通过与否，通过则推进，不通过则把同一角色召回重做（最多 2 次，第 3 次失败上报用户）。

### 2.5 失败处理
- **角色产出空/格式不符**：老周回炉重做，最多 2 次
- **第 3 次仍失败**：autopilot 中断，老周向用户上报具体问题（哪一节卡住、缺什么），由用户决定继续还是改方向
- **任何阶段用户喊停/喊改**：当前角色立即停笔，老周接管对话

## 3. 项目目录结构

```
/Users/didi/Project/ai/music/
├── CLAUDE.md                          常驻规则：默认老周主持，介绍全队
├── README.md
│
├── personas/
│   ├── 00-laozhou-producer.md
│   ├── 01-guanshan-concept.md
│   ├── 02-mojiu-lyricist.md
│   ├── 03-asheng-prompt.md
│   ├── 04-qingshan-visual.md
│   ├── 05-doushu-shortvideo.md
│   ├── 06-xiaoqi-promotion.md
│   └── 07-suanzi-analyst.md
│
├── songs/
│   ├── INDEX.md                       全部作品总台账（状态/数据/链接）
│   └── <YYYY-MM-DD-曲名>/
│       ├── 00-brief.md
│       ├── 01-lyrics.md
│       ├── 02-suno-prompt.md
│       ├── 03-visual.md
│       ├── 04-shortvideo.md
│       ├── 05-release.md
│       ├── 06-review.md               发布后填
│       ├── RUN.md                     用户操作清单
│       └── assets/
│           ├── audio/                 Suno 多版本 mp3
│           ├── cover/                 封面终图 + 海报
│           └── shorts/                抖音切片素材
│
├── knowledge/
│   ├── guofeng-imagery.md             意象词库
│   ├── guofeng-rhyme.md               押韵 + 词牌
│   ├── suno-style-cn.md               Suno 国风关键词
│   ├── suno-vocal.md                  戏腔/气声/转音 prompt
│   ├── douyin-hooks.md                抖音爆款 hook + 卡点
│   └── qishui-playbook.md             汽水音乐 SOP
│
├── templates/                         新项目用的模板（00~06.md + RUN.md）
│
└── .claude/
    ├── settings.json
    └── commands/
        ├── new-song.md
        ├── songbook.md
        ├── done.md
        ├── review.md
        └── persona.md
```

### 3.1 命名规范
- 项目文件夹：`<YYYY-MM-DD>-<曲名>` 例 `2026-05-02-青鸟不至`
- 文档前缀 `00-` ~ `06-`：天然按工作流顺序排
- `INDEX.md`：项目根台账，新歌自动登记，发布数据回填

### 3.2 资产管理
- 所有二进制（音频、图片、视频）放各项目的 `assets/` 子目录
- **不启用 Git LFS**（第一版保持简单）。`assets/` 默认 git 不忽略；当老周在 `/done <曲名>` 时检测到该项目 `assets/` 累计体积 > 50MB，会**一次性提示**用户："这首资产体积偏大，要么走 LFS、要么把原始素材移到外部存储只留终版"——具体处置由用户决定
- `.gitignore` 默认忽略：`.DS_Store`、`*.swp`、临时下载文件
- 实施清单 §10 须包含 `.gitignore` 创建项；不含 `.gitattributes`（因不启用 LFS）

### 3.3 INDEX.md 数据模型
台账每首歌一条记录，字段如下（实施时用 markdown 表格存储，便于人读）：

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `slug` | string | ✅ | 项目文件夹名，如 `2026-05-02-青鸟不至` |
| `title` | string | ✅ | 曲名 |
| `theme` | string | ✅ | 用户当初输入的一句话主题 |
| `status` | enum | ✅ | `draft` / `package_ready` / `released` / `reviewed` |
| `created_at` | date | ✅ | 立项日期 |
| `released_at` | date | 否 | 用户执行 `/done` 时写入 |
| `next_review_due` | date | 否 | `released_at + 7d`，老周每次启动扫描这字段 |
| `mode_at_creation` | enum | ✅ | `explore` / `converge`（见 §4.4） |
| `metrics` | string | 否 | 复盘时贴入的关键数据（播放/完播/点赞） |

INDEX.md 顶部还需保留一段 `## 全局状态`：
```
- published_count: <N>
- current_mode: explore | converge
- mode_switched_at: <date or null>
```
这段是 §4.4 自适应模式切换的状态源。

## 4. 工作流（autopilot 端到端）

### 4.1 启动到产出
```
用户：/new-song <一句话主题>
  ↓
[≤ 5 分钟内 AI 自动完成]
  老周创建项目骨架（拷贝 templates/）
  观山 拍板 1 版概念，写 00-brief.md
  墨九 直接出歌词终稿，写 01-lyrics.md
  阿声 出 Suno prompt，写 02-suno-prompt.md
  青衫 出封面 prompt，写 03-visual.md
  抖叔 出切片脚本，写 04-shortvideo.md
  小汽 出发布包，写 05-release.md
  老周 汇总生成 RUN.md 用户操作清单
  老周 在 INDEX.md 登记新项目，published_count 不变，mode_at_creation 取自全局
  ↓
老周向用户播报："工作包已就绪，照 RUN.md 跑就行"
```

#### 曲名生成规则
- 老周根据观山的 `00-brief.md` 中"核心概念句"提取 2~4 字曲名（不超过 6 字）
- 用户可通过 `/persona 老周 改名 <新曲名>` 覆盖

### 4.2 用户的 4 个不可避免动作（RUN.md 清单）

`RUN.md` 模板必含 4 个章节，每节对应一个外部动作：

```markdown
# <曲名> · 操作清单
## 1. 跑 Suno
- prompt 源：02-suno-prompt.md
- 操作：粘贴到 https://suno.com，生成 ≥ 4 版
- 产出：下载到 assets/audio/
- 完成判据：assets/audio/ 至少 1 个 mp3

## 2. 出封面
- prompt 源：03-visual.md（图像 prompt 段）
- 操作：粘贴到 Midjourney 或 即梦
- 产出：导出到 assets/cover/
- 完成判据：assets/cover/cover.jpg 存在

## 3. 剪短视频
- 脚本源：04-shortvideo.md
- 操作：剪映/CapCut 按时间码剪 15s + 30s 两版
- 产出：导出到 assets/shorts/
- 完成判据：至少 15s 切片存在

## 4. 上传发布
- 文案源：05-release.md
- 操作：汽水音乐上传 + 抖音同步
- 完成判据：用户在汽水/抖音点击"发布"

> 完成后回 Claude 执行 `/done <曲名>`，启动 T+7 复盘
```

### 4.3 决策机制：AI 拍板 + 用户一票否决
- 全程 AI 自动选最优解，不让用户多选
- 用户可在任意环节喊改：「这版概念太悲了，重写」/「副歌钩子换一个」
- 老周作为质量监理在内部循环（用户看不到来回，只看结果）

### 4.4 自适应学习模式（软化版 — 2026-05-09）

#### 状态存储
模式状态存于 `songs/INDEX.md` 顶部 `## 全局状态` 段：
- `published_count`: 已发布数（执行 `/done` 时 +1）
- `current_mode`: `explore` 或 `converge`（**advisory 字段，不强制行为**）
- `mode_switched_at`: 切换日期或 null

#### mode 字段的实际作用（核心：软化）

mode 是**全局倾向参考**，不是路由器：
- 路由本质永远是 **题材匹配**（参 `personas/00-laozhou-producer.md` §7）
- mode 只影响"题材匹配多个画像时倾向哪个"和"是否鼓励新画像"
- **绝不 override 题材匹配；不强制 80/20 比例**

**软化原因（2026-05-09 高爽提出）**：
原 §4.4 把 mode 设计成 hard rule（80/20 强制比 + 5 首阈值切），违背"题材决定画像"的根本逻辑。当题材没匹配 ✅ 画像时，强制 80% 复用 ✅ = 硬塞错画像。新逻辑下 mode 是 advisory tag，路由由题材决定。

| 模式 | 全局倾向 |
|---|---|
| explore | 鼓励新组合 / 多 🧪 / 大胆尝试 |
| converge | 题材匹配 ✅ 时倾向用 ✅；没匹配 ✅ 不强求，按题材自由选 |

#### 切换规则

老周在每次 `/new-song` 启动时读 `INDEX.md`：
- 若 `published_count < 5`：`current_mode = explore`
- 若 `published_count >= 5` 且 `current_mode == explore` 且 **`knowledge/styles.md` 至少有 1 个 ✅ 画像**：自动切 `converge`，写 `mode_switched_at`，向用户播报"题材匹配 ✅ 画像时倾向采纳，不强求百分比"
- 若 `published_count >= 5` 但 ✅ 画像池为空：保持 explore（converge 没意义）
- 用户可手动覆盖：`/persona 老周 切换模式 explore|converge`

#### 角色具体行为差异（软化版）

| 模式 | 观山 | 墨九 | 阿声 | 抖叔 |
|---|---|---|---|---|
| explore | 概念大胆 / 反套路；可新建画像 | 钩子句式不限制 | style 关键词可尝试新组合 | 卡点位置可实验 |
| converge | 题材匹配 ✅ 概念时倾向采纳；不强制 | 题材匹配 ✅ hook 句式时倾向采纳；不限定百分比 | 题材匹配 ✅ 组合时倾向采纳；不限定百分比 | 题材匹配 ✅ BPM/卡点时倾向采纳 |

调度时老周在召唤 prompt 里加：
- explore：「鼓励新组合 / 大胆尝试」
- converge：「如果题材匹配 ✅ 画像，请倾向采纳；如果没匹配，按题材自由选 🧪 / 新建画像」

**不再写**「80% / 20%」硬比。

#### ✅ 状态生命周期（2026-05-09 加）

✅ 是阶段性结论，不是永久 stamp。详见 `knowledge/styles.md`「## ✅ 状态生命周期」段。要点：
- ✅ 升级时记 `verified_at` + `reverify_due`（默认 +90d）
- 到期未重核 / 数据下降 / 外部变化 → 算子可降回 🧪
- 降级 ≠ 失败，可重新验证升回

### 4.5 复盘流程

#### 触发机制（无 cron，靠老周扫描）
- INDEX.md 每条记录含 `next_review_due` 字段（在 `/done` 时由系统计算 = `released_at + 7d`）
- 老周在**每次会话启动**和**每次 `/new-song` 之前**扫一次 INDEX.md
- 发现任意一条 `next_review_due <= 今天` 且 `status != reviewed`，主动提醒用户："`<曲名>` 已发布满 7 天，把数据贴一下让算子复盘"
- 用户主动执行 `/review <曲名>` 也可（不必等提醒）

#### 复盘步骤
```
用户 执行 /review <曲名>
  ↓
算子 提示用户贴数据（必须项：播放数、完播率、点赞、评论数；可选：截图）
  ↓
用户 贴入数据
  ↓
算子 写 06-review.md：
  - 数据快照
  - 爆点/哑点定位
  - 给观山的下首选题建议
  - "沉淀回知识库"清单
  ↓
算子 把"沉淀回知识库"清单的条目按 §6.3 dedup 策略补进 knowledge/
  ↓
算子 更新 INDEX.md：status = reviewed，清空 next_review_due
```

#### 用户无数据可贴的处理
若用户表示"还没数据/数据太差不想看"，算子仍写一份精简 review，仅含"无数据，原因：…"和"基于内容自评的下首建议"，避免流程卡死。INDEX.md status 仍标 `reviewed`。

## 5. Slash Commands

### 5.1 命令清单

| 命令 | 行为 |
|---|---|
| `/new-song <一句话主题>` | autopilot 启动：创建项目骨架，6 角色顺序产出，最终生成 RUN.md |
| `/songbook` | 读 `INDEX.md`，输出所有作品状态汇总 |
| `/done <曲名>` | 标记项目"已发布"，写 `released_at` 与 `next_review_due`，资产体积检查 |
| `/review <曲名>` | 算子上岗，要求用户贴数据，产出 06-review.md，回填 knowledge/ |
| `/persona <花名> <任务>` | 强制单独召唤某角色（绕过 autopilot） |

### 5.2 错误处理矩阵

| 命令 | 异常情形 | 处理 |
|---|---|---|
| `/new-song` | 主题为空 | 老周问回："给我一句话主题，比如'暮春，等不到信'" |
| `/new-song` | 同名/同 slug 已存在 | 自动加后缀 `-2`、`-3`，并在播报时告知用户 |
| `/new-song` | 任意 persona 连续失败 3 次 | 中断并向用户报告卡在哪一节、缺什么 |
| `/songbook` | INDEX.md 不存在或为空 | 输出"还没有作品。试试 `/new-song <主题>`" |
| `/done` | 曲名缺失 | 老周列出当前 `status=draft` 或 `package_ready` 的项目让用户选 |
| `/done` | 曲名匹配不到 | 老周用模糊匹配建议最接近的 1~3 个，若无任何匹配则提示 |
| `/done` | 项目已是 `released` | 提示"已经标记发布过了，要不要直接 `/review`？" |
| `/review` | 曲名缺失 | 列出 `next_review_due <= 今天` 的项目让用户选 |
| `/review` | 项目状态 `draft`/`package_ready`（未发布） | 提示"还没 `/done`，先发布完再来" |
| `/review` | 项目已 `reviewed` | 提示已复盘过，问是否要追加补充 review |
| `/persona` | 花名不存在 | 老周列出 8 位花名让用户选 |
| `/persona` | 在 song 项目外的工作目录调用 | 仍可生效（如 `/persona 老周 帮我整理 knowledge/`），不强制项目上下文 |

## 6. 知识库

### 6.1 文件清单
| 文件 | 内容 | 主要使用者 |
|---|---|---|
| `guofeng-imagery.md` | 国风意象词库（自然/情绪/时代符号），按场景分类 | 墨九、观山 |
| `guofeng-rhyme.md` | 中文 16 韵部速查、词牌结构、副歌常用韵脚 | 墨九 |
| `suno-style-cn.md` | Suno 国风 style 关键词（乐器/曲风/氛围） | 阿声 |
| `suno-vocal.md` | 戏腔/气声/转音 prompt + 已知有效/翻车组合 | 阿声 |
| `douyin-hooks.md` | 抖音爆款 hook 模式 + 卡点 BPM + 案例 | 抖叔、墨九 |
| `qishui-playbook.md` | 汽水音乐上传 SOP、标签策略、标题/简介模板 | 小汽 |

### 6.2 启动种子内容（实施时由我预填）
- `guofeng-imagery.md`：50+ 高频国风意象，带使用示例
- `suno-style-cn.md`：30+ 国风关键词组合，按曲风（古风民谣/国风电子/戏曲融合等）分类
- `douyin-hooks.md`：10 个已验证的爆款句式模板
- `qishui-playbook.md`：基础上传步骤骨架（具体最新 UI 由用户后续补充截图说明）
- 其他文件：基础结构 + 占位条目，由算子复盘后逐步填充

### 6.3 自动回填机制
算子在 `06-review.md` 中维护一段 `## 沉淀回知识库`，例：
```markdown
## 沉淀回知识库
- douyin-hooks.md: 副歌 0:48 入点 + 「我以为」句式 → 完播率 +30%
- suno-vocal.md: "breathy + slight melismatic" 组合 → 评论区情感共鸣高
- guofeng-imagery.md: "青鸟"意象在情感向选题里复用价值高
```

#### 知识库文件统一结构
每个 `knowledge/*.md` 顶部含 `## 已验证` 与 `## 实验中` 两节：
- `## 已验证`：被多次复盘验证有效（≥2 首歌），条目前缀 ✅
- `## 实验中`：仅单次出现，前缀 🧪
- 每个条目格式：`- <内容描述> [来源：曲名 / 曲名]`

#### 回填的 dedup / merge 策略
算子在 append 前必须执行：

1. **完全相同内容**（去除空格大小写后字符串相等）：不新增条目，仅在已有条目末尾追加来源标记 `[来源：旧曲名 / 新曲名]`
2. **语义相近**（关键词 70%+ 重合）：保留旧条目，追加一行 `> 关联：<新曲名> 进一步验证`
3. **冲突**（新条目结论与旧条目相反，例：旧"X 有效"vs 新"X 无效"）：不覆盖旧条目，**新建一条** `⚠️ 冲突：<新曲名> 观察到 X 在 <场景> 下不再有效，需进一步样本`
4. **晋升规则**：`## 实验中` 条目被复盘命中第 2 次后，移到 `## 已验证`，前缀改 ✅

算子每次回填完成后，在 review 末尾输出"知识库变更摘要"（新增/合并/晋升/冲突计数），便于人工抽查。

## 7. 关键设计决策记录

| 决策点 | 选择 | 理由 |
|---|---|---|
| 团队形式 | Persona markdown + 主 Claude 扮演 | 比 subagent 轻、共享上下文好；高产场景务实 |
| 老周风格 | 温和教练型 | 用户偏好；适合长期协作 |
| 自治程度 | autopilot + 用户一票否决 | 用户希望最小化介入，但保留干预权 |
| 探索/收敛节奏 | 前 5 首大胆，后续 80/20 | 用户选 C；适合数据驱动的高产 |
| 外部服务 | 手动衔接 + RUN.md 清单 | 先跑通流程，API 后期再接 |
| 视觉伴随 | 不启用 | 文档型设计无需可视化 |

## 8. 验收标准（实施后须满足）

1. **结构验收**：
   - `personas/` 8 个角色文件齐全，每个严格符合 §2.3 七段模板
   - `templates/` 8 个模板文件齐全（00~06 + RUN.md）
   - `knowledge/` 6 个文件齐全，4 个有种子内容（按 §6.2），所有文件含 `## 已验证` / `## 实验中` 两节骨架
   - `.claude/commands/` 5 个 slash command 配置齐全
   - INDEX.md 含 `## 全局状态` 段（§3.3）+ 空作品表

2. **功能验收**（端到端测试）：
   - 执行 `/new-song <测试主题>` 后，**≤ 5 分钟**自动产出完整 8 个文档（00~06 + RUN.md），含完整握手记录
   - INDEX.md 正确登记新项目，`mode_at_creation = explore`
   - 执行 `/songbook` 能看到该项目状态
   - 模拟"已发布"流程：执行 `/done` 后 `status=released`，`released_at` 与 `next_review_due` 正确写入；published_count +1
   - 模拟数据贴入：执行 `/review` 后产出 06-review.md，且 knowledge/ 至少 1 个文件被回填新条目（按 §6.3 dedup 策略），INDEX 中 `status=reviewed`

3. **错误路径验收**：覆盖 §5.2 错误处理矩阵中至少 5 个分支（如：空主题、同名 slug、未发布的 review、不存在的 persona、空 INDEX）

4. **质量验收**：
   - 老周表达风格符合"温和教练型"（先肯定后建议）
   - autopilot 全程不强求用户做选择题
   - knowledge/ 种子内容达到 §6.2 最低条数

5. **5 首切换点验收**（半自动）：手动把 `published_count` 改为 5、`current_mode = explore`，执行 `/new-song`，老周应自动切到 `converge` 并播报

## 9. 未来迭代方向（不在本次范围）

- 灵感速记入口 `inbox/`
- Suno / Midjourney / 即梦 API 接入
- 概念专辑模式（多首歌共享世界观）
- MV 制作流程
- 多平台分发（网易云/QQ音乐/Spotify 联动）
- 算子的数据采集自动化（OCR 截图 / 平台 API）

## 10. 实施清单（交给 writing-plans）

下一步由 `superpowers:writing-plans` 生成详细实施计划，需覆盖：
1. 项目骨架：`CLAUDE.md`、`README.md`、`.gitignore`、目录结构
2. 8 个 persona 文件（严格按 §2.3 七段模板，每个含完整行为指引、握手契约、§4.4 模式分支）
3. 8 个 template 文件（`templates/00-brief.md` ~ `templates/06-review.md` + `templates/RUN.md`）
4. 6 个 knowledge 文件（含 §6.2 种子内容、§6.3 已验证/实验中骨架结构）
5. 5 个 slash command 配置（`.claude/commands/*.md`，含 §5.2 错误处理逻辑）
6. INDEX.md 初始版（§3.3 全局状态段 + 空作品表）
7. `.claude/settings.json` 基础配置
8. 端到端测试用例：1 首正常路径 + 5 个错误路径 + 1 个模式切换路径
