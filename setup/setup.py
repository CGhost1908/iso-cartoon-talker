import webview
import subprocess
import os
import ctypes, sys
import pythoncom
import shutil
from win32com.shell import shell, shellcon
from win32com.client import Dispatch

class Api:
    def close(self):
        webview.windows[0].destroy()
    def log(self, text):
        js_code = f"appendOutput({text!r})"
        webview.windows[0].evaluate_js(js_code)

    def run_command(self, cmd, description=""):
        if description:
            self.log(description)
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True
            )
            for line in result.stdout.splitlines():
                self.log(line.strip())
                print(line.strip())
            return True
        except subprocess.CalledProcessError as e:
            for line in e.stdout.splitlines():
                self.log(line.strip())
                print(line.strip())
            self.log(f"Command failed: {' '.join(cmd)}")
            return False

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def install_iso(self):
        if not self.is_admin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            webview.windows[0].destroy()
            sys.exit()
            return

        if sys.version_info.major == 3 and sys.version_info.minor == 10:
            python_path = sys.executable
            print("Python 3.10 yolu:", python_path)
        else:
            webview.windows[0].evaluate_js("raiseError('Python 3.10 yüklü değil!')")
            return

        program_files = os.path.join(os.environ['ProgramFiles'])

        os.makedirs(program_files, exist_ok=True)
        os.chdir(program_files)
        iso_path = os.path.join(program_files, 'iso-cartoon-talker')

        if os.path.exists(iso_path):
            webview.windows[0].evaluate_js(r"raiseError('C:/Program Files/iso-cartoon-talker dizini zaten mevcut! Klasörü silip tekrar deneyin.')")
            return

        error_log = r"Error log:\n If you have problems, contact us and share this file.\n\n"

        #Install commands
        cmd1 = self.run_command([
            "git",
            "clone",
            "https://github.com/CGhost1908/iso-cartoon-talker.git"
        ], description="Cloning main repository...")

        os.chdir(iso_path)

        cmd2 = self.run_command([
            "pip",
            "install",
            "-r", "requirements.txt"
        ], description="Installing requirements...")

        cmd3 = self.run_command([
            "pip",
            "download",
            "torch==2.7.1+cu118", "--index-url", "https://download.pytorch.org/whl/cu118", "--no-deps"
        ], description="Downloading torch...")

        cmd4 = self.run_command([
            "pip",
            "download",
            "torchaudio==2.7.1+cu118", "--index-url", "https://download.pytorch.org/whl/cu118", "--no-deps"
        ], description="Downloading torchaudio...")

        cmd5 = self.run_command([
            "pip",
            "download",
            "torchvision==0.22.1+cu118", "--index-url", "https://download.pytorch.org/whl/cu118", "--no-deps"
        ], description="Downloading torchvision...")

        # SDXL Setup
        cmd6 = self.run_command([
            "python",
            "-m",
            "venv",
            "env_sdxl"
        ], description="Creating environment for SDXL...")

        cmd7 = self.run_command([
            "env_sdxl/Scripts/pip.exe",
            "install",
            "torch-2.7.1+cu118-cp310-cp310-win_amd64.whl"
        ], description="Installing torch...")

        cmd8 = self.run_command([
            "env_sdxl/Scripts/pip.exe",
            "install",
            "torchaudio-2.7.1+cu118-cp310-cp310-win_amd64.whl"
        ], description="Installing torchaudio...")

        cmd9 = self.run_command([
            "env_sdxl/Scripts/pip.exe",
            "install",
            "torchvision-0.22.1+cu118-cp310-cp310-win_amd64.whl"
        ], description="Installing torchvision...")

        if not (cmd7 or cmd8 or cmd9):
            cmd9_1 = self.run_command([
                "env_sdxl/Scripts/pip.exe",
                "install",
                "torch==2.7.1",
                "torchvision==0.22.1",
                "torchaudio==2.7.1",
                "--index-url",
                "https://download.pytorch.org/whl/cu118", "--no-deps"
            ], description="Installing torch...")

        cmd10 = self.run_command([
            "env_sdxl/Scripts/pip.exe",
            "install",
            "diffusers==0.34.0",
            "huggingface_hub==0.34.3",
            "pillow==11.3.0",
            "transformers==4.54.1",
            "accelerate==1.9.0",
            "typing-extensions==4.15"
        ], description="Installing requirements for SDXL...")

        #SoftVC Setup
        cmd11 = self.run_command([
            "python",
            "-m",
            "venv",
            "env_softvc"
        ], description="Creating environment for SoftVC...")

        cmd12 = self.run_command([
            "env_softvc/Scripts/python.exe",
            "-m",
            "pip",
            "install",
            "-U",
            "pip",
            "setuptools",
            "wheel"
        ], description="Installing requirements for SoftVC...")

        cmd13 = self.run_command([
            "env_softvc/Scripts/pip.exe",
            "install",
            "torch-2.7.1+cu118-cp310-cp310-win_amd64.whl"
        ], description="Installing torch...")

        cmd14 = self.run_command([
            "env_softvc/Scripts/pip.exe",
            "install",
            "torchaudio-2.7.1+cu118-cp310-cp310-win_amd64.whl"
        ], description="Installing torchaudio...")

        if not (cmd13 or cmd14):
            cmd14_1 = self.run_command([
                "env_softvc/Scripts/pip.exe",
                "install",
                "torch==2.7.1",
                "torchaudio==2.7.1",
                "--index-url",
                "https://download.pytorch.org/whl/cu118"
            ], description="Installing torch...")

        cmd15 = self.run_command([
            "env_softvc/Scripts/pip.exe",
            "install",
            "matplotlib==3.7.1",
            "psutil==7.0.0"
        ], description="Installing matplotlib...")

        cmd16 = self.run_command([
            "env_softvc/Scripts/pip.exe",
            "install",
            "-U",
            "so-vits-svc-fork"
        ], description="Installing so-vits-svc-fork...")

        # Coqui TTS Setup
        cmd17 = self.run_command([
            "python",
            "-m",
            "venv",
            "env_coqui"
        ], description="Creating environment for Coqui TTS...")

        cmd18 = self.run_command([
            "git",
            "clone",
            "https://github.com/coqui-ai/TTS"
        ], description="Cloning Coqui TTS repository...")

        cmd19 = self.run_command([
            "env_coqui/Scripts/pip.exe",
            "install",
            "-r",
            "TTS/requirements.txt"
        ], description="Installing requirements...")

        cmd20 = self.run_command([
            "env_coqui/Scripts/pip.exe",
            "install",
            "torch==2.4.1",
            "torchvision==0.19.1",
            "torchaudio==2.4.1",
            "--index-url", "https://download.pytorch.org/whl/cu118"
        ], description="Installing torch...")

        cmd21 = self.run_command([
            "env_coqui/Scripts/pip.exe",
            "install",
            "sympy==1.12",
            "TTS==0.22.0",
            "transformers==4.33.2"
        ], description="Installing requirements...")

        # SadTalker Setup
        cmd22 = self.run_command([
            "python",
            "-m",
            "venv",
            "env_sadtalker"
        ], description="Creating environment for SadTalker...")

        cmd23 = self.run_command([
            "git",
            "clone",
            "https://github.com/OpenTalker/SadTalker"
        ], description="Cloning Coqui TTS repository...")

        cmd24 = self.run_command([
            "env_sadtalker/Scripts/pip.exe",
            "install",
            "ffmpeg"
        ], description="Installing ffmpeg...")

        cmd25 = self.run_command([
            "env_sadtalker/Scripts/pip.exe",
            "install",
            "-r",
            "SadTalker/requirements.txt"
        ], description="Installing requirements...")

        cmd26 = self.run_command([
            "env_sadtalker/Scripts/pip.exe",
            "install",
            "torch==1.12.1+cu113",
            "torchvision==0.13.1+cu113",
            "torchaudio==0.12.1 ",
            "--extra-index-url", "https://download.pytorch.org/whl/cu113"
        ], description="Installing torch...")

        cmd27 = self.run_command([
            "pip",
            "cache",
            "purge"
        ], description="Cleaning cache...")

        try:
            self.log("Modifying inference.py...")
            inference_path = "SadTalker/inference.py"
            with open(inference_path, "r", encoding="utf-8") as f:
                content = f.read()

            content = content.replace("src/config", "SadTalker/src/config")

            with open(inference_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            error_log += f"Error modifying inference.py: {e}\n"
            [ self.log(f"Error modifying inference.py! That is important please read documentation!: {e}") for _ in range(30) ]

        try:
            src = "inference_api.py"
            dst = os.path.join("SadTalker", "inference_api.py")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)

            self.log(f"inference_api.py moved to SadTalker.")
        except Exception as e:
            error_log += f"Error moving inference_api.py: {e}\n"
            [ self.log(f"Error moving inference_api.py! That is important please read documentation!: {e}") for _ in range(30) ]

        checkpoints_path = os.path.join(iso_path, "SadTalker", "checkpoints")
        os.makedirs(checkpoints_path, exist_ok=True)
        self.log(f"Created {checkpoints_path}")
        weights_path = os.path.join(iso_path, "SadTalker", "gfpgan", "weights")
        os.makedirs(weights_path, exist_ok=True)
        self.log(f"Created {weights_path}")
        train_base_models_path = os.path.join(iso_path, "train_base_models")
        os.makedirs(train_base_models_path, exist_ok=True)
        self.log(f"Created {train_base_models_path}")

        cmd28 = self.run_command([
            "bash",
            "models.sh"
        ], description="Downloading models...")

        folders = [
            checkpoints_path,
            weights_path,
            train_base_models_path,
            os.path.join(iso_path, "src")
        ]

        try:
            self.log("Fixing model files...")
            for folder_path in folders:
                if not os.path.exists(folder_path):
                    continue

                for filename in os.listdir(folder_path):
                    old_path = os.path.join(folder_path, filename)
              
                    if not os.path.isfile(old_path):
                        continue

                    new_name = filename

                    if ".safetensors" in filename.lower():
                        if not filename.lower().endswith(".safetensors"):
                            new_name = os.path.splitext(filename)[0] + ".safetensors"
                    elif ".pth.tar" in filename.lower() or ".tar" in filename.lower():
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
                        self.log(f"Fixed extension: {filename} -> {new_name}")

        except Exception as e:
            error_log += f"Error fixing model files: {e}\n"
            [self.log(f"Error fixing model files! That is important please read documentation!: {e}") for _ in range(30)]

        current_dir = os.getcwd()
        for filename in os.listdir(current_dir):
            if filename.endswith(".whl"):
                file_path = os.path.join(current_dir, filename)
                try:
                    os.remove(file_path)
                    self.log(f"Deleted: {file_path}")
                except Exception as e:
                    self.log(f"Error deleting {file_path}: {e}")


        cmds = [cmd1, cmd2, cmd3, cmd4, cmd5, cmd6, cmd7, cmd8, cmd9, cmd10, cmd11, cmd12, cmd13, cmd14, cmd15, cmd16, cmd17, cmd18, cmd19, cmd20, cmd21, cmd22, cmd23, cmd24, cmd25, cmd26, cmd27, cmd28]
        for i, cmd in enumerate(cmds, start=1):
            if not cmd:
                error_log += f"{i}. Command failed.      "
            else:
                error_log += f"{i}. Command succeeded.      "

        error_log_path = os.path.join(iso_path, 'error_log.txt')
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(error_log)
        self.log(f"Error log written to {error_log_path}")

        try:
            shortcut = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'Cartoon Talker.lnk')
            target = os.path.join(iso_path, 'main.py')
            self.create_shortcut(target, shortcut)
        except Exception as e:
            [self.log(f"Error creating shortcut!: {e}") for _ in range(30)]

        self.log("Installation completed successfully!")
        webview.windows[0].evaluate_js("showFinishPage()")

    def create_shortcut(self, target_py, shortcut_path):
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        working_dir = os.path.dirname(target_py)
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = python_exe
        shortcut.Arguments = f'"{target_py}"'
        shortcut.WorkingDirectory = working_dir
        shortcut.IconLocation = python_exe
        shortcut.save()

        with open(shortcut_path, "rb") as f2:
            ba = bytearray(f2.read())

        ba[0x15] = ba[0x15] | 0x20

        with open(shortcut_path, "wb") as f3:
            f3.write(ba)

if __name__ == '__main__':
    api = Api()
    window = webview.create_window('ISO Cartoon Talker Setup', 'index.html', width=800, height=600, js_api=api)
    webview.start()
