# 声乐 / 音色辨识度知识库

> 由阿声读写，老白维护体系层。本库解决工作室一个核心盲区：**Suno 生成的音色泛、没有辨识度**。
>
> 诊断分两层：
> - **A 层·单首音色泛**——阿声 prompt 只写「warm male vocal」这种泛描述；泛描述出的是 Suno 的"统计平均声"，那正是"AI 味"的来源。解法：用**具体音色质感词**替代泛描述。
> - **B 层·跨歌无"高爽的签名声音"**——每首歌声音都不一样，听众建立不起"这是高爽"的记忆。解法：用 Suno **Persona 功能**锁声，**按画像分签名声音**。
>
> 与 `knowledge/suno-vocal.md` 分工：`suno-vocal.md` 管 g2p / 多音字 / 双版本歌词（让 Suno **念对字**）；本库管**音色辨识度**（让 Suno 唱出**有记忆点的声音**）。两库都是阿声必读。
>
> **个人验证归因**（具体歌名 + Persona 名/ID + 日期 + 数据快照）记录在 `notes/vocal-identity-attribution.md`，不入 git。

---

## 已验证 ✅

（空 — fork 后等你自己跑出验证案例。每个签名 Persona 被 ≥2 首歌经 T+7 复盘 + 算子归因验证后，由算子升级。）

## 实验中 🧪

（暂无 — 等主理人在 Suno 里实际创建首个签名 Persona 后回填）

---

## 板块 1 · 音色质感词库（直接进 Suno prompt）

**核心原理**（WebSearch 实测共识）：一个质感词 = 泛声；两个 = 略微不那么泛；**辨识度的诀窍是三层叠加 = Character + Delivery + Effects**。三层不给全，Suno 用统计平均填空——那就是 AI 味。

### Character（音色质地 — 声音"由什么做成"）

front-load 这一层：**Style 描述里音色词必须放最前面**，别埋在 genre 后面（Suno 前置处理，第 40 词后的描述被稀释）。

| 中文质感 | 英文（进 prompt） | 适合情绪 / 画像 |
|---|---|---|
| 沙哑 / 沙砾感 | raspy / gritty | 摇滚、blues、控诉、痛快直说；chinese-rap 快嘴向 |
| 颗粒感 | gravelly / textured grain | 悲伤、孤独、深情克制；叙事民谣、慢板抒情 |
| 烟嗓 | smoky / husky / whiskey-soaked | 沧桑、中年清醒、深夜独白；modern-narrative-folk |
| 气声 | breathy / airy | 亲密、私语、脆弱感；慢板抒情主歌 |
| 鼻腔共鸣 | nasal resonance | 民谣口语感、慵懒；宋冬野式叙事 |
| 磁性 / 醇厚 | velvety / warm-dark / rich baritone | 温暖、抚慰、深情；温暖大调向 |
| 清亮 / 通透 | bright / clear / crystalline | 抓耳、明朗、少年感；guofeng-pop、earworm-pop |
| 中性 / 少年感 | androgynous / boyish head-voice | 空灵、唯美、可柔可强；周深式 |
| 丝滑 | silky / smooth | 流畅、优雅；流行主歌 |
| 空灵 | ethereal | 国风缥缈、副歌升华 |
| 粗粝原始 | raw / unpolished | 真实感、authenticity；民谣、摇滚 |

> 选词原则：**明亮度**词（bright / clear）带"抓耳"商业优势；**颗粒度**词（gravelly / raspy / smoky）带"诉说感"和情绪感染力。慢歌叙事偏颗粒度，快歌抓耳偏明亮度。

### Delivery（演唱方式 — 声音"怎么唱"）

intimate / conversational / declarative / commanding / soaring / laid-back / behind-the-beat / whispered / belted / powerful

### Effects（制作处理 — 声音"怎么录的"）

dry close-mic / reverb-drenched / compressed / tape-saturated / lo-fi / wide stereo / broadcast-quality

### 写法模板

`[Character 2-3 词] + [register] + [Delivery 1-2 词] + [Effects 1 词] + [genre] + [BPM]`

例：`smoky male baritone, intimate behind-the-beat delivery, dry close-mic, modern folk, 78bpm`

**音色词总量控制 4-7 个**（约 100-150 字符）。超过 10 个互相稀释。**必带音域**（tenor / baritone / alto）——裸 "male vocal" 会被平均成中庸中音。

### 禁止 / 翻车

- ❌ 只写 `warm male vocal` / `男声温暖中音` 这种泛描述 —— 这是本库要根除的东西
- ❌ 矛盾词叠加 `whispered belting` —— 要动态对比就描述弧线：`starts whispered, builds to powerful belting`
- ❌ 音色词埋在 genre 后面 —— front-load 失效
- ❌ 全曲单一颗粒音色（如全程烟嗓）—— 听感浑浊油腻，需 verse/chorus 切换音色甩掉油腻感

---

## 板块 2 · Suno Persona 功能（B 层签名声音的技术实现）

WebSearch 查清的事实（Suno v5 / v5.5，Pro / Premier 订阅可用）：

### Persona 是什么

把一首已生成歌曲的"精华"（**主要是人声特征 + 整体风格**）存下来，跨歌复用。解决"两首歌听起来不像同一个艺人"的问题。**这是 B 层"按画像分签名声音"的技术载体。**

### 怎么创建 Persona

1. **选源歌曲**：从 library 选一首主唱**清晰稳定**的歌。源歌人声若被重效果 / 叠加和声 / 极端处理盖住，Persona 会锁到那些杂讯而非干净的声音身份。
2. 点歌曲三点菜单 → Create → **Make Persona**
3. 命名 + 可上传图 + 写 vocal style 描述
4. 保存，之后在 library 的 personas 区可见

> 关键：**Persona 的声音由捕获的源音频决定，描述文字只是组织用的标签，不改变声音**。所以选源歌曲是关键动作——选 take 时要选"辨识度最高那条"作 Persona 源。

### 怎么跨歌复用

- Custom 模式下，歌词框上方有 Personas 区，选中后 Suno 自动把 Persona 的风格填进 "Style of Music"
- 然后只补本曲的关键约束（别堆 genre）：**Persona 扛身份，prompt 只扛本曲约束**
- 烧 credit 前先用 Custom 模式跑 2-3 条短测试

### 限制

- 需 Pro / Premier 付费订阅；每首用 Persona 的歌约 10 credits
- **不能与 extend / cover 功能同用**
- 声音保真度尚可但可能抓不全极独特的唱腔细节
- **不同风格用不同 Persona** —— 官方明确建议别让一个 Persona 硬撑多风格（正是本库"按画像分签名声音"的依据）

### Persona vs Voices（voice cloning）

- **Voices**（v5.5+）：克隆**你自己**的真嗓，需读验证短语防滥用
- **Persona**：把任意已生成歌曲的声音存成可复用 profile
- 工作室用 **Persona** 路线（高爽不一定要克隆真嗓，按画像各锁一个满意的 AI 声即可）
- 注意：**用克隆 Voice 或成熟 Persona 时，Style 里别再写 `warm male vocal` 这类音色词**——Persona 已知道音色，再写会和 Persona 冲突。质感词只在**不用 Persona / 正在为某画像试音造 Persona** 时用足。

---

## 板块 3 · 多 take 选音色（标准升级）

**旧标准**：选"最稳"的 take（无跑调、无 bug）。
**新标准**：选**辨识度最高**的 take —— 在"无大 bug"的及格线之上，优先选音色质感最鲜明、最有记忆点、最像"一个具体的人"的那条。

选 take 三问：
1. 及格线：有没有跑调 / g2p 翻车 / 结构崩 → 有则直接淘汰
2. 辨识度：闭眼听，这条声音"是谁"够不够具体？还是又一个 Suno 平均声？
3. 签名一致性：若该画像已有签名 Persona，这条像不像那个声音？

**为某画像首次造签名 Persona 时**：跑多条 take，挑辨识度最高 + 音色定位最准的那条，用它 Make Persona。这一条 take 的选择决定该画像未来所有歌的声音身份，慎选。

---

## 板块 4 · 按画像分签名声音的机制

**策略**：不是全工作室一个声（太单调），也不是每首随机（无辨识度）——而是**每个风格画像锁定一个自己的签名 Suno Persona**，画像内部跨歌一致、可识别。

### 运转流程

1. 某画像第一次跑歌：阿声按该画像「目标音色定位」用足质感词写 prompt（板块 1）
2. 多 take 选辨识度最高那条（板块 3）
3. 主理人在 Suno 里把这条 Make Persona，命名（建议 `<画像名>-signature`），把 Persona 名/ID 回填到 `styles.md` 该画像的「签名声音 / Suno Persona」字段
4. 此后该画像所有新歌：阿声在 02-suno-prompt 注明调用该 Persona；Style 里不再堆音色泛词
5. 算子 T+7 复盘按签名 Persona 归因；≥2 首验证后该 Persona 在本库升 ✅

### 各画像目标音色定位（styles.md 同步加字段，详见板块 1 选词）

| 画像 | 目标音色定位（Character + Delivery 关键词） |
|---|---|
| guofeng-slow-lyric 国风慢板抒情 | 女气声空灵（breathy ethereal female）/ 男颗粒叙述 baritone（gravelly intimate baritone）；缠绵沉静、历史厚重 |
| guofeng-pop 国风流行 | 女清亮通透（bright clear female）/ 男温暖中音带微沙（warm male, slight rasp）；温暖治愈、抓耳 |
| modern-narrative-folk 现代叙事民谣 | 男烟嗓颗粒中音 + 内敛叙述（smoky gravelly male baritone, conversational close-mic）/ 女叙事感；克制、中年清醒。**这是最该用足质感词的画像**——毛不易/宋冬野的辨识度全在音色质感 |
| chinese-rap 中文说唱 | 男温暖中音 rap flow + 副歌 melodic（warm male, conversational rap delivery）；柔情向偏 husky 自陈，快嘴向偏 raw gritty 痛快 |
| earworm-pop 抓耳流行 | 清亮明朗 + doubled vocal harmony（bright punchy vocal, layered）；明亮度优先，抓耳跟唱 |

> 画像有增减时，本表同步。新画像填目标音色定位是该画像 8 字段之外的必填项。

---

## 板块 5 · Benchmark — 辨识度从哪来

WebSearch 拆解，提炼"辨识度来源"供阿声选音色 / 造 Persona 时对标：

| 歌手 | 辨识度来源 | 对工作室的启发 |
|---|---|---|
| 周深 | 中性少年感 + 薄声带通透高音；天然嗓音质地独特，可柔可强 | 中性 / androgynous 是强辨识度方向；空灵唯美题材可往这靠 |
| 林俊杰 | 强混声"金属芯" + 音色高度统一 + 渐强渐弱细腻 | 辨识度也可来自"统一" —— 签名 Persona 跨歌一致正是这个逻辑 |
| 毛不易 / 宋冬野 | 不靠炫技，靠**音色质感 + 叙事表达**；烟嗓颗粒感带天然"诉说感" | modern-narrative-folk 的核心 —— 音色质感本身就是辨识度，不需要高音 |
| Adele / Rod Stewart / Billie Eilish | 沙哑 / 颗粒 / 气声 husky 的"瑕疵"被打造成签名；raw 但有控制 | 别怕"不完美"音色 —— 颗粒感、气声的粗粝恰恰是记忆点；关键是"raw 但 controlled" |

**总结 — 辨识度四来源**：
1. 天然嗓音质地的独特性（Suno 里靠选源 take + 质感词逼近）
2. 明亮度（抓耳）与颗粒度（诉说感）—— 慢歌偏颗粒，快歌偏明亮
3. 后天发声技巧塑造的质感（烟嗓 / 强混 / 气声）—— 对应 prompt 的 Character 层
4. **统一性** —— 同一个声音反复出现才建立"这是谁"的记忆（= 签名 Persona 机制）

工作室 A 层解 1-3（质感词），B 层解 4（签名 Persona）。两层都做，才有"高爽的声音"。
