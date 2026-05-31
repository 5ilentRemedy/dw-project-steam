import subprocess
import sys

from logging_config import setup_logging

logger = setup_logging("06_run_dashboard")


def main() -> None:
    logger.info("=" * 80)
    logger.info("STREAMLIT DASHBOARD LAUNCHER")
    logger.info("=" * 80)
    
    logger.info("Starting Streamlit server...")
    logger.info("Dashboard URL: http://localhost:8501")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("-" * 80)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "05_dashboard_streamlit.py"], check=True)
    except KeyboardInterrupt:
        logger.info("Streamlit server stopped by user")
    except Exception as e:
        logger.error(f"✗ Error starting Streamlit: {e}")
        raise


if __name__ == "__main__":
    main()

