# 跨歌错峰编排模式 — 设计文档

> 日期：2026-05-17
> 状态：设计已批准，待实现
> 设计者：老白（工作室总设计师）

## 1. 背景与问题

主理人要同时推进多首歌 / MV。现状两条路都不行：

- **单会话**：每轮回复要等 Claude ~1 分钟。一个会话里所有歌串行卡在回复延迟上，主理人干等，无法并行。
- **多会话手动开**：N 个独立会话无协调中枢，共享文件（`songs/INDEX.md`、`memory/`）两个会话同时写会互相覆盖；会话之间不能交互。

需要一个有协调中枢、能并行、又不丢主理人判断权的编排模式。

## 2. 决策记录

| # | 决策点 | 结论 | 理由 |
|---|---|---|---|
| D1 | 编排架构 | 一个 orchestrator（老周）+ 后台 subagent 池 | 主理人只跟 orchestrator 一个对话；活派给后台 subagent 并行跑 |
| D2 | 主理人判断权 | 保留——每首歌每个决策点仍由主理人拍板 | 做歌是品味协作，主理人的一票否决不可让渡。编排并行的是"决策点之间的活"，不是决策本身 |
| D3 | subagent 边界 | 一个 subagent 跑"一个决策点到下一个决策点"的完整 chunk | chunk 内多 persona 顺序演在同一上下文里，无冷启动 |
| D4 | 与 2026-05-15 否决的关系 | 不冲突 | 2026-05-15 否的是"把一首歌的创作链拆成 N 个 agent、每 persona 一个、互相冷启动"。本设计是跨歌编排 + 单 subagent 跑完整 chunk，两回事。见 §5 |
| D5 | 共享文件写入 | 只有 orchestrator 写 `songs/INDEX.md` 和 `memory/`；subagent 只写自己那首歌的 `songs/<日期-曲名>/` | 避免多 subagent 并发写共享文件互相覆盖 |
| D6 | 触发 | 新命令 `/studio` 进入编排模式 | — |
| D7 | WIP 上限 | 同时在手 ≤ 3 首 | 超过主理人给不过来判断，会 thrash |

## 3. 机制

### 3.1 角色

- **orchestrator = 老周**（不新增 persona）。职责：持有所有在手歌的状态、把决策点逐个拎给主理人、派 subagent、维护 INDEX、给进度看板。
- **subagent**：执行单首歌的一个 chunk，跑完回报。后台运行（`run_in_background`），不阻塞 orchestrator。

### 3.2 循环

```
主理人在某首歌拍完一个决策点
   → orchestrator 派后台 subagent 跑"到下个决策点为止的 chunk"
   → orchestrator 立刻回来陪主理人推别的歌
   → subagent 跑完 / 跑到下个决策点 → 通知 orchestrator
   → orchestrator 把该决策点拎给主理人
```

主理人始终在动（轮流给各首歌拍板），活在后台并行煮，等待时间消除。

### 3.3 subagent 派发规则

- subagent prompt 必须**自包含**——主理人的决策 + 全部上下文一次给齐。subagent **不能找主理人**。
- subagent 跑 chunk 中途遇到歧义 / 卡住 → **停下回报**，不许猜。
- subagent 只写 `songs/<本歌目录>/`；INDEX / memory 的更新由 orchestrator 在收到回报后统一做。

### 3.4 进度看板

主理人随时说「进度」→ orchestrator 给看板：每首在手的歌一行 = 当前决策点 / 后台 subagent 在跑还是等拍板 / 下一步。
- `songs/INDEX.md` 仍是粗台账（status 字段）。
- 细粒度实时状态由 orchestrator 持有；可同时用 Claude Code task 列表（每首在手歌一个 task）。

## 4. 决策点清单 与 chunk 定义

**决策点（orchestrator 碰到就停、拎给主理人）：**

1. **起手** — 模式 A 个人IP / B 商业爆款 + 主理人的真实瞬间素材
2. **题材气质** — orchestrator 给 2-3 个 attitude 候选，主理人选
3. **歌词** — review 墨九的词，过 / 改
4. **Suno take** — 主理人跑 Suno、选 take（外部平台手动，天然异步）
5. **视觉** — 主理人按 `03-visual.md` 跑 Gemini 出封面、擦水印（外部手动，天然异步）
6. **发布** — 主理人上传汽水 / 抖音 + `/done`
7. **T+7 复盘** — `/review`

**subagent chunk（决策点之间的自动活）：**

| chunk | 从→到 | subagent 做什么 | 产出 |
|---|---|---|---|
| α | 起手 → 题材气质 | 题材 attitude 解析 + WebSearch 参照系研究 | 2-3 个 attitude 候选 |
| β | 题材气质 → 歌词 | 选画像 + 观山 `00-brief` + 墨九 `01-lyrics` | 歌词草稿 |
| γ | 歌词 → Suno take | 阿声 `02-suno-prompt` + 青衫 `03-visual` + 小汽 `05-release` + RUN.md，INDEX → package_ready | 完整工作包 |

DP4 / DP5 / DP6 本身是主理人在外部平台的手动操作，天然是异步空档。视频（`/make-video`）同理——选段是决策点，即梦 / 出图是手动异步段，拼接烧字幕是后台 chunk。

## 5. 与 2026-05-15「否决 agent team」的关系

`2026-05-15-laobai-studio-designer-design.md` D1 否决 agent team —— 否的是"把**一首歌内部**的创作链拆成 N 个 agent、每个 persona 一个、互相冷启动重建直觉"。

本设计不同：
- 跨**歌**编排，不是拆一首歌的链
- 一个 subagent 在**自己的上下文里顺序演完一个 chunk 的多个 persona**（如 chunk β：观山→墨九），无 per-persona 冷启动
- 品味协作仍在一个上下文内连续发生

故不冲突。2026-05-15 的结论（一首歌的链不拆）继续成立。

## 6. 文件改动清单

| 文件 | 动作 |
|---|---|
| `docs/.../specs/2026-05-17-cross-song-orchestration.md` | 本 spec（新建）|
| `.claude/commands/studio.md` | 新建 `/studio` 编排模式命令 |
| `personas/00-laozhou-producer.md` | 加 §8「编排模式」——老周作 orchestrator 的行为 |
| `CLAUDE.md` | Slash Commands 表登记 `/studio` + 工作流概览补一句 |

## 7. 升级 / 边界

- WIP ≤ 3 首。
- subagent 失败 → orchestrator 收到回报后按常规质量门处理（重做 / 上报主理人）。
- 编排模式是可选的——单首歌仍可直接 `/new-song`，不强制走 `/studio`。
