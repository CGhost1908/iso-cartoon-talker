FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HF_HOME=/data/hf \
    TRANSFORMERS_CACHE=/data/hf \
    COQUI_TOS_AGREED=1 \
    SADTALKER_DIR=/opt/external/SadTalker \
    COQUI_PYTHON=/app/env_coqui/bin/python \
    SDXL_PYTHON=/app/env_sdxl/bin/python \
    SOFTVC_PYTHON=/app/env_softvc/bin/python \
    SOFTVC_CLI=/app/env_softvc/bin/svc \
    SADTALKER_PYTHON=/app/env_sadtalker/bin/python

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    espeak-ng \
    ffmpeg \
    git \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsndfile1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install Flask==3.0.3 Pillow==9.5.0

# SDXL environment
RUN python -m venv /app/env_sdxl && \
    /app/env_sdxl/bin/pip install --upgrade pip setuptools wheel && \
    /app/env_sdxl/bin/pip install \
      torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 \
      --index-url https://download.pytorch.org/whl/cu118 && \
    /app/env_sdxl/bin/pip install \
      diffusers==0.34.0 \
      huggingface_hub==0.34.3 \
      pillow==11.3.0 \
      transformers==4.54.1 \
      accelerate==1.9.0 \
      typing-extensions==4.15

# SoftVC environment
RUN python -m venv /app/env_softvc && \
    /app/env_softvc/bin/python -m pip install --upgrade pip setuptools wheel && \
    /app/env_softvc/bin/pip install \
      torch==2.7.1 torchaudio==2.7.1 \
      --index-url https://download.pytorch.org/whl/cu118 && \
    /app/env_softvc/bin/pip install \
      matplotlib==3.7.1 \
      psutil==7.0.0 \
      torchcodec && \
    /app/env_softvc/bin/pip install -U so-vits-svc-fork

# Coqui TTS environment
RUN mkdir -p /opt/external && \
    git clone --depth 1 https://github.com/coqui-ai/TTS.git /opt/external/TTS && \
    python -m venv /app/env_coqui && \
    /app/env_coqui/bin/pip install --upgrade pip setuptools wheel && \
    /app/env_coqui/bin/pip install -r /opt/external/TTS/requirements.txt && \
    /app/env_coqui/bin/pip install \
      torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 \
      --index-url https://download.pytorch.org/whl/cu118 && \
    /app/env_coqui/bin/pip install \
      sympy==1.12 \
      TTS==0.22.0 \
      transformers==4.33.2

# SadTalker environment
RUN git clone --depth 1 https://github.com/OpenTalker/SadTalker.git /opt/external/SadTalker && \
    python -m venv /app/env_sadtalker && \
    /app/env_sadtalker/bin/pip install --upgrade pip setuptools wheel && \
    /app/env_sadtalker/bin/pip install ffmpeg && \
    /app/env_sadtalker/bin/pip install -r /opt/external/SadTalker/requirements.txt && \
    /app/env_sadtalker/bin/pip install \
      torch==1.12.1+cu113 \
      torchvision==0.13.1+cu113 \
      torchaudio==0.12.1 \
      --extra-index-url https://download.pytorch.org/whl/cu113

COPY inference_api.py /opt/external/SadTalker/inference_api.py

# Match setup.py: prepare folders and download the required base/model assets.
RUN mkdir -p \
      /app/src \
      /app/train_base_models \
      /opt/external/SadTalker/checkpoints \
      /opt/external/SadTalker/gfpgan/weights \
      /data/hf && \
    python - <<'PY'
from pathlib import Path
from urllib.request import urlretrieve

files = [
    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar", "/opt/external/SadTalker/checkpoints/mapping_00109-model.pth.tar"),
    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar", "/opt/external/SadTalker/checkpoints/mapping_00229-model.pth.tar"),
    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors", "/opt/external/SadTalker/checkpoints/SadTalker_V0.0.2_256.safetensors"),
    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors", "/opt/external/SadTalker/checkpoints/SadTalker_V0.0.2_512.safetensors"),
    ("https://github.com/CGhost1908/iso-cartoon-talker/releases/download/v0.0.1/sample_voice.wav", "/app/src/sample_voice.wav"),
    ("https://github.com/CGhost1908/iso-cartoon-talker/releases/download/v0.0.1/G_0.pth", "/app/train_base_models/G_0.pth"),
    ("https://github.com/CGhost1908/iso-cartoon-talker/releases/download/v0.0.1/D_0.pth", "/app/train_base_models/D_0.pth"),
]

for url, output in files:
    target = Path(output)
    if target.exists():
        continue
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {target.name}...")
    urlretrieve(url, target)
PY

COPY . .

EXPOSE 8000

CMD ["python", "docker_entrypoint.py"]
