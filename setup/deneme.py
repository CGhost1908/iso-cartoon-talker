import os

program_files = os.path.join('D:\\', 'deneme')
iso_path = os.path.join(program_files, 'iso-cartoon-talker')
os.chdir(iso_path)

checkpoints_path = os.path.join(iso_path, "SadTalker", "checkpoints")
weights_path = os.path.join(iso_path, "SadTalker", "gfpgan", "weights")

folders = [
    checkpoints_path,
    weights_path,
    os.path.join(iso_path, "src"),
    os.path.join(iso_path, "train_base_models")
]

for folder_path in folders:
    if not os.path.exists(folder_path):
        continue

    for filename in os.listdir(folder_path):
        old_path = os.path.join(folder_path, filename)
    
        if not os.path.isfile(old_path):
            continue

        new_name = filename

        if "safetensors" in filename.lower():
            if not filename.lower().endswith(".safetensors"):
                new_name = os.path.splitext(filename)[0] + ".safetensors"
        elif ".pth.tar" in filename.lower() or "tar" in filename.lower():
            if not filename.lower().endswith(".tar"):
                new_name = os.path.splitext(filename)[0] + ".tar"
        elif ".pth" in filename.lower() and ".tar" not in filename.lower():
            if not filename.lower().endswith(".pth"):
                new_name = os.path.splitext(filename)[0] + ".pth"
        elif "sample_voice.wav" in filename.lower():
            if not filename.lower().endswith(".wav"):
                new_name = os.path.splitext(filename)[0] + ".wav"

        new_path = os.path.join(folder_path, new_name)

        if old_path != new_path:
            os.rename(old_path, new_path)