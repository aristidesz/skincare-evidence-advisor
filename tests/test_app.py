import atexit
import subprocess
import time

import pytest
import requests
from seleniumbase import BaseCase


def start_streamlit():
    """Start Streamlit server as a subprocess"""
    process = subprocess.Popen(
        ["streamlit", "run", "streamlit_app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Register cleanup function
    atexit.register(lambda: process.kill())

    # Wait for server to start
    for _ in range(5):
        try:
            response = requests.get("http://localhost:8501")
            if response.status_code == 200:
                return process
        except requests.exceptions.ConnectionError:
            time.sleep(1)

    raise RuntimeError("Failed to start Streamlit server")


@pytest.fixture(scope="session", autouse=True)
def streamlit_server():
    """Fixture to start and stop Streamlit server"""
    process = start_streamlit()
    yield
    process.kill()
    process.wait()


class VisualTest(BaseCase):
    @pytest.mark.e2e
    def test_app_runs(self):
        self.open("http://localhost:8501")
        self.wait_for_element("[data-testid=stAppViewContainer]", timeout=10)
        self.assert_element("[data-testid=stAppViewContainer]")
        self.check_window(
            name="streamlit_app", level=3, baseline=True  # Forces new baseline creation
        )
