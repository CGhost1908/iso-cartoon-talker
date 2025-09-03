import webview
import base64
from io import BytesIO
import subprocess
import os
from PIL import Image
import sqlite3
import tempfile
import json
import shutil
import random
import string
import traceback

program_files = os.path.join(os.environ['ProgramFiles'])

iso_path = os.path.join(program_files, 'iso-cartoon-talker')
os.chdir(iso_path)

voice_train_config_path = 'configs/softvc_config.json'
models_path = 'models'
os.makedirs(models_path, exist_ok=True)

conn = sqlite3.connect('avatars.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS avatars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    image_base64 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    voice_model TEXT
)
''')
conn.commit()
conn.close()

tmp_dir = os.path.join(iso_path, "tmp")
os.makedirs(tmp_dir, exist_ok=True)

class Api:
    def log(self, text):
        js_code = f"appendOutput({text!r})"
        webview.windows[0].evaluate_js(js_code)

    def run_command(self, cmd, description=""):
        if description:
            self.log(description)
        process = subprocess.Popen(
            cmd,
            cwd=iso_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in process.stdout:
            self.log(line.strip())
            print(line.strip())
        process.wait()

    # ------------------ Cartoon Talker ------------------
    def run_cartoon_talker(self, image_base64, target_audio, model_path, width, height):
        print("Running Cartoon Talker...")
        final_video_output_dir = "output/"
        final_audio_path = "tmp/target_voice_to_source_voice.wav"

        target_path = os.path.join(tmp_dir, "target_voice.wav")
        with open(target_path, "wb") as f:
            f.write(base64.b64decode(target_audio))

        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        image_path = tmp_file.name
        with open(image_path, 'wb') as f:
            f.write(base64.b64decode(image_base64))

        try:
            if model_path:
                self.run_command([
                    r"env_softvc\Scripts\svc.exe",
                    "infer",
                    target_path,
                    "-o", final_audio_path,
                    "-m", model_path,
                    "-c", os.path.abspath(voice_train_config_path)
                ], description="Cloning sound...")

            else:
                final_audio_path = target_path

            self.run_command([
                "env_sadtalker\\Scripts\\python.exe",
                "run_sadtalker.py",
                image_path,
                final_audio_path,
                final_video_output_dir
            ], description="Running SadTalker animation...")

            return "✅ Process completed. Check output folder."
        except subprocess.CalledProcessError as e:
            return f"❌ Error occurred: {e}"


    # ------------------ Cartoonize ------------------
    def cartoonize_avatar(self, image, width, height):
        image_data = base64.b64decode(image.split(',')[-1])
        image = Image.open(BytesIO(image_data))
        temp_path = "tmp/temp_avatar.png"
        image.save(temp_path)
        output_path = "tmp/cartoonize_photo.png"

        self.run_command([
            "env_sdxl\\Scripts\\python.exe",
            "run_sdxl.py",
            temp_path,
            str(width),
            str(height),
            output_path
        ], description="Generating cartoon image...")

        return output_path

    # ------------------ Voice Training ------------------
    def voice_train(self, audio_base64, epoch, avatar_name):
        try:
            tmp_path = tmp_dir
            source_dir = os.path.join(tmp_path, "dataset_raw_raw")
            os.makedirs(source_dir, exist_ok=True)

            audio_path = os.path.join(source_dir, "train_input.wav")
            audio_data = base64.b64decode(audio_base64)
            with open(audio_path, "wb") as f:
                f.write(audio_data)

            dataset_raw_dir = os.path.join(tmp_path, "dataset_raw")
            dataset_dir = os.path.join(tmp_path, "dataset")
            filelists_dir = os.path.join(tmp_path, "filelists")
            avatar_dir = os.path.join(dataset_dir, avatar_name)

            for d in [dataset_raw_dir,dataset_dir,filelists_dir,avatar_dir]:
                os.makedirs(d, exist_ok=True)

            try:
                print("Modeller kopyalanıyor...")
                for f in ['G_0.pth','D_0.pth']:
                    shutil.copy(os.path.join(iso_path, 'train_base_models', f), tmp_path)
            except Exception as e:
                print("Model bulunamadı indiriliyor...")

            # ---------------- pre-split ----------------
            self.log(source_dir)
            self.log(dataset_raw_dir)
            self.run_command([
                r"env_softvc\Scripts\svc.exe",
                "pre-split",
                "-i", source_dir,
                "-o", dataset_raw_dir
            ], description="Pre-splitting dataset...")

            # copy files
            for filename in os.listdir(dataset_raw_dir):
                src_file = os.path.join(dataset_raw_dir, filename)
                dst_file = os.path.join(dataset_dir, avatar_name, filename)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)

            # ---------------- pre-config ----------------
            self.run_command([
                r"env_softvc\Scripts\svc.exe",
                "pre-config",
                "-i", dataset_dir,
                "-f", filelists_dir,
                "-c", os.path.abspath(voice_train_config_path)
            ], description="Pre-configuring...")

            # ---------------- epoch ----------------
            with open(voice_train_config_path, 'r') as f:
                config = json.load(f) 
              
            config['train']['epochs'] = int(epoch)

            with open(voice_train_config_path, 'w') as f:
                json.dump(config, f, indent=4)

            # ---------------- pre-hubert ----------------
            self.run_command([
                r"env_softvc\Scripts\svc.exe",
                "pre-hubert",
                "-i", dataset_dir,
                "-c", os.path.abspath(voice_train_config_path)
            ], description="Running pre-hubert...")

            # ---------------- train ----------------
            self.run_command([
                r"env_softvc\Scripts\svc.exe",
                "train", "-t",
                "-c", os.path.abspath(voice_train_config_path),
                "-m", os.path.abspath(tmp_dir),
                "-nt"
            ], description="Training model...")

            # move model
            model_path = os.path.join(tmp_dir, f"G_{epoch}.pth")
            rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            dst_path = os.path.join(models_path, f"{avatar_name}_{rand_str}.pth")
            shutil.move(model_path, dst_path)
            return {"status": "ok", "path": dst_path}

        except Exception as e:
            self.log(str(e))
            return {"status": "error", "message": str(e), "trace": traceback.format_exc()}
        finally:
            for f in os.listdir(tmp_path):
                file_path = os.path.join(tmp_path, f)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

    # ------------------ TTS ------------------
    def run_tts(self, text):
        output_file = "tmp/tts.wav"
        try:
            self.run_command([
                r"env_coqui\Scripts\python.exe",
                "run_coqui.py",
                "--text", text,
                "--speaker_wav", "src/sample_voice.wav",
                "--language", "tr",
                "--output", output_file
            ], description="Running TTS...")

            with open(output_file, "rb") as f:
                audio_base64 = base64.b64encode(f.read()).decode("utf-8")
            return {"status": "ok", "audio": audio_base64}
        except Exception as e:
            return {"status": "error", "message": str(e), "trace": traceback.format_exc()}

    # ------------------ Database ------------------
    def create_avatar(self, name, base64_image):
        conn = sqlite3.connect('avatars.db')
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO avatars (name, image_base64, voice_model)
        VALUES (?, ?, ?)
        ''', (name, base64_image, ''))
        conn.commit()
        conn.close()

    def get_avatars(self):
        conn = sqlite3.connect('avatars.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, image_base64, created_at, voice_model FROM avatars')
        avatars = cursor.fetchall()
        conn.close()
        return [{'id':a[0],'name':a[1],'image':a[2],'created_at':a[3],'model':a[4]} for a in avatars]

    def save_model_to_database(self, path, avatar_name):
        conn = sqlite3.connect("avatars.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE avatars SET voice_model=? WHERE name=?", (path, avatar_name))
        conn.commit()
        conn.close()

    def change_avatar_name(self, old_name, new_name):
        conn = sqlite3.connect("avatars.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE avatars SET name=? WHERE name=?", (new_name, old_name))
        conn.commit()
        conn.close()

    def delete_avatar(self, name):
        conn = sqlite3.connect('avatars.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM avatars WHERE name = ?', (name,))
        conn.commit()
        conn.close()


if __name__ == '__main__':
    api = Api()
    window = webview.create_window('CartoonTalker', 'index.html', width=800, height=600, js_api=api)
    webview.start()
