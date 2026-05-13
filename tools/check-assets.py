#!/usr/bin/env python3
"""
check-assets.py — 发布前资产规格自检 + 按需自动修复封面。

扫 <项目>/assets/，对照 knowledge/release-specs.md 检查：
1. cover/*.jpg|jpeg|png：必须 ≥ 1440×1440（汽水音乐）。低于则 lanczos 放大到 2x（不超过 2048）；备份原图为 <name>-original.<ext>
2. shorts/*.mp4：报告尺寸/时长（信息性，不阻断）
3. audio/*.mp3：报告码率（信息性，不阻断）

用法：
    python3 tools/check-assets.py songs/2026-05-03-今潮
    python3 tools/check-assets.py songs/2026-05-03-今潮 --strict   # 不修复，只报告
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

COVER_MIN = 1440
COVER_TARGET = 2048


def fmt(ok, msg):
    return ("✓ " if ok else "✗ ") + msg


def check_cover(cover_dir: Path, strict: bool):
    issues = 0
    fixed = 0
    if not cover_dir.is_dir():
        print(fmt(False, f"封面目录不存在：{cover_dir}"))
        return 1, 0

    images = sorted(
        p for p in cover_dir.iterdir()
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
        and not p.stem.endswith("-original")
        and not p.stem.endswith("-1024")
    )
    if not images:
        print(fmt(False, f"封面目录为空：{cover_dir}"))
        return 1, 0

    for p in images:
        try:
            im = Image.open(p)
            w, h = im.size
        except Exception as e:
            print(fmt(False, f"{p.name} 打不开：{e}"))
            issues += 1
            continue

        if w >= COVER_MIN and h >= COVER_MIN:
            print(fmt(True, f"{p.name} {w}×{h}"))
            continue

        if strict:
            print(fmt(False, f"{p.name} {w}×{h} < {COVER_MIN}×{COVER_MIN}"))
            issues += 1
            continue

        # 自动放大
        target = min(max(w, h) * 2, COVER_TARGET)
        if target < COVER_MIN:
            target = COVER_MIN
        backup = p.with_name(f"{p.stem}-original{p.suffix}")
        if not backup.exists():
            shutil.copy2(p, backup)
        scale = target / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)

        # 处理 RGBA → RGB（白底）
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[3])
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")

        up = im.resize((new_w, new_h), Image.LANCZOS)
        save_kwargs = {"quality": 92, "subsampling": 0} if p.suffix.lower() in (".jpg", ".jpeg") else {}
        up.save(p, **save_kwargs)
        print(fmt(True, f"{p.name} {w}×{h} → {new_w}×{new_h}（备份 → {backup.name}）"))
        fixed += 1

    return issues, fixed


def check_video(shorts_dir: Path):
    if not shorts_dir.is_dir():
        return
    videos = sorted(p for p in shorts_dir.iterdir() if p.suffix.lower() == ".mp4")
    for p in videos:
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-select_streams", "v:0",
                 "-show_entries", "stream=width,height:format=duration",
                 "-of", "default=noprint_wrappers=1",
                 str(p)],
                capture_output=True, text=True, check=True,
            ).stdout
            kv = dict(line.split("=", 1) for line in out.strip().split("\n") if "=" in line)
            w, h = int(kv.get("width", 0)), int(kv.get("height", 0))
            d = float(kv.get("duration", 0))
            ok = (w, h) == (1080, 1920)
            extra = "" if d <= 60 else f"（{d:.0f}s 超 60s 卡点窗口）"
            print(fmt(ok, f"{p.name} {w}×{h} {d:.1f}s{extra}"))
        except Exception as e:
            print(fmt(False, f"{p.name} ffprobe 失败：{e}"))


def check_audio(audio_dir: Path):
    if not audio_dir.is_dir():
        return
    audios = sorted(
        p for p in audio_dir.iterdir()
        if p.suffix.lower() in (".mp3", ".wav", ".flac")
    )
    for p in audios:
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-show_entries", "format=duration,bit_rate",
                 "-of", "default=noprint_wrappers=1",
                 str(p)],
                capture_output=True, text=True, check=True,
            ).stdout
            kv = dict(line.split("=", 1) for line in out.strip().split("\n") if "=" in line)
            br = int(kv.get("bit_rate", 0)) // 1000
            d = float(kv.get("duration", 0))
            ok = br >= 320 or p.suffix.lower() in (".wav", ".flac")
            print(fmt(ok, f"{p.name} {br}kbps {d:.1f}s"))
        except Exception as e:
            print(fmt(False, f"{p.name} ffprobe 失败：{e}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir", help="歌曲项目目录（含 assets/）")
    ap.add_argument("--strict", action="store_true",
                    help="不自动修复，只报告（CI 模式）")
    args = ap.parse_args()

    proj = Path(args.project_dir).resolve()
    assets = proj / "assets"
    if not assets.is_dir():
        sys.exit(f"找不到 assets/：{assets}")

    print(f"=== 检查 {proj.name} ===\n")
    print("[封面]")
    issues, fixed = check_cover(assets / "cover", args.strict)
    print()
    print("[短视频]")
    check_video(assets / "shorts")
    print()
    print("[音频]")
    check_audio(assets / "audio")

    print()
    if issues:
        print(f"⚠ {issues} 个封面问题{'（请手动修复）' if args.strict else ''}")
        sys.exit(1)
    if fixed:
        print(f"✓ 自动修复 {fixed} 个封面")
    else:
        print("✓ 全部达标")


if __name__ == "__main__":
    main()
