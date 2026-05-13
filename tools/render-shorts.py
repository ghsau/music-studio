#!/usr/bin/env python3
"""
render-shorts.py — 抖叔的渲染管线

吃 <project>/shots.json，吐 <project>/assets/shorts/<name>.mp4。

用法：
    python3 tools/render-shorts.py songs/2026-05-02-迟信/shots.json
    python3 tools/render-shorts.py songs/2026-05-02-迟信/shots.json --only 15s
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import (
    AudioFileClip, ImageClip, ColorClip,
    CompositeVideoClip,
)

CHINESE_FONT = "/System/Library/Fonts/Supplemental/Songti.ttc"
KB_CYCLE = ["zoom_in", "pan_up", "zoom_out", "zoom_in", "pan_down"]


# --------------------------------------------------------------------------
# PIL-based text rendering (彻底避开 moviepy TextClip 的中文裁切 bug)
# --------------------------------------------------------------------------

def render_text_to_array(text, font_path, font_size,
                         color=(255, 255, 255, 255),
                         stroke_color=(0, 0, 0, 255), stroke_width=4,
                         shadow=True, shadow_offset=(0, 6), shadow_blur=4,
                         padding=32):
    """用 PIL 渲染中文字符到 RGBA numpy 数组，含描边 + 阴影。"""
    font = ImageFont.truetype(font_path, font_size)

    # 测 bbox
    probe = Image.new("RGBA", (10, 10))
    bbox = ImageDraw.Draw(probe).textbbox(
        (0, 0), text, font=font, stroke_width=stroke_width
    )
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    extra_x = abs(shadow_offset[0]) + shadow_blur * 2
    extra_y = abs(shadow_offset[1]) + shadow_blur * 2
    canvas_w = text_w + 2 * padding + extra_x
    canvas_h = text_h + 2 * padding + extra_y

    base = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    text_xy = (padding - bbox[0], padding - bbox[1])

    # shadow
    if shadow:
        sh = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text(
            (text_xy[0] + shadow_offset[0], text_xy[1] + shadow_offset[1]),
            text, font=font, fill=(0, 0, 0, 200),
            stroke_width=stroke_width, stroke_fill=(0, 0, 0, 200),
        )
        sh = sh.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
        base = Image.alpha_composite(base, sh)

    # main text
    draw = ImageDraw.Draw(base)
    draw.text(
        text_xy, text, font=font, fill=color,
        stroke_width=stroke_width, stroke_fill=stroke_color,
    )

    return np.array(base)


def make_subtitle_clip(text, duration, target_size, font_size=88):
    if not text:
        return None
    arr = render_text_to_array(
        text, CHINESE_FONT, font_size=font_size,
        color=(255, 252, 245, 255),
        stroke_color=(0, 0, 0, 255), stroke_width=5,
        shadow=True, shadow_offset=(0, 8), shadow_blur=6,
    )
    tw, th = target_size
    clip = ImageClip(arr).with_duration(duration)
    # 字幕中心放在距底部 ~310px
    y = th - 310 - clip.h // 2
    return clip.with_position(("center", y))


def make_title_clip(title, duration, target_size, font_size=120):
    if not title:
        return None
    arr = render_text_to_array(
        title, CHINESE_FONT, font_size=font_size,
        color=(238, 226, 210, 245),
        stroke_color=(20, 18, 22, 255), stroke_width=3,
        shadow=True, shadow_offset=(0, 4), shadow_blur=8,
    )
    return ImageClip(arr).with_duration(duration).with_position(("center", 200))


def make_bottom_gradient(target_size, height=620, max_alpha=200):
    """底部黑色软渐变（numpy 向量化）。"""
    tw, _ = target_size
    rows = np.linspace(0, 1, height) ** 1.7
    alphas = (rows * max_alpha).clip(0, 255).astype(np.uint8)
    arr = np.zeros((height, tw, 4), dtype=np.uint8)
    arr[..., 0] = 10
    arr[..., 1] = 8
    arr[..., 2] = 12
    arr[..., 3] = alphas[:, None]
    return arr


def make_top_gradient(target_size, height=420, max_alpha=160):
    """顶部黑色软渐变（numpy 向量化）。"""
    tw, _ = target_size
    rows = (1 - np.linspace(0, 1, height)) ** 1.7
    alphas = (rows * max_alpha).clip(0, 255).astype(np.uint8)
    arr = np.zeros((height, tw, 4), dtype=np.uint8)
    arr[..., 0] = 10
    arr[..., 1] = 8
    arr[..., 2] = 12
    arr[..., 3] = alphas[:, None]
    return arr


def make_vignette(target_size, intensity=0.55):
    """四角暗角（numpy 向量化）。"""
    tw, th = target_size
    cx, cy = tw / 2.0, th / 2.0
    max_d = (cx ** 2 + cy ** 2) ** 0.5
    yy, xx = np.mgrid[0:th, 0:tw]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max_d
    factor = np.clip((d - 0.55) / 0.45, 0, 1)
    alphas = (255 * intensity * factor).astype(np.uint8)
    arr = np.zeros((th, tw, 4), dtype=np.uint8)
    arr[..., 0] = 8
    arr[..., 1] = 6
    arr[..., 2] = 10
    arr[..., 3] = alphas
    return arr


# --------------------------------------------------------------------------
# Image / Ken Burns
# --------------------------------------------------------------------------

def fit_image_to_canvas(image_path, target_size, headroom=1.10):
    """把图等比缩放到铺满目标画布短边 × headroom，给 KB 留余量。"""
    tw, th = target_size
    raw = ImageClip(str(image_path))
    raw_w, raw_h = raw.size
    scale = max(tw / raw_w, th / raw_h) * headroom
    return raw.resized((int(raw_w * scale), int(raw_h * scale)))


def apply_ken_burns(clip, kb, duration):
    """对已 fit 的图层叠加缓推，幅度比第一版大。"""
    if kb == "zoom_in":
        clip = clip.resized(lambda t: 1.0 + 0.12 * t / duration)
        return clip.with_duration(duration).with_position(("center", "center"))
    if kb == "zoom_out":
        clip = clip.resized(lambda t: 1.12 - 0.12 * t / duration)
        return clip.with_duration(duration).with_position(("center", "center"))
    if kb == "pan_up":
        return clip.with_duration(duration).with_position(
            lambda t: ("center", -int(80 * t / duration))
        )
    if kb == "pan_down":
        return clip.with_duration(duration).with_position(
            lambda t: ("center", int(80 * t / duration))
        )
    return clip.with_duration(duration).with_position(("center", "center"))


# --------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------

def render_cut(cut, project_root, audio_path, default_image, fps, size, title=None,
               cached_overlays=None):
    audio_in = float(cut["audio_in"])
    audio_out = float(cut["audio_out"])
    total = audio_out - audio_in

    audio = AudioFileClip(str(audio_path)).subclipped(audio_in, audio_out)

    bg = ColorClip(size=size, color=(20, 18, 22)).with_duration(total)
    layers = [bg]

    shots = cut["shots"]
    n = len(shots)

    # 图层：从 shot.start 延续到下一 shot.start（首图从 0 起，末图到 cut 结束），保证画面连续
    for i, shot in enumerate(shots):
        image_start = 0.0 if i == 0 else float(shot["start"])
        image_end = float(shots[i + 1]["start"]) if i + 1 < n else total
        image_d = max(image_end - image_start, 0.1)
        img_rel = shot.get("image") or default_image
        img_path = project_root / img_rel
        kb = shot.get("kb") or KB_CYCLE[i % len(KB_CYCLE)]

        img_layer = fit_image_to_canvas(img_path, size)
        img_layer = apply_ken_burns(img_layer, kb, image_d).with_start(image_start)
        layers.append(img_layer)

    # 暗角（贯穿整段，做画面定调）
    vignette = ImageClip(cached_overlays["vignette"]).with_duration(total)
    layers.append(vignette.with_position((0, 0)))

    # 顶部渐变 + 标题
    top_grad = ImageClip(cached_overlays["top_grad"]).with_duration(total)
    layers.append(top_grad.with_position((0, 0)))

    title_layer = make_title_clip(title, total, size)
    if title_layer:
        layers.append(title_layer)

    # 底部渐变（贯穿）
    bottom_grad = ImageClip(cached_overlays["bottom_grad"]).with_duration(total)
    layers.append(bottom_grad.with_position((0, size[1] - cached_overlays["bottom_grad"].shape[0])))

    # 字幕（按 shot.start/end 严格显示，与图层解耦）
    for shot in shots:
        start = float(shot["start"])
        end = float(shot["end"])
        d = max(end - start, 0.3)
        sub = make_subtitle_clip(shot.get("text", ""), d, size)
        if sub:
            layers.append(sub.with_start(start))

    video = CompositeVideoClip(layers, size=size).with_duration(total)
    video = video.with_audio(audio)

    out_path = project_root / cut["out"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    video.write_videofile(
        str(out_path),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="medium",
    )
    return out_path


def main():
    ap = argparse.ArgumentParser(description="抖叔渲染：shots.json → mp4")
    ap.add_argument("shots_json", help="shots.json 路径")
    ap.add_argument("--only", help="只渲染指定 cut（按 name 匹配）")
    args = ap.parse_args()

    shots_path = Path(args.shots_json).resolve()
    project_root = shots_path.parent
    cfg = json.loads(shots_path.read_text(encoding="utf-8"))

    audio_path = project_root / cfg["audio"]
    if not audio_path.exists():
        sys.exit(f"找不到音频：{audio_path}")

    default_image = cfg.get("cover", "")
    fps = int(cfg.get("fps", 30))
    size = tuple(cfg.get("size", [1080, 1920]))
    title = cfg.get("title", "")

    # 渲一次叠层缓存（暗角/渐变都和音频无关）
    print("生成叠层缓存（暗角 / 渐变）...")
    cached_overlays = {
        "vignette": make_vignette(size, intensity=0.5),
        "top_grad": make_top_gradient(size, height=460, max_alpha=170),
        "bottom_grad": make_bottom_gradient(size, height=640, max_alpha=210),
    }

    cuts = cfg["cuts"]
    if args.only:
        cuts = [c for c in cuts if c.get("name") == args.only]
        if not cuts:
            sys.exit(f"找不到名为 {args.only} 的 cut")

    for cut in cuts:
        print(f"\n=== 渲染 {cut['name']} ===")
        out = render_cut(cut, project_root, audio_path, default_image,
                         fps, size, title, cached_overlays)
        print(f"✓ {out}")


if __name__ == "__main__":
    main()
