#!/usr/bin/env bash
# Fetch the segmentation models into ./models (not committed). Both are Apache-2.0.
set -euo pipefail
cd "$(dirname "$0")/.." && mkdir -p models
curl -fL -o models/selfie_multiclass_256x256.tflite \
  https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite
curl -fL -o models/u2net_human_seg.onnx \
  https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx
ls -la models
