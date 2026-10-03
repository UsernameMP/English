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
LESSAC_MODEL="$VOICE_HOME/en_US-lessac-medium.onnx"
LESSAC_CONFIG="$VOICE_HOME/en_US-lessac-medium.onnx.json"
RYAN_MODEL="$VOICE_HOME/en_US-ryan-medium.onnx"
RYAN_CONFIG="$VOICE_HOME/en_US-ryan-medium.onnx.json"

if [ ! -x "$PIPER_BIN" ]; then
  echo "Downloading Piper neural TTS runtime..."
  curl -L --fail --retry 3     "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"     -o "$CACHE/piper.tar.gz"
  tar -xzf "$CACHE/piper.tar.gz" -C "$PIPER_HOME"
fi

download_voice() {
  local model="$1"
  local config="$2"
  local voice="$3"
  if [ ! -f "$model" ]; then
    echo "Downloading Piper voice: $voice"
    curl -L --fail --retry 3       "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/$voice/medium/en_US-$voice-medium.onnx"       -o "$model"
    curl -L --fail --retry 3       "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/$voice/medium/en_US-$voice-medium.onnx.json"       -o "$config"
  fi
}

download_voice "$LESSAC_MODEL" "$LESSAC_CONFIG" "lessac"
download_voice "$RYAN_MODEL" "$RYAN_CONFIG" "ryan"

export PIPER_BIN LESSAC_MODEL RYAN_MODEL BANK OUT

python3 - <<'PY'
import json
import os
import pathlib
import subprocess
import tempfile
import wave

bank = json.loads(pathlib.Path(os.environ["BANK"]).read_text(encoding="utf-8"))
out_root = pathlib.Path(os.environ["OUT"])
piper = os.environ["PIPER_BIN"]
models = {
    "lessac": os.environ["LESSAC_MODEL"],
    "ryan": os.environ["RYAN_MODEL"],
}

def length_scale(pace):
    return "1.12" if pace == "slow" else "1.03"

def synth(text, voice, target, pace):
    if voice not in models:
        raise RuntimeError(f"Unknown Piper voice: {voice}")
    subprocess.run(
        [
            piper,
            "--model", models[voice],
            "--output_file", str(target),
            "--length_scale", length_scale(pace),
        ],
        input=text,
        text=True,
        check=True,
    )

def concat_wavs(parts, target, silence_seconds=0.20):
    params = None
    frames = []
    for part in parts:
        with wave.open(str(part), "rb") as wav:
            current = (
                wav.getnchannels(),
                wav.getsampwidth(),
                wav.getframerate(),
                wav.getcomptype(),
                wav.getcompname(),
            )
            if params is None:
                params = current
            elif current[:3] != params[:3]:
                raise RuntimeError(f"Incompatible voice WAV parameters: {current[:3]} vs {params[:3]}")
            frames.append(wav.readframes(wav.getnframes()))

    channels, width, rate, comptype, compname = params
    silence = b"\x00" * int(rate * silence_seconds) * channels * width

    with wave.open(str(target), "wb") as out:
        out.setnchannels(channels)
        out.setsampwidth(width)
        out.setframerate(rate)
        out.setcomptype(comptype, compname)
        for index, chunk in enumerate(frames):
            if index:
                out.writeframes(silence)
            out.writeframes(chunk)

count = 0
dialogues = 0
for q in bank["questions"]:
    if q.get("mode") != "listening":
        continue

    stimulus = q["stimulus"]
    target = out_root / pathlib.Path(stimulus["audio"]).name
    pace = stimulus.get("pace", "normal")
    segments = stimulus.get("segments")

    if segments:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = pathlib.Path(temp_dir)
            parts = []
            for index, segment in enumerate(segments):
                part = temp / f"segment_{index:02d}.wav"
                synth(segment["text"], segment["voice"], part, pace)
                parts.append(part)
            concat_wavs(parts, target)
        dialogues += 1
    else:
        synth(
            stimulus["script"],
            stimulus.get("voice", "lessac"),
            target,
            pace,
        )

    count += 1

print(f"Generated {count} neural offline listening files ({dialogues} two-speaker dialogues).")
PY
