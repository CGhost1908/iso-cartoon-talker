import sys

import torch
from PIL import Image
from diffusers import StableDiffusionXLImg2ImgPipeline


image_input_path = sys.argv[1]
width = int(sys.argv[2])
height = int(sys.argv[3])
output_image_path = sys.argv[4]


def fit_to_sdxl_budget(width, height, max_side=768):
    scale = min(1.0, max_side / max(width, height))
    next_width = max(64, int(width * scale))
    next_height = max(64, int(height * scale))
    next_width = max(64, (next_width // 8) * 8)
    next_height = max(64, (next_height // 8) * 8)
    return next_width, next_height


device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32
target_width, target_height = fit_to_sdxl_budget(width, height)
print(f"SDXL device: {device}")
print(f"Input size: {width}x{height}")
print(f"Generation size: {target_width}x{target_height}")

pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=dtype,
    variant="fp16" if device == "cuda" else None,
    use_safetensors=True,
)

if device == "cuda":
    pipe.enable_attention_slicing()
    pipe.enable_vae_slicing()
    pipe.enable_model_cpu_offload()
else:
    pipe = pipe.to(device)

input_image = Image.open(image_input_path).convert("RGB").resize((target_width, target_height))

prompt = "pixar disney cartoon character portrait, big expressive eyes, 3d, smooth shading"
negative_prompt = "realistic, deformed, blurry, photo, text"

output = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,
    image=input_image,
    strength=0.5,
    guidance_scale=7.5,
).images[0]

output.save(output_image_path)
