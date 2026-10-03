#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/app/src/main/assets/audio"
CACHE="$ROOT/.cache/piper"
PIPER_HOME="$CACHE/runtime"
VOICE_HOME="$CACHE/voice"
BANK="$ROOT/app/src/main/assets/content/english_g5_vso.json"

mkdir -p "$OUT" "$PIPER_HOME" "$VOICE_HOME"

PIPER_BIN="$PIPER_HOME/piper/piper"
MODEL="$VOICE_HOME/en_US-lessac-medium.onnx"
CONFIG="$VOICE_HOME/en_US-lessac-medium.onnx.json"

if [ ! -x "$PIPER_BIN" ]; then
  echo "Downloading Piper neural TTS runtime..."
  curl -L --fail --retry 3     "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"     -o "$CACHE/piper.tar.gz"
  tar -xzf "$CACHE/piper.tar.gz" -C "$PIPER_HOME"
fi

if [ ! -f "$MODEL" ]; then
  echo "Downloading English neural voice..."
  curl -L --fail --retry 3     "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"     -o "$MODEL"
  curl -L --fail --retry 3     "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"     -o "$CONFIG"
fi

export PIPER_BIN MODEL BANK OUT

python3 - <<'PY'
import json
import os
import pathlib
import subprocess

bank = json.loads(pathlib.Path(os.environ["BANK"]).read_text(encoding="utf-8"))
out_root = pathlib.Path(os.environ["OUT"])
piper = os.environ["PIPER_BIN"]
model = os.environ["MODEL"]

count = 0
for q in bank["questions"]:
    if q.get("mode") != "listening":
        continue
    stimulus = q["stimulus"]
    audio = stimulus["audio"]
    script = stimulus["script"]
    name = pathlib.Path(audio).name
    target = out_root / name
    subprocess.run(
        [piper, "--model", model, "--output_file", str(target), "--length_scale", "1.08"],
        input=script,
        text=True,
        check=True,
    )
    count += 1

print(f"Generated {count} neural offline listening files.")
PY
