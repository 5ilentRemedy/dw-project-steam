import subprocess
import sys


def main() -> None:
    subprocess.run([sys.executable, "-m", "streamlit", "run", "05_dashboard_streamlit.py"], check=True)


if __name__ == "__main__":
    main()

