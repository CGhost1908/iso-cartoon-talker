import torch
import argparse
<<<<<<< HEAD
from TTS.api import TTS

def main():
=======
import os
import sys
from TTS.api import TTS

def main():
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    os.environ.setdefault("COQUI_TOS_AGREED", "1")

>>>>>>> 9936863f757c56e7c46bc4ac0f62d5ac2b150513
    parser = argparse.ArgumentParser(description="Coqui TTS CLI")
    parser.add_argument("--text", type=str, required=True, help="Metin")
    parser.add_argument("--speaker_wav", type=str, default="src/portal_voice.wav", help="Referans ses dosyası yolu")
    parser.add_argument("--language", type=str, default="tr", help="Dil (varsayılan: tr)")
    parser.add_argument("--output", type=str, default="tmp/tts.wav", help="Çıktı dosya adı (varsayılan: tmp/tts.wav)")

    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    tts.tts_to_file(
        text=args.text,
        speaker_wav=args.speaker_wav,
        language=args.language,
        file_path=args.output
    )

if __name__ == "__main__":
    main()
