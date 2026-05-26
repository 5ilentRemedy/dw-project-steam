import os
import subprocess
import sys
import venv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def run(command):
    print(f"> {' '.join(str(part) for part in command)}")
    subprocess.run(command, check=True)


def main() -> None:
    if not REQUIREMENTS.exists():
        raise FileNotFoundError(f"Missing {REQUIREMENTS}")

    if not VENV_DIR.exists():
        print(f"Creating virtual environment: {VENV_DIR}")
        venv.create(VENV_DIR, with_pip=True)
    else:
        print(f"Virtual environment already exists: {VENV_DIR}")

    python = venv_python()
    run([python, "-m", "pip", "install", "--upgrade", "pip"])
    run([python, "-m", "pip", "install", "-r", REQUIREMENTS])

    print("\nDone.")
    if os.name == "nt":
        print(r"Activate with: .\.venv\Scripts\Activate.ps1")
    else:
        print("Activate with: source .venv/bin/activate")


if __name__ == "__main__":
    main()

