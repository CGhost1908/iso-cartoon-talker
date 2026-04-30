import argparse
import os

import torch
from TTS.api import TTS


os.environ.setdefault("COQUI_TOS_AGREED", "1")


def main():
    parser = argparse.ArgumentParser(description="Coqui TTS CLI")
    parser.add_argument("--text", type=str, required=True)
    parser.add_argument("--speaker_wav", type=str, default="src/sample_voice.wav")
    parser.add_argument("--language", type=str, default="tr")
    parser.add_argument("--output", type=str, default="tmp/tts.wav")

    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    tts.tts_to_file(
        text=args.text,
        speaker_wav=args.speaker_wav,
        language=args.language,
        file_path=args.output,
    )


if __name__ == "__main__":
    main()