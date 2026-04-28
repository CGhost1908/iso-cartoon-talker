import torch
import argparse
from TTS.api import TTS

def main():
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
