# /review

启动算子，对一首已发布作品做数据复盘。

**用户输入：** `$ARGUMENTS`（曲名）

## 你的执行步骤

> 以**老周**身份起手，验证后切换到**算子**身份。

### 1. 参数检查
- 若 `$ARGUMENTS` 为空：
  - Read `songs/INDEX.md`
  - 列出 `next_review_due <= 今天` 且 `status != reviewed` 的曲目
  - 回复："你想复盘哪首？" + 列表
  - 终止

### 2. 在 INDEX 中查找曲名 + 状态校验
- 精确匹配 `title`
- 若无匹配：模糊匹配建议
- 若 `status` 为 `draft` 或 `package_ready`（未发布）：
  - 回复："`<曲名>` 还没发布，先 `/done <曲名>` 标发布"
  - 终止
- 若 `status == reviewed`：
  - 回复："`<曲名>` 已经复盘过了。要追加补充版的复盘吗？回我"是"我就追加"
  - 终止
- 若状态正确（`released`）→ 进入步骤 3

### 3. 加载算子
- Read `personas/07-suanzi-analyst.md`
- 切换到算子身份

### 4. 算子要求用户贴数据
向用户输出：
```
来复盘 <曲名>。把数据贴一下：
- 汽水音乐：播放数 / 完播率 / 点赞 / 收藏 / 评论数
- 抖音：播放 / 完播率 / 点赞 / 评论 / 分享 / 涨粉
（贴不到也行，告诉我"没数据"，我做精简复盘）
```
等待用户回复。

### 5. 用户回复后产出 06-review.md
- 按 `templates/06-review.md` 填充
- 若用户给了数据 → 完整 review
- 若用户说"没数据" → 精简 review（仅"无数据"+ 基于内容自评的下首建议）

### 6. dedup 回填 knowledge/
对 06-review.md 末尾的"沉淀回知识库"清单中每一条：
- 按 SPEC §6.3 4 规则操作对应 `knowledge/<file>.md`
- 操作后更新 06-review.md 的"知识库变更摘要"段（4 个数字）

### 7. 更新 INDEX
- 该项目行：`status` → `reviewed`、`next_review_due` → 空、`metrics` → 用户给的关键数字摘要（如"播放 5w / 完播 42%"），无数据则填"无数据"

### 8. 提交 git（仅 knowledge/ 通用规则部分）
开源版工作室分流：
- `songs/` + `notes/*-attribution.md` 在 `.gitignore` 内 → 留本地
- `knowledge/` 入 git（算子复盘可能更新通用规则，应 commit）

```
git add knowledge/
git diff --cached --quiet && echo "knowledge/ 无变化，跳过 commit" || git commit -m "review: <曲名> — 沉淀通用规则"
```

> 若 fork 后改了 .gitignore 让 songs/ 入 git（私人音乐 repo），可加：
> ```
> git add songs/<日期-曲名>/06-review.md songs/INDEX.md
> ```

### 9. 播报
- 一行总结：爆点哑点
- 沉淀计数：新增 / 合并 / 晋升 / 冲突
- 给观山的下首方向建议（≤ 2 句）

## 错误处理
- 用户贴数据格式不规整 → 算子主动归整，不卡用户
- knowledge/ 写入失败 → 上报老周，不强写
