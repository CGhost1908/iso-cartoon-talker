import base64
import json
import os
import random
import shutil
import sqlite3
import string
import subprocess
import sys
import tempfile
import traceback
import wave
from io import BytesIO
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from PIL import Image


ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

MODELS_PATH = ROOT / "models"
TMP_DIR = ROOT / "tmp"
DATA_DIR = ROOT / "data"
DATABASE_PATH = DATA_DIR / "avatars.db"
CONFIG_PATH = ROOT / "configs" / "softvc_config.json"
SADTALKER_DIR = Path(os.environ.get("SADTALKER_DIR", "/opt/external/SadTalker"))

MODELS_PATH.mkdir(exist_ok=True)
TMP_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


def ensure_sample_voice() -> None:
    sample_path = ROOT / "src" / "sample_voice.wav"
    if sample_path.exists():
        return

    sample_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 22050
    duration = 1.0
    frequency = 220.0
    amplitude = 16000
    total_frames = int(sample_rate * duration)

    with wave.open(str(sample_path), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for index in range(total_frames):
            value = int(amplitude * __import__("math").sin(2 * __import__("math").pi * frequency * index / sample_rate))
            wav_file.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))


def initialize_database() -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS avatars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                image_base64 TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                voice_model TEXT DEFAULT ''
            )
            """
        )
        conn.commit()


ensure_sample_voice()
initialize_database()


class Api:
    def __init__(self):
        self._captured_logs = None
        self.live_logs = []

    def _begin_logs(self):
        self._captured_logs = []

    def _with_logs(self, result):
        logs = self._captured_logs or []
        self._captured_logs = None
        if isinstance(result, dict):
            result.setdefault("logs", logs)
            return result
        return {"status": "ok", "message": str(result), "logs": logs}

    def log(self, text):
        self.live_logs.append(str(text))
        if len(self.live_logs) > 2000:
            self.live_logs = self.live_logs[-1000:]
        if self._captured_logs is not None:
            self._captured_logs.append(str(text))
        print(text, flush=True)

    def _decode_base64_payload(self, payload, field_name):
        if payload is None:
            raise ValueError(f"{field_name} is empty (None).")
        if not isinstance(payload, str):
            raise ValueError(f"{field_name} must be a base64 string.")

        raw = payload.split(",", 1)[1] if payload.startswith("data:") else payload
        raw = raw.strip()
        if not raw:
            raise ValueError(f"{field_name} is empty.")

        try:
            return base64.b64decode(raw)
        except Exception as exc:
            raise ValueError(f"{field_name} is not valid base64.") from exc

    def run_command(self, cmd, description="", env_vars=None):
        if description:
            self.log(description)

        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        env.setdefault("PYTHONIOENCODING", "utf-8")

        process = subprocess.Popen(
            cmd,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )

        lines = []
        assert process.stdout is not None
        for line in process.stdout:
            clean = line.rstrip()
            lines.append(clean)
            self.log(clean)

        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode,
                cmd,
                output="\n".join(lines),
            )

    def run_python(self):
        return os.environ.get("APP_PYTHON", sys.executable)

    def coqui_python(self):
        return os.environ.get("COQUI_PYTHON", self.run_python())

    def sdxl_python(self):
        return os.environ.get("SDXL_PYTHON", self.run_python())

    def sadtalker_python(self):
        return os.environ.get("SADTALKER_PYTHON", self.run_python())

    def softvc_cli(self):
        return os.environ.get("SOFTVC_CLI", "svc")

    def softvc_env(self, extra=None):
        env = {
            "TORCHAUDIO_USE_SOUNDFILE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTORCH_NVRTC_LOG_LEVEL": "0",
        }

        site_packages = ROOT / "env_softvc" / "lib" / "python3.10" / "site-packages"
        cuda_libs = [
            site_packages / "nvidia" / "cu13" / "lib",
            site_packages / "nvidia" / "cuda_nvrtc" / "lib",
            site_packages / "nvidia" / "cuda_runtime" / "lib",
        ]
        existing = os.environ.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = ":".join([str(path) for path in cuda_libs if path.exists()] + ([existing] if existing else []))

        if extra:
            env.update(extra)
        return env

    def prepare_filelists(self):
        self.run_command([
            self.run_python(),
            "generate_filelists.py",
        ], description="Preparing train/val/test filelists...")

    def _update_softvc_config(self, epoch):
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)

        config["train"]["epochs"] = int(epoch)
        config["data"]["training_files"] = (TMP_DIR / "filelists" / "train.txt").as_posix()
        config["data"]["validation_files"] = (TMP_DIR / "filelists" / "val.txt").as_posix()

        with CONFIG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=4)

    def run_cartoon_talker(self, image_base64, target_audio, model_path, width, height):
        self._begin_logs()
        output_dir = ROOT / "output"
        output_dir.mkdir(exist_ok=True)
        final_audio_path = TMP_DIR / "target_voice_to_source_voice.wav"

        try:
            target_audio_bytes = self._decode_base64_payload(target_audio, "target_audio")
            image_bytes = self._decode_base64_payload(image_base64, "image_base64")

            target_path = TMP_DIR / "target_voice.wav"
            target_path.write_bytes(target_audio_bytes)

            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            image_path = Path(tmp_file.name)
            image_path.write_bytes(image_bytes)

            if model_path:
                self.run_command([
                    self.softvc_cli(),
                    "infer",
                    str(target_path),
                    "-o", str(final_audio_path),
                    "-m", model_path,
                    "-c", str(CONFIG_PATH),
                ], description="Cloning sound...", env_vars=self.softvc_env())
            else:
                final_audio_path = target_path

            self.run_command([
                self.sadtalker_python(),
                "run_sadtalker.py",
                str(image_path),
                str(final_audio_path),
                str(output_dir),
            ], description="Running SadTalker animation...")

            videos = sorted(output_dir.rglob("*.mp4"), key=lambda path: path.stat().st_mtime, reverse=True)
            if not videos:
                return self._with_logs({"status": "ok", "message": "Process completed, but no mp4 output was found."})

            video_path = videos[0]
            video_url = "/" + video_path.relative_to(ROOT).as_posix()
            return self._with_logs({"status": "ok", "message": "Process completed.", "video": video_url})
        except ValueError as exc:
            self.log(str(exc))
            return self._with_logs({"status": "error", "message": str(exc)})
        except subprocess.CalledProcessError as exc:
            details = exc.output or ""
            if details:
                self.log(details)
            return self._with_logs({"status": "error", "message": str(exc), "details": details, "trace": traceback.format_exc()})
        except Exception as exc:
            trace = traceback.format_exc()
            self.log(trace)
            return self._with_logs({"status": "error", "message": str(exc), "trace": trace})

    def cartoonize_avatar(self, image, width, height):
        try:
            self._begin_logs()
            image_data = base64.b64decode(image.split(",")[-1])
            avatar_image = Image.open(BytesIO(image_data)).convert("RGB")
            temp_path = TMP_DIR / "temp_avatar.png"
            output_path = TMP_DIR / "cartoonize_photo.png"
            avatar_image.save(temp_path)

            self.run_command([
                self.sdxl_python(),
                "run_sdxl.py",
                str(temp_path),
                str(width),
                str(height),
                str(output_path),
            ], description="Generating cartoon image...")

            try:
                rel = output_path.relative_to(ROOT)
                image_url = f"/{rel.as_posix()}"
            except Exception:
                image_url = f"/tmp/{output_path.name}"

            return self._with_logs({"status": "ok", "image": image_url, "message": f"Cartoonized image saved to {image_url}"})
        except subprocess.CalledProcessError as exc:
            details = exc.output or ""
            if details:
                self.log(details)
            return self._with_logs({"status": "error", "message": str(exc), "details": details, "trace": traceback.format_exc()})
        except Exception as exc:
            trace = traceback.format_exc()
            self.log(trace)
            return self._with_logs({"status": "error", "message": str(exc), "trace": trace})

    def voice_train(self, audio_base64, epoch, avatar_name):
        self._begin_logs()
        source_dir = TMP_DIR / "dataset_raw_raw"
        dataset_raw_dir = TMP_DIR / "dataset_raw"
        dataset_dir = TMP_DIR / "dataset"
        filelists_dir = TMP_DIR / "filelists"
        avatar_dir = dataset_dir / avatar_name

        try:
            for directory in [source_dir, dataset_raw_dir, dataset_dir, filelists_dir, avatar_dir]:
                directory.mkdir(parents=True, exist_ok=True)

            audio_path = source_dir / "train_input.wav"
            audio_path.write_bytes(base64.b64decode(audio_base64))

            self.log("Copying base models...")
            for filename in ["G_0.pth", "D_0.pth"]:
                shutil.copy(ROOT / "train_base_models" / filename, TMP_DIR)

            self.run_command([
                self.softvc_cli(),
                "pre-split",
                "-i", str(source_dir),
                "-o", str(dataset_raw_dir),
            ], description="Pre-splitting dataset...", env_vars=self.softvc_env())

            for filename in os.listdir(dataset_raw_dir):
                src_file = dataset_raw_dir / filename
                dst_file = avatar_dir / filename
                if src_file.is_file():
                    shutil.copy2(src_file, dst_file)

            self.prepare_filelists()

            self.run_command([
                self.softvc_cli(),
                "pre-config",
                "-i", str(dataset_dir),
                "-f", str(filelists_dir),
                "-c", str(CONFIG_PATH),
            ], description="Pre-configuring...", env_vars=self.softvc_env())

            self._update_softvc_config(epoch)

            self.run_command([
                self.softvc_cli(),
                "pre-hubert",
                "-i", str(dataset_dir),
                "-c", str(CONFIG_PATH),
            ], description="Running pre-hubert...", env_vars=self.softvc_env())

            self.run_command([
                self.softvc_cli(),
                "train", "-t",
                "-c", str(CONFIG_PATH),
                "-m", str(TMP_DIR),
                "-nt",
            ], description="Training model...", env_vars=self.softvc_env())

            model_path = TMP_DIR / f"G_{epoch}.pth"
            rand_str = "".join(random.choices(string.ascii_letters + string.digits, k=6))
            dst_path = MODELS_PATH / f"{avatar_name}_{rand_str}.pth"
            shutil.move(str(model_path), dst_path)
            return self._with_logs({"status": "ok", "path": dst_path.as_posix(), "message": f"Voice model saved to {dst_path.as_posix()}"})
        except subprocess.CalledProcessError as exc:
            details = exc.output or ""
            if details:
                self.log(details)
            return self._with_logs({"status": "error", "message": str(exc), "details": details, "trace": traceback.format_exc()})
        except Exception as exc:
            trace = traceback.format_exc()
            self.log(trace)
            return self._with_logs({"status": "error", "message": str(exc), "trace": trace})

    def run_tts(self, text):
        output_file = TMP_DIR / "tts.wav"
        try:
            self.run_command([
                self.coqui_python(),
                "run_coqui.py",
                "--text", text,
                "--speaker_wav", str(ROOT / "src" / "sample_voice.wav"),
                "--language", "tr",
                "--output", str(output_file),
            ], description="Running TTS...")

            if not output_file.exists():
                raise FileNotFoundError("TTS output file was not created.")

            return {"status": "ok", "audio": base64.b64encode(output_file.read_bytes()).decode("utf-8")}
        except subprocess.CalledProcessError as exc:
            details = exc.output or ""
            if details:
                self.log(details)
            return {"status": "error", "message": str(exc), "details": details, "trace": traceback.format_exc()}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "trace": traceback.format_exc()}

    def create_avatar(self, name, base64_image):
        # If the client passed a server-side path (e.g. "/tmp/cartoonize_photo.png"),
        # read that file and convert to a data URL before saving.
        image_to_store = base64_image
        try:
            if isinstance(base64_image, str) and (base64_image.startswith('/') or base64_image.startswith('tmp/')):
                possible = ROOT / base64_image.lstrip('/')
                if possible.is_file():
                    try:
                        img = Image.open(possible)
                        fmt = (img.format or 'PNG').lower()
                        mime = f'image/{fmt}'
                    except Exception:
                        mime = 'image/png'

                    b = possible.read_bytes()
                    image_to_store = f"data:{mime};base64,{base64.b64encode(b).decode('utf-8')}"
        except Exception:
            # If anything goes wrong, fall back to the original value the client provided
            image_to_store = base64_image

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO avatars (name, image_base64, voice_model) VALUES (?, ?, ?)",
                (name, image_to_store, ""),
            )
            conn.commit()

    def get_avatars(self):
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, image_base64, created_at, voice_model FROM avatars")
            avatars = cursor.fetchall()

        return [
            {"id": row[0], "name": row[1], "image": row[2], "created_at": row[3], "model": row[4]}
            for row in avatars
        ]

    def save_model_to_database(self, path, avatar_name):
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE avatars SET voice_model=? WHERE name=?", (path, avatar_name))
            conn.commit()

    def change_avatar_name(self, old_name, new_name):
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE avatars SET name=? WHERE name=?", (new_name, old_name))
            conn.commit()

    def delete_avatar(self, name):
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM avatars WHERE name = ?", (name,))
            conn.commit()

    def get_voice_embedding(self, base64_audio):
        return {"status": "unsupported", "message": "Voice embedding is not implemented in Docker mode."}

    def processBase64Audio(self, base64_audio):
        return base64_audio


api = Api()
app = Flask(__name__)


@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/logs")
def logs():
    offset_arg = request.args.get("offset", "0")
    if offset_arg == "latest":
        offset = len(api.live_logs)
    else:
        try:
            offset = max(0, int(offset_arg))
        except ValueError:
            offset = 0

    entries = api.live_logs[offset:]
    return jsonify({"offset": offset + len(entries), "entries": entries})


@app.post("/api/<method_name>")
def call_api(method_name):
    method = getattr(api, method_name, None)
    if not callable(method):
        return jsonify({"ok": False, "error": f"Unknown method: {method_name}"}), 404

    payload = request.get_json(silent=True) or {}
    args = payload.get("args", [])
    kwargs = payload.get("kwargs", {})

    try:
        result = method(*args, **kwargs)
        return jsonify({"ok": True, "result": result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc), "trace": traceback.format_exc()}), 500


@app.get("/<path:requested_path>")
def static_files(requested_path):
    file_path = ROOT / requested_path
    if file_path.is_file():
        return send_from_directory(ROOT, requested_path)
    return send_from_directory(ROOT, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
