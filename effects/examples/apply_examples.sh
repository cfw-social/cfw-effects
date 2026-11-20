#!/usr/bin/env bash
# One effect per command on your own clip. Paths are placeholders.
IN=${1:-footage/clip.mp4}
python -m fx apply --effect spotlight        --in "$IN" --out out/spotlight.mp4  --start 1 --end 4 --size 1080x1920 --params '{"sparkles": 40}'
python -m fx apply --effect paper_cut        --in "$IN" --out out/paper.mp4      --start 0 --end 3 --params '{"layers": 2}' --palette neutral-mono
python -m fx apply --effect backdrop_words   --in "$IN" --out out/words.mp4      --params '{"text": "BALANCE", "y": 0.45}'
python -m fx apply --effect countdown_behind --in "$IN" --out out/countdown.mp4  --params '{"start_value": 5, "end_value": 0, "y": 0.2}'
python -m fx masks --in "$IN" --out out/mask_check.mp4 --size 1080x1920      # inspect segmentation before styling
