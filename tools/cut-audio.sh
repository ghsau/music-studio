#!/usr/bin/env bash
# cut-audio.sh — 从完整 mp3 切出指定时段，给即梦"全能参考"模式做音频锚用。
#
# 用法：
#   ./tools/cut-audio.sh <input.mp3> <start_time> <output.mp3> [duration]
#
# 参数：
#   input.mp3     完整曲文件
#   start_time    起始时间码，格式 HH:MM:SS / MM:SS / 秒（如 00:48 / 0:48 / 48）
#   output.mp3    输出文件路径
#   duration      时长（秒），默认 15（即梦音频上限）
#
# 例：
#   ./tools/cut-audio.sh \
#       songs/2026-05-07-那几年/assets/audio/那几年.mp3 \
#       00:48 \
#       songs/2026-05-07-那几年/assets/audio/那几年-15s-chorus.mp3

set -euo pipefail

if [[ $# -lt 3 ]]; then
    cat <<EOF >&2
用法: $0 <input.mp3> <start_time> <output.mp3> [duration=15]
  start_time 例: 00:48 / 0:48 / 48
EOF
    exit 1
fi

INPUT="$1"
START="$2"
OUTPUT="$3"
DURATION="${4:-15}"

if [[ ! -f "$INPUT" ]]; then
    echo "✗ 输入文件不存在: $INPUT" >&2
    exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "✗ 缺少 ffmpeg。安装：brew install ffmpeg" >&2
    exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"

# -ss 放在 -i 之后做精确切分（mp3 帧对齐）；libmp3lame VBR q:a 2 ≈ 220kbps
ffmpeg -y -i "$INPUT" -ss "$START" -t "$DURATION" \
    -c:a libmp3lame -q:a 2 \
    "$OUTPUT" 2>&1 | tail -3

# 验证输出时长
ACTUAL=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUTPUT" 2>/dev/null || echo "0")
echo ""
echo "✓ 切片完成: $OUTPUT (${ACTUAL}s)"
