#!/usr/bin/env python3
"""
align-shots.py — Whisper 自动对齐 shots.json 时间码。

流程：
1. 调 whisper-cli 跑 audio，输出 srt（缓存到 audio 同目录）
2. 把 srt 展开成 char-stream + 每字符的时间戳
3. 对 shots.json 里每个 cut 内的 shots[].text，用 difflib 在 char-stream 单调对齐
4. 重写 shots.json：audio_in/audio_out + shot.start/end（相对 audio_in）
5. 备份原 shots.json 到 shots.json.bak

用法：
    python3 tools/align-shots.py songs/2026-05-02-迟信/shots.json
    python3 tools/align-shots.py <shots.json> --pad-in 0.5 --pad-out 0.8
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

WHISPER_BIN = "whisper-cli"
WHISPER_MODEL = str(Path.home() / ".cache/whisper/ggml-large-v3-turbo.bin")
PUNCT_RE = re.compile(r"[\s，。！？、\"\"''…·,.!?\-_]+")


def run_whisper(audio_path, srt_path, force=False):
    if srt_path.exists() and not force:
        print(f"使用缓存 srt：{srt_path}")
        return srt_path
    out_base = str(srt_path).rsplit(".srt", 1)[0]
    cmd = [
        WHISPER_BIN,
        "-m", WHISPER_MODEL,
        "-f", str(audio_path),
        "-l", "zh",
        "-osrt",
        "-of", out_base,
        "--max-len", "16",
        "-np",
    ]
    print(f"运行 whisper-cli ...")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        sys.exit("whisper-cli 失败")
    if not srt_path.exists():
        sys.exit(f"srt 没生成：{srt_path}")
    return srt_path


def parse_srt(srt_path):
    raw = srt_path.read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", raw.strip())
    time_re = re.compile(
        r"(\d+):(\d+):(\d+)[,\.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,\.](\d+)"
    )

    def to_sec(h, m, s, ms):
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

    segs = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        m = time_re.search(lines[1])
        if not m:
            continue
        seg_text = "\n".join(lines[2:]).strip()
        segs.append((to_sec(*m.group(1, 2, 3, 4)),
                     to_sec(*m.group(5, 6, 7, 8)),
                     seg_text))
    return segs


def filter_hallucination(segs, max_consecutive=2):
    """连续 N 个 segment 同文本即视为尾部幻觉，丢弃从首个重复开始的整段。"""
    out = []
    last_text = None
    repeat = 0
    for s in segs:
        clean = PUNCT_RE.sub("", s[2])
        if clean == last_text:
            repeat += 1
            if repeat >= max_consecutive:
                # 把已经入栈的 repeat 个相同尾巴砍掉
                while out and PUNCT_RE.sub("", out[-1][2]) == clean:
                    out.pop()
                break
        else:
            repeat = 0
            last_text = clean
        out.append(s)
    return out


def build_char_stream(segs):
    """把每个 segment 内的字符按 (start, end) 均匀分布。"""
    chars = []
    times = []
    for s_start, s_end, txt in segs:
        clean = PUNCT_RE.sub("", txt)
        if not clean:
            continue
        n = len(clean)
        dur = max(s_end - s_start, 0.1)
        for i, c in enumerate(clean):
            chars.append(c)
            times.append(s_start + dur * i / max(n - 1, 1) if n > 1 else s_start)
    return chars, times


def normalize(text):
    return PUNCT_RE.sub("", text)


def align_text(text, char_stream, time_stream, cursor=0, lookahead=600):
    cleaned = normalize(text)
    if not cleaned:
        return None
    end = min(cursor + lookahead, len(char_stream))
    if end <= cursor:
        return None
    sub = "".join(char_stream[cursor:end])
    sm = SequenceMatcher(None, cleaned, sub, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size >= 1]
    if not blocks:
        return None
    matched_chars = sum(b.size for b in blocks)
    ratio = matched_chars / len(cleaned)
    first_b = min(b.b for b in blocks)
    last_b = max(b.b + b.size for b in blocks)
    abs_first = cursor + first_b
    abs_last = min(cursor + last_b - 1, len(time_stream) - 1)
    return {
        "t_start": time_stream[abs_first],
        "t_end": time_stream[abs_last],
        "new_cursor": cursor + last_b,
        "ratio": ratio,
    }


def align_shots(shots_path, pad_in, pad_out, sub_tail, force_whisper):
    project_root = shots_path.parent
    cfg = json.loads(shots_path.read_text(encoding="utf-8"))
    audio_path = (project_root / cfg["audio"]).resolve()
    srt_path = audio_path.with_suffix(".srt")

    run_whisper(audio_path, srt_path, force=force_whisper)
    segs_raw = parse_srt(srt_path)
    segs = filter_hallucination(segs_raw)
    if len(segs) < len(segs_raw):
        print(f"srt: {len(segs_raw)} segments → {len(segs)}（剪掉 {len(segs_raw) - len(segs)} 个尾部幻觉）")
    char_stream, time_stream = build_char_stream(segs)
    print(f"   {len(char_stream)} 字符进入对齐")

    for cut in cfg["cuts"]:
        cursor = 0  # 每个 cut 独立扫
        aligned = []
        for shot in cut["shots"]:
            text = shot.get("text", "")
            if not text:
                aligned.append((None, None, shot))
                continue
            r = align_text(text, char_stream, time_stream, cursor)
            if r is None or r["ratio"] < 0.2:
                print(f"  ⚠ [{cut.get('name')}] 找不到匹配（ratio={r['ratio'] if r else 0:.2f}）：{text}")
                aligned.append((None, None, shot))
                continue
            cursor = r["new_cursor"]
            aligned.append((r["t_start"], r["t_end"], shot))
            print(f"  [{cut.get('name')}] {r['t_start']:6.2f}–{r['t_end']:6.2f}  ratio={r['ratio']:.2f}  {text}")

        # 第一个/最后一个有效 shot 决定 audio_in/out
        valid = [(s, e, sh) for (s, e, sh) in aligned if s is not None]
        if not valid:
            print(f"⚠ [{cut.get('name')}] 全部对齐失败，跳过")
            continue
        first_t = valid[0][0]
        last_t = valid[-1][1]
        audio_in = max(0.0, first_t - pad_in)
        audio_out = last_t + pad_out
        cut["audio_in"] = round(audio_in, 2)
        cut["audio_out"] = round(audio_out, 2)

        # 重写 shots：start/end 相对 audio_in。无对齐的 shot 用上一个的 end 接上
        new_shots = []
        prev_end = 0.0
        for (g_s, g_e, sh) in aligned:
            new_shot = dict(sh)
            if g_s is not None:
                start = round(g_s - audio_in, 2)
                end = round(g_e - audio_in + sub_tail, 2)
            else:
                # 失败回退：往后顺延 3 秒
                start = round(prev_end, 2)
                end = round(prev_end + 3.0, 2)
            # 钳到 [0, audio_out - audio_in]
            duration = audio_out - audio_in
            start = max(0.0, min(start, duration))
            end = max(start + 0.5, min(end, duration))
            new_shot["start"] = start
            new_shot["end"] = end
            new_shots.append(new_shot)
            prev_end = end
        cut["shots"] = new_shots

    # 备份
    bak = shots_path.with_suffix(".json.bak")
    shutil.copyfile(shots_path, bak)
    shots_path.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n✓ 写入 {shots_path}")
    print(f"  备份 → {bak}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots_json")
    ap.add_argument("--pad-in", type=float, default=0.5,
                    help="cut 入点比首字提前多少秒（缓冲呼吸感）")
    ap.add_argument("--pad-out", type=float, default=0.8,
                    help="cut 出点比末字延后多少秒")
    ap.add_argument("--sub-tail", type=float, default=0.3,
                    help="字幕显示时长在末字后多挂几秒（避免一闪而过）")
    ap.add_argument("--force-whisper", action="store_true",
                    help="忽略 srt 缓存，重新跑 whisper")
    args = ap.parse_args()

    align_shots(Path(args.shots_json).resolve(),
                args.pad_in, args.pad_out, args.sub_tail, args.force_whisper)


if __name__ == "__main__":
    main()
