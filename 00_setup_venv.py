import os
import subprocess
import sys
import venv
from pathlib import Path

from logging_config import setup_logging

logger = setup_logging("00_setup_venv")

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def run(command):
    logger.debug(f"Executing: {' '.join(str(part) for part in command)}")
    subprocess.run(command, check=True)


def main() -> None:
    logger.info("=" * 80)
    logger.info("STARTING VIRTUAL ENVIRONMENT SETUP")
    logger.info("=" * 80)
    
    if not REQUIREMENTS.exists():
        logger.error(f"Missing requirements file: {REQUIREMENTS}")
        raise FileNotFoundError(f"Missing {REQUIREMENTS}")

    if not VENV_DIR.exists():
        logger.info(f"Creating virtual environment at: {VENV_DIR}")
        try:
            venv.create(VENV_DIR, with_pip=True)
            logger.info("✓ Virtual environment created successfully")
        except Exception as e:
            logger.error(f"✗ Failed to create virtual environment: {e}")
            raise
    else:
        logger.info(f"Virtual environment already exists at: {VENV_DIR}")

    python = venv_python()
    logger.info(f"Python executable: {python}")
    
    logger.info("Upgrading pip...")
    run([python, "-m", "pip", "install", "--upgrade", "pip"])
    logger.info("✓ Pip upgraded")
    
    logger.info(f"Installing packages from {REQUIREMENTS}...")
    run([python, "-m", "pip", "install", "-r", REQUIREMENTS])
    logger.info("✓ All packages installed successfully")

    logger.info("=" * 80)
    logger.info("VIRTUAL ENVIRONMENT SETUP COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    if os.name == "nt":
        logger.info(r"Activate with: .\.venv\Scripts\Activate.ps1")
    else:
        logger.info("Activate with: source .venv/bin/activate")


if __name__ == "__main__":
    main()

