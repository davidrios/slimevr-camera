#!/usr/bin/env bash
# One-time / repeatable setup of the GPU box (vulcanus, RTX 3090, driver 550 => CUDA <= 12.4).
# Run FROM THIS MACHINE: bash tools/vulcanus-setup.sh
# - rsyncs the repo (no .venv/data) to vulcanus:~/work/slimevr-camera
# - creates the uv env there
# - swaps onnxruntime-gpu for the CUDA-12 build and installs CUDA 12.9 runtime libs from pip
#   (minor-version compatibility lets 12.9 libs run on the 12.4-capable driver; verified 2026-08-26: 65 fps RTMPose-m)
# Always call onnxruntime.preload_dlls() before creating a CUDA session on vulcanus.
set -euo pipefail
HOST=${VULCANUS:-david@192.168.15.27}
HERE=$(cd "$(dirname "$0")/.." && pwd)
rsync -a --delete --exclude .venv --exclude data --exclude __pycache__ --exclude .pytest_cache "$HERE/" "$HOST:~/work/slimevr-camera/"
ssh "$HOST" 'set -e; export PATH=$HOME/.local/bin:$PATH
  command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
  cd ~/work/slimevr-camera && uv sync -q
  uv pip install -q --python .venv --reinstall --no-deps "onnxruntime-gpu==1.29.0" \
     --index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/
  uv pip install -q --python .venv --upgrade "nvidia-cuda-runtime-cu12==12.9.*" "nvidia-cublas-cu12==12.9.*" \
     "nvidia-cufft-cu12==11.4.*" "nvidia-curand-cu12==10.3.10.*" "nvidia-cuda-nvrtc-cu12==12.9.*" "nvidia-cudnn-cu12==9.*"
  uv run --no-sync python -c "import onnxruntime as ort; ort.preload_dlls(); print(\"ORT\", ort.__version__, ort.get_available_providers())"'
