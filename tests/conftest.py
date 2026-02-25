import pytest
import os
import socket
import tempfile
import subprocess
import sys
import time
from unittest.mock import MagicMock

import importlib

# Mock missing dependencies to allow tests to run without internet
mock_modules = [
    "google",
    "google.genai",
    "dotenv",
    "rich",
    "rich.console",
    "rich.markdown",
    "rich.panel",
    "rich.table",
    "rich.progress",
]

for mod in mock_modules:
    if mod not in sys.modules:
        try:
            importlib.import_module(mod)
        except ImportError:
            sys.modules[mod] = MagicMock()


# Improve mocks for Rich to allow CLI tests to pass
class MockConsole:
    def print(self, *args, **kwargs):
        for arg in args:
            sys.stdout.write(str(arg) + "\n")

    def print_exception(self, *args, **kwargs):
        import traceback

        sys.stdout.write("Exception occurred\n")
        traceback.print_exc(file=sys.stdout)

    @property
    def get_time(self):
        import time

        return time.time


class MockTable:
    def __init__(self, *args, **kwargs):
        self.title = kwargs.get("title", "")
        self.rows = []

    def add_column(self, *args, **kwargs):
        pass

    def add_row(self, *args):
        self.rows.append(args)

    def __str__(self):
        res = [self.title]
        for row in self.rows:
            res.append(" | ".join(map(str, row)))
        return "\n".join(res)


class MockPanel:
    def __init__(self, content, *args, **kwargs):
        self.content = content
        self.title = kwargs.get("title", "")

    def __str__(self):
        return f"Panel: {self.title}\n{self.content}"


class MockMarkdown:
    def __init__(self, content, *args, **kwargs):
        self.content = content

    def __str__(self):
        return f"Markdown:\n{self.content}"


class MockProgress:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def add_task(self, *args, **kwargs):
        return 1

    def update(self, *args, **kwargs):
        pass


class MockColumn:
    def __init__(self, *args, **kwargs):
        pass


sys.modules["rich.console"].Console = MockConsole  # type: ignore
sys.modules["rich.table"].Table = MockTable  # type: ignore
sys.modules["rich.panel"].Panel = MockPanel  # type: ignore
sys.modules["rich.markdown"].Markdown = MockMarkdown  # type: ignore
sys.modules["rich.progress"].Progress = MockProgress  # type: ignore
sys.modules["rich.progress"].SpinnerColumn = MockColumn  # type: ignore
sys.modules["rich.progress"].TextColumn = MockColumn  # type: ignore


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
    os.environ["RESEARCH_GEMINI_API_KEY"] = "fake-key"

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
    monkeypatch.setenv("RESEARCH_GEMINI_API_KEY", "fake-key")

    import research_cli
    import research_cli.config

    # Ensure the module uses the new path from env var
    research_cli.DB_PATH = db_path
    research_cli.config.DB_PATH = db_path
    research_cli.init_db()

    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)
