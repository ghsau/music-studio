# Suno 人声 Prompt（戏腔 / 气声 / 转音）

> 由阿声读写。Suno 的人声控制不稳定，本库重点记录"已知有效"和"翻车"模板。
>
> **本库管 g2p / 多音字 / 双版本歌词（让 Suno 念对字）**。音色辨识度（具体质感词、Suno Persona 签名声音、按画像分签名声音）见 `knowledge/vocal-identity.md` —— 阿声写人声指示前两库都必读。
>
> **个人验证归因**（具体歌名 + 日期 + 数据快照）记录在 `notes/suno-vocal-attribution.md`，不入 git。

## 已验证

### ✅ 双版本歌词策略（多音字 + 低频字防御）

详细做法在下方"## 翻车记录 → 防御策略 → 1. 双版本歌词"段。

- **覆盖范围**：Suno v5.5；v4.x 待验证；早期版本可能把裸拼音念成英文字母
- **降级触发条件**：reverify_due 到期未再验证 / 后续歌曲出现 g2p 翻车 / Suno 升级后 g2p 模型变化使本策略失效
- **fork 你自己的验证记录写到** `notes/suno-vocal-attribution.md`

## 实验中
（暂无）

## 种子内容

### 人声风格基础词
- female ethereal vocal
- male zen vocal
- breathy whisper vocal
- powerful belt vocal
- emotional cry vocal

### 戏腔类
- peking opera vocal
- kunqu opera influence
- chinese opera-style melisma
- traditional opera ornamentation
- 用法：仅在副歌或 bridge 偶发使用，全曲戏腔会显怪

### 气声类
- breathy
- airy whisper
- soft sighing vocal
- close-mic intimate vocal
- 用法：主歌叙事段最稳

### 转音类
- melismatic
- ornamented melody
- vocal runs
- traditional Chinese vocal embellishments
- 用法：副歌结尾或 hook 句尾，1~2 处

### 已知组合（待验证后晋升 ✅）
- 🧪 "breathy + slight melismatic"：抒情主歌 + 副歌微转音
- 🧪 "ethereal female + opera moments"：现代国风 + 副歌戏腔点缀
- 🧪 "soft whisper verse → powerful belt chorus"：动态对比，情绪推进

### 翻车记录（避免）
- ❌ "full peking opera throughout"：全曲戏腔在 Suno 上常出现跑调或机械感
- ❌ 同时指定 male + female + opera：模型混乱，常生成不一致
- ❌ "rap + chinese folk"：风格冲突，Suno 难以统一
- ❌ **中文 g2p 翻车（多音字 + 低频字共用一套解法）**：Suno 中文字到音模型对上下文敏感度差，多音字会读错音、低频/生僻字会读半边或念默认音

  - **多音字高发清单**：弹（dàn/tán）、还（hái/huán）、长（cháng/zhǎng）、重（chóng/zhòng）、藏（cáng/zàng）、了（le/liǎo）、和（hé/huò/hè）、看（kàn/kān）、划（huá/huà）、散（sàn/sǎn）、难（nán/nàn）、行（xíng/háng）、教（jiāo/jiào）、为（wéi/wèi）、得（dé/de/děi）、只（zhī/zhǐ）、咯（gē/kǎ/lo/luò）

  - **低频字翻车清单**（实测易翻车的字，遇到必拼音替换）：
    - 栈（zhàn）
    - 舷（xián）
    - 膊（bo 轻声 — "胳膊"易被读成 gē bó / 搏击义；正确 gē bo）
    - 咯噔（gē dēng — "咯"多音字 Suno 读错义项；"心里咯噔一下"作为常用拟声词组合，必拼音替换）
    - 登（dēng — 网络新词如"老登"，训练集稀疏，必带声调）
    - 笺（jiān — 古风字 / 低频，Suno 易读错偏旁如 qiān/zhǎn）
    - 舸（gě — 古典字"船"，低频，Suno 易读错）
    - 峥嵘（zhēng róng — 复合低频字，Suno 易读错单字）
    - （fork 后遇到新翻车字累加到 `notes/suno-vocal-attribution.md` + 同步回填本清单）

  - **同一首歌内同一多音字必须只用一个读音**——不要让 Suno 切换

  - 防御策略（按稳定度排）：
    1. ✅ **双版本歌词**（首推 / 已验证）。做法：
       - **发布展示版**：完整汉字（用于汽水音乐 / 抖音字幕）
       - **Suno 输入版**：把**多音字 + 翻车低频字**位置替换为带声调拼音（如「我听见 dàn」、「我替您 huán」、「雨水过 zhàn 板」），其他字保持汉字。给 Suno 时只复制 Suno 输入版
       - 原理：拼音绕开 Suno 中文 g2p 的歧义，汉字保留文学性。两边各取所需
       - 替换范围 = 多音字（必替） + 上方"低频字翻车清单"中的字（必替） + 实战中新发现的字（首次跑后回填）
       - 适用 Suno v5.5（v4.x 待验证；早期版本可能把裸拼音念成英文字母）
    2. **改词避开**：用同义常用字替换。损失文学性时不推荐——已被双版本歌词法替代
    3. **括号注音** `我听见弹(dàn)`：v4.x 约 50%；v5.5 实测仍可能失守。已被双版本歌词法替代
    4. 多音字放句尾强拍：Suno 倾向用标准/常用读音
    5. 多 take 选优：兜底
  - 写词时（墨九）+ 写 prompt 时（阿声）都要扫一遍多音字风险

### Prompt 写作模板

主歌段：
```
[Verse 1]
soft breathy female vocal, intimate close-mic
<歌词>
```

副歌段：
```
[Chorus]
soaring vocal with slight melismatic ornamentation
<歌词>
```
