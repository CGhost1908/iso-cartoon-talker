import sys

sys.path.append('./SadTalker')
from inference_api import run_sadtalker

image_input_path = sys.argv[1]
audio_input_path = sys.argv[2]
output_dir = sys.argv[3]

run_sadtalker(
    audio_path=audio_input_path,
    image_path=image_input_path,
    checkpoint_dir='SadTalker/checkpoints',
    result_dir=output_dir
)
