import os
import sys
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location
from urllib.request import urlretrieve


SADTALKER_DIR = Path(os.environ.get("SADTALKER_DIR", "/opt/external/SadTalker"))
inference_api_path = SADTALKER_DIR / "inference_api.py"
# Fallback: if the cloned upstream repo doesn't include inference_api.py, check the
# repository copied into the app context (e.g. /app/SadTalker) so local overrides work.
if not inference_api_path.exists():
    alt_dir = Path('/app') / 'SadTalker'
    if not alt_dir.exists():
        alt_dir = Path(__file__).resolve().parent.parent / 'SadTalker'
    alt_inference = alt_dir / 'inference_api.py'
    if alt_inference.exists():
        print(f"Fallback: using local SadTalker at {alt_dir}")
        inference_api_path = alt_inference
        SADTALKER_DIR = alt_dir
spec = spec_from_file_location("sadtalker_inference_api", inference_api_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load SadTalker inference API from {inference_api_path}")
module = module_from_spec(spec)
sys.path.insert(0, str(SADTALKER_DIR))
spec.loader.exec_module(module)
run_sadtalker = module.run_sadtalker

os.chdir(SADTALKER_DIR)


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
checkpoint_dir = str(SADTALKER_DIR / 'checkpoints')

ensure_sadtalker_models(checkpoint_dir)

run_sadtalker(
    audio_path=audio_input_path,
    image_path=image_input_path,
    checkpoint_dir=checkpoint_dir,
    result_dir=output_dir,
    enhancer="gfpgan",
)