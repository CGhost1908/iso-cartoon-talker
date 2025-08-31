from diffusers import StableDiffusionXLImg2ImgPipeline
from PIL import Image
import torch
import sys
import os

image_input_path = sys.argv[1]
width = int(sys.argv[2])
height = int(sys.argv[3])
output_image_path = sys.argv[4]

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")

pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    variant="fp16",
    use_safetensors=True
).to(device)

input_image = Image.open(image_input_path).convert("RGB").resize((width, height))

prompt = "pixar disney cartoon character portrait, big expressive eyes, 3d, smooth shading"
negative_prompt = "realistic, deformed, blurry, photo, text"

print("Görsel stilize ediliyor...")
output = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,
    image=input_image,
    strength=0.5,
    guidance_scale=7.5
).images[0]

output.save(output_image_path)