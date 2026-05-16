#!/usr/bin/env python3
"""
align-lyrics.py — 把歌词字幕烧入视频，输出抖音规格 mp4。

两条路径：
  优先：从 Suno 导出的 SRT 直接读时间码（毫秒精度，零模型推理）
  fallback：stable-ts 强制对齐（仅当无 SRT 时用）

依赖：
  ffmpeg（必须）
  stable-ts（仅 fallback 路径需要：pip install stable-ts）

用法（SRT 路径，推荐）：
  python3 tools/align-lyrics.py \\
      --input-video songs/2026-05-07-那几年/assets/shorts/raw-15s.mp4 \\
      --lyrics-srt songs/2026-05-07-那几年/assets/audio/那几年.srt \\
      --hook "他扑过来的那几年" \\
      --output songs/2026-05-07-那几年/assets/shorts/final-15s.mp4

  注：--lead-in 必须和 cut-chorus.py 用的值一致（默认 0.2）

用法（fallback）：
  python3 tools/align-lyrics.py \\
      --input-video raw-15s.mp4 \\
      --lyrics-file lyrics-15s.txt \\
      --output final-15s.mp4
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


WHISPER_MODELS = ["tiny", "base", "small", "medium",
                  "large", "large-v2", "large-v3", "large-v3-turbo"]
DEFAULT_MODEL = "medium"

DEFAULT_FONT = "PingFang SC"
DEFAULT_FONT_SIZE = 64
DEFAULT_OUTLINE = 3
DEFAULT_MARGIN_V = 220
PRIMARY_COLOR = "&H00FFFFFF"
OUTLINE_COLOR = "&H00000000"
BACK_COLOR = "&H80000000"
ENCODING = 134

# 卡拉OK模式（完整 MV 演唱版用 --karaoke）
KARAOKE_SUNG = "&H00FFFFFF"    # 已唱=白
KARAOKE_UNSUNG = "&H00B0B0B0"  # 未唱=灰

DEFAULT_LEAD_IN = 0.2  # 与 cut-chorus.py 同步


def check_deps(need_stable_ts: bool):
    if shutil.which("ffmpeg") is None:
        sys.exit("✗ 缺少 ffmpeg。安装：brew install ffmpeg")
    if shutil.which("ffprobe") is None:
        sys.exit("✗ 缺少 ffprobe（含在 ffmpeg 包里）")
    if need_stable_ts:
        try:
            import stable_whisper  # noqa: F401
        except ImportError:
            sys.exit("✗ 缺少 stable-ts。安装：pip install stable-ts")


def normalize(s: str) -> str:
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'[，。！？、,.!?:;\-—…"“”‘’\(\)（）]', '', s)
    return s


# ---------- SRT 路径 ----------

def parse_srt_time(s: str) -> float:
    s = s.replace(',', '.')
    h, m, rest = s.split(':')
    return int(h) * 3600 + int(m) * 60 + float(rest)


def parse_srt(srt_path: Path) -> list:
    """解析 SRT 全曲，返回 lyric blocks（已过滤结构标签和注释）"""
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
        if re.fullmatch(r'\[[^\]]+\]', content):
            continue
        if re.fullmatch(r'[（(][^）)]*[）)]', content):
            continue
        out.append({
            "start": parse_srt_time(m.group(1)),
            "end": parse_srt_time(m.group(2)),
            "text": content,
        })
    return out


def find_hook_time_srt(blocks: list, hook: str, occurrence: int = 1) -> float:
    hook_clean = normalize(hook)
    matches = [blk for blk in blocks if hook_clean in normalize(blk["text"])]
    if not matches or occurrence < 1 or occurrence > len(matches):
        return None
    return matches[occurrence - 1]["start"]


def get_video_duration(video: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def get_video_dimensions(video: Path) -> tuple:
    """读视频实际宽高 —— 卡拉OK模式让 ASS PlayRes 跟随，避免非 9:16 视频字幕被拉变形"""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    w, h = out.split(",")[:2]
    return int(w), int(h)


def extract_video_segments(blocks: list, video_offset_in_full: float,
                           video_duration: float, audio_tempo: float = 1.0) -> list:
    """从全曲 SRT blocks 提取覆盖视频时间窗的部分，时间 offset 到 video 本地。
    audio_tempo > 1 时（音频被加速压缩），字幕时间也按此压缩"""
    # 视频在原音频中的覆盖范围 = 视频时长 × tempo（因为视频时长是压缩后的）
    source_window_duration = video_duration * audio_tempo
    source_window_end = video_offset_in_full + source_window_duration

    out = []
    for blk in blocks:
        if blk["end"] <= video_offset_in_full or blk["start"] >= source_window_end:
            continue
        # 先映射到 source-clip-relative，再除以 tempo 映射到 video-local
        src_start = max(0.0, blk["start"] - video_offset_in_full)
        src_end = min(source_window_duration, blk["end"] - video_offset_in_full)
        local_start = src_start / audio_tempo
        local_end = src_end / audio_tempo
        if local_end - local_start < 0.05:
            continue
        out.append({
            "start": local_start,
            "end": local_end,
            "text": blk["text"],
        })
    return out


# ---------- stable-ts 路径（fallback） ----------

def extract_audio(video: Path, audio_out: Path):
    print(f"[fallback 1/4] 提取音轨 → {audio_out.name}")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video), "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1", str(audio_out),
    ]
    subprocess.run(cmd, check=True)


def align_lyrics_stable_ts(audio: Path, lyrics_text: str, model_size: str) -> list:
    print(f"[fallback 2/4] stable-ts 对齐（model={model_size}）...")
    import stable_whisper
    model = stable_whisper.load_model(model_size)
    try:
        result = model.align(str(audio), text=lyrics_text, language="zh")
    except Exception as e:
        sys.exit(f"✗ 对齐失败: {e}")
    return [{"start": float(s.start), "end": float(s.end), "text": s.text.strip()}
            for s in result.segments]


# ---------- 通用：写 ASS + 烧字幕 ----------

def fmt_ass_time(secs: float) -> str:
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = secs % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def write_ass(segments: list, ass_out: Path, font: str, font_size: int):
    print(f"[字幕] 生成 → {ass_out.name}")
    header = (
        "[Script Info]\n"
        "Title: lyrics\n"
        "ScriptType: v4.00+\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{font},{font_size},{PRIMARY_COLOR},&H000000FF,"
        f"{OUTLINE_COLOR},{BACK_COLOR},-1,0,0,0,100,100,2,0,1,"
        f"{DEFAULT_OUTLINE},2,2,80,80,{DEFAULT_MARGIN_V},{ENCODING}\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    )
    lines = [header]
    for seg in segments:
        text = seg["text"].replace("\n", "\\N")
        lines.append(
            f"Dialogue: 0,{fmt_ass_time(seg['start'])},"
            f"{fmt_ass_time(seg['end'])},Default,,0,0,0,,{text}\n"
        )
    ass_out.write_text("".join(lines), encoding="utf-8")


def write_ass_karaoke(segments: list, ass_out: Path, font: str,
                      video_w: int, video_h: int, font_size: int = None):
    """卡拉OK模式 ASS：逐字扫光填充（\\kf）+ 入场动效。完整 MV 演唱版用。

    - PlayRes 跟随视频实际宽高，非 9:16 视频不变形
    - 逐字时间码：按行级时长在行内按字数均分插值（足够精准；
      若将来接 Suno word-level 数据可在此替换为真实逐字时间）
    - 无关键词高亮（2026-05-16 主理人确认：先不做）
    """
    print(f"[字幕] 生成卡拉OK ASS → {ass_out.name}（PlayRes {video_w}×{video_h}）")
    fs = font_size or round(video_h * 0.055)
    margin_v = round(video_h * 0.27)        # 上移避开抖音底部描述区
    outline = max(2, round(video_h * 0.0025))
    header = (
        "[Script Info]\n"
        "Title: karaoke\n"
        "ScriptType: v4.00+\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n"
        f"PlayResX: {video_w}\n"
        f"PlayResY: {video_h}\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: K,{font},{fs},{KARAOKE_SUNG},{KARAOKE_UNSUNG},"
        f"{OUTLINE_COLOR},{BACK_COLOR},-1,0,0,0,100,100,2,0,1,"
        f"{outline},2,2,70,70,{margin_v},{ENCODING}\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    )
    entrance = "{\\fad(140,0)\\fscx82\\fscy82\\t(0,220,\\fscx100\\fscy100)}"
    lines = [header]
    for seg in segments:
        chars = list(seg["text"].replace("\n", ""))
        n = len(chars)
        if n == 0:
            continue
        dur_cs = int(round((seg["end"] - seg["start"]) * 100))
        base = dur_cs // n
        k = []
        for i, c in enumerate(chars):
            d = base if i < n - 1 else dur_cs - base * (n - 1)
            k.append(f"{{\\kf{max(d, 1)}}}{c}")
        lines.append(
            f"Dialogue: 0,{fmt_ass_time(seg['start'])},"
            f"{fmt_ass_time(seg['end'])},K,,0,0,0,,{entrance}{''.join(k)}\n"
        )
    ass_out.write_text("".join(lines), encoding="utf-8")


def burn_subtitles(video: Path, ass: Path, output: Path, fonts_dir: Path = None):
    print(f"[烧字幕] ffmpeg → {output.name}")
    vf = f"ass={ass.as_posix()}"
    if fonts_dir and fonts_dir.exists():
        vf += f":fontsdir={fonts_dir.as_posix()}"
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-stats",
        "-i", str(video), "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "copy", "-pix_fmt", "yuv420p",
        str(output),
    ]
    subprocess.run(cmd, check=True)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--input-video", required=True, type=Path,
                    help="输入视频（即梦出的 mp4）")
    ap.add_argument("--output", required=True, type=Path,
                    help="输出视频")

    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--lyrics-srt", type=Path,
                     help="Suno 全曲 SRT（推荐）")
    src.add_argument("--lyrics-file", type=Path,
                     help="逐行字幕文件 .txt（fallback 走 stable-ts）")

    ap.add_argument("--hook",
                    help="副歌第一句（用 --lyrics-srt 时必填，定位视频在全曲中的位置）")
    ap.add_argument("--lead-in", type=float, default=DEFAULT_LEAD_IN,
                    help=f"切片相对 hook 提前的秒数，必须和 cut-chorus 同步（默认 {DEFAULT_LEAD_IN}）")
    ap.add_argument("--model", default=DEFAULT_MODEL, choices=WHISPER_MODELS,
                    help=f"Whisper 模型（仅 fallback 用，默认 {DEFAULT_MODEL}）")
    ap.add_argument("--font", default=DEFAULT_FONT)
    ap.add_argument("--font-size", type=int, default=DEFAULT_FONT_SIZE)
    ap.add_argument("--karaoke", action="store_true",
                    help="卡拉OK模式：逐字扫光填充 + 入场动效 + 位置上移（完整 MV 演唱版用）")
    ap.add_argument("--keep-intermediate", action="store_true")
    ap.add_argument("--fonts-dir", type=Path, default=None)
    ap.add_argument("--occurrence", type=int, default=1,
                    help="hook 句第几次出现（必须和 cut-chorus 同步；默认 1）")
    ap.add_argument("--audio-tempo", type=float, default=1.0,
                    help="音频被 atempo 加速的倍数（如 1.076；字幕时间会按此压缩）")
    args = ap.parse_args()

    check_deps(need_stable_ts=(args.lyrics_srt is None))

    if not args.input_video.exists():
        sys.exit(f"✗ 视频不存在: {args.input_video}")
    if args.lyrics_srt and not args.hook:
        sys.exit("✗ 用 --lyrics-srt 时必须传 --hook 来定位视频在全曲中的位置")

    print("=== 烧字幕 ===")
    print(f"输入视频: {args.input_video}")
    print(f"输出视频: {args.output}")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.keep_intermediate:
        work_dir = args.output.parent / f"{args.output.stem}-debug"
        work_dir.mkdir(exist_ok=True)
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="align-lyrics-"))
    ass_file = work_dir / "lyrics.ass"

    try:
        if args.lyrics_srt:
            # SRT 快路径
            if not args.lyrics_srt.exists():
                sys.exit(f"✗ SRT 不存在: {args.lyrics_srt}")
            print(f"SRT 文件: {args.lyrics_srt}（毫秒精度路径）")

            blocks = parse_srt(args.lyrics_srt)
            print(f"  全曲解析 {len(blocks)} 行字幕")

            hook_in_full = find_hook_time_srt(blocks, args.hook, args.occurrence)
            if hook_in_full is None:
                sys.exit(f"✗ SRT 中没找到 hook「{args.hook}」第 {args.occurrence} 次出现")

            video_offset_in_full = max(0, hook_in_full - args.lead_in)
            video_duration = get_video_duration(args.input_video)

            print(f"  视频时长: {video_duration:.2f}s")
            print(f"  视频起点对应全曲: {video_offset_in_full:.3f}s "
                  f"(hook {hook_in_full:.3f}s - lead-in {args.lead_in}s)")

            segments = extract_video_segments(
                blocks, video_offset_in_full, video_duration,
                audio_tempo=args.audio_tempo,
            )
            print(f"  视频窗内字幕: {len(segments)} 行")
            for i, s in enumerate(segments, 1):
                print(f"    {i}. [{s['start']:5.2f}-{s['end']:5.2f}s] {s['text']}")
        else:
            # fallback: stable-ts
            if not args.lyrics_file.exists():
                sys.exit(f"✗ 歌词文件不存在: {args.lyrics_file}")
            print(f"歌词文件: {args.lyrics_file}（stable-ts fallback）")
            audio_wav = work_dir / "audio.wav"
            extract_audio(args.input_video, audio_wav)
            lyrics_text = args.lyrics_file.read_text(encoding="utf-8").strip()
            segments = align_lyrics_stable_ts(audio_wav, lyrics_text, args.model)
            for i, s in enumerate(segments, 1):
                print(f"    {i}. [{s['start']:5.2f}-{s['end']:5.2f}s] {s['text']}")

        # 写 ass + 烧字幕
        if not segments:
            sys.exit("✗ 没有任何字幕行，检查输入")
        if args.karaoke:
            vw, vh = get_video_dimensions(args.input_video)
            fs = args.font_size if args.font_size != DEFAULT_FONT_SIZE else None
            write_ass_karaoke(segments, ass_file, args.font, vw, vh, fs)
        else:
            write_ass(segments, ass_file, args.font, args.font_size)
        burn_subtitles(args.input_video, ass_file, args.output, args.fonts_dir)

        if args.keep_intermediate:
            (work_dir / "segments.json").write_text(
                json.dumps(segments, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"\n中间产物: {work_dir}/")
    finally:
        if not args.keep_intermediate and work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)

    print(f"\n✓ 完成: {args.output}")


if __name__ == "__main__":
    main()
