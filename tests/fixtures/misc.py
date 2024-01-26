import pytest


@pytest.fixture
def mock_env_var(monkeypatch):
    monkeypatch.setenv("MYVAR", "5")
    monkeypatch.setenv("MYOTHERVAR", "37")
