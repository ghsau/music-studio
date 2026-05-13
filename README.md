# music-studio

> **老周 · AI 音乐工作室** —— 一套基于 Claude Code 的 8 人 persona 协作框架，把"一句话主题"变成可发布的完整音乐工作包。

由独立音乐人个人使用 + 持续迭代而来。框架开源（MIT），创作产物保留在作者本地。你 fork 后可替换 persona / knowledge / templates 跑自己的工作流。

## 它做什么

输入一句话主题，自动产出：
- 概念 brief（核心句、关键词、意境、参照系、目标听众）
- 完整歌词（含 Suno 多音字 g2p 防御版）
- Suno prompt（Style + BPM + 调性 + 人声 + 结构标签）
- 封面 + 抖音海报 prompt（含 AI 出图防呆规则 + Gemini 擦水印工具链）
- 短视频切片脚本（基于 Suno 实际 SRT 时间码）
- 汽水音乐 + 抖音发布文案
- T+7 复盘 + 知识库回填

整套流程通过 `/new-song <主题>` 触发，由 8 个 persona 接力完成。

## 8 个 persona

| 花名 | 角色 |
|---|---|
| **老周** | 制作人 / 总监（默认主持人） |
| 观山 | 概念策划 |
| 墨九 | 作词人 |
| 阿声 | Suno prompt + 声乐指导 |
| 青衫 | 视觉总监 |
| 抖叔 | 短视频导演 |
| 小汽 | 汽水音乐 + 抖音运营 |
| 算子 | 数据分析师（T+7 复盘 + 知识库管理） |

详见 [`personas/`](./personas/) 与 [`CLAUDE.md`](./CLAUDE.md)。

## 快速开始

```bash
git clone https://github.com/ghsau/music-studio.git
cd music-studio

# Claude Code 启动后跑：
/new-song 暮春，等不到信
```

第一次 `/new-song` 时会自动从 `songs/INDEX.template.md` 初始化 `songs/INDEX.md` 作为你的作品台账。所有后续作品落到 `songs/<日期-曲名>/`，照 `RUN.md` 跑 Phase 2（Suno + 出封面 + 擦水印 + 上传），最后 `/done <曲名>` 标记发布。

T+7 后用 `/songbook` 触发到期复盘（默认走 playwright 自助采集音乐人后台数据）。

> **`songs/` 整个目录已默认 gitignore**——你的作品 / 音频 / 封面 / 复盘 都留本地。只有 `INDEX.template.md`（空模板）入 git。

## 平台兼容性

| 平台 | 支持度 | 说明 |
|---|---|---|
| **Claude Code**（CLI / 桌面 / Web / IDE） | ✅ 完整 | 设计目标，slash 命令 + MCP 工具链全可用 |
| **Gemini CLI** | ⚠️ 部分 | persona / templates / knowledge 可复用；`CLAUDE.md` → `GEMINI.md`，slash 命令需重写为 Gemini 格式 |
| **Codex / Cursor / 其他 LLM CLI** | ⚠️ 部分 | 同上；具体工具名映射参各 IDE 文档 |
| **网页版 Claude.ai / ChatGPT** | 🟡 文档参考 | persona / templates / knowledge 可作 prompt 上下文，失去 autopilot 编排 |

**框架解耦比例**：约 65% 内容（personas + templates + knowledge）是平台无关纯文本，35%（slash 命令 + MCP 工作流）是 Claude Code 专用。fork 后改造主要工作量在后者。

## 目录

```
.
├── CLAUDE.md              # 项目核心规则（Claude 启动必读）
├── personas/              # 8 个角色定义
├── templates/             # 项目模板（00-brief 到 06-review + RUN.md）
├── knowledge/             # 共享知识库（随复盘演化）
│   ├── styles.md          # 风格画像层（顶层路由）
│   ├── suno-vocal.md      # Suno 人声 + 多音字防御
│   ├── douyin-hooks.md    # 抖音爆款 hook 模板
│   ├── qishui-playbook.md # 汽水音乐运营
│   └── ...
├── .claude/commands/      # slash commands（/new-song / /done / /review / /songbook）
├── tools/                 # 辅助 Python 工具（check-assets / remove-watermark 等）
├── docs/superpowers/      # 设计 spec + 实施 plan（历史）
└── songs/                 # 你的作品（gitignored，本地工作目录）
```

## 设计核心

- **风格画像（顶层路由）**：5 个起步画像 + 升降级生命周期（参 `knowledge/styles.md`）
- **explore / converge 双模式**：published_count < 5 探索；≥5 且画像池有 ✅ 时收敛
- **知识库自演化**：每次 T+7 复盘按 dedup 4 规则（完全相同 / 语义相近 / 冲突 / 晋升）回填
- **多音字 g2p 双版本歌词**：发布展示版（汉字）+ Suno 输入版（带声调拼音），绕开 Suno 中文 g2p 翻车
- **外部优先原则**：自动化 / 工具 / 参照系 / 算法需求第一步 WebSearch，第二步才造轮子

完整设计：[`docs/superpowers/specs/2026-05-02-music-studio-design.md`](./docs/superpowers/specs/2026-05-02-music-studio-design.md)。

## 技术栈

- **Claude Code**（CLI / 桌面 / Web / IDE 插件均可）
- **Suno v5.5 Pro**（生成音频）
- **Gemini / Midjourney / 即梦**（出封面 + 海报）
- **Playwright MCP**（算子自助采集音乐人后台数据）
- **ffmpeg / Python 3**（音频切片 / 字幕烧入 / 资产规格自检）

## 适用人群

- 已在使用 Suno / Udio 等 AI 生成音乐，想要工作流编排的独立音乐人
- 中文音乐方向（国风 / 中文 rap / 民谣 / 流行）—— 知识库已沉淀大量中文 g2p / 国风意象 / 汽水 + 抖音运营经验
- 想 fork 后做自己工作室的人（替换 persona 名 / 调画像 / 改知识库即可）

## License

MIT —— 见 [`LICENSE`](./LICENSE)。

框架本身（personas / templates / knowledge / commands / tools / docs）随便用、随便改。

## 致谢

设计灵感来自实际独立音乐人创作日常 + Suno / Anthropic Claude Code 工具链。每一首跑通的歌都在迭代这个框架。
