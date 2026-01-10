import pytest
import os
import sqlite3
import tempfile
import subprocess
import sys
import time
import uvicorn
from pathlib import Path
from tests.fake_server import app

@pytest.fixture(scope="session")
def fake_server():
    """Starts the fake Gemini server in a background process."""
    log_file = open("fake_server.log", "w")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "tests.fake_server:app", "--host", "127.0.0.1", "--port", "8001", "--log-level", "error"],
        stdout=log_file,
        stderr=log_file
    )
    
    # Wait for server to be ready
    time.sleep(2)
    
    os.environ["GEMINI_API_BASE_URL"] = "http://127.0.0.1:8001"
    os.environ["GEMINI_API_KEY"] = "fake-key"
    
    yield "http://127.0.0.1:8001"
    
    proc.terminate()
    proc.wait()
    log_file.close()

@pytest.fixture
def temp_db():
    """Provides a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    os.environ["RESEARCH_DB_PATH"] = db_path
    
    import research
    # Reload or re-assign to ensure the module uses the new path
    research.DB_PATH = db_path
    research.init_db()
    
    yield db_path
    
    if os.path.exists(db_path):
        os.remove(db_path)
    # Don't delete env var yet as other tests might need it, but it's fine for now