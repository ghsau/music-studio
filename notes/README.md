# notes/ — 个人复盘归因记录（本地，不入 git）

这个目录装**算子 T+7 复盘产出的个人创作归因数据**——具体歌名、验证日期、数据快照、翻车案例等。

与 `knowledge/` 的区别：

| | `knowledge/` | `notes/` |
|---|---|---|
| **入 git** | ✅ 是 | ❌ 否（`.gitignore` 排除） |
| **内容** | 通用知识（参数表 / 策略 / 模板 / 字段说明） | 你的具体作品验证案例 + 复盘归因 |
| **谁写** | 算子复盘时回填**通用规则**部分 | 算子复盘时回填**具体归因**部分 |
| **谁读** | 任何 fork 的人 | 仅你本地 |

## 文件对照

| `knowledge/` | `notes/` |
|---|---|
| `styles.md`（画像参数表）| `styles-attribution.md`（你的画像验证记录）|
| `suno-vocal.md`（g2p 策略 + 翻车字清单）| `suno-vocal-attribution.md`（具体歌名 + 日期）|
| `douyin-hooks.md`（hook 模板）| `douyin-hooks-attribution.md`（你的 hook 实战归因）|
| `qishui-playbook.md`（运营 playbook）| `qishui-playbook-attribution.md`（你的发布轨迹案例）|
| `video-pipeline.md`（工具链架构）| `video-pipeline-notes.md`（你的实战记录）|

## 算子 SOP（dedup 分流）

T+7 复盘时回填两个目录：
- **通用规则**（"对照式 hook 普遍有效" / "Suno 多音字防御 X 方法"）→ `knowledge/<file>.md`
- **具体归因**（"《<曲名>》<日期> 验证 X 有效" / "<字> 翻车记录"）→ `notes/<file>-attribution.md`

详见 `personas/07-suanzi-analyst.md`。
