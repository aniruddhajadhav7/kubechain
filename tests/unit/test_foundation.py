"""Foundation validation test suite for Phase 0."""

import sys
from pathlib import Path


def test_python_version_compatibility() -> None:
    """Assert minimum supported Python runtime version (>= 3.12)."""
    assert sys.version_info >= (3, 12), f"Unsupported Python version: {sys.version}"


def test_repository_directory_structure() -> None:
    """Verify that all core top-level directories exist."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    required_dirs = [
        "api",
        "operator",
        "gateway",
        "node_manager",
        "deploy",
        "observability",
        "chaos",
        "infra",
        "tests",
        "docs",
        ".github",
    ]

    for d in required_dirs:
        dir_path = repo_root / d
        assert dir_path.is_dir(), f"Expected directory '{d}' does not exist at {dir_path}"


def test_core_documentation_and_adrs_exist() -> None:
    """Verify that architecture documentation and ADRs exist."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    required_files = [
        repo_root / "README.md",
        repo_root / "LICENSE",
        repo_root / "pyproject.toml",
        repo_root / ".gitignore",
        repo_root / ".env.example",
        repo_root / "docs" / "architecture" / "system-overview.md",
        repo_root / "docs" / "architecture" / "system-design.md",
        repo_root / "docs" / "architecture" / "component-design.md",
        repo_root / "docs" / "architecture" / "data-flow.md",
        repo_root / "docs" / "architecture" / "security-model.md",
        repo_root / "docs" / "architecture" / "testing-strategy.md",
        repo_root / "docs" / "ROADMAP.md",
        repo_root / "docs" / "decisions" / "001-initial-architecture.md",
        repo_root / "docs" / "decisions" / "ADR-001-operator-framework.md",
        repo_root / "docs" / "decisions" / "ADR-002-data-plane-isolation.md",
        repo_root / "docs" / "decisions" / "ADR-003-rpc-caching-retry-semantics.md",
    ]

    for f in required_files:
        assert f.is_file(), f"Expected required file '{f.name}' does not exist at {f}"
