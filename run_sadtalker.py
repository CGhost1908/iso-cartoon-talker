import sys
import os
from urllib.request import urlretrieve

sys.path.append('./SadTalker')
from inference_api import run_sadtalker


def _download_if_missing(url, output_path):
    if os.path.exists(output_path):
        return
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"Downloading {os.path.basename(output_path)}...")
    urlretrieve(url, output_path)


def ensure_sadtalker_models(checkpoint_dir):
    files = {
        "mapping_00109-model.pth.tar": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar",
        "mapping_00229-model.pth.tar": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar",
        "SadTalker_V0.0.2_256.safetensors": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors",
        "SadTalker_V0.0.2_512.safetensors": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors",
    }

    for filename, url in files.items():
        output_path = os.path.join(checkpoint_dir, filename)
        _download_if_missing(url, output_path)


image_input_path = sys.argv[1]
audio_input_path = sys.argv[2]
output_dir = sys.argv[3]
checkpoint_dir = os.path.join('SadTalker', 'checkpoints')

ensure_sadtalker_models(checkpoint_dir)

run_sadtalker(
    audio_path=audio_input_path,
    image_path=image_input_path,
    checkpoint_dir=checkpoint_dir,
    result_dir=output_dir,
    enhancer="gfpgan"
)
