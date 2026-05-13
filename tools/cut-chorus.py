#!/usr/bin/env python3
"""
cut-chorus.py — 找副歌起拍 + 切 N 秒副歌段。

两条路径：
  优先：从 Suno 导出的 SRT 直接读时间码（毫秒精度，零模型推理）
  fallback：stable-ts 强制对齐（无 SRT 时用；准度受模型限制）

依赖：
  ffmpeg（必须）
  stable-ts（仅 fallback 路径需要：pip install stable-ts）

用法（SRT 路径，推荐）：
  python3 tools/cut-chorus.py \\
      --input songs/2026-05-07-那几年/assets/audio/那几年.mp3 \\
      --lyrics-srt songs/2026-05-07-那几年/assets/audio/那几年.srt \\
      --hook "他扑过来的那几年" \\
      --output songs/2026-05-07-那几年/assets/audio/那几年-15s-chorus.mp3

用法（fallback 路径）：
  python3 tools/cut-chorus.py \\
      --input ... --full-lyrics 01-lyrics.md --hook "..." --output ...
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_DURATION = 15
DEFAULT_LEAD_IN = 0.2
DEFAULT_MODEL = "medium"
CONTEXT_WORDS = 4


def check_deps(need_stable_ts: bool):
    if shutil.which("ffmpeg") is None:
        sys.exit("✗ 缺少 ffmpeg。安装：brew install ffmpeg")
    if need_stable_ts:
        try:
            import stable_whisper  # noqa: F401
        except ImportError:
            sys.exit("✗ 缺少 stable-ts。安装：pip install stable-ts")


def normalize(s: str) -> str:
    """归一化：去空白 + 去标点（用于模糊匹配）"""
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'[，。！？、,.!?:;\-—…"“”‘’\(\)（）]', '', s)
    return s


# ---------- SRT 路径 ----------

def parse_srt_time(s: str) -> float:
    """SRT 时间码 → 秒（支持 ',' 或 '.' 作毫秒分隔）"""
    s = s.replace(',', '.')
    h, m, rest = s.split(':')
    return int(h) * 3600 + int(m) * 60 + float(rest)


def parse_srt(srt_path: Path) -> list:
    """解析 SRT，返回 [{start, end, text}, ...]，过滤掉结构标签和注释行"""
    text = srt_path.read_text(encoding="utf-8")
    blocks = re.split(r'\n\s*\n', text.strip())
    out = []
    for block in blocks:
        lines = [l for l in block.splitlines() if l.strip()]
        if len(lines) < 3:
            continue
        m = re.match(
            r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})',
            lines[1],
        )
        if not m:
            continue
        content = ' '.join(lines[2:]).strip()
        # 过滤结构标签 [Intro] / [Verse 1] / [Chorus]
        if re.fullmatch(r'\[[^\]]+\]', content):
            continue
        # 过滤注释行（中英括号包整行）
        if re.fullmatch(r'[（(][^）)]*[）)]', content):
            continue
        out.append({
            "start": parse_srt_time(m.group(1)),
            "end": parse_srt_time(m.group(2)),
            "text": content,
        })
    return out


def find_hook_time_srt(blocks: list, hook: str, occurrence: int = 1) -> tuple:
    """从 SRT blocks 找 hook 句第 N 次出现，返回 (start_sec, matched_block, total_count)"""
    hook_clean = normalize(hook)
    matches = [blk for blk in blocks if hook_clean in normalize(blk["text"])]
    if not matches:
        return None, None, 0
    if occurrence < 1 or occurrence > len(matches):
        return None, None, len(matches)
    blk = matches[occurrence - 1]
    return blk["start"], blk, len(matches)


# ---------- stable-ts 路径（fallback） ----------

def extract_pure_lyrics(lyrics_file: Path) -> str:
    text = lyrics_file.read_text(encoding="utf-8")
    if lyrics_file.suffix == ".md":
        m = re.search(r'(\[Intro\].*?)(?=\n## |\Z)', text, re.DOTALL)
        if m:
            text = m.group(1)
    text = re.sub(r'\[[^\]]+\]', '', text)
    text = re.sub(r'（[^）]*）', '', text)
    text = re.sub(r'\([^)]*\)', '', text)
    text = text.replace('……', '').replace('...', '')
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return '\n'.join(lines)


def find_hook_time_stable_ts(audio: Path, lyrics_text: str, hook: str,
                             model_size: str) -> float:
    print(f"[stable-ts] 对齐全曲（model={model_size}），耐心等 1-3 分钟...")
    import stable_whisper
    model = stable_whisper.load_model(model_size)
    result = model.align(str(audio), text=lyrics_text, language="zh")
    hook_clean = normalize(hook)

    words_flat = []
    for seg in result.segments:
        for w in (getattr(seg, 'words', None) or []):
            words_flat.append(w)

    if not words_flat:
        for seg in result.segments:
            if hook_clean in normalize(seg.text):
                return float(seg.start)
        sys.exit(f"✗ 没找到 hook 句「{hook}」")

    all_chars = ""
    char_to_word_idx = []
    for i, w in enumerate(words_flat):
        for c in normalize(w.word):
            all_chars += c
            char_to_word_idx.append(i)

    idx = all_chars.find(hook_clean)
    if idx < 0:
        sys.exit(f"✗ 在对齐结果里没找到 hook 句「{hook}」\n"
                 f"  全曲被识别为: {all_chars[:80]}...\n"
                 f"  排错：试更大模型 --model large-v3-turbo")

    word = words_flat[char_to_word_idx[idx]]
    print(f"  匹配 word: 「{word.word}」 @ {word.start:.2f}s")
    return float(word.start)


# ---------- 通用 ----------

def cut_audio(input_path: Path, output_path: Path, start_sec: float, duration: int):
    print(f"[切片] {start_sec:.2f}s 起，{duration}s → {output_path.name}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(input_path),
        "-ss", f"{start_sec:.2f}",
        "-t", str(duration),
        "-c:a", "libmp3lame", "-q:a", "2",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--input", required=True, type=Path,
                    help="完整曲 mp3")
    ap.add_argument("--hook", required=True,
                    help='副歌第一句字面量')
    ap.add_argument("--output", required=True, type=Path,
                    help="切片输出 mp3")

    # 两条路径二选一
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--lyrics-srt", type=Path,
                     help="Suno 导出的 SRT 文件（推荐）")
    src.add_argument("--full-lyrics", type=Path,
                     help="完整歌词文件 .md/.txt（fallback 走 stable-ts）")

    ap.add_argument("--duration", type=int, default=DEFAULT_DURATION,
                    help=f"切片时长秒（默认 {DEFAULT_DURATION}）")
    ap.add_argument("--lead-in", type=float, default=DEFAULT_LEAD_IN,
                    help=f"起点提前几秒（默认 {DEFAULT_LEAD_IN}）")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help=f"Whisper 模型（仅 fallback 路径用，默认 {DEFAULT_MODEL}）")
    ap.add_argument("--dry-run", action="store_true",
                    help="只找 hook 时间，不切片")
    ap.add_argument("--occurrence", type=int, default=1,
                    help="hook 句第几次出现（默认 1=Chorus 1；Final Chorus 通常是 3）")
    args = ap.parse_args()

    check_deps(need_stable_ts=(args.lyrics_srt is None))

    if not args.input.exists():
        sys.exit(f"✗ 音频不存在: {args.input}")

    print("=== 找副歌 + 切片 ===")
    print(f"输入音频: {args.input}")
    print(f"Hook 句: {args.hook}")

    if args.lyrics_srt:
        # SRT 快路径
        if not args.lyrics_srt.exists():
            sys.exit(f"✗ SRT 不存在: {args.lyrics_srt}")
        print(f"SRT 文件: {args.lyrics_srt}（毫秒精度路径）")
        blocks = parse_srt(args.lyrics_srt)
        print(f"  解析出 {len(blocks)} 行字幕（已过滤标签和注释）")

        hook_time, matched, total = find_hook_time_srt(
            blocks, args.hook, args.occurrence
        )
        if hook_time is None:
            if total == 0:
                sys.exit(f"✗ SRT 中没找到 hook 句「{args.hook}」")
            else:
                sys.exit(f"✗ hook 句「{args.hook}」共出现 {total} 次，"
                         f"--occurrence={args.occurrence} 越界")
        print(f"\n  ✓ 匹配行（第 {args.occurrence}/{total} 次出现）: 「{matched['text']}」")
        print(f"  时间窗口: {matched['start']:.3f}s - {matched['end']:.3f}s")
    else:
        # fallback: stable-ts
        if not args.full_lyrics.exists():
            sys.exit(f"✗ 歌词文件不存在: {args.full_lyrics}")
        print(f"歌词文件: {args.full_lyrics}（stable-ts fallback 路径）")
        lyrics_text = extract_pure_lyrics(args.full_lyrics)
        if normalize(args.hook) not in normalize(lyrics_text):
            sys.exit(f"✗ 歌词文件中找不到 hook 句「{args.hook}」")
        hook_time = find_hook_time_stable_ts(
            args.input, lyrics_text, args.hook, args.model
        )

    start_sec = max(0, hook_time - args.lead_in)
    print(f"\n  Hook 起始: {hook_time:.3f}s → 切片起点: {start_sec:.3f}s "
          f"(含 {args.lead_in}s lead-in)")

    if args.dry_run:
        print("\n  [dry-run] 不切片，仅验证")
        return

    print()
    cut_audio(args.input, args.output, start_sec, args.duration)
    print(f"\n✓ 完成: {args.output}（{args.duration}s）")


if __name__ == "__main__":
    main()
