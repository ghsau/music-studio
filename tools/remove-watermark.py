#!/usr/bin/env python3
"""
remove-watermark.py — 擦除 Gemini AI 生成图片右下角 sparkle 水印

五种引擎（按推荐度排）：
  1. GWR（默认，推荐）—— Reverse Alpha Blending 数学还原（@pilio/gemini-watermark-remover）
     ✓ 无痕迹 / 不破坏背景纹理 / 100% 还原原图（lossless）
     ✓ 自动检测水印位置 + 大小
     依赖：node + npm（已有则 npx 自动跑，零额外装包）
     源：https://github.com/GargantuaX/gemini-watermark-remover

  2. CROP（兜底）—— 直接 crop 右下角区域
     ✓ 100% 干净，3 秒，零依赖
     ✗ 损失图片边缘像素（默认 110px）

  3. ffmpeg delogo（不推荐）—— 周围像素 interpolate，复杂背景出模糊斑块
  4. OpenCV Telea/NS（不推荐）—— sparkle 主体有残留
  5. LaMa AI inpaint（不推荐）—— 当前 Python 3.13 + Pillow 11 装不上

用法：
  # 默认 GWR：lossless 还原（推荐）
  python3 tools/remove-watermark.py <input> <output>

  # GWR 失败 / 无 node 时 fallback CROP
  python3 tools/remove-watermark.py input.png output.png --engine crop

  # CROP 模式调整 crop 大小
  python3 tools/remove-watermark.py input.png output.png --engine crop --crop-size 150

依赖：node + npm + npx（GWR 引擎，首次 npx 会下 ~5MB） / ffmpeg + ffprobe（CROP 引擎）
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


CORNERS = ("br", "bl", "tr", "tl")
ENGINES = ("gwr", "crop", "delogo", "opencv", "lama")


def check_node():
    if shutil.which("npx") is None:
        return False
    return True


def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        sys.exit("✗ 缺少 ffmpeg。安装：brew install ffmpeg")


def get_image_size(path: Path) -> tuple:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0",
         str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    w, h = out.split(",")
    return int(w), int(h)


# ---------- GWR (默认，Reverse Alpha Blending) ----------

def run_gwr(input_path: Path, output_path: Path):
    """GWR (Gemini Watermark Remover) - lossless 数学还原"""
    if not check_node():
        sys.exit("✗ 缺少 node/npx。安装 Node.js：brew install node\n"
                 "  或加 --engine crop 走 fallback")

    print("[GWR] 调用 @pilio/gemini-watermark-remover（首次自动下包 ~5MB）...")
    cmd = [
        "npx", "-y", "--", "@pilio/gemini-watermark-remover",
        "remove", str(input_path), "--output", str(output_path), "--overwrite",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"✗ GWR 跑失败:\n{e.stderr}", file=sys.stderr)
        sys.exit(1)


# ---------- CROP (fallback) ----------

def crop_corner(input_path: Path, output_path: Path, img_w: int, img_h: int,
                corner: str, crop_size: int):
    """CROP 模式：直接 crop 角落区域，sparkle 100% 干净（损失图片边缘像素）"""
    check_ffmpeg()
    if corner == "br":
        x, y = 0, 0
    elif corner == "bl":
        x, y = crop_size, 0
    elif corner == "tr":
        x, y = 0, crop_size
    else:  # tl
        x, y = crop_size, crop_size
    new_w, new_h = img_w - crop_size, img_h - crop_size

    print(f"[CROP] {corner} 角 {crop_size}px → 输出 {new_w}×{new_h}")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(input_path),
        "-vf", f"crop={new_w}:{new_h}:{x}:{y}",
        "-q:v", "2",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)


# ---------- inpaint 系列 (不推荐，留作参考) ----------

def calc_inpaint_region(img_w: int, img_h: int, corner: str, size: int, margin: int) -> tuple:
    if corner == "br":
        x, y = img_w - margin - size, img_h - margin - size
    elif corner == "bl":
        x, y = margin, img_h - margin - size
    elif corner == "tr":
        x, y = img_w - margin - size, margin
    else:
        x, y = margin, margin
    return x, y, size, size


def inpaint_delogo(input_path: Path, output_path: Path, region: tuple):
    check_ffmpeg()
    x, y, w, h = region
    print(f"[ffmpeg delogo] ⚠ 复杂背景可能出模糊斑块；建议默认走 GWR")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(input_path),
        "-vf", f"delogo=x={x}:y={y}:w={w}:h={h}",
        "-q:v", "2",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)


def inpaint_opencv(input_path: Path, output_path: Path, region: tuple):
    try:
        import cv2
        import numpy as np
    except ImportError:
        sys.exit("✗ 缺少 opencv-python。安装：pip install opencv-python")
    x, y, w, h = region
    img = cv2.imread(str(input_path))
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    mask[y:y + h, x:x + w] = 255
    kernel = np.ones((20, 20), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    print(f"[OpenCV] ⚠ 对带颜色 sparkle 有残留；建议默认走 GWR")
    result = cv2.inpaint(img, mask, 7, cv2.INPAINT_NS)
    result = cv2.inpaint(result, mask, 5, cv2.INPAINT_TELEA)
    cv2.imwrite(str(output_path), result, [cv2.IMWRITE_PNG_COMPRESSION, 1])


def inpaint_lama(input_path: Path, output_path: Path, region: tuple):
    try:
        from simple_lama_inpainting import SimpleLama
        from PIL import Image, ImageDraw
    except ImportError:
        sys.exit("✗ 缺少 simple-lama-inpainting（当前 Python 3.13 + Pillow 11 装不上）\n"
                 "  建议默认走 GWR")
    x, y, w, h = region
    img = Image.open(input_path).convert("RGB")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rectangle([x, y, x + w, y + h], fill=255)
    print(f"[LaMa] 首次下模型 ~150MB")
    SimpleLama()(img, mask).save(output_path)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--engine", choices=ENGINES, default="gwr",
                    help="处理引擎（默认 gwr 最稳，lossless）")
    ap.add_argument("--corner", choices=CORNERS, default="br",
                    help="水印在哪个角（默认 br=右下；仅 CROP/inpaint 模式生效）")
    ap.add_argument("--crop-size", type=int, default=110,
                    help="CROP 模式：crop 角落多少 px（默认 110）")
    ap.add_argument("--size", type=int, default=150,
                    help="inpaint 模式 mask 大小")
    ap.add_argument("--margin", type=int, default=80,
                    help="inpaint 模式距边缘像素")
    args = ap.parse_args()

    if not args.input.exists():
        sys.exit(f"✗ 输入文件不存在: {args.input}")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    img_w, img_h = get_image_size(args.input)
    print(f"输入: {args.input} ({img_w}×{img_h})")
    print(f"输出: {args.output}")
    print(f"引擎: {args.engine}\n")

    if args.engine == "gwr":
        run_gwr(args.input, args.output)
    elif args.engine == "crop":
        crop_corner(args.input, args.output, img_w, img_h, args.corner, args.crop_size)
    else:
        region = calc_inpaint_region(img_w, img_h, args.corner, args.size, args.margin)
        if args.engine == "delogo":
            inpaint_delogo(args.input, args.output, region)
        elif args.engine == "opencv":
            inpaint_opencv(args.input, args.output, region)
        elif args.engine == "lama":
            inpaint_lama(args.input, args.output, region)

    out_w, out_h = get_image_size(args.output)
    flag = "✓" if min(out_w, out_h) >= 1440 else "⚠"
    print(f"\n{flag} 完成: {args.output} ({out_w}×{out_h})")
    if min(out_w, out_h) < 1440:
        print(f"  ⚠ 短边 < 1440（汽水音乐底线）")


if __name__ == "__main__":
    main()
