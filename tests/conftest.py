import pytest
import os
import socket
import tempfile
import subprocess
import sys
import time


def wait_for_port(port, host="127.0.0.1", timeout=5.0):
    """Wait until a port starts accepting TCP connections."""
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                return False


@pytest.fixture(scope="session")
def fake_server():
    """Starts the fake Gemini server in a background process."""
    log_file = open("fake_server.log", "w")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "tests.fake_server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
            "--log-level",
            "error",
        ],
        stdout=log_file,
        stderr=log_file,
    )

    if not wait_for_port(8001):
        proc.terminate()
        log_file.close()
        raise RuntimeError("Fake server failed to start")

    os.environ["GEMINI_API_BASE_URL"] = "http://127.0.0.1:8001"
    os.environ["GEMINI_API_KEY"] = "fake-key"

    yield "http://127.0.0.1:8001"

    proc.terminate()
    proc.wait()
    log_file.close()


@pytest.fixture
def temp_db(monkeypatch):
    """Provides a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    monkeypatch.setenv("RESEARCH_DB_PATH", db_path)

    import research

    # Ensure the module uses the new path from env var
    research.DB_PATH = db_path
    research.init_db()

    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)
