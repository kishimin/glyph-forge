from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_production_dependencies_are_runtime_only() -> None:
    requirements = (PROJECT_ROOT / "requirements-prod.txt").read_text(encoding="utf-8")

    assert requirements.splitlines() == [
        "anyio==4.2.0",
        "fastapi==0.138.1",
        "pillow==10.3.0",
        "python-multipart==0.0.20",
        "uvicorn==0.30.1",
    ]


def test_container_runs_the_api_as_a_non_root_user() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert dockerfile.count("FROM python:3.12.11-slim-bookworm") == 2
    assert "USER app" in dockerfile
    assert "EXPOSE 8080" in dockerfile
    assert (
        'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", ' '"--port", "8080"]'
    ) in dockerfile
    assert "--reload" not in dockerfile
    assert "pip install -e" not in dockerfile


def test_container_context_excludes_development_artifacts() -> None:
    ignored_paths = set(
        (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    )

    assert {
        ".git",
        ".github",
        ".pytest_cache",
        "**/__pycache__",
        "tests",
        "input",
        "output",
        ".env",
        ".env.*",
        "requirements.txt",
    } <= ignored_paths
