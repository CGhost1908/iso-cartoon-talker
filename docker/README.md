# Docker Rebuild

This folder runs Cartoon Talker through Docker instead of the Windows installer.

The image keeps the same isolation idea as `setup/setup.py`:

- `/app/env_sdxl` for SDXL cartoon image generation
- `/app/env_softvc` for so-vits-svc voice conversion and training
- `/app/env_coqui` for Coqui XTTS
- `/app/env_sadtalker` for SadTalker animation

During `docker compose build`, Docker also clones the external `TTS` and
`SadTalker` repositories, installs each environment's dependencies, and downloads
the model/base files that the original setup downloads.

## Requirements

- Docker Desktop
- A reasonably large disk cache. The first build downloads multiple PyTorch
  stacks and model files, so it can take a long time.
- For NVIDIA GPU usage, install NVIDIA Container Toolkit and run Docker Desktop
  with GPU support enabled. Without GPU support, the app may be very slow.

## Run

From this folder:

```bash
docker compose up --build
```

Open:

```text
http://localhost:8000
```

With NVIDIA GPU support:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

## Data

The compose file creates Docker volumes for generated data:

- `app_data` keeps `avatars.db`
- `app_models` keeps trained voice models
- `app_output` keeps generated videos
- `app_tmp` keeps temporary runtime files
- `hf_cache` keeps Hugging Face model cache

To rebuild the image while keeping user data:

```bash
docker compose build
docker compose up
```

Avoid `--no-cache` unless the dependency install layers are corrupted. This
image contains several large PyTorch environments, so a no-cache build is slow
and can temporarily use a lot of disk space.

To delete all generated Docker data for this app:

```bash
docker compose down -v
```
