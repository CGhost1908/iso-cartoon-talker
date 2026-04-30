import random
import shutil
from pathlib import Path


random_seed = 1234
base_tmp = Path(__file__).parent / 'tmp'
input_dir = base_tmp / 'dataset'
filelists_dir = base_tmp / 'filelists'


def ensure_min_files(speaker_dir: Path, min_files=5):
    wavs = sorted([p for p in speaker_dir.rglob('*.wav')])
    if len(wavs) >= min_files:
        return
    speaker_dir.mkdir(parents=True, exist_ok=True)
    i = 0
    while len(list(speaker_dir.rglob('*.wav'))) < min_files:
        if not wavs:
            break
        src = wavs[i % len(wavs)]
        dst = speaker_dir / f"dup_{len(list(speaker_dir.rglob('*.wav'))) + 1}_{src.name}"
        shutil.copy2(src, dst)
        i += 1


def main():
    if not input_dir.exists():
        print(f"Input dir {input_dir} does not exist.")
        return
    speakers = [p for p in input_dir.iterdir() if p.is_dir()]
    if not speakers:
        print(f"No speaker directories in {input_dir}")
        return

    random.seed(random_seed)
    train = []
    val = []
    test = []

    for sp in speakers:
        wavs = sorted([p for p in sp.rglob('*.wav')])
        if not wavs:
            print(f"No wav files for speaker {sp.name}, skipping.")
            continue
        ensure_min_files(sp, min_files=5)
        wavs = sorted([p for p in sp.rglob('*.wav')])
        random.shuffle(wavs)
        if len(wavs) <= 4:
            print(f"Speaker {sp.name} still has <=4 files after ensuring; skipping")
            continue
        train += wavs[2:-2]
        val += wavs[:2]
        test += wavs[-2:]

    filelists_dir.mkdir(parents=True, exist_ok=True)
    train_txt = filelists_dir / 'train.txt'
    val_txt = filelists_dir / 'val.txt'
    test_txt = filelists_dir / 'test.txt'

    train_txt.write_text('\n'.join([p.as_posix() for p in train]), encoding='utf-8')
    val_txt.write_text('\n'.join([p.as_posix() for p in val]), encoding='utf-8')
    test_txt.write_text('\n'.join([p.as_posix() for p in test]), encoding='utf-8')

    print("Done. Generated filelists:")
    print(train_txt)
    print(val_txt)
    print(test_txt)


if __name__ == '__main__':
    main()